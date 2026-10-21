"""Narração extra e retime preservam IDs e proporções sem alterar o plano mestre."""

import json
import shutil
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from docforja.esquemas import Bloco, Plano, Shot
from docforja.idiomas.narracao import executar_narracoes_extras, narracoes_extras_validas
from docforja.idiomas.retime import retimar_plano
from docforja.idiomas.traducao import executar_traducao_projeto
from docforja.io import atomic_write_json
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


def _instalar_mix_fake(monkeypatch):
    def mix_fake(narracao, destino, idioma, trilha=None):
        shutil.copyfile(narracao, destino)
        atomic_write_json(
            destino.with_name("relatorio_mix.json"),
            {
                "etapa": "R6_mix",
                "idioma": idioma,
                "medido_lufs": -14.0,
                "true_peak_dbtp": -1.0,
                "lra_lu": 7.0,
                "ganho_trilha_sob_fala": 0.12 if trilha else None,
                "sidechain_ducking": "teste",
                "hash_mix": "hash-mock",
                "hash_narracao": "hash-voz",
                "hash_trilha": "hash-trilha" if trilha else None,
            },
        )

    monkeypatch.setattr("docforja.producao.execucao.mixar_audio", mix_fake)


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
    _instalar_mix_fake(monkeypatch)
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
    assert (projeto.pastas.saida / "en" / "metadados" / "titulos.md").is_file()
    assert (projeto.pastas.saida / "en" / "metadados" / "descricao.md").is_file()
    assert (projeto.pastas.saida / "en" / "metadados" / "capitulos.txt").is_file()
    assert (projeto.pastas.saida / "en" / "metadados" / "metadados.json").is_file()
    assert not (projeto.pastas.saida / "en" / "metadados" / "PENDENTE.md").exists()


