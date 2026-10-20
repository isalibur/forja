"""Adaptador para narração pronta gravada pelo usuário com tolerância a divergências (05 §1)."""

from __future__ import annotations

import json
import shutil
import subprocess
import wave
from pathlib import Path
from typing import TYPE_CHECKING, Any

from docforja.audio.adaptadores.base import AdaptadorTTS
from docforja.audio.metricas import calcular_wer
from docforja.io import atomic_write_json

if TYPE_CHECKING:
    from docforja.audio.alinhamento import AlinhadorWhisperX
    from docforja.planejamento.entidades import SegmentoProcessado


class AdaptadorNarracaoPronta(AdaptadorTTS):
    """Adaptador para narração pronta gravada pelo usuário."""

    def __init__(self, arquivo_origem: Path) -> None:
        self.arquivo_origem = Path(arquivo_origem)

    def disponivel(self) -> bool:
        return self.arquivo_origem.exists()

    def gerar(
        self,
        texto: str,
        saida_wav: Path,
        voz: str | None = None,
        idioma: str = "pt-BR",
        velocidade: float = 1.0,
    ) -> Path:
        if not self.disponivel():
            raise FileNotFoundError(
                f"Arquivo de narração pronta não encontrado: {self.arquivo_origem}"
            )

        saida_wav.parent.mkdir(parents=True, exist_ok=True)

        # Padroniza a narração fornecida para WAV mono 24kHz 16-bit
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(self.arquivo_origem),
            "-ar",
            "24000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(saida_wav),
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Erro ao processar narração pronta com FFmpeg: {res.stderr}")

        return saida_wav


def processar_narracao_pronta_completa(
    arquivo_narracao: Path,
    pasta_audio: Path,
    idioma: str,
    segmentos_roteiro: list[SegmentoProcessado],
    alinhador: AlinhadorWhisperX | None = None,
    limite_divergencia_wer: float = 0.08,
    transcricao_mock: str | None = None,
) -> dict[str, Any]:
    """Processa áudio fornecido em 00_entrada/ e avalia divergência contra o roteiro (05 §1).

    Regra 05 §1: Se o áudio divergir do texto (WER > 8%, ex.: improviso do locutor),
    o sistema adota a transcrição como verdade para tempos e legendas e emite um aviso no plano.
    """
    if not arquivo_narracao.is_file():
        raise FileNotFoundError(f"Arquivo de narração pronta ausente: {arquivo_narracao}")

    pasta_audio.mkdir(parents=True, exist_ok=True)
    narracao_wav = pasta_audio / "narracao_completa.wav"

    # 1. Padroniza áudio para WAV mono 24kHz 16-bit com FFmpeg
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i",
            str(arquivo_narracao),
            "-ar",
            "24000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(narracao_wav),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0 and not narracao_wav.is_file():
            shutil.copyfile(arquivo_narracao, narracao_wav)
    else:
        shutil.copyfile(arquivo_narracao, narracao_wav)

    # Mede duração do WAV
    duracao_total_s = 0.0
    try:
        with wave.open(str(narracao_wav), "rb") as wf:
            duracao_total_s = wf.getnframes() / wf.getframerate()
    except Exception:
        duracao_total_s = float(len(segmentos_roteiro) * 3.0)

    # 2. Alinhamento e transcrição
    palavras_alinhadas: list[dict[str, Any]] = []
    texto_transcrito = transcricao_mock or ""

    if alinhador and alinhador.disponivel():
        saida_pal = pasta_audio / "palavras_temp.json"
        saida_seg = pasta_audio / "segs_temp.json"
        idioma_asr = idioma.split("-")[0].lower()
        try:
            alinhador.alinhar(
                audio_wav=narracao_wav,
                saida_palavras=saida_pal,
                saida_segmentos=saida_seg,
                idioma=idioma_asr,
            )
            if saida_pal.is_file():
                palavras_alinhadas = json.loads(saida_pal.read_text(encoding="utf-8"))
            if saida_seg.is_file():
                segs_asr = json.loads(saida_seg.read_text(encoding="utf-8"))
                texto_transcrito = " ".join(
                    s.get("text") or s.get("texto") or "" for s in segs_asr
                ).strip()
            saida_pal.unlink(missing_ok=True)
            saida_seg.unlink(missing_ok=True)
        except Exception:
            pass

    # 3. Cálculo de WER (Divergência textual)
    texto_referencia = " ".join(seg.texto_limpo for seg in segmentos_roteiro)
    wer = 0.0
    if texto_transcrito:
        wer = calcular_wer(texto_referencia, texto_transcrito, idioma=idioma)

    divergencia = wer > limite_divergencia_wer
    aviso: str | None = None
    if divergencia:
        aviso = (
            f"Divergência textual de {wer:.1%} entre áudio fornecido e roteiro "
            f"(tolerância de {limite_divergencia_wer:.0%} excedida). "
            "Transcrição adotada como verdade temporal e de legendas."
        )

    # 4. Monta os tempos dos segmentos
    segmentos_finais: list[dict[str, Any]] = []
    total_segs = max(1, len(segmentos_roteiro))
    total_palavras_ref = max(1, sum(len(s.texto_limpo.split()) for s in segmentos_roteiro))

    inicio_atual = 0.0
    for idx, seg in enumerate(segmentos_roteiro):
        # Distribuição proporcional baseada na contagem de palavras do segmento
        fracao = len(seg.texto_limpo.split()) / total_palavras_ref
        dur_seg = round(fracao * duracao_total_s, 3)
        if idx == total_segs - 1:
            dur_seg = round(duracao_total_s - inicio_atual, 3)

        fim_atual = round(inicio_atual + dur_seg, 3)
        texto_seg = seg.texto_limpo
        if divergencia and texto_transcrito:
            # Em caso de divergência > 8%, adota a transcrição como verdade
            partes_trans = texto_transcrito.split()
            ini_p = int(idx * (len(partes_trans) / total_segs))
            fim_p = int((idx + 1) * (len(partes_trans) / total_segs))
            if ini_p < len(partes_trans):
                texto_seg = " ".join(partes_trans[ini_p:fim_p])

        segmentos_finais.append({
            "id": seg.id,
            "texto": texto_seg,
            "inicio_s": inicio_atual,
            "fim_s": fim_atual,
            "duracao_s": dur_seg,
            "palavras": [
                {"palavra": p, "inicio": inicio_atual, "fim": fim_atual}
                for p in texto_seg.split()
            ],
        })
        inicio_atual = fim_atual

    # 5. Grava artefatos finais de áudio
    atomic_write_json(pasta_audio / "segmentos.json", segmentos_finais)
    atomic_write_json(pasta_audio / "palavras.json", palavras_alinhadas)
    atomic_write_json(
        pasta_audio / "qualidade.json",
        {
            "wer": round(wer, 4),
            "limite_wer": limite_divergencia_wer,
            "divergencia_detectada": divergencia,
            "aviso": aviso,
            "metodo": "narracao_pronta",
            "arquivo_origem": str(arquivo_narracao),
        },
    )

    return {
        "arquivo_completo_wav": narracao_wav,
        "duracao_total_s": duracao_total_s,
        "wer": wer,
        "divergencia_detectada": divergencia,
        "aviso": aviso,
        "segmentos": segmentos_finais,
    }
