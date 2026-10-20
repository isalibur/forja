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
) -> str:
    """Monta a descrição estratégica conforme os 6 requisitos da especificação 13 §4.2."""
    tema = plano.projeto.replace("-", " ").title()

    # 1. Duas primeiras linhas com gancho e palavra-chave (visíveis antes do "mais")
    linha1 = f"{tema}: A história completa e as revelações que os séculos tentaram apagar."
    linha2 = "Descubra neste documentário detalhado os fatos reais, minuto a minuto."

    # 2. Resumo em 3 a 4 frases
    resumo = (
        f"Neste documentário exclusivo do DocForja, investigamos a fundo os acontecimentos de "
        f"{tema}. "
        "Apoiados em documentos de época, dados arqueológicos e análises científicas recentes, "
        "reconstruímos a linha temporal exata dos acontecimentos. "
        "Entenda o impacto humano, os erros cruciais e o legado histórico deixado para o presente."
    )

    # 3. Capítulos com timestamps reais
    linhas_capitulos = ["## Capítulos", ""]
    for c in capitulos:
        linhas_capitulos.append(f"{c.timestamp} {c.titulo}")

    # 4. Fontes e créditos
    linhas_fontes = ["## Fontes e Documentação", ""]
    if fontes_roteiro:
        for f in fontes_roteiro:
            linhas_fontes.append(f"- {f}")
    else:
        linhas_fontes.append("- Relatos históricos e registros documentais do período")
        linhas_fontes.append(
            "- Artigos e relatórios de escavações e pesquisas arqueológicas recentes"
        )

    linhas_creditos = ["## Créditos de Mídia e Trilha", ""]
    if creditos_resumo.strip():
        linhas_creditos.append(creditos_resumo.strip())
    else:
        linhas_creditos.append(
            "- Imagens históricas: Acervos em Domínio Público e Wikimedia Commons "
            "(licenças CC BY/CC0)"
        )
        linhas_creditos.append(
            "- Trilha sonora e sound design: Kit Cinza e Brasa (licença comercial DocForja)"
        )

    # 5. Blocos fixos do canal e aviso ético de IA
    bloco_fixo = (
        "## Sobre as Reconstituições\n\n"
        "> [!NOTE]\n"
        "> **Aviso de Transparência:** Este documentário utiliza **RECONSTITUIÇÃO ARTÍSTICA** e "
        "recursos visuais computacionais para ilustrar passagens históricas e conceitos "
        "científicos. "
        "Todas as reconstituições são baseadas estritamente em fontes arqueológicas e relatos "
        "da época.\n\n"
        "Inscreva-se no canal para acompanhar novos documentários e investigações históricas."
    )

    # 6. Três hashtags
    tags_finais = hashtags or [f"#{tema.replace(' ', '')}", "#Documentario", "#DocForja"]
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