def test_modo_so_legendas_sem_tts_e_sincronizado_ao_base(tmp_path, monkeypatch):
    """No modo só legendas, não executa TTS e gera legendas sincronizadas ao vídeo-base."""
    projeto = Projeto.criar(
        "Modo Legendas",
        roteiro=ORIGEM,
        idiomas_extras=["en"],
        opcoes_adicionais={
            "traducao": {"modos": {"en": "arquivo"}},
            "idiomas": {"so_legendas": ["en"]},
        },
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
                        id="B0-01", segmentos=["B0-S01"], duracao_s=4.0,
                        inicio_segmento_s=0, fim_segmento_s=4.0, template="T01",
                        textos=["O Vesúvio desperta."],
                    ),
                    Shot(
                        id="B0-02", segmentos=["B0-S02"], duracao_s=5.0,
                        inicio_segmento_s=0, fim_segmento_s=5.0, template="T08",
                        textos=["A cidade observa."],
                    ),
                ],
            )
        ],
    )
    for nome in ("plano.json", "plano_verificado.json"):
        (projeto.pastas.plano / nome).write_text(plano.model_dump_json(), encoding="utf-8")
    (projeto.pastas.entrada / "traducao_en.md").write_text(INGLES, encoding="utf-8")
    executar_traducao_projeto(projeto)

    # Base audio em pt-BR
    audio_pt = projeto.pastas.audio / "pt-BR"
    with wave.open(str(audio_pt / "narracao_completa.wav"), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(8000)
        arquivo.writeframes(b"\x00\x00" * 8000)
    (audio_pt / "segmentos.json").write_text(
        json.dumps([
            {"id": "B0-S01", "texto": "O Vesúvio desperta.", "inicio_s": 0.0, "fim_s": 4.0},
            {"id": "B0-S02", "texto": "A cidade observa.", "inicio_s": 4.0, "fim_s": 9.0},
        ]),
        encoding="utf-8",
    )
    (projeto.pastas.plano / "previa.mp4").write_bytes(b"video-base-pt")

    # Motor com TTS indisponível: deve funcionar pois é só legendas!
    class MotorSemTTS:
        class TTSIndisponivel:
            def disponivel(self):
                return False
        tts = TTSIndisponivel()

    executar_narracoes_extras(projeto, MotorSemTTS())
    assert narracoes_extras_validas(projeto)

    segs_en = json.loads(
        (projeto.pastas.audio / "en" / "segmentos.json").read_text(encoding="utf-8")
    )
    assert segs_en[0]["inicio_s"] == 0.0
    assert segs_en[0]["fim_s"] == 4.0
    assert segs_en[0]["texto"] == "Vesuvius wakes."
    assert segs_en[1]["inicio_s"] == 4.0
    assert segs_en[1]["fim_s"] == 9.0
    assert segs_en[1]["texto"] == "The city watches."

    manifesto_narr = json.loads(
        (projeto.pastas.audio / "en" / "narracao_idioma.json").read_text(encoding="utf-8")
    )
    assert manifesto_narr.get("modo") == "so_legendas"

    contexto = ContextoEtapa(
        projeto=projeto,
        etapa=DefinicaoEtapa(id="R7_render"),
        banco=BancoProjeto(projeto.banco_file),
    )
    _instalar_mix_fake(monkeypatch)
    executar_r5_montagem(contexto)
    executar_r6_mix(contexto)
    executar_r7_render(contexto)
    executar_r8_qa(contexto)
    executar_r9_pacote(contexto)

    manifesto_r7 = json.loads(
        (projeto.pastas.saida / "en" / "manifesto_r7.json").read_text(encoding="utf-8")
    )
    assert manifesto_r7.get("modo") == "so_legendas"
    srt_conteudo = (projeto.pastas.saida / "en" / "legendas" / "legendas.srt").read_text(
        encoding="utf-8"
    )
    assert "00:00:00,000 --> 00:00:04,000" in srt_conteudo
    assert "Vesuvius wakes." in srt_conteudo
    assert "00:00:04,000 --> 00:00:09,000" in srt_conteudo
    assert "The city watches." in srt_conteudo


def test_render_remotion_consome_plano_retimado_e_i18n(tmp_path, monkeypatch):
    """Verifica que o render Remotion recebe props com plano retimado, i18n e duração exata."""
    projeto = Projeto.criar(
        "Render Localizado",
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
                        id="B0-01", segmentos=["B0-S01"], duracao_s=2.0,
                        inicio_segmento_s=0, fim_segmento_s=2.0, template="T06",
                        textos=["O Vesúvio desperta."], params={"texto": "O Vesúvio desperta."},
                    ),
                ],
            )
        ],
    )
    for nome in ("plano.json", "plano_verificado.json"):
        (projeto.pastas.plano / nome).write_text(plano.model_dump_json(), encoding="utf-8")
    (projeto.pastas.entrada / "traducao_en.md").write_text(INGLES, encoding="utf-8")
    executar_traducao_projeto(projeto)

    # Áudio inglês retimado com 3.5 segundos (diferente de pt-BR)
    audio_en = projeto.pastas.audio / "en"
    audio_en.mkdir(parents=True, exist_ok=True)
    with wave.open(str(audio_en / "narracao_completa.wav"), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(8000)
        arquivo.writeframes(b"\x00\x00" * 28000)
    (audio_en / "segmentos.json").write_text(
        json.dumps([{"id": "B0-S01", "texto": "Vesuvius wakes.", "inicio_s": 0.0, "fim_s": 3.5}]),
        encoding="utf-8",
    )
    (audio_en / "palavras.json").write_text("[]", encoding="utf-8")

    audio_pt = projeto.pastas.audio / "pt-BR"
    audio_pt.mkdir(parents=True, exist_ok=True)
    with wave.open(str(audio_pt / "narracao_completa.wav"), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(8000)
        arquivo.writeframes(b"\x00\x00" * 16000)
    (audio_pt / "segmentos.json").write_text(
        json.dumps([
            {"id": "B0-S01", "texto": "O Vesúvio desperta.", "inicio_s": 0.0, "fim_s": 2.0}
        ]),
        encoding="utf-8",
    )

    (projeto.pastas.plano / "previa.mp4").write_bytes(b"video-base-portugues-2s")
    contexto = ContextoEtapa(
        projeto=projeto,
        etapa=DefinicaoEtapa(id="R7_render"),
        banco=BancoProjeto(projeto.banco_file),
    )

    comando_capturado = []
    props_capturadas = []

    def subprocess_spy(comando, **kwargs):
        comando_capturado.append(list(comando))
        # Extrai props.json
        props_arg = next(arg for arg in comando if arg.startswith("--props="))
        props_path = Path(props_arg.split("=", 1)[1])
        props_capturadas.append(json.loads(props_path.read_text(encoding="utf-8")))

        # Simula saída gerada pelo Remotion
        out_arg = comando[8] if len(comando) > 8 else comando[-1]
        Path(out_arg).write_bytes(b"video-remotion-renderizado-en-3.5s")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("docforja.producao.execucao.subprocess.run", subprocess_spy)
    _instalar_mix_fake(monkeypatch)

    executar_r5_montagem(contexto)
    executar_r6_mix(contexto)
    executar_r7_render(contexto)

    # Remotion foi acionado para renderizar o inglês!
    assert len(comando_capturado) == 1
    props_en = props_capturadas[0]
    assert props_en["idioma"] == "en"
    assert props_en["tem_trilha_provisoria"] is False
    assert props_en["i18n"]["B0-S01"] == "Vesuvius wakes."
    assert props_en["shots"][0]["texto"] == "Vesuvius wakes."
    assert props_en["duracao_frames"] == 84  # 3.5s * 24 fps

    # O vídeo final não reutilizou os bytes de previa.mp4 em português!
    video_en = projeto.pastas.saida / "en" / "video.mp4"
    assert video_en.read_bytes() == b"video-remotion-renderizado-en-3.5s"
    assert video_en.read_bytes() != b"video-base-portugues-2s"

    manifesto_r7 = json.loads(
        (projeto.pastas.saida / "en" / "manifesto_r7.json").read_text(encoding="utf-8")
    )
    assert manifesto_r7["duracao_s"] == 3.5
    assert manifesto_r7["duracao_frames"] == 84
