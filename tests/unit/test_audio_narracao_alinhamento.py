import json
import wave
from pathlib import Path

import pytest

from docforja.audio.adaptadores.base import AdaptadorTTS
from docforja.audio.adaptadores.chatterbox import AdaptadorChatterbox
from docforja.audio.adaptadores.pronta import AdaptadorNarracaoPronta
from docforja.audio.narracao import OrquestradorNarracao
from docforja.planejamento.entidades import SegmentoProcessado


class MockTTS(AdaptadorTTS):
    """Adaptador TTS sintetico rapido para testes unitarios sem uso de GPU."""

    def disponivel(self) -> bool:
        return True

    def gerar(
        self,
        texto: str,
        saida_wav: Path,
        voz: str | None = None,
        idioma: str = "pt-BR",
        velocidade: float = 1.0,
    ) -> Path:
        saida_wav.parent.mkdir(parents=True, exist_ok=True)
        # Cria um arquivo WAV mono de 0.5s a 24kHz valido
        sample_rate = 24000
        n_frames = int(sample_rate * 0.5)
        with wave.open(str(saida_wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(b"\x00\x00" * n_frames)
        return saida_wav


def test_orquestrador_narracao_com_mock(tmp_path: Path):
    """Testa o fluxo completo do orquestrador de narracao com adaptador rapido."""
    mock_tts = MockTTS()
    orquestrador = OrquestradorNarracao(adaptador_tts=mock_tts)

    segmentos = [
        SegmentoProcessado(
            id="B0-S01",
            texto_original="Numa parede de Pompeia alguém escreveu uma data.",
            texto_limpo="Numa parede de Pompeia alguém escreveu uma data.",
        ),
        SegmentoProcessado(
            id="B0-S02",
            texto_original="Dezesseis dias antes das calendas de novembro.",
            texto_limpo="Dezesseis dias antes das calendas de novembro.",
            silencio_apos_s=0.2,
        ),
    ]

    pasta_audio = tmp_path / "03_audio"
    relatorio = orquestrador.processar_projeto_completo(
        segmentos=segmentos,
        pasta_audio=pasta_audio,
        idioma="pt-BR",
        executar_alinhamento=False,
    )

    assert relatorio.duracao_total_s > 0
    assert relatorio.wer_medio is None
    assert all(segmento.wer is None for segmento in relatorio.segmentos)
    assert relatorio.arquivo_completo_wav.exists()
    assert relatorio.arquivo_palavras_json.exists()
    assert relatorio.arquivo_segmentos_json.exists()

    # Valida estrutura do palavras.json gerado
    with open(relatorio.arquivo_palavras_json, encoding="utf-8") as f:
        palavras = json.load(f)
    assert len(palavras) > 0
    assert "palavra" in palavras[0]
    assert "inicio_s" in palavras[0]
    assert "fim_s" in palavras[0]
    assert "segmento_id" in palavras[0]

    # Valida estrutura do segmentos.json gerado
    with open(relatorio.arquivo_segmentos_json, encoding="utf-8") as f:
        segs_json = json.load(f)
    assert len(segs_json) == 2
    assert segs_json[0]["id"] == "B0-S01"
    assert segs_json[1]["id"] == "B0-S02"


def test_adaptador_narracao_pronta(tmp_path: Path):
    """Testa o adaptador para narracao enviada pelo usuario."""
    origem_wav = tmp_path / "locucao_usuario.wav"
    sample_rate = 44100
    with wave.open(str(origem_wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(b"\x00\x00\x00\x00" * 4410)

    adaptador = AdaptadorNarracaoPronta(origem_wav)
    assert adaptador.disponivel() is True

    saida_wav = tmp_path / "saida_padronizada.wav"
    adaptador.gerar("texto", saida_wav)
    assert saida_wav.exists()

    # Confere se foi convertido para 24kHz mono
    with wave.open(str(saida_wav), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getframerate() == 24000


def test_chatterbox_indisponivel_nao_se_disfarca_de_kokoro(tmp_path: Path):
    adaptador = AdaptadorChatterbox(tmp_path / "python-inexistente.exe")

    assert adaptador.disponivel() is False
    with pytest.raises(RuntimeError, match="Chatterbox não disponível"):
        adaptador.gerar("teste", tmp_path / "saida.wav")
