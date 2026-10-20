"""Geração consolidada de metadados, publicações e agenda (13 §4 e 15 §2.3)."""

from __future__ import annotations

import csv
import io

from docforja.esquemas import Plano
from docforja.estrategia.capitulos import extrair_capitulos_plano
from docforja.estrategia.descricao import gerar_descricao_md
from docforja.estrategia.modelos import PacoteEstrategico
from docforja.estrategia.thumbnails import gerar_conceitos_thumbnails
from docforja.estrategia.titulos import gerar_titulos_estrategicos


def extrair_tags_e_palavras_chave(
    plano: Plano, idioma: str = "pt-BR"
) -> tuple[list[str], list[str], list[str]]:
    """Extrai tags, hashtags e palavras-chave a partir das entidades e blocos do plano."""
    tema = plano.projeto.replace("-", " ").title()

    if idioma.startswith("en"):
        palavras_chave_base = [
            tema,
            f"{tema} documentary",
            f"{tema} history",
            f"{tema} explained",
            "archaeology",
            "ancient history",
            "historical reconstruction",
            "science and history",
            "historical facts",
            "full documentary",
        ]
        hashtags = [
            f"#{tema.replace(' ', '')}",
            "#Documentary",
            "#DocForja",
        ]
    elif idioma.startswith("es"):
        palavras_chave_base = [
            tema,
            f"{tema} documental",
            f"{tema} historia",
            f"{tema} explicacion",
            "arqueologia",
            "historia antigua",
            "reconstitucion historica",
            "ciencia e historia",
            "hechos historicos",
            "documental completo",
        ]
        hashtags = [
            f"#{tema.replace(' ', '')}",
            "#Documental",
            "#DocForja",
        ]
    else:
        palavras_chave_base = [
            tema,
            f"{tema} documentario",
            f"{tema} historia",
            f"{tema} explicacao",
            "arqueologia",
            "historia antiga",
            "reconstituicao historica",
            "ciencia e historia",
            "fatos historicos",
            "documentario completo",
        ]
        hashtags = [
            f"#{tema.replace(' ', '')}",
            "#Documentario",
            "#DocForja",
        ]

    # Extrai termos de blocos e shots
    for bloco in plano.blocos:
        titulo_limpo = bloco.titulo.replace("##", "").strip()
        if len(titulo_limpo) > 3 and titulo_limpo not in palavras_chave_base:
            palavras_chave_base.append(titulo_limpo.lower())

    tags = palavras_chave_base[:15]
    return tags, hashtags, palavras_chave_base


def formatar_tags_txt(tags: list[str]) -> str:
    """Gera string de tags separadas por vírgula respeitando limite de 500 chars do YouTube."""
    acumulado = []
    total_len = 0
    for tag in tags:
        tamanho = len(tag) + 2
        if total_len + tamanho <= 480:
            acumulado.append(tag)
            total_len += tamanho
        else:
            break
    return ", ".join(acumulado) + "\n"


def formatar_hashtags_txt(hashtags: list[str]) -> str:
    """Gera arquivo com as hashtags recomendadas."""
    return " ".join(hashtags) + "\n"


def formatar_palavras_chave_md(palavras_chave: list[str], idioma: str = "pt-BR") -> str:
    """Gera tabela de palavras-chave primárias e de cauda longa."""
    if idioma.startswith("en"):
        linhas = [
            "# SEO Keyword Mapping — DocForja",
            "",
            "| Type | Keyword | Search Intent |",
            "|---|---|---|",
        ]
        tipo_prim = "Primary"
        tipo_sec = "Secondary"
        tipo_cauda = "Long-Tail"
        intencao = "Educational / Documentary"
    elif idioma.startswith("es"):
        linhas = [
            "# Mapeo de Palabras Clave para SEO — DocForja",
            "",
            "| Tipo | Palabra Clave | Intención de Búsqueda |",
            "|---|---|---|",
        ]
        tipo_prim = "Primaria"
        tipo_sec = "Secundaria"
        tipo_cauda = "Cola Larga"
        intencao = "Educativo / Documental"
    else:
        linhas = [
            "# Mapeamento de Palavras-Chave para SEO — DocForja",
            "",
            "| Tipo | Palavra-Chave | Intenção de Busca |",
            "|---|---|---|",
        ]
        tipo_prim = "Primária"
        tipo_sec = "Secundária"
        tipo_cauda = "Cauda Longa"
        intencao = "Educacional / Documental"

    for i, pk in enumerate(palavras_chave):
        tipo = tipo_prim if i < 3 else tipo_sec if i < 7 else tipo_cauda
        linhas.append(f"| {tipo} | {pk} | {intencao} |")
    linhas.append("")
    return "\n".join(linhas)


