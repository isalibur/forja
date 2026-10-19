from fastapi.testclient import TestClient

from docforja.api import app
from docforja.nucleo.banco import BancoProjeto
from docforja.nucleo.projeto import Projeto


def test_api_saude():
    client = TestClient(app)
    resp = client.get("/api/saude")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert "gpu" in data
    assert "cotas" in data


def test_api_projetos_fluxo(tmp_path, monkeypatch):
    mock_settings = lambda: type(  # noqa: E731
        "Settings", (), {"paths": type("Paths", (), {"projects": tmp_path})()}
    )()
    monkeypatch.setattr("docforja.api.load_settings", mock_settings)
    monkeypatch.setattr("docforja.nucleo.projeto.load_settings", mock_settings)
    client = TestClient(app)

    # 1. Criação de projeto
    payload = {
        "nome": "Vesúvio Teste API",
        "tipo": "longo",
        "roteiro": "Roteiro da API",
        "idioma_principal": "pt-BR",
        "idiomas_extras": ["en"],
        "preset": "padrao",
    }
    resp = client.post("/api/projetos", json=payload)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["sucesso"] is True
    slug = res_data["slug"]
    assert slug == "vesuvio-teste-api"

    # Inicializa banco para simular etapa
    proj = Projeto.carregar(slug, raiz_projetos=tmp_path)
    banco = BancoProjeto(proj.banco_file)
    banco.salvar_etapa("P1_leitura", status="concluida")

    # 2. Listar projetos
    resp_list = client.get("/api/projetos")
    assert resp_list.status_code == 200
    projetos = resp_list.json()
    assert any(p["slug"] == slug for p in projetos)

    # 3. Obter projeto individual
    resp_get = client.get(f"/api/projetos/{slug}")
    assert resp_get.status_code == 200
    proj_detalhe = resp_get.json()
    assert proj_detalhe["slug"] == slug
    assert proj_detalhe["roteiro"] == "Roteiro da API"
    assert any(e["id"] == "P1_leitura" for e in proj_detalhe["etapas"])


def test_api_servir_web_dist():
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "DocForja" in resp.text
    assert '<div id="root">' in resp.text
