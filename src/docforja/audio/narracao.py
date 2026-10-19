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
from docforja.audio.metricas import calcular_wer
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
        velocidade: float = 1.0,
        executar_alinhamento: bool = True,
        limite_wer: float = 0.02,
        max_refacoes_qualidade: int = 1,
    ) -> RelatorioNarracao:
        pasta_idioma = pasta_audio / idioma
        pasta_segs = pasta_idioma / "segmentos"
        pasta_segs.mkdir(parents=True, exist_ok=True)

        resultados_segs: list[ResultadoSegmentoAudio] = []
        for seg in segmentos:
            res_seg = self.processar_segmento(
                seg, pasta_segs, idioma=idioma, voz=voz, velocidade=velocidade
            )
            resultados_segs.append(res_seg)

        # Concatena em um arquivo mestre de narração
        narracao_completa_wav = pasta_idioma / "narracao_completa.wav"
        segmentos_info = self._montar_segmentos_info(segmentos, resultados_segs)
        self._montar_narracao(resultados_segs, narracao_completa_wav)

        palavras_json = pasta_idioma / "palavras.json"
        segmentos_json = pasta_idioma / "segmentos.json"
        wer_medio: float | None = None

        # Executa alinhamento WhisperX se disponivel
        if executar_alinhamento and self.alinhador.disponivel():
            lang_code = "pt" if "pt" in idioma.lower() else idioma[:2].lower()
            # Primeiro transcreve sem fornecer o roteiro. Isso permite medir WER
            # contra uma hipótese independente, em vez de confundir alinhamento
            # forçado com reconhecimento correto.
            palavras_asr = pasta_idioma / "wer_palavras_temp.json"
            segmentos_asr = pasta_idioma / "wer_segmentos_temp.json"
            for rodada in range(max_refacoes_qualidade + 1):
                self.alinhador.alinhar(
                    audio_wav=narracao_completa_wav,
                    saida_palavras=palavras_asr,
                    saida_segmentos=segmentos_asr,
                    idioma=lang_code,
                )
                try:
                    transcricao = json.loads(segmentos_asr.read_text(encoding="utf-8"))
                finally:
                    palavras_asr.unlink(missing_ok=True)
                    segmentos_asr.unlink(missing_ok=True)

                referencia = " ".join(s.texto_limpo for s in segmentos)
                hipotese = " ".join(item.get("texto", "") for item in transcricao)
                wer_medio = calcular_wer(referencia, hipotese)
                self._atualizar_wer_segmentos(resultados_segs, segmentos_info, transcricao)

                reprovados = [
                    r for r in resultados_segs if r.wer is not None and r.wer > limite_wer
                ]
                if not reprovados or rodada >= max_refacoes_qualidade:
                    break

                segmentos_por_id = {s.id: s for s in segmentos}
                for resultado in reprovados:
                    anterior = resultado.takes
                    novo = self.processar_segmento(
                        segmentos_por_id[resultado.id],
                        pasta_segs,
                        idioma=idioma,
                        voz=voz,
                        velocidade=max(0.8, velocidade * 0.9),
                    )
                    novo.takes += anterior
                    resultados_segs[resultados_segs.index(resultado)] = novo

                segmentos_info = self._montar_segmentos_info(segmentos, resultados_segs)
                self._montar_narracao(resultados_segs, narracao_completa_wav)

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
            duracao_total_s=self._medir_duracao_wav(narracao_completa_wav),
            segmentos=resultados_segs,
            wer_medio=wer_medio,
        )

    @staticmethod
    def _montar_segmentos_info(
        segmentos: list[SegmentoProcessado], resultados: list[ResultadoSegmentoAudio]
    ) -> list[dict[str, str | float]]:
        info = []
        tempo = 0.0
        for segmento, resultado in zip(segmentos, resultados, strict=True):
            fim = round(tempo + resultado.duracao_s, 3)
            info.append(
                {
                    "id": segmento.id,
                    "texto": segmento.texto_limpo,
                    "inicio_s": round(tempo, 3),
                    "fim_s": fim,
                }
            )
            tempo = fim
        return info

    @staticmethod
    def _atualizar_wer_segmentos(
        resultados: list[ResultadoSegmentoAudio],
        segmentos_info: list[dict[str, str | float]],
        transcricao: list[dict],
    ) -> None:
        hipoteses = {resultado.id: [] for resultado in resultados}
        for item in transcricao:
            meio = (float(item.get("inicio_s", item.get("start", 0.0))) + float(
                item.get("fim_s", item.get("end", 0.0))
            )) / 2
            alvo = min(
                segmentos_info,
                key=lambda segmento: min(
                    abs(meio - float(segmento["inicio_s"])),
                    abs(meio - float(segmento["fim_s"])),
                    0.0
                    if float(segmento["inicio_s"]) <= meio <= float(segmento["fim_s"])
                    else float("inf"),
                ),
            )
            hipoteses[str(alvo["id"])].append(item.get("texto", ""))

        for resultado in resultados:
            resultado.wer = calcular_wer(
                resultado.texto, " ".join(hipoteses.get(resultado.id, []))
            )

    @staticmethod
    def _montar_narracao(
        resultados: list[ResultadoSegmentoAudio], destino: Path
    ) -> None:
        concatenar_audios([resultado.arquivo_wav for resultado in resultados], destino)

    def _medir_duracao_wav(self, wav_path: Path) -> float:
        import wave

        try:
            with wave.open(str(wav_path), "rb") as w:
                frames = w.getnframes()
                rate = w.getframerate()
                return round(frames / float(rate), 3)
        except Exception:
            return 0.0
