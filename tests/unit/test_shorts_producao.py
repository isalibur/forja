from __future__ import annotations

import hashlib
import json
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from docforja.esquemas import Plano
from docforja.idiomas.traducao import RoteiroTraduzido, SegmentoTraduzido
from docforja.io import atomic_write_json
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.nucleo.projeto import Projeto
from docforja.shorts.candidatos import pontuar_candidatos_do_plano
from docforja.shorts.modelos import (
    AtivoReenquadrado,
    CandidatoShort,
    CropVertical,
    FrasePonte,
    ManifestoVertical,
    ShotVerticalizado,
)
from docforja.shorts.producao import (
    _agrupar_palavras,
    _captions_remotion,
    _metadados,
    _rotulos_cta,
    _srt,
    aprovar_ponte_short_idioma,
    produzir_short_derivado,
)


def _escrever_wav(caminho: Path, duracao: float) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(caminho), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(24_000)
        arquivo.writeframes(b"\x00\x00" * int(24_000 * duracao))


def test_legendas_sao_frases_legiveis_com_palavra_falada_destacada() -> None:
    palavras = [
        {"text": "No", "start": 0.0, "end": 0.4},
        {"text": "início", "start": 0.4, "end": 0.9},
        {"text": "do", "start": 0.9, "end": 1.1},
        {"text": "século", "start": 1.1, "end": 1.7},
        {"text": "vinte,", "start": 1.7, "end": 2.2},
        {"text": "a", "start": 2.2, "end": 2.4},
        {"text": "equipe", "start": 2.4, "end": 3.0},
        {"text": "chegou.", "start": 3.0, "end": 3.7},
    ]

    grupos = _agrupar_palavras(palavras)
    captions = _captions_remotion(palavras, 0.0, 3.7)
    srt = _srt(palavras)

    assert [grupo["text"] for grupo in grupos] == [
        "No início do século vinte, a equipe chegou."
    ]
    assert len(captions) == 1
    assert captions[0].text == grupos[0]["text"]
    assert len(captions[0].palavras) == len(palavras)
    assert captions[0].palavras[1].startMs == 400
    assert "No início do século vinte, a equipe chegou." in " ".join(srt.split())
    assert srt.count("\n\n") == 0


def test_metadados_short_oferecem_titulos_exatos_e_limites(tmp_path: Path) -> None:
    projeto = Projeto.criar(
        nome="História Antiga",
        roteiro="Roteiro",
        raiz_projetos=tmp_path,
    )
    candidato = CandidatoShort(
        id="candidato-1",
        inicio_s=0,
        fim_s=20,
        segmento_ids=["S01"],
        texto="Uma descoberta histórica aconteceu em um instante inesperado nos arquivos antigos.",
        pontuacao=80,
        componentes={"autonomia": 8},
    )

    dados = _metadados(projeto, candidato, "Veja o vídeo completo.", "pt-BR")
    titulos = dados["arquivos"]["titulos.md"].splitlines()
    opcoes = [linha.split(". ", 1)[1] for linha in titulos if linha[:1].isdigit()]

    assert 5 <= len(opcoes) <= 8
    assert all(len(titulo) <= 40 for titulo in opcoes)
    assert all(titulo in candidato.texto for titulo in opcoes)
    assert "vincular como vídeo relacionado" in dados["arquivos"]["youtube.md"]
    assert "#Shorts" in dados["arquivos"]["instagram.md"]
    dados_en = _metadados(projeto, candidato, "Watch the full video.", "en")
    assert "Title:" in dados_en["arquivos"]["youtube.md"]
    assert "Related video:" in dados_en["arquivos"]["youtube.md"]
    assert "Vertical video with narration:" in dados_en["arquivos"]["instagram.md"]
    with pytest.raises(ValueError, match="CTA"):
        _rotulos_cta("fr-FR")


