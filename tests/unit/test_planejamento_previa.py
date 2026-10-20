"""P8: a linha do tempo deve obedecer ao WAV, não à duração alterada pela dosagem."""

import pytest

from docforja.esquemas import Bloco, Plano, Shot
from docforja.nucleo.handlers import criar_executor_projeto
from docforja.nucleo.projeto import Projeto
from docforja.planejamento.estimativa import estimar_tempo_plano
from docforja.planejamento.previa import montar_manifesto_previa
from docforja.planejamento.relatorios import gerar_plano_md


def _plano() -> Plano:
    return Plano(
        projeto="teste",
        blocos=[
            Bloco(
                id="B0",
                titulo="Abertura",
                shots=[
                    Shot(id="B0-00", duracao_s=1, template="T00"),
                    Shot(id="B0-01", segmentos=["B0-S01"], duracao_s=1, template="T01"),
                    Shot(id="B0-02", segmentos=["B0-S02"], duracao_s=1, template="T06"),
                ],
            )
        ],
    )


def test_manifesto_usa_tempos_reais_e_cartao_sobreposto():
    segmentos = [
        {"id": "B0-S01", "inicio_s": 0, "fim_s": 4},
        {"id": "B0-S02", "inicio_s": 4, "fim_s": 9},
    ]
    manifesto = montar_manifesto_previa(_plano(), segmentos, {})
    assert manifesto["duracao_frames"] == 216
    assert [(s["inicio_frame"], s["fim_frame"]) for s in manifesto["shots"]] == [
        (0, 96), (96, 216)
    ]
    assert manifesto["cartoes"][0]["fim_frame"] == 24


def test_manifesto_recusa_segmento_ausente():
    with pytest.raises(ValueError, match="ordem ou cobertura"):
        montar_manifesto_previa(
            _plano(), [{"id": "B0-S01", "inicio_s": 0, "fim_s": 4}], {}
        )


def test_estimativa_p8_usa_duracao_real():
    curta = estimar_tempo_plano(_plano())
    real = estimar_tempo_plano(_plano(), duracao_audio_s=900)
    assert real.tempo_total_minutos > curta.tempo_total_minutos
    assert real.itens[0].quantidade == 900


def test_p8_exige_artefatos_em_projeto_novo(tmp_path):
    projeto = Projeto.criar(
        nome="p8_vazio", roteiro="## B0\n\n**B0-S01**\nTeste.", raiz_projetos=tmp_path
    )
    executor = criar_executor_projeto(projeto)
    assert "P8_estimativa_previa" in executor._handlers


def test_plano_md_mostra_horarios_reais_sem_somar_cartao():
    plano = _plano()
    cartao, primeiro, segundo = plano.blocos[0].shots
    cartao.inicio_s, cartao.fim_s = 0, 1
    primeiro.inicio_s, primeiro.fim_s, primeiro.duracao_s = 0, 4, 4
    segundo.inicio_s, segundo.fim_s, segundo.duracao_s = 4, 9, 5
    texto = gerar_plano_md(plano)
    assert "(00:00-00:09" in texto
    assert "| B0-02 | 00:04 · 5.0 s" in texto