def gerar_comentario_fixado_md(plano: Plano, idioma: str = "pt-BR") -> str:
    """Gera texto para comentário fixado que estimula retenção e debate nos comentários."""
    tema = plano.projeto.replace("-", " ").title()
    if idioma.startswith("en"):
        return (
            f"Which fact revealed about {tema} surprised you the most in this documentary?\n\n"
            "Share your thoughts in the comments! "
            "Our research is strictly grounded in primary sources and archaeological findings.\n\n"
            "📌 Sources and further reading listed in the video description.\n"
        )
    elif idioma.startswith("es"):
        return (
            f"¿Qué hecho revelado sobre {tema} te sorprendió más en este documental?\n\n"
            "¡Deja tu reflexión en los comentarios! "
            "Nuestras investigaciones se basan en fuentes documentales y excavaciones.\n\n"
            "📌 Fuentes y lecturas complementarias en la descripción del video.\n"
        )
    return (
        f"Qual fato revelado sobre {tema} mais surpreendeu você neste documentário?\n\n"
        "Deixe sua reflexão nos comentários! "
        "Apoiamos nossas pesquisas em fontes documentais e novas escavações arqueológicas.\n\n"
        "📌 Fontes e leituras complementares listadas na descrição do vídeo.\n"
    )


def gerar_post_comunidade_md(
    plano: Plano, titulo_destaque: str = "", idioma: str = "pt-BR"
) -> str:
    """Gera texto para publicação na aba Comunidade do YouTube."""
    tema = plano.projeto.replace("-", " ").title()
    if idioma.startswith("en"):
        tit = titulo_destaque or f"The truth about {tema}"
        return (
            f"🚨 NEW DOCUMENTARY LIVE: {tit}\n\n"
            f"After weeks of research into archives and meticulous visual reconstruction, "
            f"the full documentary on {tema} is now available on the channel!\n\n"
            "👉 Watch now and discover the real facts that centuries tried to conceal.\n"
            "Link is right above on the channel. Let us know what you think!\n"
        )
    elif idioma.startswith("es"):
        tit = titulo_destaque or f"La verdad sobre {tema}"
        return (
            f"🚨 DOCUMENTAL EN LÍNEA: {tit}\n\n"
            f"Tras semanas de investigación en archivos y minuciosa reconstitución visual, "
            f"¡el documental completo sobre {tema} ya está disponible en el canal!\n\n"
            "👉 Míralo ahora y descubre los hechos reales que los siglos intentaron ocultar.\n"
            "El enlace está arriba en el canal. ¡Comenta qué te pareció!\n"
        )
    tit = titulo_destaque or f"A verdade sobre {tema}"
    return (
        f"🚨 DOCUMENTÁRIO NO AR: {tit}\n\n"
        f"Depois de semanas de pesquisa em fontes históricas e reconstituição visual minuciosa, "
        f"o documentário completo sobre {tema} já está disponível no canal!\n\n"
        "👉 Assista agora e descubra os fatos reais que os séculos tentaram ocultar.\n"
        "O link está logo acima no canal. Comente o que achou!\n"
    )


