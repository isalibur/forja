from __future__ import annotations

import re

from docforja.planejamento.entidades import (
    BlocoProcessado,
    SegmentoProcessado,
    extrair_entidades_heuristica,
    inferir_batida_heuristica,
)


def normalizar_palavras(texto: str) -> list[str]:
    """Extrai lista de palavras faladas em minusculo, sem pontuacao e sem marcas tecnicas."""
    # Remove marcas de sistema
    t = re.sub(r">>VISUAL:.*?<<", "", texto, flags=re.DOTALL)
    t = re.sub(r"\[F-[^\]]+\]", "", t)
    t = re.sub(r"`?\[PAUSA-[CML]\]`?", "", t)
    t = re.sub(r"`?\[SILÊNCIO[^\]]*\]`?", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\{[^}]*\}", "", t)
    t = re.sub(r"\*\*HUD:.*?\*\*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\*\*END CARD.*?\*\*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\*\*B\d+-S\d+[^*]*\*\*", "", t)
    t = re.sub(r"^#{1,6}\s+.*$", "", t, flags=re.MULTILINE)

    # Remove pontuacao e caracteres especiais, mantendo acentos
    palavras = []
    for token in re.findall(r"\b[\w\-']+\b", t):
        token_limpo = token.strip("-'").lower()
        if token_limpo:
            palavras.append(token_limpo)
    return palavras


def verificar_preservacao_palavras(texto_original: str, texto_processado: str) -> tuple[bool, str]:
    """Verifica de forma estrita se 100% das palavras do texto foram preservadas."""
    p_orig = normalizar_palavras(texto_original)
    p_proc = normalizar_palavras(texto_processado)

    if p_orig == p_proc:
        return True, f"100% das palavras preservadas ({len(p_orig)} palavras)."

    len_orig = len(p_orig)
    len_proc = len(p_proc)

    return False, (
        f"Divergência detectada! Original: {len_orig} palavras, Processado: {len_proc} palavras. "
        f"Primeira divergência por volta de: "
        f"orig='{p_orig[min(len_orig - 1, 0) : min(len_orig, 10)]}' vs "
        f"proc='{p_proc[min(len_proc - 1, 0) : min(len_proc, 10)]}'"
    )


def limpar_texto_para_tts(texto: str) -> str:
    """Limpa o texto do segmento para envio ao motor de TTS, preservando o ritmo."""
    t = texto
    # Remove tags de fatos [F-xxx] e notas
    t = re.sub(r"\[F-[^\]]+\]", "", t)
    # Remove diretivas visuais
    t = re.sub(r">>VISUAL:.*?<<", "", t, flags=re.DOTALL)
    # Remove anotacoes entre chaves
    t = re.sub(r"\{[^}]*\}", "", t)
    # Remove diretivas de tela HUD e END CARD
    t = re.sub(r"\*\*HUD:.*?\*\*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\*\*END CARD.*?\*\*", "", t, flags=re.IGNORECASE)
    # Remove silêncios marcados (são tratados na cadeia de áudio)
    t = re.sub(r"`?\[SILÊNCIO[^\]]*\]`?", "", t, flags=re.IGNORECASE)
    # Substitui marcadores de pausa por virgulas ou reticencias suaves se nao houver pontuacao
    t = re.sub(r"`?\[PAUSA-C\]`?", ",", t)
    t = re.sub(r"`?\[PAUSA-M\]`?", "…", t)
    t = re.sub(r"`?\[PAUSA-L\]`?", "…", t)
    # Remove enfases em asterisco (*palavra* -> palavra)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    # Limpa espacos duplicados
    t = re.sub(r"\s+", " ", t).strip()
    return t


