"""Verificação das regras de dosagem DS1-DS9 para shorts."""

from __future__ import annotations

from itertools import pairwise

from docforja.shorts.modelos import (
    IntervaloLegendaShort,
    ResultadoDosagemShort,
    ShortParaVerificar,
    ViolacaoDosagemShort,
)

TOLERANCIA_GAP_LEGENDA_S = 0.75
TOLERANCIA_BORDA_LEGENDA_S = 0.1


def _maior_lacuna(legendas: list[IntervaloLegendaShort]) -> float:
    """Maior intervalo sem legenda entre blocos consecutivos."""
    if len(legendas) < 2:
        return 0.0
    return max(
        atual.inicio_s - anterior.fim_s
        for anterior, atual in pairwise(sorted(legendas, key=lambda item: item.inicio_s))
    )


def verificar_short(short: ShortParaVerificar) -> ResultadoDosagemShort:
    """Avalia as regras do guia e devolve todas as falhas encontradas."""
    resultados: list[ViolacaoDosagemShort] = []

    elementos_fora = []
    for elemento in short.elementos:
        x2, y2 = elemento.x + elemento.largura, elemento.y + elemento.altura
        if elemento.importante and (
            elemento.x < 0.05 or x2 > 0.88 or elemento.y < 0.15 or y2 > 0.75
        ):
            elementos_fora.append(elemento.id)
    resultados.append(
        ViolacaoDosagemShort(
            regra="DS1",
            aprovada=not elementos_fora,
            descricao="Texto e elementos importantes ficam dentro das zonas seguras.",
            detalhes=", ".join(elementos_fora),
        )
    )

    ganchos = [short.inicio_gancho_visual_s, short.inicio_gancho_textual_s]
    if short.possui_fala:
        ganchos.append(short.inicio_gancho_falado_s)
    gancho_aprovado = all(valor is not None and valor <= 2.0 for valor in ganchos)
    resultados.append(
        ViolacaoDosagemShort(
            regra="DS2",
            aprovada=gancho_aprovado,
            descricao="Gancho visual e textual em até 2 segundos; fala também quando presente.",
            detalhes=f"Inícios registrados: {ganchos}",
        )
    )

    mudancas = sorted(short.mudancas_visuais_s)
    gaps = [
        fim - inicio
        for inicio, fim in zip(
            [0.0, *mudancas], [*mudancas, short.duracao_s], strict=True
        )
    ]
    maior_gap = max(gaps, default=short.duracao_s)
    tempos_mudanca_validos = all(0 <= tempo <= short.duracao_s for tempo in mudancas)
    resultados.append(
        ViolacaoDosagemShort(
            regra="DS3",
            aprovada=maior_gap <= 3.0 and tempos_mudanca_validos,
            descricao="Há uma mudança visual ao menos a cada 3 segundos.",
            detalhes=(
                f"Maior intervalo sem mudança: {maior_gap:.2f} s"
                if tempos_mudanca_validos
                else "Há mudança visual fora da duração do short."
            ),
        )
    )

    legendas_em_ordem = sorted(short.legendas, key=lambda item: item.inicio_s)
    legenda_cobre = not short.possui_fala
    if short.possui_fala and legendas_em_ordem:
        legenda_cobre = (
            legendas_em_ordem[0].inicio_s <= TOLERANCIA_BORDA_LEGENDA_S
            and legendas_em_ordem[-1].fim_s >= short.duracao_s - TOLERANCIA_BORDA_LEGENDA_S
            and all(
                atual.inicio_s <= anterior.fim_s + TOLERANCIA_GAP_LEGENDA_S
                for anterior, atual in pairwise(legendas_em_ordem)
            )
        )
    resultados.append(
        ViolacaoDosagemShort(
            regra="DS4",
            aprovada=legenda_cobre,
            descricao="Legendas cobrem a fala do início ao fim.",
            detalhes=(
                ""
                if legenda_cobre
                else f" Maior lacuna entre legendas: {_maior_lacuna(legendas_em_ordem):.2f} s"
            ),
        )
    )

    resultados.append(
        ViolacaoDosagemShort(
            regra="DS5",
            aprovada=short.quantidade_ctas_principais == 1,
            descricao="Existe exatamente um CTA principal.",
            detalhes=f"CTAs encontrados: {short.quantidade_ctas_principais}",
        )
    )

    texto_longo = [
        texto for texto in short.textos_tela if len(texto.split()) > 6
    ]
    resultados.append(
        ViolacaoDosagemShort(
            regra="DS6",
            aprovada=not texto_longo,
            descricao="Cada texto na tela tem no máximo 6 palavras.",
            detalhes="; ".join(texto_longo),
        )
    )

    dentro_faixa = abs(short.duracao_s - short.duracao_alvo_s) <= 2.0
    resultados.append(
        ViolacaoDosagemShort(
            regra="DS7",
            aprovada=dentro_faixa,
            descricao="A duração fica dentro do alvo com tolerância de 2 segundos.",
            detalhes=f"{short.duracao_s:.2f} s para alvo de {short.duracao_alvo_s:.2f} s",
        )
    )

    derivado_ok = not short.derivado or (
        short.frase_ponte_aprovada and bool(short.video_longo_id)
    )
    resultados.append(
        ViolacaoDosagemShort(
            regra="DS8",
            aprovada=derivado_ok,
            descricao="Short derivado tem frase-ponte aprovada e aponta para o vídeo longo.",
        )
    )

    comparacao_musica_ok = (
        short.musica_mais_presente_que_longo is True if short.derivado else True
    )
    if short.musica_ausente:
        comparacao_musica_ok = True
    mascara_ok = short.musica_cobre_voz is False or short.musica_ausente
    audio_ok = (
        short.audio_lufs_integrado is not None
        and abs(short.audio_lufs_integrado - (-14.0)) <= 1.0
        and comparacao_musica_ok
        and mascara_ok
    )
    sem_comparacao = short.derivado and not short.musica_ausente
    detalhes_ds9 = (
        "Loudness integrado ausente."
        if short.audio_lufs_integrado is None
        else "Comparação de nível da música com o longo ausente."
        if sem_comparacao and short.musica_mais_presente_que_longo is None
        else "Mascaramento da voz ainda não foi medido."
        if not short.musica_ausente and short.musica_cobre_voz is None
        else f"Loudness integrado: {short.audio_lufs_integrado:.1f} LUFS"
        + (
            "; sem trilha na mix, não há música a comparar nem a mascarar"
            if short.musica_ausente
            else ""
        )
    )
    resultados.append(
        ViolacaoDosagemShort(
            regra="DS9",
            aprovada=audio_ok,
            descricao=(
                "Mix próximo de -14 LUFS, sem mascarar a voz; "
                "comparar com o longo se derivado."
            ),
            detalhes=detalhes_ds9,
        )
    )

    return ResultadoDosagemShort(
        aprovado=all(item.aprovada for item in resultados),
        violacoes=resultados,
    )
