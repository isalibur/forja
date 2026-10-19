from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from docforja.audio.adaptadores.base import AdaptadorTTS
from docforja.audio.adaptadores.kokoro import AdaptadorKokoro
from docforja.audio.alinhamento import AlinhadorWhisperX
from docforja.audio.cadeia import (
    aplicar_cadeia_voz,
    concatenar_audios,
    gerar_silencio_ou_room_tone,
)
from docforja.audio.pronuncia import aplicar_pronuncia
from docforja.planejamento.entidades import SegmentoProcessado


@dataclass
class ResultadoSegmentoAudio:
    id: str
    texto: str
    arquivo_wav: Path
    duracao_s: float
    wer: float | None = None
    takes: int = 1


@dataclass
class RelatorioNarracao:
    idioma: str
    arquivo_completo_wav: Path
    arquivo_palavras_json: Path
    arquivo_segmentos_json: Path
    duracao_total_s: float
    segmentos: list[ResultadoSegmentoAudio]
    wer_medio: float | None


class OrquestradorNarracao:
    """Orquestra a geracao de narracao por segmento, cadeia de audio e alinhamento."""

    def __init__(
        self,
        adaptador_tts: AdaptadorTTS | None = None,
        alinhador: AlinhadorWhisperX | None = None,
    ) -> None:
        self.tts = adaptador_tts or AdaptadorKokoro()
        self.alinhador = alinhador or AlinhadorWhisperX()

    def processar_segmento(
        self,
        segmento: SegmentoProcessado,
        pasta_destino: Path,
        idioma: str = "pt-BR",
        voz: str | None = None,
        velocidade: float = 1.0,
        max_tentativas: int = 2,
    ) -> ResultadoSegmentoAudio:
        pasta_destino.mkdir(parents=True, exist_ok=True)
        saida_bruta = pasta_destino / f"{segmento.id}_raw.wav"
        saida_processada = pasta_destino / f"{segmento.id}.wav"

        # 1. Aplica dicionario de pronuncia
        texto_fonetico = aplicar_pronuncia(segmento.texto_limpo, idioma=idioma)

        # 2. Sintetiza com TTS (tentando ate max_tentativas em caso de falha)
        tentativas = 0
        ultimo_erro = None
        while tentativas < max_tentativas:
            tentativas += 1
            try:
                self.tts.gerar(
                    texto=texto_fonetico,
                    saida_wav=saida_bruta,
                    voz=voz,
                    idioma=idioma,
                    velocidade=velocidade,
                )
                break
            except Exception as e:
                ultimo_erro = e

        if not saida_bruta.exists():
            raise RuntimeError(f"Falha ao gerar áudio para o segmento {segmento.id}: {ultimo_erro}")

        # 3. Aplica cadeia de voz FFmpeg (high-pass, presença, compressor)
        aplicar_cadeia_voz(saida_bruta, saida_processada)

        # 4. Se houver silêncio ou pausas após o segmento, anexa room tone
        arquivos_para_juntar = [saida_processada]
        if segmento.silencio_apos_s > 0:
            silencio_wav = pasta_destino / f"{segmento.id}_silence.wav"
            gerar_silencio_ou_room_tone(segmento.silencio_apos_s, silencio_wav)
            arquivos_para_juntar.append(silencio_wav)

        if len(arquivos_para_juntar) > 1:
            saida_final = pasta_destino / f"{segmento.id}_final.wav"
            concatenar_audios(arquivos_para_juntar, saida_final)
            saida_processada = saida_final

        # Limpa o arquivo temporario bruto
        if saida_bruta.exists():
            saida_bruta.unlink()

        # Mede duracao do arquivo gerado
        duracao = self._medir_duracao_wav(saida_processada)

        return ResultadoSegmentoAudio(
            id=segmento.id,
            texto=segmento.texto_limpo,
            arquivo_wav=saida_processada,
            duracao_s=duracao,
            # WER exige transcrição ASR independente; alinhamento forçado não
            # mede se o áudio corresponde ao roteiro.
            wer=None,
            takes=tentativas,
        )

    def processar_projeto_completo(
        self,
        segmentos: list[SegmentoProcessado],
        pasta_audio: Path,
        idioma: str = "pt-BR",
        voz: str | None = None,
        executar_alinhamento: bool = True,
    ) -> RelatorioNarracao:
        pasta_idioma = pasta_audio / idioma
        pasta_segs = pasta_idioma / "segmentos"
        pasta_segs.mkdir(parents=True, exist_ok=True)

        resultados_segs: list[ResultadoSegmentoAudio] = []
        arquivos_wavs: list[Path] = []
        segmentos_info = []
        tempo_acumulado = 0.0

        for seg in segmentos:
            res_seg = self.processar_segmento(seg, pasta_segs, idioma=idioma, voz=voz)
            resultados_segs.append(res_seg)
            arquivos_wavs.append(res_seg.arquivo_wav)

            fim_seg = round(tempo_acumulado + res_seg.duracao_s, 3)
            segmentos_info.append(
                {
                    "id": seg.id,
                    "texto": seg.texto_limpo,
                    "inicio_s": round(tempo_acumulado, 3),
                    "fim_s": fim_seg,
                }
            )
            tempo_acumulado = fim_seg

        # Concatena em um arquivo mestre de narração
        narracao_completa_wav = pasta_idioma / "narracao_completa.wav"
        concatenar_audios(arquivos_wavs, narracao_completa_wav)
        duracao_total = self._medir_duracao_wav(narracao_completa_wav)

        palavras_json = pasta_idioma / "palavras.json"
        segmentos_json = pasta_idioma / "segmentos.json"

        # Executa alinhamento WhisperX se disponivel
        if executar_alinhamento and self.alinhador.disponivel():
            lang_code = "pt" if "pt" in idioma.lower() else idioma[:2].lower()
            self.alinhador.alinhar(
                audio_wav=narracao_completa_wav,
                saida_palavras=palavras_json,
                saida_segmentos=segmentos_json,
                segmentos_info=segmentos_info,
                idioma=lang_code,
            )
        else:
            # Fallback determinístico sem GPU / modelo instalado
            with open(segmentos_json, "w", encoding="utf-8") as f:
                json.dump(segmentos_info, f, ensure_ascii=False, indent=2)

            palavras_estimadas = []
            for s in segmentos_info:
                palavras = s["texto"].split()
                if not palavras:
                    continue
                dt_p = (s["fim_s"] - s["inicio_s"]) / len(palavras)
                t_p = s["inicio_s"]
                for p in palavras:
                    palavras_estimadas.append(
                        {
                            "palavra": p,
                            "inicio_s": round(t_p, 3),
                            "fim_s": round(t_p + dt_p, 3),
                            "score": 1.0,
                            "segmento_id": s["id"],
                        }
                    )
                    t_p += dt_p

            with open(palavras_json, "w", encoding="utf-8") as f:
                json.dump(palavras_estimadas, f, ensure_ascii=False, indent=2)

        return RelatorioNarracao(
            idioma=idioma,
            arquivo_completo_wav=narracao_completa_wav,
            arquivo_palavras_json=palavras_json,
            arquivo_segmentos_json=segmentos_json,
            duracao_total_s=duracao_total,
            segmentos=resultados_segs,
            wer_medio=None,
        )

    def _medir_duracao_wav(self, wav_path: Path) -> float:
        import wave

        try:
            with wave.open(str(wav_path), "rb") as w:
                frames = w.getnframes()
                rate = w.getframerate()
                return round(frames / float(rate), 3)
        except Exception:
            return 0.0
