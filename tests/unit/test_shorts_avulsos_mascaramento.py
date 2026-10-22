import json
import wave
from array import array
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from docforja.api import app
from docforja.shorts.avulsos import ler_lote_avulsos, ler_lote_avulsos_texto
from docforja.shorts.campanhas import obter_campanha
from docforja.shorts.mascaramento import medir_mascaramento
from docforja.shorts.midias_avulsas import (
    listar_imagens_globais,
    listar_midias_globais,
    resolver_imagem_global,
    resolver_midia_global,
)


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
    resposta = TestClient(app).post("/api/shorts/avulsos/planejar", json={"csv_texto": texto})

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


def test_campanha_avulsa_persiste_snapshot_sem_aprovacao_ou_producao(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def mock_settings() -> object:
        return type("Settings", (), {"paths": type("Paths", (), {"projects": tmp_path})()})()

    monkeypatch.setattr("docforja.api.load_settings", mock_settings)
    client = TestClient(app)
    payload = {
        "nome": "Ensaio editorial",
        "csv_texto": (
            "tema,objetivo,duracao_s,roteiro\n"
            'Pompeia,educativo,30,"A cidade foi soterrada pela erupção."\n'
        ),
    }
    primeira = client.post("/api/shorts/avulsos/campanhas", json=payload)
    segunda = client.post("/api/shorts/avulsos/campanhas", json=payload)

    assert primeira.status_code == 201
    assert segunda.json() == primeira.json()
    campanha = primeira.json()
    assert campanha["status"] == "aguardando_revisao"
    assert campanha["pedidos"][0]["roteiro"] == "A cidade foi soterrada pela erupção."
    assert "aprovar roteiro" in campanha["pedidos"][0]["pendencias"]
    assert client.get("/api/shorts/avulsos/campanhas").json() == [campanha]
    assert client.get(f"/api/shorts/avulsos/campanhas/{campanha['id']}").json() == campanha
    assert obter_campanha(tmp_path, campanha["id"]).id == campanha["id"]
    assert list((tmp_path / "_campanhas_avulsas").glob("*.json"))
    assert not list(tmp_path.glob("*/05_saida"))


def test_campanha_avulsa_invalida_nao_grava_e_id_invalido_falha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def mock_settings() -> object:
        return type("Settings", (), {"paths": type("Paths", (), {"projects": tmp_path})()})()

    monkeypatch.setattr("docforja.api.load_settings", mock_settings)
    client = TestClient(app)
    resposta = client.post(
        "/api/shorts/avulsos/campanhas",
        json={"nome": "Teste", "csv_texto": "tema,objetivo,duracao_s\nA,educativo,90\n"},
    )
    assert resposta.status_code == 400
    assert not (tmp_path / "_campanhas_avulsas").exists()
    assert client.get("/api/shorts/avulsos/campanhas/nao-valido").status_code == 404


def test_aprovacao_de_roteiro_avulso_e_versionada_sem_alterar_campanha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def mock_settings() -> object:
        return type("Settings", (), {"paths": type("Paths", (), {"projects": tmp_path})()})()

    monkeypatch.setattr("docforja.api.load_settings", mock_settings)
    client = TestClient(app)
    campanha = client.post(
        "/api/shorts/avulsos/campanhas",
        json={
            "nome": "Campanha",
            "csv_texto": "tema,objetivo,duracao_s\nPompeia,educativo,30\n",
        },
    ).json()
    caminho_snapshot = tmp_path / "_campanhas_avulsas" / f"{campanha['id']}.json"
    snapshot_original = caminho_snapshot.read_bytes()
    url = f"/api/shorts/avulsos/campanhas/{campanha['id']}/pedidos/A001/roteiro/aprovar"
    payload = {"texto": "Texto revisado pelo usuário.", "hash_campanha": campanha["hash_conteudo"]}

    primeira = client.post(url, json=payload)
    assert primeira.status_code == 200
    aprovacao = primeira.json()
    assert aprovacao["status"] == "roteiro_aprovado"
    assert aprovacao["texto"] == "Texto revisado pelo usuário."
    assert client.post(url, json=payload).json() == aprovacao

    segunda = client.post(
        url, json={"texto": "Outra revisão humana.", "hash_campanha": campanha["hash_conteudo"]}
    )
    assert segunda.status_code == 200
    assert segunda.json()["revisao"] != aprovacao["revisao"]
    pasta_revisoes = tmp_path / "_campanhas_avulsas" / campanha["id"] / "roteiros" / "A001"
    assert len(list((pasta_revisoes / "revisoes").glob("*.json"))) == 2
    reaberta = client.get(f"/api/shorts/avulsos/campanhas/{campanha['id']}").json()
    assert reaberta["aprovacoes_roteiro"]["A001"] == segunda.json()
    assert caminho_snapshot.read_bytes() == snapshot_original
    assert reaberta["pedidos"][0]["roteiro"] is None
    assert "aprovar mídias e licenças" in reaberta["pedidos"][0]["pendencias"]


def test_aprovacao_avulsa_bloqueia_campanha_obsoleta_e_pedido_estranho(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def mock_settings() -> object:
        return type("Settings", (), {"paths": type("Paths", (), {"projects": tmp_path})()})()

    monkeypatch.setattr("docforja.api.load_settings", mock_settings)
    client = TestClient(app)
    campanha = client.post(
        "/api/shorts/avulsos/campanhas",
        json={"nome": "Campanha", "csv_texto": "tema,objetivo,duracao_s\nA,educativo,30\n"},
    ).json()
    base = f"/api/shorts/avulsos/campanhas/{campanha['id']}/pedidos"
    assert (
        client.post(
            f"{base}/A001/roteiro/aprovar",
            json={"texto": "Roteiro", "hash_campanha": "0" * 64},
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"{base}/A002/roteiro/aprovar",
            json={"texto": "Roteiro", "hash_campanha": campanha["hash_conteudo"]},
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"{base}/A001/roteiro/aprovar",
            json={"texto": "   ", "hash_campanha": campanha["hash_conteudo"]},
        ).status_code
        == 409
    )
    assert not (tmp_path / "_campanhas_avulsas" / campanha["id"]).exists()


def _imagem_global(raiz: Path, item_id: str, **campos: object) -> Path:
    pasta = raiz / "imagens"
    pasta.mkdir(parents=True, exist_ok=True)
    imagem = pasta / f"{item_id}.png"
    imagem.write_bytes(b"imagem-de-teste")
    ficha = {
        "id": item_id,
        "arquivo": imagem.name,
        "descricao": "Ilustração de teste",
        "licenca": "CC0-1.0",
        "comercial": True,
        **campos,
    }
    (pasta / f"{item_id}.json").write_text(json.dumps(ficha), encoding="utf-8")
    return imagem


def test_catalogo_avulso_bloqueia_fichas_inseguras(tmp_path: Path) -> None:
    _imagem_global(tmp_path, "liberada")
    _imagem_global(tmp_path, "nao-comercial", licenca="CC BY-NC")
    _imagem_global(tmp_path, "sem-confirmacao", comercial=False)
    _imagem_global(tmp_path, "restrita", restricao_editorial="não publicar")
    _imagem_global(tmp_path, "patrimonio", patrimonio_restrito=True)
    _imagem_global(tmp_path, "hash-divergente", sha256="0" * 64)
    _imagem_global(tmp_path, "arquivo-externo", arquivo="../fora.png")

    disponiveis = listar_imagens_globais(tmp_path)

    assert [item.id_global for item in disponiveis] == ["global:imagens:liberada"]
    with pytest.raises(ValueError, match="inválido"):
        resolver_imagem_global(tmp_path, "global:imagens:../segredo")


def test_catalogo_clipes_so_expoe_mp4_licenciado(tmp_path: Path) -> None:
    loops = tmp_path / "loops"
    loops.mkdir()
    for item_id, licenca, publicacao in (
        ("proprio", "CC0-1.0", True),
        ("nao-comercial", "CC BY-NC", True),
        ("restrito", "CC0-1.0", False),
    ):
        (loops / f"{item_id}.mp4").write_bytes(item_id.encode())
        (loops / f"{item_id}.json").write_text(
            json.dumps(
                {
                    "arquivo": f"{item_id}.mp4",
                    "descricao": item_id,
                    "licenca": licenca,
                    "comercial": True,
                    "publicacao_permitida": publicacao,
                }
            ),
            encoding="utf-8",
        )
    disponiveis = listar_midias_globais(tmp_path)
    assert [item.id_global for item in disponiveis] == ["global:loops:proprio"]
    arquivo, midia = resolver_midia_global(tmp_path, "global:loops:proprio")
    assert arquivo.suffix == ".mp4"
    assert midia.tipo == "clipe"
    with pytest.raises(ValueError, match="não é uma imagem"):
        resolver_imagem_global(tmp_path, "global:loops:proprio")


def test_selecao_de_midia_avulsa_invalida_ao_trocar_roteiro_ou_arquivo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    projetos = tmp_path / "projetos"
    global_dir = tmp_path / "global"
    imagem = _imagem_global(global_dir, "cena")

    def mock_settings() -> object:
        return type("Settings", (), {"paths": type("Paths", (), {"projects": projetos})()})()

    monkeypatch.setattr("docforja.api.load_settings", mock_settings)
    monkeypatch.setattr("docforja.api.obter_pasta_global", lambda: global_dir)
    client = TestClient(app)
    campanha = client.post(
        "/api/shorts/avulsos/campanhas",
        json={"nome": "Campanha", "csv_texto": "tema,objetivo,duracao_s\nA,educativo,30\n"},
    ).json()
    base = f"/api/shorts/avulsos/campanhas/{campanha['id']}/pedidos/A001"
    rota = f"{base}/midias/selecionar"
    payload_roteiro = {"texto": "Texto A", "hash_campanha": campanha["hash_conteudo"]}
    aprovacao = client.post(f"{base}/roteiro/aprovar", json=payload_roteiro).json()
    payload = {
        "ids_globais": ["global:imagens:cena"],
        "hash_campanha": campanha["hash_conteudo"],
        "revisao_roteiro": aprovacao["revisao"],
    }

    resposta = client.post(rota, json=payload)
    assert resposta.status_code == 200
    assert client.post(rota, json=payload).json() == resposta.json()
    assert resposta.json()["midias"][0]["hash_arquivo"]
    assert client.get("/api/shorts/avulsos/midias-disponiveis").json()["midias"]
    assert client.get("/api/shorts/avulsos/midias/imagens/cena/imagem").status_code == 200
    assert (
        client.get(f"/api/shorts/avulsos/campanhas/{campanha['id']}").json()["selecoes_midias"][
            "A001"
        ]
        == resposta.json()
    )

    client.post(
        f"{base}/roteiro/aprovar",
        json={"texto": "Texto B", "hash_campanha": campanha["hash_conteudo"]},
    )
    reaberta = client.get(f"/api/shorts/avulsos/campanhas/{campanha['id']}").json()
    assert reaberta["selecoes_midias"] == {}
    assert reaberta["midias_desatualizadas"] == ["A001"]
    assert client.post(rota, json=payload).status_code == 409

    nova_aprovacao = reaberta["aprovacoes_roteiro"]["A001"]
    payload["revisao_roteiro"] = nova_aprovacao["revisao"]
    assert client.post(rota, json=payload).status_code == 200
    imagem.write_bytes(b"imagem-mudou")
    reaberta = client.get(f"/api/shorts/avulsos/campanhas/{campanha['id']}").json()
    assert reaberta["selecoes_midias"] == {}
    assert reaberta["midias_desatualizadas"] == ["A001"]
    assert client.post(rota, json=payload).status_code == 200
    ficha = global_dir / "imagens" / "cena.json"
    dados_ficha = json.loads(ficha.read_text(encoding="utf-8"))
    dados_ficha["licenca"] = "CC BY-NC"
    ficha.write_text(json.dumps(dados_ficha), encoding="utf-8")
    reaberta = client.get(f"/api/shorts/avulsos/campanhas/{campanha['id']}").json()
    assert reaberta["selecoes_midias"] == {}
    assert reaberta["midias_desatualizadas"] == ["A001"]
    assert client.post(rota, json=payload).status_code == 409


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