def gerar_checklist_publicacao_md(idioma: str = "pt-BR") -> str:
    """Gera checklist marcável de pós-produção e publicação (13 §4.2)."""
    if idioma.startswith("en"):
        return (
            "# Publication Checklist — DocForja\n\n"
            "## Technical Verification\n"
            "- [x] Integrated master audio normalized to -14 LUFS and True Peak ≤ -1 dBTP.\n"
            "- [x] Narration 100% intelligible over soundtrack and sound effects.\n"
            "- [x] No accidental black frames or anomalous freezes.\n"
            "- [x] Safe area respected for titles, graphics, and overlays (1080p).\n\n"
            "## Platform (YouTube / Social)\n"
            "- [ ] Title A/B test configured with recommended variations.\n"
            "- [ ] High-resolution thumbnail uploaded and verified at mobile scale (120 px).\n"
            "- [ ] Complete description filled with chapters starting at `00:00`.\n"
            "- [ ] Pinned comment published right after release.\n"
            "- [ ] Interactive cards and end screen linked to playlists.\n"
            "- [ ] Mandatory artistic reconstruction / AI disclosure enabled in channel settings.\n"
        )
    elif idioma.startswith("es"):
        return (
            "# Checklist de Publicación — DocForja\n\n"
            "## Verificación Técnica\n"
            "- [x] Audio master integrado normalizado a -14 LUFS y True Peak ≤ -1 dBTP.\n"
            "- [x] Locución 100% inteligible sobre banda sonora y efectos de sonido.\n"
            "- [x] Ausencia de cuadros negros accidentales o congelamientos anómalos.\n"
            "- [x] Safe area respetada para textos, gráficos y superposiciones (1080p).\n\n"
            "## Plataforma (YouTube / Redes)\n"
            "- [ ] Prueba A/B de títulos configurada con las opciones recomendadas.\n"
            "- [ ] Miniatura en alta resolución subida y comprobada a escala móvil (120 px).\n"
            "- [ ] Descripción completa con capítulos iniciando en `00:00`.\n"
            "- [ ] Comentario fijado publicado inmediatamente tras el lanzamiento.\n"
            "- [ ] Tarjetas interactivas y pantalla final enlazando a listas de reproducción.\n"
            "- [ ] Divulgación obligatoria de reconstitución artística/IA activada en el panel.\n"
        )
    return (
        "# Checklist de Publicação — DocForja\n\n"
        "## Verificação Técnica\n"
        "- [x] Áudio master normalizado em -14 LUFS integrado e True Peak ≤ -1 dBTP.\n"
        "- [x] Narração 100% inteligível sob a trilha musical e efeitos sonoros.\n"
        "- [x] Ausência de quadros pretos acidentais ou congelamentos anômalos.\n"
        "- [x] Safe area respeitada para textos, gráficos e sobreposições (1080p).\n\n"
        "## Plataforma (YouTube / Redes)\n"
        "- [ ] Teste A/B de títulos configurado com as opções recomendadas.\n"
        "- [ ] Thumbnail em alta resolução enviada e conferida em escala móvel (120 px).\n"
        "- [ ] Descrição completa preenchida com capítulos iniciando em `00:00`.\n"
        "- [ ] Comentário fixado publicado logo após o lançamento.\n"
        "- [ ] Cards interativos e tela final configurados apontando para playlists.\n"
        "- [ ] Divulgação obrigatória de reconstituição artística/IA ativada no painel.\n"
    )


