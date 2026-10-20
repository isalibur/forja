"""Pontuação determinística de trechos candidatos a shorts derivados."""

from __future__ import annotations

import re
from collections.abc import Sequence

from docforja.esquemas import Plano
from docforja.shorts.modelos import CandidatoShort, FrasePonte, SegmentoShort

PESOS_CANDIDATURA = {
    "batida_forte": 0.30,
    "autonomia": 0.25,
    "curiosidade": 0.25,
    "forca_visual": 0.10,
    "duracao_ritmo": 0.10,
}
BATIDAS_FORTES = {"gancho", "revelacao", "revelação", "dado"}


def _nota_batida(segmentos: Sequence[SegmentoShort]) -> float:
    primeira = segmentos[0].batida.strip().lower()
    if primeira in BATIDAS_FORTES:
        return 10.0
    notas = [
        6.0 if item.batida.strip().lower() in BATIDAS_FORTES else 0.0
        for item in segmentos
    ]
    return max(notas, default=0)


def _nota_duracao(duracao: float) -> float:
    if 20 <= duracao <= 55:
        return 10.0
    if 15 <= duracao < 20 or 55 < duracao <= 60:
        return 7.0
    return 0.0


def _janelas(
    segmentos: Sequence[SegmentoShort], duracao_min_s: float, duracao_max_s: float
) -> list[list[SegmentoShort]]:
    janelas: list[list[SegmentoShort]] = []
    for inicio in range(len(segmentos)):
        janela: list[SegmentoShort] = []
        for segmento in segmentos[inicio:]:
            if janela and segmento.inicio_s > janela[-1].fim_s + 0.25:
                break
            janela.append(segmento)
            duracao = janela[-1].fim_s - janela[0].inicio_s
            if duracao > duracao_max_s:
                break
            if duracao_min_s <= duracao <= duracao_max_s:
                janelas.append(janela.copy())
    return janelas


def pontuar_candidatos(
    segmentos: Sequence[SegmentoShort],
    *,
    duracao_min_s: float = 20,
    duracao_max_s: float = 55,
    limite: int = 5,
) -> list[CandidatoShort]:
    """Pontua janelas contíguas de 20-55 s sem alterar os dados de origem."""
    if duracao_min_s <= 0 or duracao_max_s < duracao_min_s:
        raise ValueError("Faixa de duração inválida.")
    if limite < 1:
        raise ValueError("limite deve ser maior que zero.")
    ordenados = sorted(segmentos, key=lambda item: (item.inicio_s, item.fim_s, item.id))
    candidatas: list[CandidatoShort] = []
    for janela in _janelas(ordenados, duracao_min_s, duracao_max_s):
        duracao = janela[-1].fim_s - janela[0].inicio_s
        componentes = {
            "batida_forte": _nota_batida(janela),
            "autonomia": sum(item.autonomia_solo for item in janela) / len(janela),
            "curiosidade": sum(item.curiosidade_para_longo for item in janela) / len(janela),
            "forca_visual": sum(item.forca_visual_vertical for item in janela) / len(janela),
            "duracao_ritmo": _nota_duracao(duracao),
        }
        total = sum(componentes[chave] * peso for chave, peso in PESOS_CANDIDATURA.items()) * 10
        texto = " ".join(item.texto.strip() for item in janela)
        motivos = [
            f"{nome}: {nota:.1f}/10 (peso {PESOS_CANDIDATURA[nome]:.0%})"
            for nome, nota in componentes.items()
        ]
        candidatas.append(
            CandidatoShort(
                id=f"short-{janela[0].id}-{janela[-1].id}",
                inicio_s=janela[0].inicio_s,
                fim_s=janela[-1].fim_s,
                segmento_ids=[item.id for item in janela],
                texto=texto,
                pontuacao=round(total, 2),
                componentes={nome: round(nota, 2) for nome, nota in componentes.items()},
                motivos=motivos,
            )
        )
    candidatas.sort(key=lambda item: (-item.pontuacao, item.inicio_s, item.id))
    selecionadas: list[CandidatoShort] = []
    for candidata in candidatas:
        # Evita sugerir vários recortes quase idênticos do mesmo trecho.
        if any(
            candidata.inicio_s < item.fim_s and item.inicio_s < candidata.fim_s
            for item in selecionadas
        ):
            continue
        selecionadas.append(candidata)
        if len(selecionadas) >= limite:
            break
    return selecionadas


def segmentos_de_plano(
    plano: Plano, segmentos_audio: Sequence[dict[str, object]]
) -> list[SegmentoShort]:
    """Converte tempos/transcrições e sinais visuais do plano em segmentos pontuáveis."""
    mapa_shots = {
        segmento_id: shot
        for bloco in plano.blocos
        for shot in bloco.shots
        for segmento_id in shot.segmentos
    }
    resultado: list[SegmentoShort] = []
    for item in segmentos_audio:
        segmento_id = str(item.get("id", ""))
        if not segmento_id:
            continue
        shot = mapa_shots.get(segmento_id)
        inicio = item.get("inicio_s")
        fim = item.get("fim_s")
        texto = item.get("texto")
        if shot is None or not isinstance(inicio, (int, float)):
            continue
        if not isinstance(fim, (int, float)) or not isinstance(texto, str) or not texto.strip():
            continue
        parametros = shot.params
        resultado.append(
            SegmentoShort(
                id=segmento_id,
                inicio_s=float(inicio),
                fim_s=float(fim),
                texto=texto.strip(),
                batida=str(item.get("batida") or parametros.get("batida") or "contexto"),
                autonomia_solo=int(item.get("autonomia_solo", 5)),
                curiosidade_para_longo=int(item.get("curiosidade_para_longo", 5)),
                forca_visual_vertical=int(item.get("forca_visual_vertical", 5)),
            )
        )
    return resultado


def pontuar_candidatos_do_plano(
    plano: Plano,
    segmentos_audio: Sequence[dict[str, object]],
    *,
    duracao_min_s: float = 20,
    duracao_max_s: float = 55,
    limite: int = 5,
) -> list[CandidatoShort]:
    """Gera candidatos de um Plano longo usando transcrição e tempos reais por segmento."""
    if plano.tipo != "longo":
        raise ValueError("Shorts derivados só podem ser extraídos de um projeto longo.")
    segmentos = segmentos_de_plano(plano, segmentos_audio)
    return pontuar_candidatos(
        segmentos,
        duracao_min_s=duracao_min_s,
        duracao_max_s=duracao_max_s,
        limite=limite,
    )


def gerar_frases_ponte(titulo_longo: str) -> list[FrasePonte]:
    """Cria opções genéricas de ponte; nenhuma é aprovada automaticamente."""
    titulo = re.sub(r"\s+", " ", titulo_longo).strip().rstrip(".!?…")
    if not titulo:
        raise ValueError("Informe o título do vídeo longo.")
    return [
        FrasePonte(texto="O restante dessa história está no vídeo completo."),
        FrasePonte(texto=f"Descubra como essa história termina em: {titulo}."),
        FrasePonte(texto="Assista ao documentário completo para conhecer o contexto."),
    ]


def aprovar_frase_ponte(candidato: CandidatoShort, indice: int) -> CandidatoShort:
    """Retorna uma cópia do candidato com a opção escolhida aprovada."""
    if indice < 0 or indice >= len(candidato.frases_ponte):
        raise IndexError("Índice de frase-ponte inválido.")
    frases = [
        frase.model_copy(update={"aprovada": posicao == indice})
        for posicao, frase in enumerate(candidato.frases_ponte)
    ]
    return candidato.model_copy(update={"frases_ponte": frases})
