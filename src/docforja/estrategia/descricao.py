"""Geração da descrição completa do documentário para publicação (13 §4.2)."""

from __future__ import annotations

from docforja.esquemas import Plano
from docforja.estrategia.capitulos import Capitulo


def gerar_descricao_md(
    plano: Plano,
    capitulos: list[Capitulo],
    creditos_resumo: str = "",
    fontes_roteiro: list[str] | None = None,
    hashtags: list[str] | None = None,
    idioma: str = "pt-BR",
) -> str:
    """Monta a descrição estratégica conforme os 6 requisitos da especificação 13 §4.2."""
    tema = plano.projeto.replace("-", " ").title()

    if idioma.startswith("en"):
        linha1 = f"{tema}: The complete history and revelations centuries tried to erase."
        linha2 = "Discover in this detailed documentary the real facts, minute by minute."
        resumo = (
            f"In this exclusive DocForja documentary, we investigate the events of {tema}. "
            "Drawing upon period documents, archaeological records, and recent scientific "
            "analyses, we reconstruct the exact chronological timeline of events. "
            "Understand the human impact, crucial mistakes, and the enduring historical legacy."
        )
        titulo_capitulos = "## Chapters"
        titulo_fontes = "## Sources and Documentation"
        fontes_padrao = [
            "- Historical accounts and period documentary records",
            "- Recent archaeological research and excavation reports",
        ]
        titulo_creditos = "## Media and Soundtrack Credits"
        creditos_padrao = [
            "- Historical images: Public Domain and Wikimedia Commons collections (CC BY/CC0)",
            "- Soundtrack and sound design: Cinza e Brasa Kit (DocForja Commercial License)",
        ]
        bloco_fixo = (
            "## About the Reconstructions\n\n"
            "> [!NOTE]\n"
            "> **Transparency Notice:** This documentary uses **ARTISTIC RECONSTRUCTION** and "
            "computational visual resources to illustrate historical passages and scientific "
            "concepts. All artistic reconstructions are strictly based on archaeological "
            "sources and period records.\n\n"
            "Subscribe to the channel for upcoming historical investigations and documentaries."
        )
        tags_padrao = [f"#{tema.replace(' ', '')}", "#Documentary", "#DocForja"]
    elif idioma.startswith("es"):
        linha1 = (
            f"{tema}: La historia completa y las revelaciones que los siglos intentaron borrar."
        )
        linha2 = "Descubre en este documental detallado los hechos reales, minuto a minuto."
        resumo = (
            f"En este documental exclusivo de DocForja, investigamos a fondo los "
            f"acontecimientos de {tema}. Apoyados en documentos de época, datos arqueológicos "
            "y análisis científicos recientes, reconstruimos la línea temporal exacta de los "
            "acontecimientos. Comprende el impacto humano, los errores cruciales y el legado "
            "histórico."
        )
        titulo_capitulos = "## Capítulos"
        titulo_fontes = "## Fuentes y Documentación"
        fontes_padrao = [
            "- Relatos históricos y registros documentales del período",
            "- Artículos e informes de excavaciones e investigaciones arqueológicas recientes",
        ]
        titulo_creditos = "## Créditos de Medios y Banda Sonora"
        creditos_padrao = [
            "- Imágenes históricas: Acervos en Dominio Público y Wikimedia Commons "
            "(licencias CC BY/CC0)",
            "- Banda sonora y diseño sonoro: Kit Cinza e Brasa (licencia comercial DocForja)",
        ]
        bloco_fixo = (
            "## Sobre las Reconstrucciones\n\n"
            "> [!NOTE]\n"
            "> **Aviso de Transparencia:** Este documental utiliza **RECONSTITUCIÓN ARTÍSTICA** y "
            "recursos visuales computacionales para ilustrar pasajes históricos y conceptos "
            "científicos. Todas las reconstrucciones artísticas se basan estrictamente en "
            "fuentes arqueológicas y relatos de época.\n\n"
            "Suscríbete al canal para más investigaciones históricas y documentales."
        )
        tags_padrao = [f"#{tema.replace(' ', '')}", "#Documental", "#DocForja"]
    else:
        linha1 = f"{tema}: A história completa e as revelações que os séculos tentaram apagar."
        linha2 = "Descubra neste documentário detalhado os fatos reais, minuto a minuto."
        resumo = (
            f"Neste documentário exclusivo do DocForja, investigamos a fundo os acontecimentos de "
            f"{tema}. "
            "Apoiados em documentos de época, dados arqueológicos e análises científicas recentes, "
            "reconstruímos a linha temporal exata dos acontecimentos. "
            "Entenda o impacto humano, os erros cruciais e o legado histórico deixado para o "
            "presente."
        )
        titulo_capitulos = "## Capítulos"
        titulo_fontes = "## Fontes e Documentação"
        fontes_padrao = [
            "- Relatos históricos e registros documentais do período",
            "- Artigos e relatórios de escavações e pesquisas arqueológicas recentes",
        ]
        titulo_creditos = "## Créditos de Mídia e Trilha"
        creditos_padrao = [
            "- Imagens históricas: Acervos em Domínio Público e Wikimedia Commons "
            "(licenças CC BY/CC0)",
            "- Trilha sonora e sound design: Kit Cinza e Brasa (licença comercial DocForja)",
        ]
        bloco_fixo = (
            "## Sobre as Reconstituições\n\n"
            "> [!NOTE]\n"
            "> **Aviso de Transparência:** Este documentário utiliza "
            "**RECONSTITUIÇÃO ARTÍSTICA** e "
            "recursos visuais computacionais para ilustrar passagens históricas e conceitos "
            "científicos. "
            "Todas as reconstituições são baseadas estritamente em fontes arqueológicas e relatos "
            "da época.\n\n"
            "Inscreva-se no canal para acompanhar novos documentários e investigações históricas."
        )
        tags_padrao = [f"#{tema.replace(' ', '')}", "#Documentario", "#DocForja"]

    # 3. Capítulos com timestamps reais
    linhas_capitulos = [titulo_capitulos, ""]
    for c in capitulos:
        linhas_capitulos.append(f"{c.timestamp} {c.titulo}")

    # 4. Fontes e créditos
    linhas_fontes = [titulo_fontes, ""]
    if fontes_roteiro:
        for f in fontes_roteiro:
            linhas_fontes.append(f"- {f}")
    else:
        linhas_fontes.extend(fontes_padrao)

    linhas_creditos = [titulo_creditos, ""]
    if creditos_resumo.strip():
        linhas_creditos.append(creditos_resumo.strip())
    else:
        linhas_creditos.extend(creditos_padrao)

    # 6. Três hashtags
    tags_finais = hashtags or tags_padrao
    linha_tags = " ".join(tags_finais[:3])

    partes = [
        linha1,
        linha2,
        "",
        resumo,
        "",
        "\n".join(linhas_capitulos),
        "",
        "\n".join(linhas_fontes),
        "",
        "\n".join(linhas_creditos),
        "",
        bloco_fixo,
        "",
        linha_tags,
        "",
    ]

    return "\n".join(partes)
