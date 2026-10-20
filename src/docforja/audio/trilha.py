"""Trilha sonora provisória para o animatic P8 e prévia do DocForja."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from docforja.io import atomic_write_json
from docforja.nucleo.projeto import Projeto

KIT_PADRAO_DIR = Path(__file__).resolve().parents[3] / "kits" / "cinza-e-brasa"


def gerar_trilha_provisoria_drone(
    saida_wav: Path,
    duracao_s: float = 30.0,
    sample_rate: int = 48000,
) -> Path:
    """Gera um drone ambiente documental suave e quente em 48 kHz estéreo.

    O áudio é loopável de forma perfeitamente contínua, com modulações lentas
    (LFOs) e harmônicos em Lá (55 Hz, 110 Hz, 165 Hz, 220 Hz) em nível moderado
    (-22 dBFS), ideal como cama musical provisória sob ducking.
    """
    saida_wav.parent.mkdir(parents=True, exist_ok=True)
    num_amostras = int(duracao_s * sample_rate)
    amplitude_base = 0.12  # ~ -18 dBFS de pico para harmonizar sob a narração

    # Frequências em Lá (A1 = 55 Hz, A2 = 110 Hz, E3 = 165 Hz, A3 = 220 Hz)
    f0 = 55.0
    f1 = 110.0
    f2 = 165.0
    f3 = 220.0

    buffer = bytearray()
    dois_pi = 2.0 * math.pi

    for i in range(num_amostras):
        t = i / sample_rate
        # Envelope de ciclo para loop perfeito
        # LFOs lentos para movimento orgânico
        lfo1 = 0.8 + 0.2 * math.sin(dois_pi * (1.0 / duracao_s) * 2 * t)
        lfo2 = 0.8 + 0.2 * math.cos(dois_pi * (1.0 / duracao_s) * 3 * t)

        onda_l = (
            0.50 * math.sin(dois_pi * f0 * t)
            + 0.30 * math.sin(dois_pi * f1 * t + 0.2) * lfo1
            + 0.15 * math.sin(dois_pi * f2 * t + 0.5) * lfo2
            + 0.05 * math.sin(dois_pi * f3 * t + 0.8)
        )
        onda_r = (
            0.50 * math.sin(dois_pi * f0 * t + 0.1)
            + 0.30 * math.sin(dois_pi * f1 * t + 0.4) * lfo2
            + 0.15 * math.sin(dois_pi * f2 * t + 0.1) * lfo1
            + 0.05 * math.sin(dois_pi * f3 * t + 0.3)
        )

        val_l = int(max(-32767, min(32767, onda_l * amplitude_base * 32767)))
        val_r = int(max(-32767, min(32767, onda_r * amplitude_base * 32767)))
        buffer.extend(struct.pack("<hh", val_l, val_r))

    with wave.open(str(saida_wav), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(buffer)

    return saida_wav


def garantir_trilha_provisoria_kit(kit_dir: Path | None = None) -> Path:
    """Garante a existência da trilha provisória e sua ficha de licença no kit."""
    pasta_kit = kit_dir or KIT_PADRAO_DIR
    trilhas_dir = pasta_kit / "trilhas"
    destino = trilhas_dir / "provisoria.wav"
    licenca = trilhas_dir / "provisoria.licenca.json"

    if not destino.is_file():
        trilhas_dir.mkdir(parents=True, exist_ok=True)
        gerar_trilha_provisoria_drone(destino)

    if not licenca.is_file():
        dados_licenca = {
            "nome": "Trilha Provisória DocForja (Drone Documental)",
            "arquivo": "provisoria.wav",
            "origem": "kit_cinza_e_brasa",
            "licenca": "CC0-1.0",
            "comercial": True,
            "autor": "DocForja",
            "descricao": (
                "Cama musical provisória ambiente em tom documental para animatic de planejamento"
            ),
            "tags": ["drone", "documentario", "ambiente", "provisoria"],
        }
        atomic_write_json(licenca, dados_licenca)

    return destino


def resolver_trilha_provisoria(
    projeto: Projeto,
    kit_dir: Path | None = None,
    pasta_global: Path | None = None,
) -> Path | None:
    """Resolve a trilha sonora provisória prioritária para a prévia.

    1. Trilha específica do projeto em 03_audio/trilha/ (se fornecida).
    2. Trilha na Pasta Global (global/trilhas ou global/musica com licença comercial).
    3. Trilha provisória do kit visual configurado.
    4. Trilha padrão documental gerada e licenciada no kit.
    """
    pasta_trilha_projeto = projeto.pastas.audio / "trilha"
    if pasta_trilha_projeto.is_dir():
        for nome in [
            "provisoria.wav",
            "provisoria.mp3",
            "trilha_provisoria.wav",
            "trilha_provisoria.mp3",
        ]:
            candidato = pasta_trilha_projeto / nome
            if candidato.is_file():
                return candidato

    # 2. Pasta Global (se houver trilha licenciada ou solicitada nas opções)
    try:
        from docforja.global_assets.resolucao import buscar_trilha_global, obter_pasta_global

        root_global = pasta_global or obter_pasta_global()
        trilha_opt = projeto.obter_opcoes().get("audio", {}).get("trilha")
        termo = str(trilha_opt) if trilha_opt else None
        res_global = buscar_trilha_global(termo, pasta_global=root_global)
        if res_global:
            caminho_trilha, _ficha = res_global
            return caminho_trilha
    except Exception:
        pass

    pasta_kit = kit_dir or KIT_PADRAO_DIR
    kit_trilhas = pasta_kit / "trilhas"
    if kit_trilhas.is_dir():
        for nome in [
            "provisoria.wav",
            "provisoria.mp3",
            "trilha_provisoria.wav",
            "trilha_provisoria.mp3",
        ]:
            candidato = kit_trilhas / nome
            if candidato.is_file():
                return candidato

    return garantir_trilha_provisoria_kit(kit_dir=pasta_kit)
