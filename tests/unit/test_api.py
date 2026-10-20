import json

from fastapi.testclient import TestClient

from docforja.api import app
from docforja.io import atomic_write_json
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
    projeto_raiz = tmp_path / slug
    assert (projeto_raiz / "sistema" / "banco.db").is_file()

    # Um projeto sem etapas executadas não pode aparecer como concluído.
    resp_list = client.get("/api/projetos")
    projeto_novo = next(p for p in resp_list.json() if p["slug"] == slug)
    assert projeto_novo["etapa_atual"] == "Aguardando início"

    # Inicializa banco para simular etapa
    proj = Projeto.carregar(slug, raiz_projetos=tmp_path)
    banco = BancoProjeto(proj.banco_file)
    banco.salvar_etapa("P1_leitura", status="concluida")
    for etapa_id in (
        "P2_narracao",
        "P4_shots",
        "P6_verificador",
        "P8_estimativa_previa",
        "REVISAO",
    ):
        banco.salvar_etapa(etapa_id, status="concluida")

    # 2. Listar projetos
    resp_list = client.get("/api/projetos")
    assert resp_list.status_code == 200
    projetos = resp_list.json()
    item = next(p for p in projetos if p["slug"] == slug)
    assert item["etapa_atual"] == "Saídas pendentes de M3/M4"

    # 3. Obter projeto individual
    resp_get = client.get(f"/api/projetos/{slug}")
    assert resp_get.status_code == 200
    proj_detalhe = resp_get.json()
    assert proj_detalhe["slug"] == slug
    assert proj_detalhe["roteiro"] == "Roteiro da API"
    assert any(e["id"] == "P1_leitura" for e in proj_detalhe["etapas"])

    resp_etapa_invalida = client.post(f"/api/projetos/{slug}/executar?ate=etapa_inexistente")
    assert resp_etapa_invalida.status_code == 400


def test_api_servir_web_dist():
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "DocForja" in resp.text
    assert '<div id="root">' in resp.text