def gerar_agenda_csv(
    titulo: str,
    descricao_resumo: str,
    tags_str: str,
    arquivo_video: str = "video.mp4",
    arquivo_capa: str = "thumb_A.jpg",
    data_prevista: str = "2026-10-25",
    hora_prevista: str = "18:00",
) -> str:
    """Gera a planilha de publicação agenda.csv para ferramentas de automação (15 §2.3)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_ALL)
    writer.writerow([
        "Data", "Hora", "Titulo", "Descricao", "Tags", "Arquivo_Video", "Arquivo_Capa"
    ])
    writer.writerow([
        data_prevista,
        hora_prevista,
        titulo,
        descricao_resumo.replace("\n", " ").strip(),
        tags_str.strip(),
        arquivo_video,
        arquivo_capa,
    ])
    return buffer.getvalue()


def construir_pacote_estrategico(
    plano: Plano,
    duracao_s: float,
    creditos_resumo: str = "",
    idioma: str = "pt-BR",
) -> PacoteEstrategico:
    """Constrói o pacote completo de metadados estratégicos para o projeto no idioma indicado."""
    capitulos = extrair_capitulos_plano(plano)
    tags, hashtags, palavras_chave = extrair_tags_e_palavras_chave(plano, idioma=idioma)
    titulos = gerar_titulos_estrategicos(plano, idioma=idioma)
    top_ab = [t.titulo for t in titulos if t.recomendado_ab]
    thumbnails = gerar_conceitos_thumbnails(plano, idioma=idioma)
    descricao = gerar_descricao_md(
        plano=plano,
        capitulos=capitulos,
        creditos_resumo=creditos_resumo,
        hashtags=hashtags,
        idioma=idioma,
    )
    comentario = gerar_comentario_fixado_md(plano, idioma=idioma)
    post = gerar_post_comunidade_md(
        plano, titulo_destaque=top_ab[0] if top_ab else "", idioma=idioma
    )
    checklist = [
        "Verificação de Loudness (-14 LUFS)",
        "Capítulos em 00:00",
        "Teste A/B de Títulos",
        "Legibilidade de Thumbnail",
        "Aviso Ético de IA",
    ]

    return PacoteEstrategico(
        projeto=plano.projeto,
        idioma=idioma,
        duracao_s=round(duracao_s, 2),
        titulos=titulos,
        top_titulos_ab=top_ab,
        descricao=descricao,
        capitulos=capitulos,
        tags=tags,
        hashtags=hashtags,
        palavras_chave=palavras_chave,
        comentario_fixado=comentario,
        post_comunidade=post,
        checklist_publicacao=checklist,
        thumbnails=thumbnails,
    )


def validar_pacote_estrategico(pacote: PacoteEstrategico) -> tuple[bool, list[str]]:
    """Valida a conformidade e integridade de um pacote estratégico gerado."""
    erros: list[str] = []

    if not pacote.idioma:
        erros.append("Idioma do pacote não informado.")
    if pacote.duracao_s <= 0:
        erros.append("Duração do vídeo deve ser maior que zero.")

    if len(pacote.titulos) != 10:
        erros.append(f"Devem ser gerados exatamente 10 títulos (gerados: {len(pacote.titulos)}).")
    for i, t in enumerate(pacote.titulos, start=1):
        if len(t.titulo) > 60:
            erros.append(f"Título #{i} excede limite de 60 caracteres: '{t.titulo}'.")
        if not (0.0 <= t.nota <= 10.0):
            erros.append(f"Nota do título #{i} fora do intervalo 0-10: {t.nota}.")

    if len(pacote.top_titulos_ab) != 3:
        erros.append(
            "Devem existir exatamente 3 títulos recomendados para A/B "
            f"(encontrados: {len(pacote.top_titulos_ab)})."
        )

    if not pacote.capitulos:
        erros.append("Nenhum capítulo foi extraído.")
    elif pacote.capitulos[0].timestamp != "00:00":
        erros.append(
            "O primeiro capítulo deve começar obrigatoriamente em 00:00 "
            f"(iniciou em {pacote.capitulos[0].timestamp})."
        )

    if len(pacote.thumbnails) != 3:
        erros.append(
            f"Devem existir 3 conceitos de thumbnail (encontrados: {len(pacote.thumbnails)})."
        )
    for c in pacote.thumbnails:
        if not c.legibilidade_120px:
            erros.append(f"Conceito de thumbnail {c.id} reprovado no teste de 120 px.")

    if not pacote.tags:
        erros.append("Lista de tags vazia.")
    elif len(formatar_tags_txt(pacote.tags)) > 500:
        erros.append("String de tags excede limite de 500 caracteres do YouTube.")

    if len(pacote.descricao) < 80:
        erros.append("Descrição muito curta.")

    # Validação do aviso ético de reconstituição artística
    desc_upper = pacote.descricao.upper()
    tem_aviso = (
        "RECONSTITUIÇÃO ARTÍSTICA" in desc_upper
        or "ARTISTIC RECONSTRUCTION" in desc_upper
        or "RECONSTITUCIÓN ARTÍSTICA" in desc_upper
        or "RECONSTITUCION ARTISTICA" in desc_upper
    )
    if not tem_aviso:
        erros.append("Aviso ético de 'RECONSTITUIÇÃO ARTÍSTICA' ausente na descrição.")

    return len(erros) == 0, erros
