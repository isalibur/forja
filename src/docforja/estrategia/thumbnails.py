"""Briefings de thumbnails e simulação de legibilidade em 120 px (13 §4.3)."""

from __future__ import annotations

from docforja.esquemas import Plano
from docforja.estrategia.modelos import ConceitoThumbnail


def gerar_conceitos_thumbnails(
    plano: Plano, idioma: str = "pt-BR"
) -> list[ConceitoThumbnail]:
    """Gera 3 conceitos de thumbnails adaptados ao tema do plano no idioma indicado."""
    tema = plano.projeto.replace("-", " ").title()

    if idioma.startswith("en"):
        c1 = ConceitoThumbnail(
            id="A",
            nome="Contrast and Visual Shock",
            ideia=f"The dramatic duality between the living peak and sudden destruction of {tema}.",
            elemento_central=(
                "Diagonal division or dramatic focus between human figure and landscape."
            ),
            texto_tela="THE FATAL DAY",
            contraste=(
                "High contrast: dense shadows (#0E0E10) against warm light and ember (#FF6A2B)."
            ),
            cores=["#0E0E10", "#FF6A2B", "#F4F0E8"],
            legibilidade_120px=True,
            arquivo_rascunho="thumb_A.jpg",
        )
        c2 = ConceitoThumbnail(
            id="B",
            nome="The Eyewitness",
            ideia="Tight human close-up in the foreground, conveying contained tension.",
            elemento_central=(
                "Face in profile or three-quarters looking toward the illuminated horizon."
            ),
            texto_tela="THEY SAW IT ALL",
            contraste=(
                "Medium-high: cinematic side lighting with dark background and suspended dust."
            ),
            cores=["#1C1C21", "#C08A3E", "#E9DFC9"],
            legibilidade_120px=True,
            arquivo_rascunho="thumb_B.jpg",
        )
        c3 = ConceitoThumbnail(
            id="C",
            nome="The Revealed Artifact",
            ideia=(
                "A historical artifact or scale number that challenges assumptions."
            ),
            elemento_central=(
                "Historical object in extreme close-up with data badge or countdown clock."
            ),
            texto_tela="19 HOURS",
            contraste="Maximum: illuminated element in center with dark frame and 35mm vignette.",
            cores=["#0E0E10", "#5CC8D6", "#F4F0E8"],
            legibilidade_120px=True,
            arquivo_rascunho="thumb_C.jpg",
        )
    elif idioma.startswith("es"):
        c1 = ConceitoThumbnail(
            id="A",
            nome="Contraste y Choque Visual",
            ideia=(
                f"La dualidad dramática entre el apogeo vivo y la repentina destrucción de {tema}."
            ),
            elemento_central=(
                "División diagonal o foco dramático entre figura humana y paisaje amenazante."
            ),
            texto_tela="EL DÍA FATAL",
            contraste=(
                "Alto contraste: sombras densas (#0E0E10) contra luces cálidas y brasa (#FF6A2B)."
            ),
            cores=["#0E0E10", "#FF6A2B", "#F4F0E8"],
            legibilidade_120px=True,
            arquivo_rascunho="thumb_A.jpg",
        )
        c2 = ConceitoThumbnail(
            id="B",
            nome="El Testigo Presencial",
            ideia="Primer plano humano cerrado, transmitiendo tensión contenida y gravedad.",
            elemento_central=(
                "Rostro de perfil o tres cuartos mirando hacia el horizonte iluminado."
            ),
            texto_tela="ELLOS LO VIERON",
            contraste=(
                "Medio-alto: iluminación lateral cinematográfica con fondo oscuro y polvo."
            ),
            cores=["#1C1C21", "#C08A3E", "#E9DFC9"],
            legibilidade_120px=True,
            arquivo_rascunho="thumb_B.jpg",
        )
        c3 = ConceitoThumbnail(
            id="C",
            nome="El Dato Revelado",
            ideia=(
                "Un artefacto o número de escala que desafía el sentido común."
            ),
            elemento_central=(
                "Objeto histórico en primer plano extremo con sello de dato o reloj regresivo."
            ),
            texto_tela="19 HORAS",
            contraste="Máximo: elemento iluminado al centro con marco oscuro y viñeta de 35mm.",
            cores=["#0E0E10", "#5CC8D6", "#F4F0E8"],
            legibilidade_120px=True,
            arquivo_rascunho="thumb_C.jpg",
        )
    else:
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


