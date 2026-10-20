"""Narração extra e retime preservam IDs e proporções sem alterar o plano mestre."""

import json
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from docforja.esquemas import Bloco, Plano, Shot
from docforja.idiomas.narracao import executar_narracoes_extras, narracoes_extras_validas
from docforja.idiomas.retime import retimar_plano
from docforja.idiomas.traducao import executar_traducao_projeto
from docforja.nucleo.banco import BancoProjeto
from docforja.nucleo.etapas import DefinicaoEtapa
from docforja.nucleo.executor import ContextoEtapa, ExecutorPipeline
from docforja.nucleo.handlers import registrar_handlers_disponiveis
from docforja.nucleo.projeto import Projeto
from docforja.producao.execucao import (
    executar_r5_montagem,
    executar_r6_mix,
    executar_r7_render,
    executar_r8_qa,
    executar_r9_pacote,
)

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


def test_producao_multilingue_gera_artefatos_separados(tmp_path, monkeypatch):
    projeto = Projeto.criar(
        "Produção idiomas",
        roteiro=ORIGEM,
        idiomas_extras=["en"],
        opcoes_adicionais={"traducao": {"modos": {"en": "arquivo"}}},
        raiz_projetos=tmp_path,
    )
    plano = Plano(
        projeto=projeto.slug,
        blocos=[
            Bloco(
                id="B0",
                titulo="Introdução",
                shots=[
                    Shot(
                        id="B0-01", segmentos=["B0-S01"], duracao_s=0.5,
                        inicio_segmento_s=0, fim_segmento_s=0.5, template="T06",
                        textos=["O Vesúvio desperta."], params={"texto": "O Vesúvio desperta."},
                    ),
                    Shot(
                        id="B0-02", segmentos=["B0-S02"], duracao_s=0.5,
                        inicio_segmento_s=0, fim_segmento_s=0.5, template="T01",
                    ),
                ],
            )
        ],
    )
    for nome in ("plano.json", "plano_verificado.json"):
        (projeto.pastas.plano / nome).write_text(plano.model_dump_json(), encoding="utf-8")
    (projeto.pastas.entrada / "traducao_en.md").write_text(INGLES, encoding="utf-8")
    executar_traducao_projeto(projeto)
    executar_narracoes_extras(projeto, MotorFake())

    audio_principal = projeto.pastas.audio / "pt-BR"
    with wave.open(str(audio_principal / "narracao_completa.wav"), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(8000)
        arquivo.writeframes(b"\x00\x00" * 8000)
    (audio_principal / "segmentos.json").write_text(
        json.dumps([
            {"id": "B0-S01", "texto": "O Vesúvio desperta.", "inicio_s": 0, "fim_s": 0.5},
            {"id": "B0-S02", "texto": "A cidade observa.", "inicio_s": 0.5, "fim_s": 1},
        ]),
        encoding="utf-8",
    )
    (projeto.pastas.plano / "previa.mp4").write_bytes(b"video-base")
    contexto = ContextoEtapa(
        projeto=projeto,
        etapa=DefinicaoEtapa(id="R5_montagem"),
        banco=BancoProjeto(projeto.banco_file),
    )

    def subprocess_fake(comando, **kwargs):
        Path(comando[-1]).write_bytes(b"video-dublado")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("docforja.producao.execucao.subprocess.run", subprocess_fake)
    executar_r5_montagem(contexto)
    executar_r6_mix(contexto)
    executar_r7_render(contexto)
    executar_r8_qa(contexto)
    executar_r9_pacote(contexto)

    plano_en = json.loads(
        (projeto.pastas.plano / "idiomas" / "en" / "plano_retimado.json").read_text(
            encoding="utf-8"
        )
    )
    assert plano_en["blocos"][0]["shots"][0]["textos"] == ["Vesuvius wakes."]
    assert (projeto.pastas.plano / "i18n" / "en.json").is_file()
    assert (projeto.pastas.sistema / "montagem" / "en" / "timeline.otio").is_file()
    assert (projeto.pastas.audio / "en" / "mix_final.wav").is_file()
    assert (projeto.pastas.saida / "en" / "video.mp4").is_file()
    assert "Vesuvius wakes." in (
        projeto.pastas.saida / "en" / "legendas" / "legendas.srt"
    ).read_text(encoding="utf-8")
    assert (projeto.pastas.saida / "en" / "video" / "video.mp4").is_file()
    assert (projeto.pastas.saida / "en" / "metadados" / "PENDENTE.md").is_file()
