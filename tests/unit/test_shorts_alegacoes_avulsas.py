"""Fluxo de documentação editorial de alegações, sem rede ou GPU."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from docforja.api import app


def _preparar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, formula: str, roteiro: str
) -> tuple[TestClient, dict[str, object], str, dict[str, object]]:
    projetos = tmp_path / "projetos"
    global_dir = tmp_path / "global"
    pasta = global_dir / "imagens"
    pasta.mkdir(parents=True)
    (pasta / "cena.png").write_bytes(b"imagem-de-teste")
    (pasta / "cena.json").write_text(
        json.dumps({
            "arquivo": "cena.png", "descricao": "Ilustração genérica",
            "licenca": "CC0-1.0", "comercial": True,
        }),
        encoding="utf-8",
    )

    def mock_settings() -> object:
        return type("Settings", (), {"paths": type("Paths", (), {"projects": projetos})()})()

    monkeypatch.setattr("docforja.api.load_settings", mock_settings)
    monkeypatch.setattr("docforja.api.obter_pasta_global", lambda: global_dir)
    client = TestClient(app)
    campanha = client.post(
        "/api/shorts/avulsos/campanhas",
        json={
            "nome": "Campanha de teste",
            "csv_texto": (
                "tema,objetivo,duracao_s,formula\n"
                f"Produto,vendas,30,{formula}\n"
            ),
        },
    ).json()
    base = f"/api/shorts/avulsos/campanhas/{campanha['id']}/pedidos/A001"
    aprovacao = client.post(
        f"{base}/roteiro/aprovar",
        json={"texto": roteiro, "hash_campanha": campanha["hash_conteudo"]},
    ).json()
    selecao = client.post(
        f"{base}/midias/selecionar",
        json={
            "ids_globais": ["global:imagens:cena"],
            "hash_campanha": campanha["hash_conteudo"],
            "revisao_roteiro": aprovacao["revisao"],
        },
    ).json()
    prefixo = {
        "hash_campanha": campanha["hash_conteudo"],
        "revisao_roteiro": aprovacao["revisao"],
        "revisao_midias": selecao["revisao"],
    }
    return client, campanha, base, prefixo


def test_oferta_exige_fontes_prova_preco_e_condicao_real(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, campanha, base, prefixo = _preparar(
        tmp_path, monkeypatch, "oferta", "Só hoje, 20% de desconto por R$ 40."
    )
    rota = f"{base}/alegacoes/registrar"
    dados = {
        "fontes": [{"alegacao": "Benefício real", "fonte": "Documento interno 1"}],
        "prova_real": {"alegacao": "Demonstração real", "fonte": "Relatório 2"},
        "relacao_comercial": "produto_proprio",
        "revisado_pelo_usuario": True,
    }
    assert client.post(rota, json={**prefixo, "dados": dados}).status_code == 409
    dados["fonte_preco"] = "Tabela vigente de preços"
    assert client.post(rota, json={**prefixo, "dados": dados}).status_code == 409
    dados["condicao_urgencia"] = "Oferta válida até 22/10/2026, conforme regulamento"
    primeira = client.post(rota, json={**prefixo, "dados": dados})
    assert primeira.status_code == 200
    assert primeira.json()["status"] == "documentacao_registrada_sem_verificacao_externa"
    assert client.post(rota, json={**prefixo, "dados": dados}).json() == primeira.json()
    reaberta = client.get(f"/api/shorts/avulsos/campanhas/{campanha['id']}").json()
    assert reaberta["documentacoes_alegacoes"]["A001"] == primeira.json()
    assert reaberta["pedidos"][0]["roteiro"] is None
    assert not list((tmp_path / "projetos").glob("*/05_saida"))

    client.post(
        f"{base}/roteiro/aprovar",
        json={"texto": "Novo roteiro", "hash_campanha": campanha["hash_conteudo"]},
    )
    reaberta = client.get(f"/api/shorts/avulsos/campanhas/{campanha['id']}").json()
    assert reaberta["documentacoes_alegacoes"] == {}
    assert reaberta["alegacoes_desatualizadas"] == ["A001"]
    assert client.post(rota, json={**prefixo, "dados": dados}).status_code == 409


def test_afiliado_exige_aviso_e_relacao_declarada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _, base, prefixo = _preparar(
        tmp_path, monkeypatch, "produto_afiliado", "Veja o produto em uso."
    )
    rota = f"{base}/alegacoes/registrar"
    dados = {
        "fontes": [{"alegacao": "Benefício descrito", "fonte": "Ficha do fabricante"}],
        "revisado_pelo_usuario": True,
    }
    assert client.post(rota, json={**prefixo, "dados": dados}).status_code == 409
    dados["relacao_comercial"] = "afiliado"
    assert client.post(rota, json={**prefixo, "dados": dados}).status_code == 422
    dados["aviso_publicidade"] = True
    resposta = client.post(rota, json={**prefixo, "dados": dados})
    assert resposta.status_code == 200
    assert resposta.json()["dados"]["aviso_publicidade"] is True


def test_preco_em_reais_e_prazo_ate_sexta_exigem_documentacao(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _, base, prefixo = _preparar(
        tmp_path, monkeypatch, "oferta", "Produto por 40 reais até sexta."
    )
    rota = f"{base}/alegacoes/registrar"
    dados = {
        "fontes": [{"alegacao": "Benefício real", "fonte": "Manual do produto"}],
        "prova_real": {"alegacao": "Uso demonstrado", "fonte": "Arquivo original"},
        "revisado_pelo_usuario": True,
    }
    assert client.post(rota, json={**prefixo, "dados": dados}).status_code == 409
    dados["fonte_preco"] = "Tabela comercial vigente"
    assert client.post(rota, json={**prefixo, "dados": dados}).status_code == 409
    dados["condicao_urgencia"] = "Vigência até sexta no regulamento"
    assert client.post(rota, json={**prefixo, "dados": dados}).status_code == 200


def test_ficha_sem_revisao_humana_nao_e_guardada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _, base, prefixo = _preparar(
        tmp_path, monkeypatch, "oferta", "Oferta sem prazo indicado."
    )
    resposta = client.post(
        f"{base}/alegacoes/registrar",
        json={
            **prefixo,
            "dados": {
                "fontes": [{"alegacao": "Oferta", "fonte": "Documento interno"}],
                "prova_real": {"alegacao": "Teste real", "fonte": "Arquivo do usuário"},
                "revisado_pelo_usuario": False,
            },
        },
    )
    assert resposta.status_code == 422
