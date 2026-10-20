from __future__ import annotations

import subprocess
from pathlib import Path

DURACOES_PAUSAS_S: dict[str, float] = {
    "PAUSA-C": 0.4,
    "PAUSA-M": 0.75,
    "PAUSA-L": 1.5,
}


def gerar_silencio_ou_room_tone(
    duracao_s: float,
    saida_wav: Path,
    sample_rate: int = 24000,
    usar_room_tone: bool = True,
) -> Path:
    """Gera um arquivo de áudio com silêncio ou room tone imperceptível via FFmpeg."""
    saida_wav.parent.mkdir(parents=True, exist_ok=True)

    if usar_room_tone:
        # Gera ruido rosa baixissimo (-56 dB) com filtro passa-baixa em 1kHz
        # simulando ambiencia de sala tratada
        filtro = "anoisesrc=c=pink:r=24000:a=0.0008,lowpass=f=1000,volume=-56dB"
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            filtro,
            "-t",
            str(duracao_s),
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(saida_wav),
        ]
    else:
        # Silencio digital puro
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r={sample_rate}:cl=mono",
            "-t",
            str(duracao_s),
            "-c:a",
            "pcm_s16le",
            str(saida_wav),
        ]

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return saida_wav


def aplicar_cadeia_voz(
    entrada_wav: Path,
    saida_wav: Path,
    sample_rate: int = 24000,
) -> Path:
    """Aplica a cadeia padrao de processamento vocal do DocForja via FFmpeg.

    - Filtro passa-alta em 80 Hz (corta graves e rumbles indesejados)
    - Equalizador de presenca em 3.000 Hz (+2 dB)
    - Compressor de dinamica suave (threshold -18 dB, ratio 3:1)
    """
    saida_wav.parent.mkdir(parents=True, exist_ok=True)

    filtros = [
        # Redução espectral leve para hiss de síntese sem apagar consoantes.
        "afftdn=nr=6:nf=-50:tn=1",
        "highpass=f=80",
        "equalizer=f=3000:width_type=o:w=1:g=2",
        "acompressor=threshold=-18dB:ratio=3:attack=5:release=50",
    ]
    filtro_str = ",".join(filtros)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(entrada_wav),
        "-af",
        filtro_str,
        "-ar",
        str(sample_rate),
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(saida_wav),
    ]

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return saida_wav


def concatenar_audios(
    arquivos_wav: list[Path],
    saida_wav: Path,
    sample_rate: int = 24000,
) -> Path:
    """Concatena uma lista de arquivos de áudio WAV em um único arquivo de saída."""
    if not arquivos_wav:
        raise ValueError("Lista de arquivos para concatenacao vazia.")

    saida_wav.parent.mkdir(parents=True, exist_ok=True)

    if len(arquivos_wav) == 1:
        # Apenas converte/copia para a saida
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(arquivos_wav[0]),
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(saida_wav),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return saida_wav

    # Usa o concat demuxer do FFmpeg criando um arquivo temporario de lista
    lista_txt = saida_wav.with_suffix(".txt")
    with open(lista_txt, "w", encoding="utf-8") as f:
        for arq in arquivos_wav:
            f.write(f"file '{arq.resolve().as_posix()}'\n")

    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(lista_txt),
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(saida_wav),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        if lista_txt.exists():
            lista_txt.unlink()

    return saida_wav