def test_api_plano_ui_leitura_local_e_pasta_manual(tmp_path, monkeypatch):
    mock_settings = lambda: type(  # noqa: E731
        "Settings", (), {"paths": type("Paths", (), {"projects": tmp_path})()}
    )()
    monkeypatch.setattr("docforja.api.load_settings", mock_settings)
    projeto = Projeto.criar(
        nome="Teste Plano", roteiro="## B0\n\n**B0-S01**\nTeste.", raiz_projetos=tmp_path
    )
    atomic_write_json(
        projeto.pastas.plano / "plano.json",
        {"projeto": projeto.slug, "blocos": [], "ativos": {}},
    )
    ativo = {
        "id": "A-001", "descricao": "Imagem histórica", "origem": "pedir_ao_usuario",
        "nome_arquivo": "A-001.jpg", "usado_em": ["B0-01"],
    }
    atomic_write_json(
        projeto.pastas.plano / "ativos_resolvidos.json",
        {"ativos": {"A-001": ativo}},
    )
    client = TestClient(app)
    dados = client.get(f"/api/projetos/{projeto.slug}/plano").json()
    assert dados["pronto"] is True
    assert dados["pedidos"][0]["recebido"] is False
    assert dados["manifesto"] is None

    imagem = projeto.pastas.midias / "manual" / "A-001.jpg"
    imagem.write_bytes(b"imagem de teste")
    dados = client.get(f"/api/projetos/{projeto.slug}/plano").json()
    assert dados["pedidos"][0]["recebido"] is True
    assert dados["ativos"]["A-001"]["imagem_url"] is None
    assert client.get(f"/api/projetos/{projeto.slug}/ativos/A-001/imagem").status_code == 404
    assert imagem.read_bytes() == b"imagem de teste"
    assert not imagem.with_name("A-001.jpg.licenca.json").exists()
    ficha = imagem.with_name("A-001.jpg.licenca.json")
    atomic_write_json(ficha, {"licenca": "CC BY 4.0", "comercial": True})
    dados = client.get(f"/api/projetos/{projeto.slug}/plano").json()
    assert dados["ativos"]["A-001"]["imagem_url"].endswith("/ativos/A-001/imagem")
    assert dados["ativos"]["A-001"]["licenca_previa"] == "CC BY 4.0"
    assert dados["imagens_por_shot"]["B0-01"].endswith("/ativos/A-001/imagem")
    resposta_imagem = client.get(f"/api/projetos/{projeto.slug}/ativos/A-001/imagem")
    assert resposta_imagem.status_code == 200
    assert resposta_imagem.content == b"imagem de teste"
    assert resposta_imagem.headers["cache-control"] == "no-store"
    pasta_candidatas = projeto.pastas.midias / "pesquisadas" / "A-001"
    pasta_candidatas.mkdir(parents=True)
    candidata = pasta_candidatas / "cand_wikimedia_1.jpg"
    candidata.write_bytes(b"candidata liberada")
    atomic_write_json(
        candidata.with_name("cand_wikimedia_1.jpg.licenca.json"),
        {
            "licenca": "CC BY 4.0", "comercial": True, "autor": "Arquivo Exemplo",
            "url_origem": "https://example.org/origem",
            "texto_credito": "Arquivo Exemplo / CC BY 4.0",
        },
    )
    bloqueada = pasta_candidatas / "cand_wikimedia_2.jpg"
    bloqueada.write_bytes(b"candidata bloqueada")
    atomic_write_json(
        bloqueada.with_name("cand_wikimedia_2.jpg.licenca.json"),
        {"licenca": "CC BY-NC 4.0", "comercial": True},
    )
    dados = client.get(f"/api/projetos/{projeto.slug}/plano").json()
    assert dados["ativos"]["A-001"]["credito_imagem"]["licenca"] == "CC BY 4.0"
    candidatas = dados["ativos"]["A-001"]["candidatas"]
    assert len(candidatas) == 1
    assert candidatas[0]["autor"] == "Arquivo Exemplo"
    assert candidatas[0]["fonte"] == "https://example.org/origem"
    assert client.get(candidatas[0]["imagem_url"]).content == b"candidata liberada"
    assert client.get(
        f"/api/projetos/{projeto.slug}/ativos/A-001/candidatas/cand_wikimedia_2.jpg/imagem"
    ).status_code == 404
    endpoint_selecao = f"/api/projetos/{projeto.slug}/ativos/A-001/selecionar"
    hash_atual = dados["hash_resolvidos"]
    assert client.post(endpoint_selecao, json={
        "candidata": "cand_wikimedia_2.jpg", "hash_resolvidos": hash_atual,
    }).status_code == 400
    assert client.post(endpoint_selecao, json={
        "candidata": "cand_wikimedia_1.jpg", "hash_resolvidos": "antigo",
    }).status_code == 409
    assert client.post(endpoint_selecao, json={
        "candidata": "cand_wikimedia_1.jpg", "hash_resolvidos": hash_atual,
    }).status_code == 200
    dados = client.get(f"/api/projetos/{projeto.slug}/plano").json()
    assert dados["ativos"]["A-001"]["candidata_selecionada"] == "cand_wikimedia_1.jpg"
    assert dados["previa_mp4_desatualizada"] is True
    assert client.get(dados["ativos"]["A-001"]["imagem_url"]).content == b"candidata liberada"
    atomic_write_json(
        candidata.with_name("cand_wikimedia_1.jpg.licenca.json"),
        {"licenca": "CC BY-NC 4.0", "comercial": True},
    )
    dados = client.get(f"/api/projetos/{projeto.slug}/plano").json()
    assert dados["ativos"]["A-001"]["candidata_selecionada"] is None
    assert client.get(dados["ativos"]["A-001"]["imagem_url"]).content == b"imagem de teste"
    assert client.post(endpoint_selecao, json={
        "candidata": None, "hash_resolvidos": hash_atual,
    }).status_code == 200
    dados = client.get(f"/api/projetos/{projeto.slug}/plano").json()
    assert dados["ativos"]["A-001"]["candidata_selecionada"] is None
    assert dados["previa_mp4_desatualizada"] is False
    assert client.get(dados["ativos"]["A-001"]["imagem_url"]).content == b"imagem de teste"
    assert len(list((projeto.pastas.midias / "selecoes_ui").glob("*.json"))) == 2
    assert json.loads(
        (projeto.pastas.plano / "ativos_resolvidos.json").read_text(encoding="utf-8")
    )["ativos"]["A-001"] == ativo
    atomic_write_json(ficha, {"licenca": "CC BY-NC 4.0", "comercial": True})
    assert client.get(f"/api/projetos/{projeto.slug}/ativos/A-001/imagem").status_code == 404
    atomic_write_json(ficha, {"licenca": "manual_autorizado", "comercial": True})
    assert client.get(f"/api/projetos/{projeto.slug}/ativos/A-001/imagem").status_code == 404
    atomic_write_json(ficha, {"licenca": "CC BY 4.0", "patrimonio_restrito": True})
    assert client.get(f"/api/projetos/{projeto.slug}/ativos/A-001/imagem").status_code == 404
    externo_imagem = tmp_path / "fora.jpg"
    externo_imagem.write_bytes(b"fora")
    atomic_write_json(externo_imagem.with_name("fora.jpg.licenca.json"), {"licenca": "CC0"})
    ativo["caminho"] = str(externo_imagem)
    atomic_write_json(projeto.pastas.plano / "ativos_resolvidos.json", {"ativos": {"A-001": ativo}})
    assert client.get(f"/api/projetos/{projeto.slug}/ativos/A-001/imagem").status_code == 404
    assert client.get(f"/api/projetos/{projeto.slug}/ativos/A-999/imagem").status_code == 404
    assert client.get(f"/api/projetos/{projeto.slug}/narracao.wav").status_code == 404
    assert client.get("/api/projetos/%2E%2E/plano").status_code == 404
    externo = client.get(
        f"/api/projetos/{projeto.slug}/plano",
        headers={"Origin": "https://site-externo.example"},
    )
    assert "access-control-allow-origin" not in externo.headers
