"""Portões de produção avulsa, sem rede, GPU ou render real."""

from __future__ import annotations

import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from docforja.api import app
from docforja.shorts.modelos import ShortParaVerificar
from docforja.shorts.producao_avulsos import (
    _criar_cenas,
    _gancho,
    obter_artefato,
    preparar_producao,
    produzir_avulso,
)
from docforja.shorts.verificador import verificar_short


def _campanha_pronta(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    comercial: bool = False,
    roteiro: str = "Uma cena histórica. Veja a cena.",
    objetivo: str = "educativo",
    formula_id: str = "",
    cta: str = "Veja a cena",
) -> tuple[TestClient, Path, Path, str, str]:
    projetos = tmp_path / "projetos"
    global_ = tmp_path / "global"
    imagens = global_ / "imagens"
    imagens.mkdir(parents=True)
    (imagens / "cena.png").write_bytes(b"imagem-de-teste")
    (imagens / "cena.json").write_text(
        json.dumps(
            {
                "arquivo": "cena.png",
                "descricao": "Cena genérica",
                "licenca": "CC0-1.0",
                "comercial": True,
            }
        ),
        encoding="utf-8",
    )

    def settings() -> object:
        return type("Settings", (), {"paths": type("Paths", (), {"projects": projetos})()})()

    monkeypatch.setattr("docforja.api.load_settings", settings)
    monkeypatch.setattr("docforja.api.obter_pasta_global", lambda: global_)
    monkeypatch.setattr("docforja.shorts.producao_avulsos._voz_ptbr", lambda: "pm_alex")
    client = TestClient(app)
    csv = f"tema,objetivo,duracao_s,formula,roteiro,cta\nCena,{objetivo},30,{formula_id},,{cta}\n"
    campanha = client.post(
        "/api/shorts/avulsos/campanhas", json={"nome": "Teste", "csv_texto": csv}
    ).json()
    base = f"/api/shorts/avulsos/campanhas/{campanha['id']}/pedidos/A001"
    aprovacao = client.post(
        f"{base}/roteiro/aprovar",
        json={
            "texto": roteiro,
            "hash_campanha": campanha["hash_conteudo"],
        },
    ).json()
    selecao = client.post(
        f"{base}/midias/selecionar",
        json={
            "ids_globais": ["global:imagens:cena"],
            "hash_campanha": campanha["hash_conteudo"],
            "revisao_roteiro": aprovacao["revisao"],
        },
    ).json()
    dados_alegacoes: dict[str, object] = {
        "revisado_pelo_usuario": True,
        "relacao_comercial": "produto_proprio" if comercial else "nenhuma",
    }
    if objetivo in {"promocao_canal", "anuncio"}:
        dados_alegacoes["fontes"] = [
            {
                "alegacao": "Informação sintética para ensaio de produção.",
                "fonte": "Plano fictício do teste unitário.",
            }
        ]
    else:
        dados_alegacoes["sem_alegacoes_verificaveis"] = True
    ficha = client.post(
        f"{base}/alegacoes/registrar",
        json={
            "hash_campanha": campanha["hash_conteudo"],
            "revisao_roteiro": aprovacao["revisao"],
            "revisao_midias": selecao["revisao"],
            "dados": dados_alegacoes,
        },
    )
    assert ficha.status_code == 200
    return client, projetos, global_, campanha["id"], base


def test_producao_exige_codigo_e_revisoes_vigentes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, projetos, global_, campanha_id, base = _campanha_pronta(tmp_path, monkeypatch)
    assert client.post(f"{base}/produzir", json={"codigo": "sim"}).status_code == 403
    assert client.get(f"{base}/producao").json()["status"] == "nao_iniciada"
    preparo = preparar_producao(projetos, global_, campanha_id, "A001")
    assert preparo.cta == "Veja a cena"
    assert preparo.revisao_alegacoes

    monkeypatch.setattr("docforja.api.executar_avulso_background", lambda *_: None)
    resposta = client.post(f"{base}/produzir", json={"codigo": "PRODUZIR"})
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "aguardando"
    assert client.post(f"{base}/produzir", json={"codigo": "PRODUZIR"}).status_code == 409
    assert client.get(f"{base}/artefatos/video.mp4").status_code == 404

    imagem = global_ / "imagens" / "cena.png"
    imagem.write_bytes(b"imagem-modificada")
    assert client.post(f"{base}/produzir", json={"codigo": "PRODUZIR"}).status_code == 409


