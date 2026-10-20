"""Gerador de linha do tempo OpenTimelineIO (.otio) para DaVinci Resolve (13 §2)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docforja.esquemas import Plano
from docforja.io import atomic_write_json


def gerar_timeline_otio_dict(
    plano: Plano,
    fps: int = 24,
    caminho_audio_relativo: str = "narracao/narracao.wav",
) -> dict[str, Any]:
    """Constrói a estrutura JSON compatível com OpenTimelineIO Timeline.1."""
    video_clips: list[dict[str, Any]] = []
    audio_clips: list[dict[str, Any]] = []

    quadro_atual = 0

    for bloco in plano.blocos:
        for shot in bloco.shots:
            duracao_frames = max(1, round(shot.duracao_s * fps))

            clip = {
                "OTIO_SCHEMA": "Clip.1",
                "name": f"{shot.id} · {shot.template}",
                "source_range": {
                    "OTIO_SCHEMA": "TimeRange.1",
                    "start_time": {
                        "OTIO_SCHEMA": "RationalTime.1",
                        "value": 0,
                        "rate": fps,
                    },
                    "duration": {
                        "OTIO_SCHEMA": "RationalTime.1",
                        "value": duracao_frames,
                        "rate": fps,
                    },
                },
                "metadata": {
                    "DocForja": {
                        "shot_id": shot.id,
                        "template": shot.template,
                        "bloco": bloco.titulo,
                        "ativos": shot.ativos,
                        "textos": shot.textos,
                    }
                },
            }
            video_clips.append(clip)
            quadro_atual += duracao_frames

    total_frames = max(1, quadro_atual)

    # Clip da narração mestre sincronizada
    audio_clips.append({
        "OTIO_SCHEMA": "Clip.1",
        "name": "Narração Principal",
        "media_reference": {
            "OTIO_SCHEMA": "ExternalReference.1",
            "target_url": caminho_audio_relativo,
        },
        "source_range": {
            "OTIO_SCHEMA": "TimeRange.1",
            "start_time": {
                "OTIO_SCHEMA": "RationalTime.1",
                "value": 0,
                "rate": fps,
            },
            "duration": {
                "OTIO_SCHEMA": "RationalTime.1",
                "value": total_frames,
                "rate": fps,
            },
        },
    })

    return {
        "OTIO_SCHEMA": "Timeline.1",
        "name": plano.projeto,
        "global_start_time": {
            "OTIO_SCHEMA": "RationalTime.1",
            "value": 0,
            "rate": fps,
        },
        "tracks": {
            "OTIO_SCHEMA": "Stack.1",
            "children": [
                {
                    "OTIO_SCHEMA": "Track.1",
                    "name": "Vídeo (Shots DocForja)",
                    "kind": "Video",
                    "children": video_clips,
                },
                {
                    "OTIO_SCHEMA": "Track.1",
                    "name": "Áudio (Narração)",
                    "kind": "Audio",
                    "children": audio_clips,
                },
            ],
        },
        "metadata": {
            "DocForja": {
                "kit": plano.kit,
                "preset": plano.preset,
                "versao": plano.versao,
                "total_shots": sum(len(b.shots) for b in plano.blocos),
            }
        },
    }


def exportar_projeto_otio(
    plano: Plano,
    destino_otio: Path,
    fps: int = 24,
) -> Path:
    """Exporta o plano como arquivo .otio pronto para o DaVinci Resolve."""
    dados = gerar_timeline_otio_dict(plano, fps=fps)
    atomic_write_json(destino_otio, dados)
    return destino_otio
