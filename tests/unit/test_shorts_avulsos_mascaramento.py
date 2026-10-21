import wave
from array import array
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from docforja.api import app
from docforja.shorts.avulsos import ler_lote_avulsos, ler_lote_avulsos_texto
from docforja.shorts.mascaramento import medir_mascaramento


def test_csv_cinco_temas_cria_pedidos_revisaveis_sem_inventar_roteiro(tmp_path: Path) -> None:
    csv_path = tmp_path / "temas.csv"
    csv_path.write_text(
        "tema,objetivo,duracao_s,formula,origem_roteiro,roteiro,cta\n"
        "Vesúvio,educativo,30,,,,\n"
        "Pompeia,promocao_canal,45,,,,\n"
        "Escavações,engajamento,30,,,,\n"
        "Museu,bastidores,45,,,,\n"
        "Nova série,anuncio,30,,,,\n",
        encoding="utf-8-sig",
    )

    pedidos = ler_lote_avulsos(csv_path)

    assert [pedido.id for pedido in pedidos] == ["A001", "A002", "A003", "A004", "A005"]
    assert len({pedido.formula_id for pedido in pedidos}) >= 4
    assert all(pedido.roteiro is None for pedido in pedidos)
    assert all("aprovar roteiro" in pedido.pendencias for pedido in pedidos)


def test_api_planeja_csv_colado_e_expoe_estrutura_para_revisao() -> None:
    texto = "tema,objetivo,duracao_s\nVesúvio,educativo,30\nPompeia,engajamento,30\n"
    resposta = TestClient(app).post(
        "/api/shorts/avulsos/planejar", json={"csv_texto": texto}
    )

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["status"] == "aguardando_revisao"
    assert dados["quantidade"] == 2
    assert set(dados["formulas"]) == {item["formula_id"] for item in dados["pedidos"]}
    assert all(dados["formulas"][item["formula_id"]]["estrutura"] for item in dados["pedidos"])
    assert ler_lote_avulsos_texto(texto)[0].tema == "Vesúvio"


def test_api_retorna_erro_de_linha_sem_gravar_pedido() -> None:
    resposta = TestClient(app).post(
        "/api/shorts/avulsos/planejar",
        json={"csv_texto": "tema,objetivo,duracao_s\nVesúvio,educativo,90\n"},
    )

    assert resposta.status_code == 400
    assert "Linha 2" in resposta.json()["detail"]


@pytest.mark.parametrize(
    ("conteudo", "erro"),
    [
        ("tema,objetivo,duracao_s\nTeste,educativo,90\n", "Nenhuma fórmula compatível"),
        (
            "tema,objetivo,duracao_s,origem_roteiro\nTeste,educativo,30,proprio\n",
            "Roteiro próprio exige texto",
        ),
        ("tema,tema,objetivo,duracao_s\nA,B,educativo,30\n", "colunas duplicadas"),
    ],
)
def test_csv_recusa_pedidos_que_nao_podem_ser_planejados(
    tmp_path: Path, conteudo: str, erro: str
) -> None:
    csv_path = tmp_path / "temas.csv"
    csv_path.write_text(conteudo, encoding="utf-8")
    with pytest.raises(ValueError, match=erro):
        ler_lote_avulsos(csv_path)


def _gravar_wav(caminho: Path, amostras: list[int]) -> None:
    with wave.open(str(caminho), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(1000)
        arquivo.writeframes(array("h", amostras).tobytes())


def test_medicao_sinaliza_aproximacao_da_musica_sem_aprovar_ds9(tmp_path: Path) -> None:
    voz = tmp_path / "voz.wav"
    musica = tmp_path / "musica.wav"
    _gravar_wav(voz, [5000] * 400)
    _gravar_wav(musica, [500] * 200 + [5000] * 200)

    medicao = medir_mascaramento(voz, musica)

    assert medicao.janelas_com_voz == 2
    assert medicao.fracao_janelas_acima_menos_6_db == 0.5
    assert medicao.possivel_mascaramento is True


def test_medicao_sem_voz_nao_declara_audio_aprovado(tmp_path: Path) -> None:
    voz = tmp_path / "voz.wav"
    musica = tmp_path / "musica.wav"
    _gravar_wav(voz, [0] * 200)
    _gravar_wav(musica, [1000] * 200)

    medicao = medir_mascaramento(voz, musica)

    assert medicao.janelas_com_voz == 0
    assert medicao.possivel_mascaramento is None
