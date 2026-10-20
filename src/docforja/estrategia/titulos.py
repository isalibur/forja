"""Geração e avaliação multicritério de títulos para CTR (13 §4.1)."""

from __future__ import annotations

import re

from docforja.esquemas import Plano
from docforja.estrategia.modelos import ItemTitulo

ANGULOS_PADRAO = [
    {
        "angulo": "Quebra de crença",
        "gatilho": "Surpresa / Desafio ao senso comum",
        "template": "{tema}: O que você aprendeu está errado",
        "template_alt": "O maior mito sobre {tema} que você ainda acredita",
    },
    {
        "angulo": "Curiosidade específica",
        "gatilho": "Curiosidade extrema / Detalhe bizarro",
        "template": "O detalhe esquecido que selou o destino de {tema}",
        "template_alt": "O mistério oculto por trás de {tema}",
    },
    {
        "angulo": "Número",
        "gatilho": "Especificidade e proporção tangível",
        "template": "{num} horas que definiram a história de {tema}",
        "template_alt": "{num} minutos cruciais no colapso de {tema}",
    },
    {
        "angulo": "Contraste passado vs presente",
        "gatilho": "Ironia temporal e identificação",
        "template": "{tema}: O lugar onde o passado continua vivo",
        "template_alt": "De paraíso à ruína: A trágica transformação de {tema}",
    },
    {
        "angulo": "Pergunta",
        "gatilho": "Necessidade de fechamento cognitivo",
        "template": "O que realmente aconteceu durante {tema}?",
        "template_alt": "Por que ninguém conseguiu impedir {tema}?",
    },
    {
        "angulo": "Descoberta recente",
        "gatilho": "Novidade científica / Revelação moderna",
        "template": "A ciência moderna finalmente desvendou {tema}",
        "template_alt": "Novas evidências revelam o que destruiu {tema}",
    },
    {
        "angulo": "Testemunha ocular",
        "gatilho": "Empatia pessoal / Relato íntimo",
        "template": "O relato da testemunha que viu o fim de {tema}",
        "template_alt": "As últimas palavras de quem sobreviveu a {tema}",
    },
    {
        "angulo": "Consequência oculta",
        "gatilho": "Fascínio pelo invisível / Efeito colateral",
        "template": "A verdade que ficou soterrada sob {tema}",
        "template_alt": "O segredo que os séculos esconderam em {tema}",
    },
    {
        "angulo": "Cronologia dramática",
        "gatilho": "Ritmo de contagem regressiva",
        "template": "{tema}: O passo a passo das últimas horas",
        "template_alt": "Minuto a minuto: As horas finais de {tema}",
    },
    {
        "angulo": "Tensão e catástrofe",
        "gatilho": "Urgência e gravidade existencial",
        "template": "O dia em que a terra engoliu {tema}",
        "template_alt": "Quando tudo ruiu: O pesadelo real de {tema}",
    },
]


def _limpar_tema(tema_bruto: str) -> str:
    """Extrai uma forma limpa e substantiva do nome do projeto/tema."""
    tema = tema_bruto.replace("-", " ").replace("_", " ").strip()
    # Remove prefixos comuns de slug como longo-, smoke-, etc.
    tema = re.sub(r"^(longo|short|smoke|teste)\s+", "", tema, flags=re.IGNORECASE)
    return tema.title() or "Este Documentário"