def test_avulso_comercial_e_bloqueado(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, projetos, global_, campanha_id, _ = _campanha_pronta(tmp_path, monkeypatch, comercial=True)
    with pytest.raises(ValueError, match="educativos"):
        preparar_producao(projetos, global_, campanha_id, "A001")


@pytest.mark.parametrize(
    ("objetivo", "formula_id", "titulo_cta"),
    [
        ("promocao_canal", "curiosidade_1_fato", "MAIS NO CANAL"),
        ("anuncio", "anuncio", "NOVIDADE"),
    ],
)
def test_objetivos_nao_comerciais_usam_cartao_final_sem_duplicar_cta(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    objetivo: str,
    formula_id: str,
    titulo_cta: str,
) -> None:
    _, projetos, global_, campanha_id, _ = _campanha_pronta(
        tmp_path,
        monkeypatch,
        roteiro="Uma informação de teste. Veja a cena.",
        objetivo=objetivo,
        formula_id=formula_id,
    )

    preparo = preparar_producao(projetos, global_, campanha_id, "A001")
    cenas = _criar_cenas(preparo, [], ["ativos/cena.png"], 30.0)

    assert preparo.objetivo == objetivo
    assert preparo.formula_id == formula_id
    assert cenas[0].props.variante == "V01"
    assert cenas[-1].props.variante == "V07"
    assert cenas[-1].props.titulo == titulo_cta
    assert [cena.props.cta for cena in cenas].count("Veja a cena") == 1
    assert all(cena.duracao_frames <= 75 for cena in cenas[1:])


def test_objetivo_sem_cenas_apropriadas_continua_bloqueado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, projetos, global_, campanha_id, _ = _campanha_pronta(
        tmp_path, monkeypatch, objetivo="engajamento", formula_id="pergunta_comentarios"
    )

    with pytest.raises(ValueError, match="Esta produção aceita"):
        preparar_producao(projetos, global_, campanha_id, "A001")


def test_teaser_sem_video_longo_relacionado_nao_e_liberado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, projetos, global_, campanha_id, _ = _campanha_pronta(
        tmp_path, monkeypatch, objetivo="promocao_canal", formula_id="teaser_video"
    )

    with pytest.raises(ValueError, match="render seguro"):
        preparar_producao(projetos, global_, campanha_id, "A001")


def test_cta_repetido_no_roteiro_bloqueia_render(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, projetos, global_, campanha_id, _ = _campanha_pronta(
        tmp_path, monkeypatch, roteiro="Veja a cena. Agora veja a cena."
    )
    with pytest.raises(ValueError, match="uma vez"):
        preparar_producao(projetos, global_, campanha_id, "A001")


def test_gancho_usa_primeira_frase_completa_quando_cabe_em_seis_palavras() -> None:
    assert _gancho("Um rio pode mudar de nome. O mesmo curso nasce pequeno.") == (
        "Um rio pode mudar de nome"
    )
    assert _gancho("Uma frase com mais de seis palavras precisa ser cortada no limite") == (
        "Uma frase com mais de seis"
    )


def test_cenas_e_ds9_avulso_sem_musica(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, projetos, global_, campanha_id, _ = _campanha_pronta(tmp_path, monkeypatch)
    preparo = preparar_producao(projetos, global_, campanha_id, "A001")
    palavras = [{"text": "Veja", "start": 0.0, "end": 0.5}]
    cenas = _criar_cenas(preparo, palavras, ["ativos/cena.png"], 5.0)
    assert cenas[0].props.variante == "V01"
    assert all(cena.duracao_frames <= 75 for cena in cenas[1:])
    assert len(cenas) == 3
    qa = verificar_short(
        ShortParaVerificar(
            duracao_s=30,
            duracao_alvo_s=30,
            inicio_gancho_visual_s=0,
            inicio_gancho_textual_s=0,
            inicio_gancho_falado_s=0,
            mudancas_visuais_s=[2.5 * n for n in range(1, 12)],
            possui_fala=False,
            quantidade_ctas_principais=1,
            audio_lufs_integrado=-14.0,
            musica_cobre_voz=False,
        )
    )
    assert next(item for item in qa.violacoes if item.regra == "DS9").aprovada
    with pytest.raises(ValueError, match="Artefato"):
        obter_artefato(projetos, global_, campanha_id, "A001", "../segredo")


@pytest.mark.parametrize(
    ("objetivo", "formula_id"),
    [
        ("educativo", ""),
        ("promocao_canal", "curiosidade_1_fato"),
        ("anuncio", "anuncio"),
    ],
)
def test_producao_piloto_publica_revisao_ou_usa_cache_sem_rederivar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, objetivo: str, formula_id: str
) -> None:
    _, projetos, global_, campanha_id, _ = _campanha_pronta(
        tmp_path, monkeypatch, objetivo=objetivo, formula_id=formula_id
    )
    preparo = preparar_producao(projetos, global_, campanha_id, "A001")
    chamadas = {"render": 0}

    class Narrador:
        tts = SimpleNamespace(disponivel=lambda: True)
        alinhador = SimpleNamespace(disponivel=lambda: True)

        def processar_projeto_completo(
            self, _segmentos: object, pasta: Path, **_kw: object
        ) -> object:
            pasta.mkdir(parents=True)
            audio = pasta / "voz.wav"
            audio.write_bytes(b"wav-simulado")
            palavras = pasta / "palavras.json"
            palavras.write_text(
                json.dumps(
                    [
                        {"segmento_id": "avulso", "palavra": "Veja", "inicio_s": 0, "fim_s": 15},
                        {"segmento_id": "avulso", "palavra": "a cena", "inicio_s": 15, "fim_s": 30},
                    ]
                ),
                encoding="utf-8",
            )
            return SimpleNamespace(
                wer_medio=0.0,
                duracao_total_s=30.0,
                arquivo_completo_wav=audio,
                arquivo_palavras_json=palavras,
            )

    def mixar(_voz: Path, destino: Path, _trilha: object, _relatorio: Path) -> tuple[float, None]:
        destino.write_bytes(b"mix-simulado")
        return -14.0, None

    def renderizar(
        _composicao: str, _props: Path, _public: Path, destino: Path, *, still: bool = False
    ) -> None:
        chamadas["render"] += 1
        destino.write_bytes(b"capa" if still else b"video")

    monkeypatch.setattr(
        "docforja.shorts.producao_avulsos._criar_orquestrador", lambda _: Narrador()
    )
    monkeypatch.setattr(
        "docforja.shorts.producao_avulsos._criar_orquestrador", lambda _: Narrador()
    )
    monkeypatch.setattr(
        "docforja.shorts.producao_avulsos.semaforo_gpu.adquirir_sync", lambda **_: nullcontext()
    )
    monkeypatch.setattr("docforja.shorts.producao_avulsos._mixar_audio", mixar)
    monkeypatch.setattr("docforja.shorts.producao_avulsos._medir_lufs", lambda _caminho: -14.0)
    monkeypatch.setattr("docforja.shorts.producao_avulsos._renderizar", renderizar)

    primeira = produzir_avulso(projetos, global_, preparo)
    assert primeira["status"] == "concluido"
    assert chamadas["render"] == 2
    assert produzir_avulso(projetos, global_, preparo)["cache"] is True
    assert chamadas["render"] == 2
    saida = projetos / "_campanhas_avulsas" / campanha_id / "saidas" / "A001"
    meta = json.loads((saida / "revisoes" / preparo.revisao / "metadados.json").read_text())
    assert meta["publicacao_autorizada"] is False
    assert meta["objetivo"] == objetivo
    assert meta["formula_id"] == preparo.formula_id
    assert meta["fontes"]["roteiro"] == preparo.revisao_roteiro
    ds9 = next(item for item in meta["qa"]["violacoes"] if item["regra"] == "DS9")
    assert ds9["aprovada"] is True
    assert "-14.0 LUFS" in ds9["detalhes"]
