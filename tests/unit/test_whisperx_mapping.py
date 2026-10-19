from docforja.workers.whisperx_mapping import montar_saida_alinhamento


def test_mapeia_frases_divididas_aos_ids_originais():
    originais = [
        {"id": "B0-S01", "text": "Primeira frase.", "start": 0.0, "end": 2.0},
        {"id": "B0-S02", "text": "Segunda frase.", "start": 2.0, "end": 4.0},
    ]
    alinhados = [
        {"text": "Primeira", "start": 0.1, "end": 0.8,
         "words": [{"word": "Primeira", "start": 0.1, "end": 0.8}]},
        {"text": "frase", "start": 0.9, "end": 1.8,
         "words": [{"word": "frase", "start": 0.9, "end": 1.8}]},
        {"text": "Segunda frase", "start": 2.1, "end": 3.8,
         "words": [{"word": "Segunda", "start": 2.1, "end": 2.8},
                   {"word": "frase", "start": 2.9, "end": 3.8}]},
    ]

    palavras, segmentos = montar_saida_alinhamento(alinhados, originais)

    assert [item["id"] for item in segmentos] == ["B0-S01", "B0-S02"]
    assert [item["segmento_id"] for item in palavras] == [
        "B0-S01", "B0-S01", "B0-S02", "B0-S02"
    ]


def test_transcricao_sem_roteiro_preserva_segmentos_asr():
    alinhados = [
        {"text": "Uma frase", "start": 0.0, "end": 1.0,
         "words": [{"word": "Uma", "start": 0.0, "end": 0.4}]}
    ]
    palavras, segmentos = montar_saida_alinhamento(alinhados)
    assert segmentos[0]["texto"] == "Uma frase"
    assert palavras[0]["segmento_id"] == ""