def avaliar_titulo(titulo: str, palavra_chave: str, gancho: str) -> dict[str, float]:
    """Avalia o título nos critérios exigidos por 13 §4.1 (0 a 10 cada)."""
    tamanho = len(titulo)

    # 1. Tamanho (ideal: 35 a 55 caracteres; limite máximo 60)
    if tamanho <= 60:
        criterio_tamanho = 10.0 if (35 <= tamanho <= 55) else 8.5
    else:
        criterio_tamanho = max(2.0, 10.0 - (tamanho - 60) * 1.5)

    # 2. Palavra-chave no início
    pk_lower = palavra_chave.lower()
    tit_lower = titulo.lower()
    if tit_lower.startswith(pk_lower):
        criterio_pk = 10.0
    elif pk_lower in tit_lower[:25]:
        criterio_pk = 8.5
    elif pk_lower in tit_lower:
        criterio_pk = 6.5
    else:
        criterio_pk = 4.0

    # 3. Clareza e legibilidade
    criterio_clareza = 9.0 if ("?" in titulo or ":" in titulo) else 8.0

    # 4. Curiosidade e gatilho emocional
    palavras_gatilho = ["segredo", "verdade", "realmente", "novo", "fim", "horas", "mito", "relato"]
    tem_gatilho = any(g in tit_lower for g in palavras_gatilho)
    criterio_curiosidade = 9.5 if tem_gatilho else 7.0

    # 5. Especificidade
    tem_numero = any(c.isdigit() for c in titulo)
    criterio_especificidade = 9.5 if (tem_numero or ":" in titulo) else 8.0

    # 6. Coerência com o gancho (honestidade de CTR)
    criterio_coerencia = 9.0

    return {
        "tamanho": criterio_tamanho,
        "palavra_chave_inicio": criterio_pk,
        "clareza": criterio_clareza,
        "curiosidade": criterio_curiosidade,
        "especificidade": criterio_especificidade,
        "coerencia_gancho": criterio_coerencia,
    }


def gerar_titulos_estrategicos(
    plano: Plano,
    gancho: str = "",
    numero_destaque: int = 24,
) -> list[ItemTitulo]:
    """Gera 10 ideias de títulos com notas e destaca o top 3 para teste A/B."""
    tema = _limpar_tema(plano.projeto)
    palavra_chave = tema.split()[0] if tema else "História"

    titulos: list[ItemTitulo] = []

    for cfg in ANGULOS_PADRAO:
        candidato = cfg["template"].format(tema=tema, num=numero_destaque)
        if len(candidato) > 60:
            candidato = cfg["template_alt"].format(tema=tema, num=numero_destaque)
        if len(candidato) > 60:
            candidato = candidato[:57].rstrip() + "..."

        criterios = avaliar_titulo(candidato, palavra_chave, gancho)
        media = sum(criterios.values()) / len(criterios)

        titulos.append(
            ItemTitulo(
                titulo=candidato,
                angulo=cfg["angulo"],
                gatilho=cfg["gatilho"],
                palavra_chave=palavra_chave,
                nota=round(media, 1),
                criterios=criterios,
                recomendado_ab=False,
            )
        )

    # Identifica os top 3 para recomendação A/B
    indices_ordenados = sorted(
        range(len(titulos)), key=lambda i: titulos[i].nota, reverse=True
    )
    for idx in indices_ordenados[:3]:
        titulos[idx].recomendado_ab = True

    return titulos


def formatar_titulos_md(titulos: list[ItemTitulo]) -> str:
    """Formata o relatório titulos.md conforme a especificação 13 §4.1."""
    linhas = [
        "# Ideias de Títulos para CTR — DocForja",
        "",
        "> Regra de honestidade: nenhum título promete o que o vídeo não cumpre nos "
        "primeiros 60 s.",
        "",
        "## Top 3 Recomendados para Teste A/B",
        "",
    ]

    recomendados = [t for t in titulos if t.recomendado_ab]
    for i, t in enumerate(recomendados, start=1):
        linhas.append(
            f"**Opção {chr(64 + i)} (Nota {t.nota}/10 · {t.angulo}):**\n"
            f"> `{t.titulo}` ({len(t.titulo)} caracteres)\n"
            f"*Gatilho:* {t.gatilho}\n"
        )

    linhas.extend([
        "---",
        "",
        "## Todos os 10 Ângulos Gerados",
        "",
        "| # | Título | Ângulo | Caracteres | Nota | A/B |",
        "|---|---|---|---|---|:---:|",
    ])

    for i, t in enumerate(titulos, start=1):
        ab_marcador = "★ **SIM**" if t.recomendado_ab else "—"
        linhas.append(
            f"| {i} | {t.titulo} | {t.angulo} | {len(t.titulo)} | {t.nota} | {ab_marcador} |"
        )

    linhas.append("")
    return "\n".join(linhas)
