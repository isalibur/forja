"""Gerador de shots e decupagem (Etapa P4 do planejamento).

Mapeia segmentos da narração em unidades audiovisuais usando catálogo fechado T00-T14
e sobreposições O1-O4, garantindo 100% de cobertura da narração.
"""

from __future__ import annotations

import re
from typing import Any

from docforja.esquemas import BatidaSegmento, Shot
from docforja.planejamento.entidades import BlocoProcessado, SegmentoProcessado
from docforja.planejamento.estrategia import EstrategiaBloco

TEMPLATES_CATALOGO = {
    "T00": "Respiro",
    "T01": "Foto",
    "T02": "FotoProfundidade",
    "T03": "FotoRecorte",
    "T04": "FotoDetalhe",
    "T05": "Comparacao",
    "T06": "TextoImpacto",
    "T07": "Citacao",
    "T08": "Numero",
    "T09": "Grafico",
    "T10": "Mapa",
    "T11": "LinhaDoTempo",
    "T12": "Capitulo",
    "T13": "Abertura",
    "T14": "Encerramento",
}


def calcular_duracao_estimada_segmento(segmento: SegmentoProcessado) -> float:
    """Calcula duração estimada baseada no ritmo padrão de 145 palavras por minuto."""
    texto = segmento.texto_limpo
    palavras = len(texto.split())
    # 145 palavras / 60 s = ~2.416 palavras/s
    duracao_fala = max(1.5, round(palavras / 2.416, 1))
    return duracao_fala + segmento.silencio_apos_s


def extrair_pista_template(
    visual_sugerido: str | None,
) -> tuple[str | None, dict[str, Any], list[str]]:
    """Extrai sugestão explícita de template e parâmetros da diretiva >>VISUAL<<."""
    if not visual_sugerido:
        return None, {}, []

    v = visual_sugerido.upper()
    for tid in sorted(TEMPLATES_CATALOGO.keys(), key=len, reverse=True):
        if tid in v:
            textos: list[str] = []
            params: dict[str, Any] = {}
            # Extrai texto entre aspas ou após dois pontos
            match_txt = re.search(r'[:\-]\s*["\']?([^"\']+)["\']?', visual_sugerido)
            if match_txt:
                texto_extraido = match_txt.group(1).strip()
                if len(texto_extraido.split()) <= 7:
                    textos.append(texto_extraido)
            return tid, params, textos

    return None, {}, []


