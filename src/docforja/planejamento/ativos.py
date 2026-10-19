"""Consolidação e resolução de ativos visuais (Etapa P5 do planejamento).

Deduplica necessidades visuais, categoriza origens e aplica regras éticas de proibição de IA.
"""

from __future__ import annotations

import re
from typing import Any

from docforja.esquemas import Ativo, Bloco, OrigemAtivo

# Sufixo padrão de estilo do kit cinza e brasa (04 §4)
SUFIXO_ESTILO_KIT = (
    ", historical documentary cinematography, natural lighting, warm embers, "
    "atmospheric ash particles, 35mm film grain, 8k resolution, shot on Arri Alexa, masterwork"
)

# Termos negativos padrão para o tema Pompeia/Vesúvio
PROIBICOES_VESUVIO = [
    "lava líquida vermelha escorrendo pela cidade (erupção pliniana de 79 não teve lava nas ruas)",
    "vulcão com cume duplo moderno (em 79 d.C. o cone era único, Monte Somma antes do colapso)",
    "roupas anacrônicas medievais ou renascentistas",
    "qualquer texto, marca d'água ou legenda embutida na imagem gerada",
]


def determinar_origem_ativo(
    descricao: str,
    bloco_id: str,
    proporcao_geradas_atual: float,
    max_prop_gerar: float = 0.30,
) -> tuple[OrigemAtivo, list[str]]:
    """Determina a melhor origem do ativo respeitando regras éticas e cotas do preset."""
    d_lower = descricao.lower()
    proibicoes: list[str] = []

    # Regra D17 / D9: Vítimas reais e moldes NUNCA podem ser gerados por IA
    if any(
        k in d_lower
        for k in ["molde", "esqueleto", "vítima", "vitima", "corpo", "restos", "fiorelli"]
    ):
        proibicoes.append("proibido_gerar_vitimas_reais")
        return OrigemAtivo.PESQUISAR, proibicoes

    # Regra D9: Pessoas contemporâneas vivas/reais nunca podem ser geradas por IA
    if any(
        k in d_lower
        for k in ["pesquisador", "arqueólogo", "contemporâneo", "napoles hoje", "satélite"]
    ):
        proibicoes.append("proibido_gerar_contemporaneo")
        return OrigemAtivo.PESQUISAR, proibicoes

    # Obras de arte reais específicas (afrescos, estátuas, documentos, inscrições)
    if any(
        k in d_lower
        for k in ["afresco", "baco e o vesúvio", "inscrição", "carvão", "papiro", "herculano"]
    ):
        return OrigemAtivo.PEDIR_AO_USUARIO, proibicoes

    # Reconstituições históricas hipotéticas (cenas de 79 d.C.)
    if proporcao_geradas_atual < max_prop_gerar and any(
        k in d_lower
        for k in ["plínio", "erupção", "coluna", "rua romana", "fumaca", "porto", "noite"]
    ):
        return OrigemAtivo.GERAR, proibicoes

    # Padrão de acervo real
    return OrigemAtivo.PESQUISAR, proibicoes


def consolidar_ativos_plano(
    blocos: list[Bloco],
    preset: str = "padrao",
    max_prop_gerar: float = 0.30,
) -> dict[str, Ativo]:
    """Consolida ativos usados nos shots, deduplica e monta ficha completa de cada um."""
    ativos_map: dict[str, Ativo] = {}
    usos_por_id: dict[str, list[str]] = {}

    # Mapeia shots que usam cada ativo
    for bloco in blocos:
        for shot in bloco.shots:
            for aid in shot.ativos:
                usos_por_id.setdefault(aid, []).append(shot.id)

    total_ativos = len(usos_por_id)
    ativos_gerados_count = 0

    for _idx, (aid, shots_usando) in enumerate(sorted(usos_por_id.items()), start=1):
        bloco_origem = shots_usando[0].split("-")[0]

        # Descrição base inferida a partir do bloco e do uso
        descricao = f"Cena histórica de contexto para {aid} (usado em {', '.join(shots_usando)})"
        if "B0" in bloco_origem:
            descricao = (
                "Inscrição antiga a carvão em parede de reboco de Pompeia descoberta em 2018"
            )
        elif "B1" in bloco_origem:
            descricao = (
                "Baía de Nápoles com o Monte Somma verde coberto de vinhedos no ano 79 d.C."
            )
        elif "B2" in bloco_origem:
            descricao = (
                "Rua movimentada de Pompeia com cidadãos e animais assustados por tremores"
            )
        elif "B3" in bloco_origem:
            descricao = (
                "Coluna eruptiva pliniana de cinzas e pomes subindo a 30 km sobre o vulcão"
            )
        elif "B4" in bloco_origem:
            descricao = (
                "Arcadas dos fornici de Herculano iluminadas pelo brilho da nuvem piroclástica"
            )
        elif "B5" in bloco_origem:
            descricao = (
                "Cinzas vulcânicas cobrindo os telhados e o porto de Pompeia na escuridão da manhã"
            )
        elif "B6" in bloco_origem:
            descricao = (
                "Molde de gesso histórico de Fiorelli revelando a silhueta de uma vítima"
            )
        elif "B7" in bloco_origem:
            descricao = (
                "Papiro carbonizado de Herculano revelando texto sob escaneamento por IA"
            )
        elif "B8" in bloco_origem:
            descricao = (
                "Vista aérea contemporânea da zona vermelha ao redor do cone moderno do Vesúvio"
            )

        prop_atual = ativos_gerados_count / max(1, total_ativos)
        origem, proibicoes = determinar_origem_ativo(
            descricao=descricao,
            bloco_id=bloco_origem,
            proporcao_geradas_atual=prop_atual,
            max_prop_gerar=max_prop_gerar,
        )

        prompt_gerar: str | None = None
        busca_info: dict[str, Any] | None = None
        motivo: str | None = None

        if origem == OrigemAtivo.GERAR:
            ativos_gerados_count += 1
            prompt_gerar = f"{descricao}{SUFIXO_ESTILO_KIT}"
            proibicoes.extend(PROIBICOES_VESUVIO)
        elif origem == OrigemAtivo.PEDIR_AO_USUARIO:
            motivo = "Bem cultural ou artefato histórico com possíveis restrições de direitos"
            busca_info = {
                "termos": [descricao, f"Pompeii {aid}"],
                "sites": [
                    "Wikimedia Commons",
                    "Parco Archeologico di Pompei",
                    "Museo Archeologico Nazionale di Napoli",
                ],
            }
        elif origem == OrigemAtivo.PESQUISAR:
            busca_info = {
                "termos": [re.sub(r"\(.*?\)", "", descricao).strip()],
                "sites": ["Wikimedia Commons", "Openverse", "Library of Congress"],
            }

        ativo = Ativo(
            id=aid,
            descricao=descricao,
            origem=origem,
            personagem="plinio_jovem" if "Plínio" in descricao else None,
            prompt=prompt_gerar,
            motivo=motivo,
            busca=busca_info,
            nome_arquivo=f"{aid}.jpg",
            usado_em=shots_usando,
            proibicoes=proibicoes,
            plano_b="pesquisar" if origem == OrigemAtivo.GERAR else "gerar",
        )
        ativos_map[aid] = ativo

    return ativos_map
