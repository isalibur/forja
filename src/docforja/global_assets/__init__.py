"""Módulo de biblioteca e pasta global compartilhada (13 §3)."""

from docforja.global_assets.promocao import (
    ItemPromocao,
    avaliar_ativos_para_promocao,
    formatar_promover_para_global_md,
    promover_itens_para_global,
)

__all__ = [
    "ItemPromocao",
    "avaliar_ativos_para_promocao",
    "formatar_promover_para_global_md",
    "promover_itens_para_global",
]
