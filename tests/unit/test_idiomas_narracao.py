"""Narração extra e retime preservam IDs e proporções sem alterar o plano mestre."""

import json
import wave
from types import SimpleNamespace

import pytest

from docforja.esquemas import Bloco, Plano, Shot
from docforja.idiomas.narracao import executar_narracoes_extras, narracoes_extras_validas
from docforja.idiomas.retime import retimar_plano
from docforja.idiomas.traducao import executar_traducao_projeto
from docforja.nucleo.executor import ExecutorPipeline
from docforja.nucleo.handlers import registrar_handlers_disponiveis
from docforja.nucleo.projeto import Projeto

ORIGEM = """## B0 — Introdução
**B0-S01** O Vesúvio desperta.
**B0-S02** A cidade observa.
"""

INGLES = """## B0 — Introduction
**B0-S01** Vesuvius wakes.
**B0-S02** The city watches.
"""


class TTSFake:
    def disponivel(self):
        return True


class MotorFake:
    def __init__(self):
        self.tts = TTSFake()
        self.chamadas = 0
        self.vozes = []

    def processar_projeto_completo(
        self, segmentos, pasta_audio, idioma, voz=None, **kwargs
    ):
        self.chamadas += 1
        self.vozes.append(voz)
        pasta = pasta_audio / idioma
        pasta.mkdir(parents=True, exist_ok=True)
        wav = pasta / "narracao_completa.wav"
        with wave.open(str(wav), "wb") as arquivo:
            arquivo.setnchannels(1)
            arquivo.setsampwidth(2)
            arquivo.setframerate(8000)
            arquivo.writeframes(b"\x00\x00" * 8000)
        tempos = []
        for indice, segmento in enumerate(segmentos):
            tempos.append(
                {
                    "id": segmento.id,
                    "texto": segmento.texto_limpo,
                    "inicio_s": indice * 0.5,
                    "fim_s": (indice + 1) * 0.5,
                }
            )
        segmentos_path = pasta / "segmentos.json"
        segmentos_path.write_text(json.dumps(tempos), encoding="utf-8")
        palavras = pasta / "palavras.json"
        palavras.write_text("[]", encoding="utf-8")
        return SimpleNamespace(
            arquivo_completo_wav=wav,
            arquivo_segmentos_json=segmentos_path,
            arquivo_palavras_json=palavras,
            duracao_total_s=1.0,
        )


def test_narracao_extra_usa_traducao_voz_e_cache(tmp_path):
    projeto = Projeto.criar(
        "Narração extra",
        roteiro=ORIGEM,
        idiomas_extras=["en"],
        opcoes_adicionais={
            "traducao": {"modos": {"en": "arquivo"}},
            "vozes": {"en": "af_sarah"},
        },
        raiz_projetos=tmp_path,
    )
    (projeto.pastas.entrada / "traducao_en.md").write_text(INGLES, encoding="utf-8")
    executar_traducao_projeto(projeto)
    motor = MotorFake()

    executar_narracoes_extras(projeto, motor)

    assert motor.chamadas == 1
    assert motor.vozes == ["af_sarah"]
    segmentos = json.loads(
        (projeto.pastas.audio / "en" / "segmentos.json").read_text(encoding="utf-8")
    )
    assert [item["texto"] for item in segmentos] == [
        "Vesuvius wakes.", "The city watches."
    ]
    assert narracoes_extras_validas(projeto) is True
    executar_narracoes_extras(projeto, motor)
    assert motor.chamadas == 1


def test_retime_mantem_fracoes_e_plano_original():
    plano = Plano(
        projeto="teste",
        blocos=[
            Bloco(
                id="B0",
                titulo="Introdução",
                shots=[
                    Shot(
                        id="B0-01", segmentos=["B0-S01"], duracao_s=1,
                        inicio_segmento_s=0, fim_segmento_s=1, template="T01",
                    ),
                    Shot(
                        id="B0-02", segmentos=["B0-S01"], duracao_s=3,
                        inicio_segmento_s=1, fim_segmento_s=4, template="T01",
                    ),
                ],
            )
        ],
    )
    origem = [{"id": "B0-S01", "inicio_s": 0, "fim_s": 4}]
    destino = [{"id": "B0-S01", "inicio_s": 0, "fim_s": 8}]

    resultado = retimar_plano(plano, origem, destino)

    assert plano.blocos[0].shots[0].fim_segmento_s == 1
    assert resultado.blocos[0].shots[0].fim_segmento_s == 2
    assert resultado.blocos[0].shots[1].inicio_segmento_s == 2
    assert resultado.blocos[0].shots[1].fim_segmento_s == 8
    assert resultado.blocos[0].shots[-1].fim_s == 8


@pytest.mark.anyio
async def test_handler_t2_conclui_somente_com_artefatos_validos(tmp_path):
    projeto = Projeto.criar(
        "Pipeline idioma",
        roteiro=ORIGEM,
        idiomas_extras=["en"],
        opcoes_adicionais={"traducao": {"modos": {"en": "arquivo"}}},
        raiz_projetos=tmp_path,
    )
    (projeto.pastas.entrada / "traducao_en.md").write_text(INGLES, encoding="utf-8")
    executor = registrar_handlers_disponiveis(ExecutorPipeline(projeto), MotorFake())

    status = await executor.executar(ate_etapa="T2_narracao_idiomas")

    assert status["T1_traducao"] == "concluida"
    assert status["T2_narracao_idiomas"] == "concluida"
    assert narracoes_extras_validas(projeto) is True
