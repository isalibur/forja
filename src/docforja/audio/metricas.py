from __future__ import annotations

import re

_NUMEROS_PT = {
    "zero": 0,
    "um": 1,
    "uma": 1,
    "dois": 2,
    "duas": 2,
    "três": 3,
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
    "vinte": 20,
    "trinta": 30,
    "quarenta": 40,
    "cinquenta": 50,
    "sessenta": 60,
    "setenta": 70,
    "oitenta": 80,
    "noventa": 90,
}


def _normalizar_numeros_pt(tokens: list[str]) -> list[str]:
    """Iguala grafias faladas e numéricas sem alterar as palavras originais."""
    normalizados: list[str] = []
    indice = 0
    while indice < len(tokens):
        palavra = tokens[indice]
        valor = _NUMEROS_PT.get(palavra)
        if valor is not None:
            if (
                valor >= 20
                and indice + 2 < len(tokens)
                and tokens[indice + 1] == "e"
                and 1 <= _NUMEROS_PT.get(tokens[indice + 2], -1) <= 9
            ):
                valor += _NUMEROS_PT[tokens[indice + 2]]
                indice += 2
            normalizados.append(str(valor))
        else:
            normalizados.append(palavra)
        indice += 1
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