def ler_roteiro_formatado(conteudo: str) -> list[BlocoProcessado]:
    """Parseia roteiro formatado conforme especificacao (Markdown B<n>-S<nn>)."""
    linhas = conteudo.splitlines()

    blocos: list[BlocoProcessado] = []
    bloco_atual: BlocoProcessado | None = None
    segmento_atual: SegmentoProcessado | None = None
    linhas_segmento: list[str] = []

    # Regex para cabecalho de bloco: ## ou ### B<n> — Nome ... intensidade X -> Y
    re_bloco = re.compile(
        r"^#{2,3}\s+(B\d+)\s*[-—\u2013]\s*(.*?)(?:·|\s+intensidade\s+|$)",
        re.IGNORECASE,
    )
    re_intensidade = re.compile(
        r"intensidade\s+(\d+(?:\.\d+)?)(?:\s*(?:→|->)\s*(\d+(?:\.\d+)?))?", re.IGNORECASE
    )

    # Regex para identificador de segmento: **B<n>-S<nn>** ou **B<n>-S<nn> (opcional)**
    re_seg_header = re.compile(r"^\s*\*\*(B\d+-S\d+)(?:[^*]*)\*\*\s*(?:\{([^}]+)\})?(.*)$")

    def fechar_segmento_atual():
        nonlocal segmento_atual, linhas_segmento, bloco_atual
        if segmento_atual and bloco_atual:
            texto_bruto = "\n".join(linhas_segmento).strip()

            # Extrai visual sugerido se houver
            m_visual = re.search(r">>VISUAL:\s*(.*?)<<", texto_bruto, re.DOTALL)
            if m_visual:
                segmento_atual.visual_sugerido = m_visual.group(1).strip()

            # Extrai silencio apos o segmento se houver
            m_silencio = re.search(
                r"\[SILÊNCIO\s+(\d+(?:\.\d+)?)\s*s?\]", texto_bruto, re.IGNORECASE
            )
            if m_silencio:
                segmento_atual.silencio_apos_s = float(m_silencio.group(1))

            # Extrai pausas
            pausas = re.findall(r"\[PAUSA-([CML])\]", texto_bruto)
            segmento_atual.pausas = [f"PAUSA-{p}" for p in pausas]

            # Fatos inline
            fatos_inline = re.findall(r"\[(F-[^\]]+)\]", texto_bruto)
            for f in fatos_inline:
                for sub_f in f.split(","):
                    clean_f = sub_f.strip()
                    if clean_f and clean_f not in segmento_atual.fatos:
                        segmento_atual.fatos.append(clean_f)

            segmento_atual.texto_original = texto_bruto
            segmento_atual.texto_limpo = limpar_texto_para_tts(texto_bruto)
            segmento_atual.entidades = extrair_entidades_heuristica(segmento_atual.texto_limpo)
            if not segmento_atual.batida:
                segmento_atual.batida = inferir_batida_heuristica(
                    segmento_atual.direcao_voz, segmento_atual.texto_limpo
                )

            bloco_atual.segmentos.append(segmento_atual)
            segmento_atual = None
            linhas_segmento = []

    for linha in linhas:
        # Verifica se eh secao terminal (ex: ## FONTES ou ## 7. Notas...)
        if bloco_atual and re.match(r"^#{1,3}\s+(?!(?:B\d+|Bloco\s+\d+)\b)", linha, re.IGNORECASE):
            fechar_segmento_atual()
            break

        # Verifica cabecalho de bloco
        m_b = re_bloco.match(linha)
        if m_b:
            fechar_segmento_atual()
            bid = m_b.group(1).upper()
            nome_bloco = m_b.group(2).strip(" ·-—")

            # Intensidades
            int_ini = 5.0
            int_fim = 5.0
            m_int = re_intensidade.search(linha)
            if m_int:
                int_ini = float(m_int.group(1))
                int_fim = float(m_int.group(2)) if m_int.group(2) else int_ini

            bloco_atual = BlocoProcessado(
                id=bid,
                nome=nome_bloco,
                intensidade_inicio=int_ini,
                intensidade_fim=int_fim,
                segmentos=[],
            )
            blocos.append(bloco_atual)
            continue

        # Verifica se eh inicio de segmento
        m_s = re_seg_header.match(linha)
        if m_s:
            fechar_segmento_atual()

            sid = m_s.group(1).upper()
            direcao = m_s.group(2).strip() if m_s.group(2) else None
            resto = m_s.group(3).strip()

            # Extrai fatos no proprio cabecalho do segmento
            fatos = []
            m_fatos = re.findall(r"\[(F-[^\]]+)\]", resto)
            for f in m_fatos:
                for sub_f in f.split(","):
                    clean_f = sub_f.strip()
                    if clean_f and clean_f not in fatos:
                        fatos.append(clean_f)

            # Se ainda nao ha bloco ativo, cria um generico
            if not bloco_atual:
                bloco_atual = BlocoProcessado(id="B0", nome="Abertura", segmentos=[])
                blocos.append(bloco_atual)

            segmento_atual = SegmentoProcessado(
                id=sid,
                texto_original="",
                texto_limpo="",
                direcao_voz=direcao,
                fatos=fatos,
                intensidade=bloco_atual.intensidade_inicio if bloco_atual else 5.0,
            )

            # O resto da linha pode conter texto se nao for apenas tags
            resto_limpo = re.sub(r"\[F-[^\]]+\]", "", resto).strip()
            if resto_limpo:
                linhas_segmento.append(resto_limpo)
            continue

        # Acumula linhas de texto do segmento atual
        if segmento_atual is not None:
            # Ignora separadores horizontais markdown '---'
            if linha.strip() == "---":
                continue
            # Ignora diretivas de tela HUD e END CARD
            if re.match(r"^\s*\*\*(?:HUD:|END CARD\b)", linha, re.IGNORECASE):
                continue
            m_silencio_linha = re.search(
                r"\[SILÊNCIO\s+(\d+(?:\.\d+)?)\s*s?\]", linha, re.IGNORECASE
            )
            if m_silencio_linha:
                segmento_atual.silencio_apos_s = float(m_silencio_linha.group(1))
                continue
            if re.match(r"^\s*`\[PAUSA-[CML]\]`(?:\s*[-—].*)?$", linha):
                continue
            linhas_segmento.append(linha)

    fechar_segmento_atual()
    return blocos


