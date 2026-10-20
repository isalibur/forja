from __future__ import annotations

import json
import wave
from pathlib import Path
from types import SimpleNamespace

from docforja.esquemas import Plano
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
from docforja.shorts.producao import _metadados, produzir_short_derivado


def _escrever_wav(caminho: Path, duracao: float) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(caminho), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(24_000)
        arquivo.writeframes(b"\x00\x00" * int(24_000 * duracao))


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


def test_producao_renderiza_revisao_sem_alterar_midia_manual(tmp_path, monkeypatch) -> None:
    projeto = Projeto.criar(
        nome="Short Integrado",
        roteiro="Roteiro",
        raiz_projetos=tmp_path,
        opcoes_adicionais={"voz": "voz-teste", "motor_tts": "kokoro"},
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

    assert resultado.status == "concluido"
    assert resultado.duracao_s == 20.5
    assert Path(resultado.caminho_video).is_file()
    assert Path(resultado.caminho_capa).is_file()
    assert Path(resultado.caminho_legendas).is_file()
    assert (Path(resultado.caminho_video).parent / "metadados" / "youtube.md").is_file()
    assert (Path(resultado.caminho_video).parents[2] / "atual.json").is_file()
    assert cache.cache is True
    assert imagem.read_bytes() == imagem_antes
    assert sidecar.read_bytes() == sidecar_antes