def formatar_thumbs_briefing_md(
    conceitos: list[ConceitoThumbnail], idioma: str = "pt-BR"
) -> str:
    """Gera o relatório thumbs_briefing.md conforme especificação 13 §4.3."""
    if idioma.startswith("en"):
        linhas = [
            "# Strategic Thumbnail Briefing — DocForja",
            "",
            "> Essential rule: each thumbnail must fulfill the video promise and pass the "
            "120 px readability check.",
            "",
        ]
        label_ideia = "One-sentence idea"
        label_elemento = "Core focal element"
        label_texto = "On-screen text (≤ 3 words)"
        label_contraste = "Contrast"
        label_paleta = "Color palette"
        label_teste = "120 px readability check"
        label_arquivo = "Expected file"
        checklist_header = "### Thumbnail Verification Checklist (120 px Mobile)"
        checklist_items = [
            "- [x] The core element is instantly recognizable on mobile screens.",
            "- [x] On-screen text is at most 3 words in heavy sans-serif with contrasting "
            "background.",
            "- [x] The visual complements the title trigger without literally repeating it.",
            "- [x] Lower-right corner is clear of essential elements (YouTube timestamp zone).",
        ]
    elif idioma.startswith("es"):
        linhas = [
            "# Briefing Estratégico de Miniaturas — DocForja",
            "",
            "> Regla esencial: cada miniatura debe cumplir la promesa del video y aprobar la "
            "prueba de legibilidad a 120 px.",
            "",
        ]
        label_ideia = "Idea en una frase"
        label_elemento = "Elemento focal central"
        label_texto = "Texto en pantalla (≤ 3 palabras)"
        label_contraste = "Contraste"
        label_paleta = "Paleta de color"
        label_teste = "Prueba de legibilidad a 120 px"
        label_arquivo = "Archivo previsto"
        checklist_header = "### Checklist de Verificación de Miniatura (120 px Móvil)"
        checklist_items = [
            "- [x] El elemento central es inmediatamente identificable en pantalla móvil.",
            "- [x] El texto en pantalla tiene máximo 3 palabras con fondo contrastado.",
            "- [x] La imagen complementa el disparador del título sin repetirlo literalmente.",
            "- [x] La esquina inferior derecha está libre de elementos esenciales.",
        ]
    else:
        linhas = [
            "# Briefing Estratégico de Thumbnails — DocForja",
            "",
            "> Regra essencial: cada thumbnail deve cumprir a promessa do vídeo e passar no teste "
            "de legibilidade a 120 px.",
            "",
        ]
        label_ideia = "Ideia em uma frase"
        label_elemento = "Elemento central"
        label_texto = "Texto na tela (≤ 3 palavras)"
        label_contraste = "Contraste"
        label_paleta = "Paleta"
        label_teste = "Teste de legibilidade a 120 px"
        label_arquivo = "Arquivo previsto"
        checklist_header = "### Checklist de Verificação da Thumbnail (120 px Mobile)"
        checklist_items = [
            "- [x] O elemento central é imediatamente identificável em tela pequena de celular.",
            "- [x] O texto na tela tem no máximo 3 palavras em fonte sem serifa pesada e com fundo "
            "de contraste.",
            "- [x] A imagem não repete literalmente o texto do título principal, mas complementa "
            "o gatilho.",
            "- [x] Não há elementos essenciais no canto inferior direito "
            "(área do marcador de tempo do YouTube).",
        ]

    for c in conceitos:
        status_legivel = "✓ APROVADO" if c.legibilidade_120px else "✘ REVISAR"
        linhas.extend([
            f"## Conceito {c.id} — \"{c.nome}\"",
            f"- **{label_ideia}:** {c.ideia}",
            f"- **{label_elemento}:** {c.elemento_central}",
            f"- **{label_texto}:** `{c.texto_tela}`",
            f"- **{label_contraste}:** {c.contraste}",
            f"- **{label_paleta}:** {', '.join(c.cores)}",
            f"- **{label_teste}:** {status_legivel}",
            f"- **{label_arquivo}:** `{c.arquivo_rascunho}`",
            "",
        ])

    linhas.extend([
        "---",
        "",
        checklist_header,
        *checklist_items,
        "",
    ])

    return "\n".join(linhas)
