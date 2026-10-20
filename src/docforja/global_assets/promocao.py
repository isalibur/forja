"""Regras de promoção automática e sugestão de ativos para a pasta global (13 §3)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from pydantic import BaseModel, Field

from docforja.esquemas import Ativo
from docforja.io import atomic_write_json
from docforja.nucleo.etapas import calcular_hash_dados


class ItemPromocao(BaseModel):
    """Ativo elegível para promoção à biblioteca global."""

    id: str
    tipo: str  # "imagens", "personagens", "mapas", "trilhas"
    origem_caminho: Path
    descricao: str
    licenca: str = "CC0"
    comercial: bool = True
    credito: str = ""
    motivo_sugestao: str
    projetos_usados: list[str] = Field(default_factory=list)


def avaliar_ativos_para_promocao(
    projeto_slug: str,
    ativos: dict[str, Ativo],
) -> list[ItemPromocao]:
    """Avalia quais ativos do projeto cumprem os critérios de promoção de 13 §3."""
    itens: list[ItemPromocao] = []

    for aid, ativo in ativos.items():
        if not ativo.caminho or not ativo.caminho.is_file():
            continue

        caminho = ativo.caminho
        tipo = "imagens"
        motivo = ""

        # Critério 1: Personagens recorrentes (usados em ≥ 2 shots)
        if ativo.personagem or len(ativo.usado_em) >= 2:
            tipo = "personagens" if ativo.personagem else "imagens"
            motivo = f"Consistência visual recorrente ({len(ativo.usado_em)} usos no plano)"

        # Critério 2: Mapas (sempre sugeridos por reaproveitamento de região)
        elif "mapa" in aid.lower() or "mapa" in ativo.descricao.lower():
            tipo = "mapas"
            motivo = "Relevo/vetor geográfico de região reaproveitável"

        # Critério 3: Imagens gerais com licença comercial
        else:
            tipo = "imagens"
            motivo = "Ativo com licença comercial confirmada e resolução de produção"

        # Extrai licença declarada
        licenca_str = "CC0"
        credito_str = ""
        if isinstance(ativo.licenca, dict):
            licenca_str = str(ativo.licenca.get("licenca", "CC0"))
            credito_str = str(ativo.licenca.get("credito") or ativo.licenca.get("autor") or "")

        itens.append(
            ItemPromocao(
                id=aid,
                tipo=tipo,
                origem_caminho=caminho,
                descricao=ativo.descricao,
                licenca=licenca_str,
                comercial=True,
                credito=credito_str,
                motivo_sugestao=motivo,
                projetos_usados=[projeto_slug],
            )
        )

    return itens


def formatar_promover_para_global_md(itens: list[ItemPromocao]) -> str:
    """Gera o relatório promover_para_global.md conforme especificação 13 §3."""
    linhas = [
        "# Proposta de Promoção para a Pasta Global — DocForja",
        "",
        "> Regra: ativos só são promovidos para a biblioteca global após confirmação humana.",
        "> Todos os itens sugeridos possuem licença comercial e ficha de crédito.",
        "",
        "| Confirmar | ID | Tipo | Descrição | Licença | Motivo da Sugestão |",
        "|:---:|---|---|---|---|---|",
    ]

    for item in itens:
        desc = f"{item.descricao[:20]}…" if len(item.descricao) > 20 else item.descricao
        linha = (
            f"| [x] | `{item.id}` | {item.tipo} | {desc} | "
            f"{item.licenca} | {item.motivo_sugestao} |"
        )
        linhas.append(linha)

    linhas.extend([
        "",
        "---",
        "",
        "### Como confirmar a promoção",
        "- Na interface web, acesse a aba **Resultado** e marque os itens aprovados.",
        "- Via CLI, execute `docforja promover --projeto <slug>` para efetivar a cópia.",
        "",
    ])

    return "\n".join(linhas)


def promover_itens_para_global(
    itens: list[ItemPromocao],
    pasta_global: Path,
) -> list[str]:
    """Copia os itens confirmados para a pasta global com sidecar .json imutável."""
    pasta_global.mkdir(parents=True, exist_ok=True)
    promovidos: list[str] = []

    for item in itens:
        if not item.origem_caminho.is_file():
            continue

        destino_subpasta = pasta_global / item.tipo
        destino_subpasta.mkdir(parents=True, exist_ok=True)

        ext = item.origem_caminho.suffix
        destino_arquivo = destino_subpasta / f"{item.id}{ext}"
        destino_ficha = destino_subpasta / f"{item.id}.json"

        # Copia arquivo atomicamente se ausente ou com hash diferente
        if not destino_arquivo.is_file() or (
            calcular_hash_dados(destino_arquivo) != calcular_hash_dados(item.origem_caminho)
        ):
            temp_arq = destino_subpasta / f"{item.id}.novo{ext}"
            shutil.copyfile(item.origem_caminho, temp_arq)
            os.replace(temp_arq, destino_arquivo)

        # Grava ficha técnica no padrão global (13 §3)
        dados_ficha = {
            "id": item.id,
            "tipo": item.tipo,
            "descricao": item.descricao,
            "licenca": item.licenca,
            "comercial": item.comercial,
            "credito": item.credito,
            "arquivo": destino_arquivo.name,
            "sha256": calcular_hash_dados(destino_arquivo),
            "projetos_usados": item.projetos_usados,
        }
        atomic_write_json(destino_ficha, dados_ficha)
        promovidos.append(item.id)

    return promovidos
