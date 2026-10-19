from pathlib import Path

from docforja.planejamento.leitura import (
    ler_roteiro_formatado,
    segmentar_texto_livre,
    verificar_preservacao_palavras,
)


def test_ler_roteiro_vesuvio_116_segmentos():
    """Valida que o roteiro do Vesuvio produz 116 segmentos em 9 blocos."""
    caminho_roteiro = Path("docs/pipeline/04-roteiro.md")
    assert caminho_roteiro.exists(), "Arquivo docs/pipeline/04-roteiro.md não encontrado"

    conteudo = caminho_roteiro.read_text(encoding="utf-8")
    blocos = ler_roteiro_formatado(conteudo)

    assert len(blocos) == 9, f"Esperado 9 blocos (B0 a B8), obtido {len(blocos)}"
    assert [b.id for b in blocos] == ["B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]

    total_segmentos = sum(len(b.segmentos) for b in blocos)
    assert total_segmentos == 116, f"Esperado exatamente 116 segmentos, obtido {total_segmentos}"

    # Valida segmentos especificos
    b0 = blocos[0]
    assert b0.segmentos[0].id == "B0-S01"
    assert "carvão" in b0.segmentos[0].texto_original
    assert "PAUSA-C" in b0.segmentos[0].pausas
    assert "F-018" in b0.segmentos[0].fatos

    # Valida o ultimo segmento B8-S13 (opcional)
    b8 = blocos[-1]
    assert b8.segmentos[-1].id == "B8-S13"
    assert "Obrigado por assistir" in b8.segmentos[-1].texto_original


def test_verificar_preservacao_palavras_estrita():
    """Valida a funcao de verificacao estrita de palavras."""
    texto1 = "Numa parede de Pompeia alguém pegou um pedaço de carvão."
    texto2 = "numa parede de pompeia, alguém pegou um pedaço de carvão!"
    preservado, detalhe = verificar_preservacao_palavras(texto1, texto2)
    assert preservado is True
    assert "100%" in detalhe

    # Falha se uma palavra for alterada ou removida
    texto_alterado = "Numa parede de Roma alguém pegou um pedaço de carvão."
    preservado_err, _ = verificar_preservacao_palavras(texto1, texto_alterado)
    assert preservado_err is False

    texto_incompleto = "Numa parede de Pompeia alguém pegou um pedaço."
    preservado_incomp, _ = verificar_preservacao_palavras(texto1, texto_incompleto)
    assert preservado_incomp is False


def test_segmentar_texto_livre_100_porcento_preservado():
    """Valida que texto corrido livre e segmentado e 100% das palavras sao preservadas."""
    texto_livre = (
        "O Vesúvio é um dos vulcões mais perigosos do mundo moderno. "
        "Em 79 depois de Cristo, sua erupção destruiu Pompeia e Herculano em menos de 24 horas. "
        "Milhares de cidadãos romanos foram pegos de surpresa pela coluna eruptiva "
        "de mais de trinta quilômetros de altura. "
        "Hoje, centenas de milhares de habitantes vivem diretamente na encosta do vulcão. "
        "A ciência moderna monitora a caldeira dia e noite com sismógrafos de alta precisão."
    )

    blocos = segmentar_texto_livre(texto_livre, max_palavras_por_segmento=25)
    assert len(blocos) >= 1

    total_segs = sum(len(b.segmentos) for b in blocos)
    assert total_segs >= 3

    # Verifica integridade total
    texto_recomposto = " ".join(s.texto_original for b in blocos for s in b.segmentos)
    preservado, _ = verificar_preservacao_palavras(texto_livre, texto_recomposto)
    assert preservado is True
