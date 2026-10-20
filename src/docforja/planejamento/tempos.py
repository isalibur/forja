"""Cobertura temporal da narração por shots, inclusive fatias do mesmo segmento."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import groupby

from docforja.esquemas import Shot


def segmentos_em_ordem(shots: Iterable[Shot]) -> list[str]:
    """Lista IDs do roteiro uma vez por grupo de fatias contíguas."""
    return [sid for sid, _ in groupby(sid for shot in shots for sid in shot.segmentos)]


def intervalos_narrados(
    shots: Iterable[Shot], segmentos_audio: list[dict], tolerancia_s: float = 0.05
) -> dict[str, tuple[float, float]]:
    """Valida ordem, duração e continuidade; devolve intervalos absolutos por shot."""
    audio = {str(item["id"]): item for item in segmentos_audio}
    ids_audio = list(audio)
    if len(audio) != len(segmentos_audio):
        raise ValueError("IDs de segmentos duplicados no áudio.")
    narrados = [shot for shot in shots if shot.segmentos]
    intervalos: dict[str, tuple[float, float]] = {}
    indice = 0
    posicao = 0.0
    for shot in narrados:
        if len(shot.segmentos) != 1 or indice >= len(ids_audio):
            raise ValueError("A ordem ou cobertura dos segmentos do plano difere do áudio.")
        sid = shot.segmentos[0]
        if sid != ids_audio[indice]:
            raise ValueError("A ordem ou cobertura dos segmentos do plano difere do áudio.")
        item = audio[sid]
        duracao = float(item["fim_s"]) - float(item["inicio_s"])
        inicio = shot.inicio_segmento_s if shot.inicio_segmento_s is not None else 0.0
        fim = shot.fim_segmento_s if shot.fim_segmento_s is not None else duracao
        if (
            inicio < -tolerancia_s
            or fim > duracao + tolerancia_s
            or fim <= inicio
            or abs(inicio - posicao) > tolerancia_s
            or abs(shot.duracao_s - (fim - inicio)) > tolerancia_s
            or shot.id in intervalos
        ):
            raise ValueError(f"Fatia inválida ou descontínua no segmento {sid}.")
        intervalos[shot.id] = (
            float(item["inicio_s"]) + inicio,
            float(item["inicio_s"]) + fim,
        )
        posicao = fim
        if abs(posicao - duracao) <= tolerancia_s:
            indice += 1
            posicao = 0.0
    if indice != len(ids_audio):
        raise ValueError("Há segmentos sem cobertura integral no plano.")
    return intervalos