def gerar_shots_bloco(
    bloco: BlocoProcessado,
    estrategia: EstrategiaBloco,
    tempos_reais: dict[str, float] | None = None,
    total_blocos: int = 1,
    ativo_counter: list[int] | None = None,
) -> list[Shot]:
    """Gera lista de shots para um bloco, cobrindo 100% dos segmentos sem sobreposições."""
    if ativo_counter is None:
        ativo_counter = [1]

    shots: list[Shot] = []
    shot_idx = 1
    bid = bloco.id.upper()

    # Regra D16: Inserir T12 Capítulo no início se houver >= 4 blocos (exceto B0 que é cold open)
    tem_capitulo = False
    if total_blocos >= 4 and bid != "B0":
        # Se for início de bloco novo, insere cartão T12
        dur_cap = 2.5
        shots.append(
            Shot(
                id=f"{bid}-{shot_idx:02d}",
                segmentos=[],
                duracao_s=dur_cap,
                template="T12",
                params={"numero": bid.replace("B", ""), "titulo": bloco.nome},
                sobreposicoes=[],
                ativos=[],
                textos=[bloco.nome],
                sfx=["whoosh_grave"],
                transicao="fade_preto",
                plano_b={"template": "T00", "params": {}},
                motivo=f"Abertura de capítulo {bid}: {bloco.nome}",
            )
        )
        shot_idx += 1
        tem_capitulo = True

    # Se for B0 (cold open), insere respiro inicial com fade de preto
    if bid == "B0" and shot_idx == 1:
        shots.append(
            Shot(
                id=f"{bid}-{shot_idx:02d}",
                segmentos=[],
                duracao_s=1.5,
                template="T00",
                params={"cor": "#0a0a0a", "particulas": True},
                sobreposicoes=[],
                ativos=[],
                textos=[],
                sfx=["room_tone"],
                transicao="fade_preto",
                motivo="Respiro inicial antes da narração",
            )
        )
        shot_idx += 1

    ultimo_template = shots[-1].template if shots else None
    repeticoes_template = 1

    for seg in bloco.segmentos:
        duracao = (
            tempos_reais.get(seg.id)
            if (tempos_reais and seg.id in tempos_reais)
            else calcular_duracao_estimada_segmento(seg)
        )

        template_sug, params_sug, textos_sug = extrair_pista_template(seg.visual_sugerido)

        # Escolha do template com base no visual sugerido ou na batida
        template = "T01"
        params: dict[str, Any] = {"movimento": "push_in", "amplitude": 0.04}
        sobreposicoes: list[dict[str, Any]] = []
        textos: list[str] = list(textos_sug)
        sfx: list[str] = []
        ativos: list[str] = []

        if template_sug:
            template = template_sug
            params.update(params_sug)
        elif seg.batida == BatidaSegmento.DADO:
            if "km" in seg.texto_limpo or "altitude" in seg.texto_limpo:
                template = "T09"
                params = {"tipo": "escala", "rotulos": ["Everest", "Coluna"]}
                textos = ["Coluna eruptiva"]
            else:
                template = "T08"
                num_encontrado = next(iter(seg.entidades.get("numeros", [])), "700.000")
                params = {"valor": num_encontrado, "legenda": "habitantes"}
                textos = [num_encontrado]
        elif seg.batida == BatidaSegmento.CITACAO:
            template = "T07"
            params = {"fonte": "Plínio, o Jovem", "estilo": "papel"}
            textos = ["Citação histórica"]
        elif seg.batida == BatidaSegmento.REVELACAO:
            template = "T06"
            palavras = seg.texto_limpo.split()[:4]
            params = {"estilo": "carvão"}
            textos = [" ".join(palavras).upper()]
        elif seg.batida == BatidaSegmento.TRANSICAO_LUGAR:
            template = "T10"
            params = {"regiao": "Campânia", "animar": True}
        elif seg.batida == BatidaSegmento.TRANSICAO_TEMPO:
            template = "T11"
            params = {"destaque": "79 d.C."}
        elif seg.batida == BatidaSegmento.RESPIRO:
            template = "T00"
            params = {"particulas": True}
        elif estrategia.modo_visual == "dados":
            template = "T08" if shot_idx % 2 == 0 else "T01"
        elif estrategia.modo_visual == "arquivo":
            template = "T01"
            params = {"movimento": "push_in", "amplitude": 0.02}
        else:
            # Alternância harmônica entre T01 e T02 para dinamismo
            if shot_idx % 3 == 0:
                template = "T02"
                params = {"movimento": "dolly", "intensidade": 0.3}
            else:
                template = "T01"
                params = {"movimento": "push_in", "amplitude": 0.03}

        # Gestão de repetições sequenciais (Regra D3 preventiva)
        if template == ultimo_template:
            repeticoes_template += 1
            limite = 4 if template == "T01" else 3
            if repeticoes_template > limite:
                template = "T02" if template == "T01" else "T01"
                params = {"movimento": "push_in", "amplitude": 0.03}
                repeticoes_template = 1
        else:
            ultimo_template = template
            repeticoes_template = 1

        # Atribui ativo visual se o template requer imagem (T01 a T05)
        if template in {"T01", "T02", "T03", "T04", "T05"}:
            ativo_id = f"A-{ativo_counter[0]:03d}"
            ativos.append(ativo_id)
            ativo_counter[0] += 1

        # Identificação O1 se houver pessoa ou lugar novo
        pessoas = seg.entidades.get("pessoas", [])
        if pessoas and template in {"T01", "T02", "T03"}:
            sobreposicoes.append({"tipo": "O1", "texto": pessoas[0].upper()})

        # Som associado à batida
        if seg.batida == BatidaSegmento.REVELACAO:
            sfx.append("impacto_sub_grave")
        elif seg.batida == BatidaSegmento.DADO:
            sfx.append("tick_ui")

        # Transição: primeira transição de bloco com capítulo é tratada;
        # dentro do bloco usa corte ou dissolve ocasional
        transicao = "corte"
        if shot_idx == 1 and not tem_capitulo:
            transicao = "fade_preto"
        elif shot_idx % 7 == 0:
            transicao = "dissolve"

        batida_str = seg.batida.value if hasattr(seg.batida, "value") else str(seg.batida)
        shots.append(
            Shot(
                id=f"{bid}-{shot_idx:02d}",
                segmentos=[seg.id],
                duracao_s=duracao,
                template=template,
                params=params,
                sobreposicoes=sobreposicoes,
                ativos=ativos,
                textos=textos,
                sfx=sfx,
                transicao=transicao,
                plano_b={"template": "T01", "params": {"movimento": "push_in"}},
                motivo=f"Segmento {seg.id} ({batida_str})",
            )
        )
        shot_idx += 1

    # Se for o último bloco (B8), insere Encerramento T14
    if bid == "B8":
        shots.append(
            Shot(
                id=f"{bid}-{shot_idx:02d}",
                segmentos=[],
                duracao_s=15.0,
                template="T14",
                params={},
                sobreposicoes=[],
                ativos=[],
                textos=["Inscreva-se", "Próximo vídeo"],
                sfx=["whoosh_grave"],
                transicao="fade_preto",
                motivo="Tela final e encerramento com espaço para elementos YouTube",
            )
        )

    return shots
