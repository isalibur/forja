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


def test_api_fluxo_short_derivado_versionado(tmp_path, monkeypatch):
    mock_settings = lambda: type(  # noqa: E731
        "Settings", (), {"paths": type("Paths", (), {"projects": tmp_path})()}
    )()
    monkeypatch.setattr("docforja.api.load_settings", mock_settings)
    projeto = Projeto.criar(nome="Short API", roteiro="roteiro", raiz_projetos=tmp_path)
    plano = {
        "projeto": projeto.slug,
        "tipo": "longo",
        "blocos": [
            {
                "id": "B0",
                "titulo": "Bloco",
                "shots": [
                    {
                        "id": "B0-01",
                        "segmentos": ["S01", "S02"],
                        "duracao_s": 40,
                        "inicio_s": 0,
                        "fim_s": 40,
                        "template": "T01",
                    }
                ],
            }
        ],
        "ativos": {},
    }
    atomic_write_json(projeto.pastas.plano / "plano.json", plano)
    pasta_audio = projeto.pastas.audio / "pt-BR"
    atomic_write_json(
        pasta_audio / "segmentos.json",
        [
            {"id": "S01", "inicio_s": 0, "fim_s": 20, "texto": "Primeira parte."},
            {"id": "S02", "inicio_s": 20, "fim_s": 40, "texto": "Segunda parte."},
        ],
    )
    client = TestClient(app)
    plano_mestre_antes = (projeto.pastas.plano / "plano.json").read_bytes()
    endpoint = f"/api/projetos/{projeto.slug}/shorts/derivados"
    dados = client.get(endpoint)
    assert dados.status_code == 200
    candidatos = dados.json()["candidatos"]
    assert len(candidatos) == 2
    referencia = candidatos[0]["referencia"]
    assert len(candidatos[0]["candidato"]["frases_ponte"]) == 3
    aprovar_url = f"{endpoint}/{referencia}/aprovar"
    aprovacao = client.post(aprovar_url, json={"indice_frase": 1})
    assert aprovacao.status_code == 200
    versao = aprovacao.json()["versao"]
    assert (
        projeto.pastas.montagem / "shorts" / "derivados" / referencia / f"aprovacao-{versao}.json"
    ).is_file()
    aprovacao_atual = client.get(endpoint).json()["candidatos"][0]["aprovacao"]
    assert aprovacao_atual["versao"] == versao
    manifesto = client.post(
        f"{endpoint}/{referencia}/manifesto-vertical",
        json={"dimensoes": {}},
    )
    assert manifesto.status_code == 200
    assert manifesto.json()["manifesto"]["proporcao"] == "9:16"
    assert len(manifesto.json()["manifesto"]["shots"]) == 1
    assert manifesto.json()["manifesto"]["shots"][0]["fim_s"] == 20
    atual = client.get(endpoint).json()["candidatos"][0]
    assert atual["manifesto_atual"]["versao"] == manifesto.json()["versao"]
    chamadas: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "docforja.api.executar_producao_background",
        lambda projeto_arg, referencia_arg: chamadas.append((projeto_arg.slug, referencia_arg)),
    )
    producao = client.post(f"{endpoint}/{referencia}/produzir")
    assert producao.status_code == 202
    assert producao.json()["status"] == "aguardando"
    assert chamadas == [(projeto.slug, referencia)]
    assert client.get(f"{endpoint}/{referencia}/saida/video.mp4").status_code == 404
    assert client.get(endpoint).json()["candidatos"][0]["producao"]["status"] == "aguardando"
    nova_aprovacao = client.post(aprovar_url, json={"indice_frase": 2})
    assert nova_aprovacao.status_code == 200
    desatualizado = client.get(endpoint).json()["candidatos"][0]
    assert desatualizado["manifesto_atual"] is None
    assert desatualizado["producao"] is None
    assert (projeto.pastas.plano / "plano.json").read_bytes() == plano_mestre_antes
    assert client.post(aprovar_url, json={}).status_code == 400


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
        "id": "A-001",
        "descricao": "Imagem histórica",
        "origem": "pedir_ao_usuario",
        "nome_arquivo": "A-001.jpg",
        "usado_em": ["B0-01"],
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
            "licenca": "CC BY 4.0",
            "comercial": True,
            "autor": "Arquivo Exemplo",
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
    assert (
        client.get(
            f"/api/projetos/{projeto.slug}/ativos/A-001/candidatas/cand_wikimedia_2.jpg/imagem"
        ).status_code
        == 404
    )
    endpoint_selecao = f"/api/projetos/{projeto.slug}/ativos/A-001/selecionar"
    hash_atual = dados["hash_resolvidos"]
    assert (
        client.post(
            endpoint_selecao,
            json={
                "candidata": "cand_wikimedia_2.jpg",
                "hash_resolvidos": hash_atual,
            },
        ).status_code
        == 400
    )
    assert (
        client.post(
            endpoint_selecao,
            json={
                "candidata": "cand_wikimedia_1.jpg",
                "hash_resolvidos": "antigo",
            },
        ).status_code
        == 409
    )
    assert (
        client.post(
            endpoint_selecao,
            json={
                "candidata": "cand_wikimedia_1.jpg",
                "hash_resolvidos": hash_atual,
            },
        ).status_code
        == 200
    )
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
    assert (
        client.post(
            endpoint_selecao,
            json={
                "candidata": None,
                "hash_resolvidos": hash_atual,
            },
        ).status_code
        == 200
    )
    dados = client.get(f"/api/projetos/{projeto.slug}/plano").json()
    assert dados["ativos"]["A-001"]["candidata_selecionada"] is None
    assert dados["previa_mp4_desatualizada"] is False
    assert client.get(dados["ativos"]["A-001"]["imagem_url"]).content == b"imagem de teste"
    assert len(list((projeto.pastas.midias / "selecoes_ui").glob("*.json"))) == 2
    assert (
        json.loads((projeto.pastas.plano / "ativos_resolvidos.json").read_text(encoding="utf-8"))[
            "ativos"
        ]["A-001"]
        == ativo
    )
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
    trilha_proj = projeto.pastas.audio / "trilha" / "provisoria.wav"
    trilha_proj.write_bytes(b"RIFF....WAVE")
    resp_trilha = client.get(f"/api/projetos/{projeto.slug}/trilha_provisoria.wav")
    assert resp_trilha.status_code == 200
    assert resp_trilha.content == b"RIFF....WAVE"
    assert client.get("/api/projetos/%2E%2E/plano").status_code == 404
    externo = client.get(
        f"/api/projetos/{projeto.slug}/plano",
        headers={"Origin": "https://site-externo.example"},
    )
    assert "access-control-allow-origin" not in externo.headers


