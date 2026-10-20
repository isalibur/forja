"""Cálculos puros de reenquadramento sem alterar o Plano mestre."""

from __future__ import annotations

from typing import Literal

from docforja.esquemas import Plano
from docforja.midia.licenca import classificar_licenca, detectar_patrimonio_restrito
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.shorts.modelos import (
    AtivoReenquadrado,
    CropVertical,
    ManifestoVertical,
    ShotVerticalizado,
)


def calcular_recorte_vertical(
    largura_origem: int,
    altura_origem: int,
    *,
    foco_x: float = 0.5,
    foco_y: float = 0.5,
    razao_destino: float = 9 / 16,
    estrategia: Literal["recorte", "fundo_desfocado"] = "recorte",
) -> CropVertical:
    """Calcula crop máximo em 9:16 centrado no foco, em coordenadas de 0 a 1."""
    if largura_origem <= 0 or altura_origem <= 0:
        raise ValueError("Dimensões da mídia de origem devem ser positivas.")
    if not 0 <= foco_x <= 1 or not 0 <= foco_y <= 1:
        raise ValueError("O ponto de foco deve estar no intervalo normalizado de 0 a 1.")
    if razao_destino <= 0:
        raise ValueError("A razão de aspecto de destino deve ser positiva.")
    if estrategia not in ("recorte", "fundo_desfocado"):
        raise ValueError("Estratégia de verticalização desconhecida.")

    razao_origem = largura_origem / altura_origem
    if razao_origem > razao_destino:
        altura = 1.0
        largura = razao_destino / razao_origem
    else:
        largura = 1.0
        altura = razao_origem / razao_destino

    x = min(max(foco_x - largura / 2, 0.0), 1.0 - largura)
    y = min(max(foco_y - altura / 2, 0.0), 1.0 - altura)
    # Se o foco não coube no crop, é mais seguro preservar o quadro inteiro como fundo.
    foco_preservado = x <= foco_x <= x + largura and y <= foco_y <= y + altura
    if estrategia == "fundo_desfocado":
        x, y, largura, altura = 0.0, 0.0, 1.0, 1.0
    return CropVertical(
        x=round(x, 6),
        y=round(y, 6),
        largura=round(largura, 6),
        altura=round(altura, 6),
        usar_fundo_desfocado=estrategia == "fundo_desfocado" or not foco_preservado,
    )


def verticalizar_plano(
    plano: Plano,
    dimensoes_ativos: dict[str, tuple[int, int]],
    *,
    focos: dict[str, tuple[float, float]] | None = None,
    estrategia: Literal["recorte", "fundo_desfocado"] = "recorte",
) -> ManifestoVertical:
    """Cria manifesto 9:16 derivado; exige licença comercial aprovada para cada imagem."""
    focos = focos or {}
    saidas: list[ShotVerticalizado] = []
    for bloco in plano.blocos:
        for shot in bloco.shots:
            ativos: list[AtivoReenquadrado] = []
            for ativo_id in shot.ativos:
                ativo = plano.ativos.get(ativo_id)
                if ativo is None:
                    raise ValueError(f"Ativo {ativo_id} do shot {shot.id} não existe no plano.")
                ficha = ativo.licenca or {}
                licenca = str(ficha.get("licenca", ""))
                comercial, _ = classificar_licenca(licenca)
                if (
                    not comercial
                    or ficha.get("comercial") is not True
                    or ficha.get("patrimonio_restrito", False)
                    or detectar_patrimonio_restrito(ativo_id, ativo.descricao)
                ):
                    raise ValueError(f"Ativo {ativo_id} não tem licença liberada para o short.")
                if ativo_id not in dimensoes_ativos:
                    raise ValueError(f"Dimensões não informadas para o ativo {ativo_id}.")
                largura, altura = dimensoes_ativos[ativo_id]
                foco_x, foco_y = focos.get(ativo_id, (0.5, 0.5))
                recorte = calcular_recorte_vertical(
                    largura,
                    altura,
                    foco_x=foco_x,
                    foco_y=foco_y,
                    estrategia=estrategia,
                )
                caminho = ativo.caminho
                hash_origem = calcular_hash_dados(caminho) if caminho and caminho.is_file() else ""
                ativos.append(
                    AtivoReenquadrado(
                        ativo_id=ativo_id,
                        recorte=recorte,
                        hash_origem=hash_origem,
                    )
                )
            inicio = shot.inicio_s if shot.inicio_s is not None else 0.0
            fim = shot.fim_s if shot.fim_s is not None else inicio + shot.duracao_s
            saidas.append(
                ShotVerticalizado(
                    shot_id=shot.id,
                    inicio_s=inicio,
                    fim_s=fim,
                    template_origem=shot.template,
                    ativos=ativos,
                )
            )
    arquivos_fontes = {
        ativo_id: calcular_hash_dados(ativo.caminho)
        for ativo_id, ativo in plano.ativos.items()
        if ativo.caminho and ativo.caminho.is_file()
    }
    dados_hash = {
        "plano": plano.model_dump(mode="json"),
        "dimensoes": dimensoes_ativos,
        "focos": focos,
        "estrategia": estrategia,
        "arquivos_fontes": arquivos_fontes,
    }
    return ManifestoVertical(
        projeto=plano.projeto,
        hash_entrada=calcular_hash_dados(dados_hash),
        shots=saidas,
    )
