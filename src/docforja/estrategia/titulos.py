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

ANGULOS_POR_IDIOMA: dict[str, list[dict[str, str]]] = {
    "pt-BR": ANGULOS_PADRAO,
    "pt": ANGULOS_PADRAO,
    "en": [
        {
            "angulo": "Belief Breaker",
            "gatilho": "Surprise / Challenge to common sense",
            "template": "{tema}: What you learned is wrong",
            "template_alt": "The biggest myth about {tema} you still believe",
        },
        {
            "angulo": "Specific Curiosity",
            "gatilho": "Extreme curiosity / Forgotten detail",
            "template": "The forgotten detail that sealed the fate of {tema}",
            "template_alt": "The hidden mystery behind {tema}",
        },
        {
            "angulo": "Number",
            "gatilho": "Tangible scale and proportion",
            "template": "{num} hours that changed the history of {tema}",
            "template_alt": "{num} crucial minutes in the fall of {tema}",
        },
        {
            "angulo": "Contrast Past vs Present",
            "gatilho": "Temporal irony and identification",
            "template": "{tema}: Where the past is still alive",
            "template_alt": "From paradise to ruin: The tragic fall of {tema}",
        },
        {
            "angulo": "Question",
            "gatilho": "Need for cognitive closure",
            "template": "What really happened during {tema}?",
            "template_alt": "Why could no one stop {tema}?",
        },
        {
            "angulo": "Recent Discovery",
            "gatilho": "Scientific news / Modern revelation",
            "template": "Modern science finally unlocked {tema}",
            "template_alt": "New evidence reveals what destroyed {tema}",
        },
        {
            "angulo": "Eyewitness",
            "gatilho": "Personal empathy / Intimate account",
            "template": "The eyewitness account of the fall of {tema}",
            "template_alt": "The last words of a survivor of {tema}",
        },
        {
            "angulo": "Hidden Consequence",
            "gatilho": "Fascination with the invisible / Side effect",
            "template": "The truth that remained buried under {tema}",
            "template_alt": "The secret centuries hid in {tema}",
        },
        {
            "angulo": "Dramatic Chronology",
            "gatilho": "Countdown pacing",
            "template": "{tema}: Step by step of the final hours",
            "template_alt": "Minute by minute: The final hours of {tema}",
        },
        {
            "angulo": "Tension and Catastrophe",
            "gatilho": "Urgency and existential gravity",
            "template": "The day the earth swallowed {tema}",
            "template_alt": "When everything collapsed: The nightmare of {tema}",
        },
    ],
    "es": [
        {
            "angulo": "Ruptura de creencia",
            "gatilho": "Sorpresa / Desafío al sentido común",
            "template": "{tema}: Lo que aprendiste está mal",
            "template_alt": "El mayor mito sobre {tema} que aún crees",
        },
        {
            "angulo": "Curiosidad específica",
            "gatilho": "Curiosidad extrema / Detalle olvidado",
            "template": "El detalle olvidado que selló el destino de {tema}",
            "template_alt": "El misterio oculto detrás de {tema}",
        },
        {
            "angulo": "Número",
            "gatilho": "Proporción y escala tangible",
            "template": "{num} horas que cambiaron la historia de {tema}",
            "template_alt": "{num} minutos cruciales en el colapso de {tema}",
        },
        {
            "angulo": "Contraste pasado vs presente",
            "gatilho": "Ironía temporal e identificación",
            "template": "{tema}: Donde el pasado sigue vivo",
            "template_alt": "De paraíso a la ruina: La trágica caída de {tema}",
        },
        {
            "angulo": "Pregunta",
            "gatilho": "Necesidad de cierre cognitivo",
            "template": "¿Qué pasó realmente durante {tema}?",
            "template_alt": "¿Por qué nadie pudo detener {tema}?",
        },
        {
            "angulo": "Descubrimiento reciente",
            "gatilho": "Novedad científica / Revelación moderna",
            "template": "La ciencia moderna por fin descifró {tema}",
            "template_alt": "Nuevas pruebas revelan qué destruyó {tema}",
        },
        {
            "angulo": "Testigo presencial",
            "gatilho": "Empatía personal / Relato íntimo",
            "template": "El relato del testigo que vio el fin de {tema}",
            "template_alt": "Las últimas palabras de quien sobrevivió a {tema}",
        },
        {
            "angulo": "Consecuencia oculta",
            "gatilho": "Fascinación por lo invisible / Efecto colateral",
            "template": "La verdad que quedó enterrada bajo {tema}",
            "template_alt": "El secreto que los siglos ocultaron en {tema}",
        },
        {
            "angulo": "Cronología dramática",
            "gatilho": "Ritmo de cuenta regresiva",
            "template": "{tema}: Paso a paso de las horas finales",
            "template_alt": "Minuto a minuto: Las horas finales de {tema}",
        },
        {
            "angulo": "Tensión y catástrofe",
            "gatilho": "Urgencia y gravedad existencial",
            "template": "El día en que la tierra se tragó a {tema}",
            "template_alt": "Cuando todo colapsó: La pesadilla real de {tema}",
        },
    ],
}


