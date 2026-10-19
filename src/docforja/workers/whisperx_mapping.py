"""Associa palavras do WhisperX aos IDs estáveis do roteiro."""

from __future__ import annotations

from typing import Any


def _id_por_tempo(inicio: float, fim: float, originais: list[dict[str, Any]]) -> str:
    meio = (inicio + fim) / 2
    alvo = min(
        originais,
        key=lambda item: (
            0.0
            if float(item["start"]) <= meio <= float(item["end"])
            else min(abs(meio - float(item["start"])), abs(meio - float(item["end"])))
        ),
    )
    return str(alvo["id"])


def montar_saida_alinhamento(
    alinhados: list[dict[str, Any]],
    originais: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Preserva os segmentos do roteiro mesmo se o WhisperX dividir frases."""
    palavras: list[dict[str, Any]] = []
    segmentos: list[dict[str, Any]] = []
    fonte_segmentos = originais if originais else alinhados

    for seg in fonte_segmentos:
        inicio = round(float(seg.get("start", 0.0)), 3)
        fim = round(float(seg.get("end", inicio)), 3)
        segmentos.append(
            {
                "id": seg.get("id", ""),
                "texto": seg.get("text", "").strip(),
                "inicio_s": inicio,
                "fim_s": fim,
                "duracao_s": round(fim - inicio, 3),
            }
        )

    for seg in alinhados:
        seg_inicio = float(seg.get("start", 0.0))
        seg_fim = float(seg.get("end", seg_inicio))
        for word in seg.get("words", []):
            texto = word.get("word", "").strip()
            if not texto:
                continue
            inicio = round(float(word.get("start", seg_inicio)), 3)
            fim = round(float(word.get("end", seg_fim)), 3)
            seg_id = (
                _id_por_tempo(inicio, fim, originais)
                if originais
                else str(seg.get("id", ""))
            )
            palavras.append(
                {
                    "palavra": texto,
                    "inicio_s": inicio,
                    "fim_s": fim,
                    "score": round(float(word.get("score", 1.0)), 3),
                    "segmento_id": seg_id,
                }
            )

    return palavras, segmentos
