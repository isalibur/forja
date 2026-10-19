from pathlib import Path

import pytest

from docforja.audio.cadeia import DURACOES_PAUSAS_S
from docforja.audio.metricas import calcular_wer
from docforja.audio.pronuncia import DicionarioPronuncia


def test_dicionario_pronuncia():
    """Valida substituicao fonetica correta conforme config/pronuncia.yaml."""
    caminho_yaml = Path("config/pronuncia.yaml")
    assert caminho_yaml.exists()

    dicionario = DicionarioPronuncia(caminho_yaml)

    # Teste pt-BR
    texto_pt = "O Vesúvio cobriu Pompeia e Herculano perto de Miseno."
    convertido_pt = dicionario.aplicar(texto_pt, idioma="pt-BR")
    assert "Vezúvio" in convertido_pt
    assert "Pompéia" in convertido_pt
    assert "Erculano" in convertido_pt
    assert "Mizêno" in convertido_pt

    # Palavras que contem parte de outras palavras nao devem ser afetadas incorretamente
    texto_fronteira = "plínio foi ao porto de miseno"
    convertido_fronteira = dicionario.aplicar(texto_fronteira, idioma="pt-BR")
    assert "plínio" in convertido_fronteira
    assert "mizêno" in convertido_fronteira


def test_calculo_wer():
    """Valida calculo matematico da taxa de erro de palavras (Word Error Rate)."""
    # Correspondencia exata
    assert calcular_wer("pompeia cidade romana", "pompeia cidade romana") == 0.0

    # Uma substituicao em 4 palavras = 25% (0.25)
    wer_sub = calcular_wer("pompeia cidade romana antiga", "pompeia cidade grega antiga")
    assert pytest.approx(wer_sub, 0.01) == 0.25

    # Uma delecao em 3 palavras = 33.3%
    wer_del = calcular_wer("o grande vulcao", "o vulcao")
    assert pytest.approx(wer_del, 0.01) == 0.333

    # Uma insercao em 2 palavras = 50%
    wer_ins = calcular_wer("nuvem escura", "nuvem muito escura")
    assert pytest.approx(wer_ins, 0.01) == 0.5


def test_duracoes_pausas_padrao():
    """Valida constantes de tempo das pausas do roteiro."""
    assert DURACOES_PAUSAS_S["PAUSA-C"] == 0.4
    assert DURACOES_PAUSAS_S["PAUSA-M"] == 0.75
    assert DURACOES_PAUSAS_S["PAUSA-L"] == 1.5
