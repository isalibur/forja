from __future__ import annotations

import re

_UNIDADES_PT = {
    "zero": 0,
    "um": 1,
    "uma": 1,
    "dois": 2,
    "duas": 2,
    "três": 3,
    "tres": 3,
    "quatro": 4,
    "cinco": 5,
    "seis": 6,
    "sete": 7,
    "oito": 8,
    "nove": 9,
    "dez": 10,
    "onze": 11,
    "doze": 12,
    "treze": 13,
    "catorze": 14,
    "quatorze": 14,
    "quinze": 15,
    "dezesseis": 16,
    "dezassete": 17,
    "dezessete": 17,
    "dezoito": 18,
    "dezenove": 19,
}

_DEZENAS_PT = {
    "vinte": 20,
    "trinta": 30,
    "quarenta": 40,
    "cinquenta": 50,
    "sessenta": 60,
    "setenta": 70,
    "oitenta": 80,
    "noventa": 90,
}

_CENTENAS_PT = {
    "cem": 100,
    "cento": 100,
    "duzentos": 200,
    "duzentas": 200,
    "trezentos": 300,
    "trezentas": 300,
    "quatrocentos": 400,
    "quatrocentas": 400,
    "quinhentos": 500,
    "quinhentas": 500,
    "seiscentos": 600,
    "seiscentas": 600,
    "setecentos": 700,
    "setecentas": 700,
    "oitocentos": 800,
    "oitocentas": 800,
    "novecentos": 900,
    "novecentas": 900,
}


def _parse_numero_composto_pt(tokens: list[str], start_idx: int) -> tuple[int | None, int]:
    """Converte sequência de palavras numéricas em português a partir de start_idx."""
    idx = start_idx
    total = 0
    corrente = 0
    stage = 0  # 0: init/mil, 1: centena, 2: dezena, 3: unidade
    consumidas = 0

    while idx < len(tokens):
        w = tokens[idx]
        if w == "e":
            if idx + 1 < len(tokens):
                prox = tokens[idx + 1]
                if stage == 1 and (prox in _DEZENAS_PT or prox in _UNIDADES_PT):
                    idx += 1
                    continue
                if stage == 2 and (prox in _UNIDADES_PT and _UNIDADES_PT[prox] <= 9):
                    idx += 1
                    continue
                if (
                    stage in (0, 1, 2, 3)
                    and (prox in _CENTENAS_PT or prox in _DEZENAS_PT or prox in _UNIDADES_PT)
                    and total > 0
                    and corrente == 0
                ):
                    idx += 1
                    continue
            break

        if w in _CENTENAS_PT and stage == 0:
            corrente += _CENTENAS_PT[w]
            stage = 1
            consumidas += 1
            idx += 1
        elif w in _DEZENAS_PT and stage in (0, 1):
            corrente += _DEZENAS_PT[w]
            stage = 2
            consumidas += 1
            idx += 1
        elif w in _UNIDADES_PT and stage in (0, 1, 2):
            if stage == 2 and _UNIDADES_PT[w] > 9:
                break
            corrente += _UNIDADES_PT[w]
            stage = 3
            consumidas += 1
            idx += 1
        elif w == "mil":
            if corrente == 0:
                corrente = 1
            total += corrente * 1000
            corrente = 0
            stage = 0
            consumidas += 1
            idx += 1
        elif w in ("milhão", "milhao", "milhoes", "milhões"):
            if corrente == 0:
                corrente = 1
            total += corrente * 1_000_000
            corrente = 0
            stage = 0
            consumidas += 1
            idx += 1
        else:
            break

    if consumidas > 0:
        return total + corrente, idx
    return None, start_idx


def _normalizar_numeros_pt(tokens: list[str]) -> list[str]:
    """Iguala grafias faladas e numéricas sem alterar as palavras originais."""
    normalizados: list[str] = []
    idx = 0
    while idx < len(tokens):
        valor, next_idx = _parse_numero_composto_pt(tokens, idx)
        if valor is not None:
            normalizados.append(str(valor))
            idx = next_idx
        else:
            normalizados.append(tokens[idx])
            idx += 1
    return normalizados


def _tokenizar(texto: str) -> list[str]:
    """Tokeniza texto em palavras minusculas sem pontuacao."""
    tokens = []
    for t in re.findall(r"\b[\w\-']+\b", texto.lower()):
        limpo = t.strip("-'")
        if limpo:
            tokens.append(limpo)
    return tokens


def calcular_wer(referencia: str, hipotese: str, idioma: str | None = None) -> float:
    """Calcula a Taxa de Erro de Palavras (Word Error Rate - WER).

    WER = (Substituicoes + Delecoes + Insercoes) / Total de palavras de referencia.
    Retorna 0.0 para correspondencia exata. Para português, a opção ``idioma``
    iguala números por extenso e em algarismos antes da comparação.
    """
    ref = _tokenizar(referencia)
    hyp = _tokenizar(hipotese)
    if idioma and idioma.lower().startswith("pt"):
        ref = _normalizar_numeros_pt(ref)
        hyp = _normalizar_numeros_pt(hyp)

    n = len(ref)
    m = len(hyp)

    if n == 0:
        return 0.0 if m == 0 else 1.0

    # Matriz DP para distancia de Levenshtein entre listas de palavras
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                substituicao = dp[i - 1][j - 1] + 1
                delecao = dp[i - 1][j] + 1
                insercao = dp[i][j - 1] + 1
                dp[i][j] = min(substituicao, delecao, insercao)

    distancia = dp[n][m]
    return float(distancia / n)
