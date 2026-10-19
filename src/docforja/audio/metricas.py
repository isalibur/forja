from __future__ import annotations

import re


def _tokenizar(texto: str) -> list[str]:
    """Tokeniza texto em palavras minusculas sem pontuacao."""
    tokens = []
    for t in re.findall(r"\b[\w\-']+\b", texto.lower()):
        limpo = t.strip("-'")
        if limpo:
            tokens.append(limpo)
    return tokens


def calcular_wer(referencia: str, hipotese: str) -> float:
    """Calcula a Taxa de Erro de Palavras (Word Error Rate - WER).

    WER = (Substituicoes + Delecoes + Insercoes) / Total de palavras de referencia.
    Retorna 0.0 para correspondencia exata.
    """
    ref = _tokenizar(referencia)
    hyp = _tokenizar(hipotese)

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
