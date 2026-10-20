"""Testes unitários para o módulo de mídia, curadoria e resolução de ativos (P7 / M5).

Não utiliza rede externa nem GPU.
"""

from __future__ import annotations

import json
from pathlib import Path

from docforja.esquemas import Ativo, Candidato, OrigemAtivo
from docforja.io import atomic_write_json
from docforja.midia.acervo import AdaptadorAcervoMock
from docforja.midia.curadoria import CuradorImagens
from docforja.midia.licenca import (
    FichaLicenca,
    carregar_ficha_licenca,
    classificar_licenca,
    detectar_patrimonio_restrito,
    salvar_ficha_licenca,
)
from docforja.midia.lista_busca import gerar_lista_de_busca_md
from docforja.midia.pasta_manual import escanear_pasta_manual, identificar_ativo_por_nome
from docforja.midia.resolucao import resolver_ativos_projeto
from docforja.nucleo.handlers import criar_executor_projeto
from docforja.nucleo.projeto import Projeto


def test_p7_resolve_ativos_criados_pelo_verificador(tmp_path: Path):
    projeto = Projeto.criar(
        nome="ativos_p6", roteiro="## B0\n\n**B0-S01**\nTeste.", raiz_projetos=tmp_path
    )
    base = Ativo(
        id="A-001", descricao="Imagem de teste", origem=OrigemAtivo.PEDIR_AO_USUARIO,
        usado_em=["B0-01"],
    )
    alternativo = base.model_copy(update={"id": "A-001_b", "usado_em": ["B0-01-p2"]})
    atomic_write_json(
        projeto.pastas.plano / "ativos.json",
        {"ativos": {"A-001": base.model_dump(mode="json")}},
    )
    atomic_write_json(
        projeto.pastas.plano / "plano_verificado.json",
        {"ativos": {
            "A-001": base.model_dump(mode="json"),
            "A-001_b": alternativo.model_dump(mode="json"),
        }},
    )

    resolvidos = resolver_ativos_projeto(projeto)

    assert set(resolvidos) == {"A-001", "A-001_b"}


def test_classificar_licenca():
    """Valida bloqueio de licenças NC/ND e liberação de PD/CC BY comercial."""
    # Proibidos em comercial
    comercial, _ = classificar_licenca("CC BY-NC 4.0")
    assert not comercial
    comercial, _ = classificar_licenca("Creative Commons Attribution-NonCommercial")
    assert not comercial
    comercial, _ = classificar_licenca("CC BY-ND 3.0")
    assert not comercial

    # Liberados em comercial
    comercial, req_credito = classificar_licenca("CC0 1.0 Universal")
    assert comercial
    assert not req_credito

    comercial, req_credito = classificar_licenca("Public Domain")
    assert comercial
    assert not req_credito

    comercial, req_credito = classificar_licenca("CC BY 4.0")
    assert comercial
    assert req_credito

    comercial, req_credito = classificar_licenca("CC BY-SA 3.0")
    assert comercial
    assert req_credito

    comercial, _ = classificar_licenca("Pexels License")
    assert comercial


def test_detectar_patrimonio_restrito():
    """Detecta referências a bens culturais protegidos italianos."""
    assert detectar_patrimonio_restrito("Afresco de Baco em Pompeia")
    assert detectar_patrimonio_restrito("Parco Archeologico di Ercolano")
    assert detectar_patrimonio_restrito("Paredes da Casa del Fauno")
    assert not detectar_patrimonio_restrito("Fotografia aérea de satélite de 2024")
    assert not detectar_patrimonio_restrito("Erupção do vulcão Pinatubo nas Filipinas")


def test_sidecar_licenca(tmp_path: Path):
    """Testa salvar e carregar ficha de licenca sidecar."""
    img = tmp_path / "teste.jpg"
    img.write_bytes(b"dummy image")

    ficha = FichaLicenca(
        url_origem="https://commons.wikimedia.org/wiki/File:Test.jpg",
        autor="Pintor Romano",
        licenca="CC BY-SA 4.0",
        comercial=True,
        patrimonio_restrito=False,
        texto_credito="Pintor Romano / CC BY-SA 4.0",
    )
    salvar_ficha_licenca(img, ficha)

    carregada = carregar_ficha_licenca(img)
    assert carregada is not None
    assert carregada.autor == "Pintor Romano"
    assert carregada.licenca == "CC BY-SA 4.0"
    assert carregada.comercial is True


def test_lista_de_busca_md():
    """Gera lista de busca formatada para pedidos ao usuário."""
    ativos = {
        "A-017": Ativo(
            id="A-017",
            descricao="Afresco Baco e o Vesúvio",
            origem=OrigemAtivo.PEDIR_AO_USUARIO,
            motivo="Foto de bem cultural restrito do MANN",
            busca={"termos": ["Bacco e Vesuvio affresco"], "sites": ["MANN", "Wikimedia"]},
            nome_arquivo="A-017.jpg",
            usado_em=["B1-05", "B1-06"],
            plano_b="gerar",
        )
    }
    conteudo = gerar_lista_de_busca_md(ativos, tema="Vesúvio")
    assert "# Lista de Busca" in conteudo
    assert "## A-017 — Afresco Baco e o Vesúvio (usado em B1-05, B1-06)" in conteudo
    assert "- **Por que preciso de você:** Foto de bem cultural restrito" in conteudo
    assert "- **Mínimo:** 1600 px · **Salvar como:** `A-017.jpg`" in conteudo


