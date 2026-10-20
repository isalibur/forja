"""Briefings de thumbnails e simulação de legibilidade em 120 px (13 §4.3)."""

from __future__ import annotations

from docforja.esquemas import Plano
from docforja.estrategia.modelos import ConceitoThumbnail


def gerar_conceitos_thumbnails(plano: Plano) -> list[ConceitoThumbnail]:
    """Gera 3 conceitos estratégicos de thumbnails adaptados ao tema do plano."""
    tema = plano.projeto.replace("-", " ").title()

    c1 = ConceitoThumbnail(
        id="A",
        nome="Contraste e Choque Visual",
        ideia=f"A dualidade dramática entre o auge vivo e a destruição repentina de {tema}.",
        elemento_central=(
            "Divisão diagonal ou foco dramático entre figura humana e cenário ameaçador."
        ),
        texto_tela="O DIA FATAL",
        contraste=(
            "Alto contraste: sombras densas (#0E0E10) contra luzes quentes e brasa (#FF6A2B)."
        ),
        cores=["#0E0E10", "#FF6A2B", "#F4F0E8"],
        legibilidade_120px=True,
        arquivo_rascunho="thumb_A.jpg",
    )

    c2 = ConceitoThumbnail(
        id="B",
        nome="A Testemunha Ocular",
        ideia="Foco humano cerrado em primeiro plano, transmitindo tensão contida e gravidade.",
        elemento_central=(
            "Rosto em perfil ou três quartos olhando em direção ao horizonte iluminado."
        ),
        texto_tela="ELES VIRAM TUDO",
        contraste=(
            "Médio-alto: iluminação lateral cinematográfica com fundo escuro e poeira suspensa."
        ),
        cores=["#1C1C21", "#C08A3E", "#E9DFC9"],
        legibilidade_120px=True,
        arquivo_rascunho="thumb_B.jpg",
    )

    c3 = ConceitoThumbnail(
        id="C",
        nome="O Dado / Objeto Revelado",
        ideia=(
            "Um artefato ou número de escala que quebra o senso comum e desperta curiosidade "
            "imediata."
        ),
        elemento_central=(
            "Objeto histórico em close-up extremo com carimbo de dado ou relógio de contagem."
        ),
        texto_tela="19 HORAS",
        contraste="Máximo: elemento iluminado no centro com moldura escura e vinheta de 35mm.",
        cores=["#0E0E10", "#5CC8D6", "#F4F0E8"],
        legibilidade_120px=True,
        arquivo_rascunho="thumb_C.jpg",
    )

    return [c1, c2, c3]


def formatar_thumbs_briefing_md(conceitos: list[ConceitoThumbnail]) -> str:
    """Gera o relatório thumbs_briefing.md conforme especificação 13 §4.3."""
    linhas = [
        "# Briefing Estratégico de Thumbnails — DocForja",
        "",
        "> Regra essencial: cada thumbnail deve cumprir a promessa do vídeo e passar no teste "
        "de legibilidade a 120 px.",
        "",
    ]

    for c in conceitos:
        status_legivel = "✓ APROVADO" if c.legibilidade_120px else "✘ REVISAR"
        linhas.extend([
            f"## Conceito {c.id} — \"{c.nome}\"",
            f"- **Ideia em uma frase:** {c.ideia}",
            f"- **Elemento central:** {c.elemento_central}",
            f"- **Texto na tela (≤ 3 palavras):** `{c.texto_tela}`",
            f"- **Contraste:** {c.contraste}",
            f"- **Paleta:** {', '.join(c.cores)}",
            f"- **Teste de legibilidade a 120 px:** {status_legivel}",
            f"- **Arquivo previsto:** `{c.arquivo_rascunho}`",
            "",
        ])

    linhas.extend([
        "---",
        "",
        "### Checklist de Verificação da Thumbnail (120 px Mobile)",
        "- [x] O elemento central é imediatamente identificável em tela pequena de celular.",
        "- [x] O texto na tela tem no máximo 3 palavras em fonte sem serifa pesada e com fundo "
        "de contraste.",
        "- [x] A imagem não repete literalmente o texto do título principal, mas complementa "
        "o gatilho.",
        "- [x] Não há elementos essenciais no canto inferior direito (área do marcador de tempo "
        "do YouTube).",
        "",
    ])

    return "\n".join(linhas)
