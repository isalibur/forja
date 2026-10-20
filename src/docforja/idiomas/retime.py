"""Retime proporcional de shots para a duração da narração traduzida."""

from __future__ import annotations

from copy import deepcopy

from docforja.esquemas import Plano
from docforja.planejamento.previa import montar_manifesto_previa
from docforja.planejamento.tempos import intervalos_narrados


def retimar_plano(
    plano: Plano,
    segmentos_origem: list[dict],
    segmentos_destino: list[dict],
) -> Plano:
    """Redistribui cada fatia do segmento mantendo sua proporção no idioma alvo."""
    origem = {str(item["id"]): item for item in segmentos_origem}
    destino = {str(item["id"]): item for item in segmentos_destino}
    if list(origem) != list(destino) or not origem:
        raise ValueError("Os idiomas devem conter os mesmos segmentos e na mesma ordem.")

    resultado = deepcopy(plano)
    for bloco in resultado.blocos:
        for shot in bloco.shots:
            if not shot.segmentos:
                continue
            if len(shot.segmentos) != 1 or shot.segmentos[0] not in origem:
                raise ValueError(f"Shot {shot.id} não corresponde a um segmento traduzido.")
            sid = shot.segmentos[0]
            duracao_origem = float(origem[sid]["fim_s"]) - float(origem[sid]["inicio_s"])
            duracao_destino = float(destino[sid]["fim_s"]) - float(destino[sid]["inicio_s"])
            if duracao_origem <= 0 or duracao_destino <= 0:
                raise ValueError(f"Duração inválida no segmento {sid}.")
            inicio = shot.inicio_segmento_s or 0.0
            fim = shot.fim_segmento_s if shot.fim_segmento_s is not None else duracao_origem
            shot.inicio_segmento_s = round((inicio / duracao_origem) * duracao_destino, 3)
            shot.fim_segmento_s = round((fim / duracao_origem) * duracao_destino, 3)
            shot.duracao_s = round(shot.fim_segmento_s - shot.inicio_segmento_s, 3)

    intervalos_narrados(
        (shot for bloco in resultado.blocos for shot in bloco.shots), segmentos_destino
    )
    manifesto = montar_manifesto_previa(resultado, segmentos_destino, {})
    intervalos = {item["id"]: item for item in [*manifesto["shots"], *manifesto["cartoes"]]}
    fps = 24
    for bloco in resultado.blocos:
        for shot in bloco.shots:
            item = intervalos[shot.id]
            shot.inicio_s = item["inicio_frame"] / fps
            shot.fim_s = item["fim_frame"] / fps
            shot.duracao_s = round(shot.fim_s - shot.inicio_s, 3)
    return resultado