def test_api_producao_e_saida_endpoints(tmp_path, monkeypatch):
    mock_settings = lambda: type(  # noqa: E731
        "Settings",
        (),
        {
            "paths": type(
                "Paths",
                (),
                {
                    "projects": tmp_path,
                    "models": tmp_path / "models",
                    "temp": tmp_path / "temp",
                },
            )(),
            "python_environments": {"kokoro": "py311", "whisperx": "py311"},
            "alinhamento": type(
                "Alin",
                (),
                {
                    "modelo_asr": "whisper",
                    "modelo_alinhador": "wav2vec2",
                },
            )(),
        },
    )()
    monkeypatch.setattr("docforja.api.load_settings", mock_settings)
    monkeypatch.setattr("docforja.nucleo.projeto.load_settings", mock_settings)
    client = TestClient(app)

    proj = Projeto.criar(
        nome="Projeto Producao",
        roteiro="## B0\n\n**B0-S01**\nTexto.",
        raiz_projetos=tmp_path,
    )

    # 1. Teste de aprovação de gate com código incorreto e correto
    resp_bad = client.post(
        f"/api/projetos/{proj.slug}/aprovar_gate",
        json={"gate": "REVISAO", "codigo": "ERRADO"},
    )
    assert resp_bad.status_code == 400

    resp_ok = client.post(
        f"/api/projetos/{proj.slug}/aprovar_gate",
        json={"gate": "REVISAO", "codigo": "PRODUZIR"},
    )
    assert resp_ok.status_code == 200
    assert resp_ok.json()["status"] == "aprovado"

    # 2. Teste do endpoint /producao
    resp_prod = client.get(f"/api/projetos/{proj.slug}/producao")
    assert resp_prod.status_code == 200
    dados_prod = resp_prod.json()
    assert "progresso_percent" in dados_prod
    assert "tempo_restante_min" in dados_prod
    assert "etapas" in dados_prod

    # 3. Teste do endpoint /saida
    resp_saida = client.get(f"/api/projetos/{proj.slug}/saida")
    assert resp_saida.status_code == 200
    dados_saida = resp_saida.json()
    assert dados_saida["slug"] == proj.slug
    assert "pronto" in dados_saida

    # 4. Teste de endpoints globais e sistema
    resp_global = client.get("/api/global/itens")
    assert resp_global.status_code == 200
    assert "categorias" in resp_global.json()

    resp_sis = client.get("/api/sistema/detalhes")
    assert resp_sis.status_code == 200
    dados_sis = resp_sis.json()
    assert "gpu" in dados_sis
    assert "cotas" in dados_sis