def test_pasta_manual_identificacao(tmp_path: Path):
    """Identifica arquivos manuais por ID do ativo ou shot e separa desconhecidos."""
    pasta_manual = tmp_path / "manual"
    pasta_nao_atribuidas = tmp_path / "nao_atribuidas"
    pasta_manual.mkdir(parents=True)

    (pasta_manual / "A-017.jpg").write_bytes(b"img1")
    (pasta_manual / "B1-05.png").write_bytes(b"img2")
    (pasta_manual / "desconhecido.jpg").write_bytes(b"img3")

    ativos = {
        "A-017": Ativo(id="A-017", descricao="Afresco", origem=OrigemAtivo.PEDIR_AO_USUARIO),
        "A-018": Ativo(
            id="A-018",
            descricao="Vaso",
            origem=OrigemAtivo.PESQUISAR,
            usado_em=["B1-05"],
        ),
    }
    mapa_shots = {"B1-05": "A-018"}

    assert identificar_ativo_por_nome("A-017.jpg", ativos) == "A-017"
    assert identificar_ativo_por_nome("A-017_versao2.png", ativos) == "A-017"
    assert identificar_ativo_por_nome("B1-05.png", ativos, mapa_shots=mapa_shots) == "A-018"
    assert identificar_ativo_por_nome("desconhecido.jpg", ativos) is None

    atribuidos, nao_atribuidos = escanear_pasta_manual(
        pasta_manual, pasta_nao_atribuidas, ativos, mapa_shots=mapa_shots
    )
    assert "A-017" in atribuidos
    assert "A-018" in atribuidos
    assert len(nao_atribuidos) == 1
    assert nao_atribuidos[0].name == "desconhecido.jpg"


def test_resolver_ativos_projeto_com_mock(tmp_path: Path):
    """Valida resolução completa de ativos com acervo mock sem rede."""
    roteiro = "## B0 — Abertura\n\n**B0-S01**\nInscrição em Pompeia."
    projeto = Projeto.criar(nome="proj-midia", roteiro=roteiro, raiz_projetos=tmp_path)

    ativos = {
        "A-001": Ativo(
            id="A-001",
            descricao="Inscrição a carvão de 2018 na parede de Pompeia",
            origem=OrigemAtivo.PESQUISAR,
            usado_em=["B0-01"],
            plano_b="gerar",
        ),
        "A-002": Ativo(
            id="A-002",
            descricao="Reconstituição da erupção do Vesúvio vista do mar",
            origem=OrigemAtivo.GERAR,
            prompt="Erupção pliniana em 79 d.C.",
            usado_em=["B0-02"],
        ),
    }

    atomic_write_json(
        projeto.pastas.plano / "ativos.json",
        {"versao": 1, "ativos": {aid: a.model_dump(mode="json") for aid, a in ativos.items()}},
    )

    candidato_mock = Candidato(
        id="mock-1",
        origem="mock",
        url_origem="https://mock.local/foto.jpg",
        url_download="https://mock.local/foto.jpg",
        autor="Arqueólogo",
        licenca="CC BY 4.0",
        comercial=True,
        patrimonio_restrito=False,
        largura=2000,
        altura=1500,
    )
    acervo = AdaptadorAcervoMock(candidatos=[candidato_mock])
    curador = CuradorImagens(nota_mock=8.5)

    resolvidos = resolver_ativos_projeto(
        projeto, acervos=[acervo], curador=curador, usar_mock_se_sem_rede=True
    )

    assert len(resolvidos) == 2
    assert (projeto.pastas.plano / "ativos_resolvidos.json").is_file()
    assert (projeto.pastas.plano / "lista_de_busca.md").is_file()
    assert (projeto.pastas.midias / "escolhas.json").is_file()

    escolhas = json.loads((projeto.pastas.midias / "escolhas.json").read_text(encoding="utf-8"))
    assert "A-001" in escolhas
    assert "A-002" in escolhas
    assert escolhas["A-001"]["origem"] == "pesquisar"
    assert escolhas["A-002"]["origem"] == "gerar"


def test_handler_p7_resolucao_validador(tmp_path: Path):
    """Verifica comportamento do validador e handler de P7_resolucao."""
    roteiro = "## B0 — Bloco\n\n**B0-S01**\nInscrição em Pompeia.\n"
    projeto = Projeto.criar(nome="proj_handler_p7", roteiro=roteiro, raiz_projetos=tmp_path)
    executor = criar_executor_projeto(projeto)

    assert "P7_resolucao" in executor._handlers
    validador = executor._validadores["P7_resolucao"]

    from docforja.nucleo.executor import ContextoEtapa

    ctx = ContextoEtapa(
        projeto=projeto,
        etapa=executor.grafo.etapas["P7_resolucao"],
        banco=executor.banco,
    )
    # Antes da resolução, validador deve retornar False
    assert validador(ctx) is False

    # Prepara ativos mínimos e executa resolver_ativos_projeto
    ativos = {
        "A-001": Ativo(
            id="A-001",
            descricao="Inscrição antiga",
            origem=OrigemAtivo.GERAR,
            prompt="Inscrição a carvão",
            usado_em=["B0-01"],
        )
    }
    atomic_write_json(
        projeto.pastas.plano / "ativos.json",
        {"versao": 1, "ativos": {aid: a.model_dump(mode="json") for aid, a in ativos.items()}},
    )
    resolver_ativos_projeto(projeto)

    # Após execução, validador deve retornar True
    assert validador(ctx) is True
    assert (projeto.pastas.plano / "ativos_resolvidos.json").is_file()
    assert (projeto.pastas.plano / "lista_de_busca.md").is_file()