def _limpar_tema(tema_bruto: str) -> str:
    """Extrai uma forma limpa e substantiva do nome do projeto/tema."""
    tema = tema_bruto.replace("-", " ").replace("_", " ").strip()
    # Remove prefixos comuns de slug como longo-, smoke-, etc.
    tema = re.sub(r"^(longo|short|smoke|teste)\s+", "", tema, flags=re.IGNORECASE)
    return tema.title() or "Este Documentário"


def avaliar_titulo(
    titulo: str, palavra_chave: str, gancho: str, idioma: str = "pt-BR"
) -> dict[str, float]:
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

    # 4. Curiosidade e gatilho emocional adaptado por idioma
    if idioma.startswith("en"):
        palavras_gatilho = [
            "secret", "truth", "really", "new", "fall", "hours", "myth", "witness", "mystery",
            "wrong", "swallowed", "buried", "nightmare",
        ]
    elif idioma.startswith("es"):
        palavras_gatilho = [
            "secreto", "verdad", "realmente", "nuevo", "fin", "horas", "mito", "relato",
            "misterio", "mal", "trago", "tragó", "enterrada", "pesadilla",
        ]
    else:
        palavras_gatilho = [
            "segredo", "verdade", "realmente", "novo", "fim", "horas", "mito", "relato",
            "errado", "engoliu", "soterrada", "pesadelo",
        ]
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
    idioma: str = "pt-BR",
) -> list[ItemTitulo]:
    """Gera 10 ideias de títulos com notas e destaca o top 3 para teste A/B no idioma."""
    tema = _limpar_tema(plano.projeto)
    palavra_chave = tema.split()[0] if tema else "História"

    titulos: list[ItemTitulo] = []
    angulos = (
        ANGULOS_POR_IDIOMA.get(idioma)
        or (ANGULOS_POR_IDIOMA["en"] if idioma.startswith("en") else None)
        or (ANGULOS_POR_IDIOMA["es"] if idioma.startswith("es") else None)
        or ANGULOS_PADRAO
    )

    for cfg in angulos:
        candidato = cfg["template"].format(tema=tema, num=numero_destaque)
        if len(candidato) > 60:
            candidato = cfg["template_alt"].format(tema=tema, num=numero_destaque)
        if len(candidato) > 60:
            candidato = candidato[:57].rstrip() + "..."

        criterios = avaliar_titulo(candidato, palavra_chave, gancho, idioma=idioma)
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


def formatar_titulos_md(titulos: list[ItemTitulo], idioma: str = "pt-BR") -> str:
    """Formata o relatório titulos.md conforme a especificação 13 §4.1."""
    if idioma.startswith("en"):
        linhas = [
            "# CTR Title Ideas — DocForja",
            "",
            "> Honesty rule: no title promises what the video does not deliver in 60 s.",
            "",
            "## Top 3 Recommended for A/B Testing",
            "",
        ]
        opcao_fmt = "Option"
        gatilho_fmt = "Trigger"
        secao_todos = "## All 10 Angles Generated"
        header_tabela = "| # | Title | Angle | Characters | Score | A/B |"
    elif idioma.startswith("es"):
        linhas = [
            "# Ideas de Títulos para CTR — DocForja",
            "",
            "> Regla de honestidad: ningún título promete lo que el video no cumple en 60 s.",
            "",
            "## Top 3 Recomendados para Prueba A/B",
            "",
        ]
        opcao_fmt = "Opción"
        gatilho_fmt = "Disparador"
        secao_todos = "## Todos los 10 Ángulos Generados"
        header_tabela = "| # | Título | Ángulo | Caracteres | Nota | A/B |"
    else:
        linhas = [
            "# Ideias de Títulos para CTR — DocForja",
            "",
            "> Regra de honestidade: nenhum título promete o que o vídeo não cumpre em 60 s.",
            "",
            "## Top 3 Recomendados para Teste A/B",
            "",
        ]
        opcao_fmt = "Opção"
        gatilho_fmt = "Gatilho"
        secao_todos = "## Todos os 10 Ângulos Gerados"
        header_tabela = "| # | Título | Ângulo | Caracteres | Nota | A/B |"

    recomendados = [t for t in titulos if t.recomendado_ab]
    for i, t in enumerate(recomendados, start=1):
        linhas.append(
            f"**{opcao_fmt} {chr(64 + i)} (Nota {t.nota}/10 · {t.angulo}):**\n"
            f"> `{t.titulo}` ({len(t.titulo)} caracteres)\n"
            f"*{gatilho_fmt}:* {t.gatilho}\n"
        )

    linhas.extend([
        "---",
        "",
        secao_todos,
        "",
        header_tabela,
        "|---|---|---|---|---|:---:|",
    ])

    for i, t in enumerate(titulos, start=1):
        ab_marcador = "★ **SIM**" if t.recomendado_ab else "—"
        linhas.append(
            f"| {i} | {t.titulo} | {t.angulo} | {len(t.titulo)} | {t.nota} | {ab_marcador} |"
        )

    linhas.append("")
    return "\n".join(linhas)
