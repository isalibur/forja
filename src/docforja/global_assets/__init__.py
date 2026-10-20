"""Módulo de biblioteca e pasta global compartilhada (13 §3)."""

from docforja.global_assets.promocao import (
    ItemPromocao,
    avaliar_ativos_para_promocao,
    formatar_promover_para_global_md,
    promover_itens_para_global,
)
from docforja.global_assets.resolucao import (
    buscar_ativo_global,
    buscar_mapa_global,
    buscar_trilha_global,
    obter_pasta_global,
)

__all__ = [
    "ItemPromocao",
    "avaliar_ativos_para_promocao",
    "buscar_ativo_global",
    "buscar_mapa_global",
    "buscar_trilha_global",
    "formatar_promover_para_global_md",
    "obter_pasta_global",
    "promover_itens_para_global",
]
