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


def extrair_tags_e_palavras_chave(plano: Plano) -> tuple[list[str], list[str], list[str]]:
    """Extrai tags, hashtags e palavras-chave a partir das entidades e blocos do plano."""
    tema = plano.projeto.replace("-", " ").title()
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

    # Extrai termos de blocos e shots
    for bloco in plano.blocos:
        titulo_limpo = bloco.titulo.replace("##", "").strip()
        if len(titulo_limpo) > 3 and titulo_limpo not in palavras_chave_base:
            palavras_chave_base.append(titulo_limpo.lower())

    tags = palavras_chave_base[:15]
    hashtags = [
        f"#{tema.replace(' ', '')}",
        "#Documentario",
        "#DocForja",
    ]
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


def formatar_palavras_chave_md(palavras_chave: list[str]) -> str:
    """Gera tabela de palavras-chave primárias e de cauda longa."""
    linhas = [
        "# Mapeamento de Palavras-Chave para SEO — DocForja",
        "",
        "| Tipo | Palavra-Chave | Intenção de Busca |",
        "|---|---|---|",
    ]
    for i, pk in enumerate(palavras_chave):
        tipo = "Primária" if i < 3 else "Secundária" if i < 7 else "Cauda Longa"
        intencao = "Educacional / Documental"
        linhas.append(f"| {tipo} | {pk} | {intencao} |")
    linhas.append("")
    return "\n".join(linhas)


def gerar_comentario_fixado_md(plano: Plano) -> str:
    """Gera texto para comentário fixado que estimula retenção e debate nos comentários."""
    tema = plano.projeto.replace("-", " ").title()
    return (
        f"Qual fato revelado sobre {tema} mais surpreendeu você neste documentário?\n\n"
        "Deixe sua reflexão nos comentários! "
        "Apoiamos nossas pesquisas em fontes documentais e novas escavações arqueológicas.\n\n"
        "📌 Fontes e leituras complementares listadas na descrição do vídeo.\n"
    )


def gerar_post_comunidade_md(plano: Plano, titulo_destaque: str = "") -> str:
    """Gera texto para publicação na aba Comunidade do YouTube."""
    tema = plano.projeto.replace("-", " ").title()
    tit = titulo_destaque or f"A verdade sobre {tema}"
    return (
        f"🚨 DOCUMENTÁRIO NO AR: {tit}\n\n"
        f"Depois de semanas de pesquisa em fontes históricas e reconstituição visual minuciosa, "
        f"o documentário completo sobre {tema} já está disponível no canal!\n\n"
        "👉 Assista agora e descubra os fatos reais que os séculos tentaram ocultar.\n"
        "O link está logo acima no canal. Comente o que achou!\n"
    )


def gerar_checklist_publicacao_md() -> str:
    """Gera checklist marcável de pós-produção e publicação (13 §4.2)."""
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
) -> PacoteEstrategico:
    """Constrói o pacote completo de metadados estratégicos para o projeto."""
    capitulos = extrair_capitulos_plano(plano)
    tags, hashtags, palavras_chave = extrair_tags_e_palavras_chave(plano)
    titulos = gerar_titulos_estrategicos(plano)
    top_ab = [t.titulo for t in titulos if t.recomendado_ab]
    thumbnails = gerar_conceitos_thumbnails(plano)
    descricao = gerar_descricao_md(
        plano=plano,
        capitulos=capitulos,
        creditos_resumo=creditos_resumo,
        hashtags=hashtags,
    )
    comentario = gerar_comentario_fixado_md(plano)
    post = gerar_post_comunidade_md(plano, titulo_destaque=top_ab[0] if top_ab else "")
    checklist = [
        "Verificação de Loudness (-14 LUFS)",
        "Capítulos em 00:00",
        "Teste A/B de Títulos",
        "Legibilidade de Thumbnail",
        "Aviso Ético de IA",
    ]

    return PacoteEstrategico(
        projeto=plano.projeto,
        idioma="pt-BR",
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