def test_producao_renderiza_revisao_sem_alterar_midia_manual(tmp_path, monkeypatch) -> None:
    projeto = Projeto.criar(
        nome="Short Integrado",
        roteiro="Roteiro",
        raiz_projetos=tmp_path,
        idiomas_extras=["en"],
        opcoes_adicionais={
            "voz": "voz-teste",
            "motor_tts": "kokoro",
            "vozes": {"en": "voz-en-teste"},
        },
    )
    imagem = projeto.pastas.midias / "manual" / "A-001.png"
    imagem.parent.mkdir(parents=True, exist_ok=True)
    imagem.write_bytes(b"imagem de teste, somente leitura")
    sidecar = imagem.with_name(f"{imagem.name}.licenca.json")
    atomic_write_json(sidecar, {"licenca": "CC0-1.0", "comercial": True})
    imagem_antes = imagem.read_bytes()
    sidecar_antes = sidecar.read_bytes()
    plano = {
        "projeto": projeto.slug,
        "tipo": "longo",
        "blocos": [
            {
                "id": "B0",
                "titulo": "Descoberta",
                "shots": [
                    {
                        "id": "B0-01",
                        "segmentos": ["S01"],
                        "duracao_s": 20,
                        "inicio_s": 0,
                        "fim_s": 20,
                        "template": "T01",
                        "ativos": ["A-001"],
                    }
                ],
            }
        ],
        "ativos": {
            "A-001": {
                "id": "A-001",
                "descricao": "Ilustração licenciada",
                "caminho": str(imagem),
                "licenca": {"licenca": "CC0-1.0", "comercial": True},
            }
        },
    }
    atomic_write_json(projeto.pastas.plano / "plano.json", plano)
    audio_dir = projeto.pastas.audio / "pt-BR"
    _escrever_wav(audio_dir / "narracao_completa.wav", 21)
    atomic_write_json(
        audio_dir / "segmentos.json",
        [{"id": "S01", "inicio_s": 0, "fim_s": 20, "texto": "Uma descoberta histórica aconteceu."}],
    )
    traducao = RoteiroTraduzido(
        idioma="en",
        hash_roteiro_origem=hashlib.sha256(projeto.obter_roteiro().encode("utf-8")).hexdigest(),
        hash_traducao="e" * 64,
        segmentos=[
            SegmentoTraduzido(
                id="S01",
                bloco="B0",
                texto_original="Uma descoberta histórica aconteceu.",
                texto_limpo="A historic discovery happened.",
            )
        ],
    )
    pasta_traducao = projeto.pastas.plano / "idiomas" / "en"
    pasta_traducao.mkdir(parents=True)
    atomic_write_json(pasta_traducao / "roteiro_eeeeeeeeeeeeeeee.json", traducao.model_dump())
    atomic_write_json(pasta_traducao / "atual.json", {"versao": "roteiro_eeeeeeeeeeeeeeee.json"})
    audio_en = projeto.pastas.audio / "en"
    _escrever_wav(audio_en / "narracao_completa.wav", 23)
    atomic_write_json(
        audio_en / "segmentos.json",
        [{"id": "S01", "inicio_s": 0, "fim_s": 22, "texto": "A historic discovery happened."}],
    )
    atomic_write_json(
        audio_en / "palavras.json",
        [
            {"segmento_id": "S01", "palavra": "A", "inicio_s": 0, "fim_s": 2},
            {"segmento_id": "S01", "palavra": "historic", "inicio_s": 2, "fim_s": 7},
            {"segmento_id": "S01", "palavra": "discovery", "inicio_s": 7, "fim_s": 14},
            {"segmento_id": "S01", "palavra": "happened.", "inicio_s": 14, "fim_s": 22},
        ],
    )
    atomic_write_json(
        audio_en / "narracao_idioma.json",
        {
            "hash_traducao": traducao.hash_traducao,
            "hash_saidas": {
                nome: calcular_hash_dados(audio_en / nome)
                for nome in ("narracao_completa.wav", "segmentos.json", "palavras.json")
            },
        },
    )
    candidato_base = pontuar_candidatos_do_plano(
        Plano.model_validate(plano),
        json.loads((audio_dir / "segmentos.json").read_text(encoding="utf-8")),
        limite=5,
    )[0]
    atomic_write_json(
        audio_dir / "palavras.json",
        [
            {"segmento_id": "S01", "palavra": "Uma", "inicio_s": 0, "fim_s": 4},
            {"segmento_id": "S01", "palavra": "descoberta", "inicio_s": 4, "fim_s": 8},
            {"segmento_id": "S01", "palavra": "histórica", "inicio_s": 8, "fim_s": 12},
            {"segmento_id": "S01", "palavra": "aconteceu.", "inicio_s": 12, "fim_s": 20},
        ],
    )
    referencia = "a" * 24
    pasta = projeto.pastas.montagem / "shorts" / "derivados" / referencia
    fonte_hash = calcular_hash_dados(
        {
            "plano": calcular_hash_dados(projeto.pastas.plano / "plano.json"),
            "segmentos": calcular_hash_dados(audio_dir / "segmentos.json"),
        }
    )
    candidato = CandidatoShort(
        id=candidato_base.id,
        inicio_s=0,
        fim_s=20,
        segmento_ids=["S01"],
        texto="Uma descoberta histórica aconteceu.",
        pontuacao=80,
        componentes={"autonomia": 8},
        frases_ponte=[FrasePonte(texto="Veja o vídeo completo.", aprovada=True)],
    )
    aprovacao_id = "b" * 64
    atomic_write_json(
        pasta / f"aprovacao-{aprovacao_id}.json",
        {"fonte_hash": fonte_hash, "candidato": candidato.model_dump(mode="json")},
    )
    atomic_write_json(
        pasta / "aprovacao_atual.json", {"versao": aprovacao_id, "fonte_hash": fonte_hash}
    )
    manifesto_id = "c" * 64
    manifesto = ManifestoVertical(
        projeto=projeto.slug,
        hash_entrada=manifesto_id,
        shots=[
            ShotVerticalizado(
                shot_id="B0-01",
                inicio_s=0,
                fim_s=20,
                template_origem="T01",
                ativos=[
                    AtivoReenquadrado(
                        ativo_id="A-001",
                        hash_origem=calcular_hash_dados(imagem),
                        recorte=CropVertical(x=0, y=0, largura=1, altura=1),
                    )
                ],
            )
        ],
    )
    atomic_write_json(
        pasta / f"manifesto-vertical-{manifesto_id}.json", manifesto.model_dump(mode="json")
    )
    atomic_write_json(
        pasta / "manifesto_atual.json",
        {"versao": manifesto_id, "aprovacao_versao": aprovacao_id, "fonte_hash": fonte_hash},
    )
    ponte_en = aprovar_ponte_short_idioma(
        projeto, referencia, "en", "The full story is in the complete video."
    )
    assert ponte_en["aprovacao"]["aprovada"] is True

    class OrquestradorFalso:
        tts = SimpleNamespace(disponivel=lambda: True)

        def processar_segmento(self, _segmento, pasta_destino, **_kwargs):
            destino = pasta_destino / "ponte-short.wav"
            _escrever_wav(destino, 0.5)
            return SimpleNamespace(arquivo_wav=destino)

    def executar_falso(comando, *, cwd, timeout=3600):
        destino = Path(comando[-1])
        _escrever_wav(destino, 0.5)
        return ""

    def renderizar_falso(_composicao, _props, _public, destino, *, still=False):
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(b"render de teste")

    monkeypatch.setattr(
        "docforja.shorts.producao._criar_orquestrador",
        lambda **_kwargs: OrquestradorFalso(),
    )
    monkeypatch.setattr("docforja.shorts.producao._executar", executar_falso)
    monkeypatch.setattr("docforja.shorts.producao._renderizar", renderizar_falso)
    monkeypatch.setattr("docforja.shorts.producao._mixar_audio", lambda *_args: (-14.1, True))
    monkeypatch.setattr(
        "docforja.shorts.producao.resolver_trilha_provisoria", lambda _projeto: None
    )

    resultado = produzir_short_derivado(projeto, referencia)
    cache = produzir_short_derivado(projeto, referencia)
    resultado_en = produzir_short_derivado(projeto, referencia, "en")

    assert resultado.status == "concluido"
    assert resultado.duracao_s == 20.5
    assert Path(resultado.caminho_video).is_file()
    assert Path(resultado.caminho_capa).is_file()
    assert Path(resultado.caminho_legendas).is_file()
    assert (Path(resultado.caminho_video).parent / "metadados" / "youtube.md").is_file()
    assert (Path(resultado.caminho_video).parents[2] / "atual.json").is_file()
    assert cache.cache is True
    assert resultado_en.idioma == "en"
    assert resultado_en.duracao_s == 22.5
    assert Path(resultado_en.caminho_video).is_file()
    legendas_en = Path(resultado_en.caminho_legendas).read_text(encoding="utf-8")
    assert "historic" in legendas_en and "discovery" in legendas_en
    assert "The full story is in the complete video." in (
        Path(resultado_en.caminho_video).parent / "metadados" / "metadados.json"
    ).read_text(encoding="utf-8")
    assert imagem.read_bytes() == imagem_antes
    assert sidecar.read_bytes() == sidecar_antes