def segmentar_texto_livre(texto: str, max_palavras_por_segmento: int = 35) -> list[BlocoProcessado]:
    """Segmenta texto corrido/livre em blocos e segmentos, garantindo 100% de preservacao."""
    # Divide em sentencas preservando espacos e pontuacao
    sentencas = re.split(r"([.!?…]+(?:\s+|$))", texto)

    frases: list[str] = []
    buffer = ""
    for parte in sentencas:
        buffer += parte
        if re.search(r"[.!?…]+(?:\s+|$)", parte):
            if buffer.strip():
                frases.append(buffer.strip())
            buffer = ""
    if buffer.strip():
        frases.append(buffer.strip())

    if not frases:
        frases = [texto.strip()]

    # Agrupa frases em segmentos de tamanho balanceado
    segmentos_texto: list[str] = []
    seg_atual: list[str] = []
    palavras_seg_atual = 0

    for frase in frases:
        num_palavras = len(frase.split())
        if palavras_seg_atual + num_palavras > max_palavras_por_segmento and seg_atual:
            segmentos_texto.append(" ".join(seg_atual))
            seg_atual = [frase]
            palavras_seg_atual = num_palavras
        else:
            seg_atual.append(frase)
            palavras_seg_atual += num_palavras

    if seg_atual:
        segmentos_texto.append(" ".join(seg_atual))

    # Agrupa segmentos em blocos (~12 segmentos por bloco)
    blocos: list[BlocoProcessado] = []
    bloco_idx = 1
    segmentos_bloco: list[SegmentoProcessado] = []

    for i, stexto in enumerate(segmentos_texto, start=1):
        sid = f"B{bloco_idx}-S{len(segmentos_bloco) + 1:02d}"
        tlimpo = limpar_texto_para_tts(stexto)
        sp = SegmentoProcessado(
            id=sid,
            texto_original=stexto,
            texto_limpo=tlimpo,
            batida=inferir_batida_heuristica(None, tlimpo),
            entidades=extrair_entidades_heuristica(tlimpo),
        )
        segmentos_bloco.append(sp)

        if len(segmentos_bloco) >= 12 or i == len(segmentos_texto):
            b = BlocoProcessado(
                id=f"B{bloco_idx}",
                nome=f"Parte {bloco_idx}",
                segmentos=segmentos_bloco,
            )
            blocos.append(b)
            bloco_idx += 1
            segmentos_bloco = []

    # Valida rigorosamente que nenhuma palavra do texto foi perdida
    texto_reconstruido = " ".join(seg.texto_original for b in blocos for seg in b.segmentos)
    preservado, detalhe = verificar_preservacao_palavras(texto, texto_reconstruido)
    if not preservado:
        raise ValueError(f"Falha na integridade da segmentacao de texto livre: {detalhe}")

    return blocos
