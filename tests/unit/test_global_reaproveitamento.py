"""Testes de reaproveitamento de ativos da Pasta Global por ID (13 §3, Marco M7)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from docforja.audio.trilha import resolver_trilha_provisoria
from docforja.cli import app
from docforja.esquemas import Ativo, Bloco, OrigemAtivo, Plano, Shot
from docforja.global_assets import (
    avaliar_ativos_para_promocao,
    buscar_ativo_global,
    buscar_mapa_global,
    promover_itens_para_global,
)
from docforja.io import atomic_write_json
from docforja.midia.resolucao import resolver_ativos_projeto
from docforja.nucleo.projeto import Projeto


@pytest.fixture
def pasta_global(tmp_path: Path) -> Path:
    global_dir = tmp_path / "global"
    global_dir.mkdir(parents=True, exist_ok=True)
    return global_dir


def test_promocao_e_reaproveitamento_imagem_por_id(tmp_path: Path, pasta_global: Path):
    """Verifica que o Projeto A promove um ativo e o Projeto B o consome pelo ID global."""
    raiz = tmp_path / "projetos"
    # 1. Projeto A gera e promove ativo A-01
    proj_a = Projeto.criar(nome="projeto_a", roteiro="Texto A", raiz_projetos=raiz)
    img_a = proj_a.pastas.midias / "pesquisadas" / "A-01" / "escolhida.jpg"
    img_a.parent.mkdir(parents=True, exist_ok=True)
    img_a.write_bytes(b"\xFF\xD8\xFF\xE0" + b"\x00" * 32)  # JPEG mock

    ativo_a = Ativo(
        id="A-01",
        descricao="Retrato histórico de Pompeia",
        origem=OrigemAtivo.PESQUISAR,
        caminho=img_a,
        licenca={
            "licenca": "CC-BY-4.0",
            "comercial": True,
            "autor": "Fotógrafo Documental",
        },
        usado_em=["S01", "S02"],
    )

    # Avaliação e promoção com portão humano
    itens_promo = avaliar_ativos_para_promocao(proj_a.slug, {"A-01": ativo_a})
    assert len(itens_promo) == 1
    promovidos = promover_itens_para_global(itens_promo, pasta_global)
    assert promovidos == ["A-01"]

    ficha_global = pasta_global / "imagens" / "A-01.json"
    assert ficha_global.is_file()
    dados_ficha = json.loads(ficha_global.read_text(encoding="utf-8"))
    assert dados_ficha["id_global"] == "global:imagens:A-01"
    assert dados_ficha["comercial"] is True

    # 2. Projeto B consome ativo A-01 referenciando por ID global
    proj_b = Projeto.criar(nome="projeto_b", roteiro="Texto B", raiz_projetos=raiz)
    shot_b = Shot(
        id="B0-01",
        duracao_s=4.0,
        template="KenBurns",
        ativos=["A-REAPROVEITADO"],
    )
    plano_b = Plano(
        versao=1,
        projeto=proj_b.slug,
        blocos=[Bloco(id="B0", titulo="Bloco Único", shots=[shot_b])],
        ativos={
            "A-REAPROVEITADO": Ativo(
                id="A-REAPROVEITADO",
                descricao="Mesmo retrato de Pompeia",
                origem=OrigemAtivo.BIBLIOTECA,
                id_global="global:imagens:A-01",
                usado_em=["B0-01"],
            )
        },
    )
    atomic_write_json(
        proj_b.pastas.plano / "plano_verificado.json",
        plano_b.model_dump(mode="json"),
    )

    resolvidos_b = resolver_ativos_projeto(
        proj_b,
        usar_mock_se_sem_rede=True,
        pasta_global=pasta_global,
    )
    ativo_res = resolvidos_b["A-REAPROVEITADO"]
    assert ativo_res.caminho is not None
    assert ativo_res.caminho.is_file()
    assert ativo_res.id_global == "global:imagens:A-01"

    escolhas = json.loads((proj_b.pastas.midias / "escolhas.json").read_text(encoding="utf-8"))
    assert escolhas["A-REAPROVEITADO"]["origem"] == "global"
    assert escolhas["A-REAPROVEITADO"]["id_global"] == "global:imagens:A-01"


def test_reaproveitamento_de_mapas_regionais(pasta_global: Path):
    """Verifica que mapas regionais na pasta global são resolvidos por correspondência temática."""
    pasta_mapas = pasta_global / "mapas"
    pasta_mapas.mkdir(parents=True, exist_ok=True)

    arquivo_mapa = pasta_mapas / "mapa_campania_vesuvio.png"
    arquivo_mapa.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)

    ficha_mapa = pasta_mapas / "mapa_campania_vesuvio.json"
    atomic_write_json(
        ficha_mapa,
        {
            "id": "mapa_campania_vesuvio",
            "tipo": "mapas",
            "descricao": "Mapa topográfico de relevo da região da Campânia e do Monte Vesúvio",
            "licenca": "ODbL-1.0",
            "comercial": True,
            "arquivo": "mapa_campania_vesuvio.png",
            "tags": ["italia", "campania", "vesuvio", "napoli", "relevo"],
        },
    )

    # Busca por termo direto
    res = buscar_mapa_global("vesuvio", pasta_global=pasta_global)
    assert res is not None
    caminho, ficha = res
    assert caminho.name == "mapa_campania_vesuvio.png"
    assert ficha["id_global"] == "global:mapas:mapa_campania_vesuvio"

    # Busca por região secundária
    res_regiao = buscar_mapa_global("relevo da regiao da campania", pasta_global=pasta_global)
    assert res_regiao is not None
    assert res_regiao[0] == caminho


def test_reaproveitamento_de_trilhas_globais(tmp_path: Path, pasta_global: Path):
    """Verifica que trilhas na pasta global têm prioridade sobre o kit e drone gerado."""
    pasta_trilhas = pasta_global / "trilhas"
    pasta_trilhas.mkdir(parents=True, exist_ok=True)

    wav_trilha = pasta_trilhas / "cinza_tema_epico.wav"
    wav_trilha.write_bytes(b"RIFF" + b"\x00" * 40)
    atomic_write_json(
        pasta_trilhas / "cinza_tema_epico.json",
        {
            "id": "cinza_tema_epico",
            "tipo": "trilhas",
            "descricao": "Tema orquestral sombrio documental",
            "licenca": "CC0",
            "comercial": True,
            "arquivo": "cinza_tema_epico.wav",
            "tags": ["documentario", "epico", "sombrio"],
        },
    )

    proj = Projeto.criar(nome="proj_trilha", roteiro="Texto", raiz_projetos=tmp_path / "projetos")
    trilha_resolvida = resolver_trilha_provisoria(proj, pasta_global=pasta_global)
    assert trilha_resolvida is not None
    assert trilha_resolvida == wav_trilha


def test_bloqueio_estrito_licenca_nao_comercial_na_pasta_global(pasta_global: Path):
    """Garante que ativos com licença NC ou comercial=False são rejeitados na resolução global."""
    pasta_img = pasta_global / "imagens"
    pasta_img.mkdir(parents=True, exist_ok=True)

    # Ativo com licença NC
    arq_nc = pasta_img / "foto_proibida.jpg"
    arq_nc.write_bytes(b"\xFF\xD8\xFF" + b"\x00" * 10)
    atomic_write_json(
        pasta_img / "foto_proibida.json",
        {
            "id": "foto_proibida",
            "tipo": "imagens",
            "descricao": "Foto restrita para uso não comercial",
            "licenca": "CC-BY-NC-4.0",
            "comercial": False,
            "arquivo": "foto_proibida.jpg",
        },
    )

    # Resolução por ID deve retornar None (bloqueio ético e legal mandatório)
    res = buscar_ativo_global("global:imagens:foto_proibida", pasta_global=pasta_global)
    assert res is None


def test_cli_promover_ativo_global(tmp_path: Path, monkeypatch):
    """Testa o comando CLI 'docforja promover' com confirmação de ativo."""
    pasta_global_tmp = tmp_path / "global"
    pasta_global_tmp.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        "docforja.global_assets.obter_pasta_global",
        lambda *args, **kwargs: pasta_global_tmp,
    )
    monkeypatch.setattr(
        "docforja.global_assets.resolucao.obter_pasta_global",
        lambda *args, **kwargs: pasta_global_tmp,
    )

    raiz = tmp_path / "projetos"
    proj = Projeto.criar(nome="proj_cli_promo", roteiro="Roteiro", raiz_projetos=raiz)
    img = proj.pastas.midias / "pesquisadas" / "A-CLI" / "escolhida.jpg"
    img.parent.mkdir(parents=True, exist_ok=True)
    img.write_bytes(b"\xFF\xD8\xFF\xE0" + b"\x00" * 20)

    ativo = Ativo(
        id="A-CLI",
        descricao="Foto de arquivo CLI",
        origem=OrigemAtivo.PESQUISAR,
        caminho=img,
        licenca={"licenca": "CC0", "comercial": True},
        usado_em=["S01", "S02"],
    )
    atomic_write_json(
        proj.pastas.plano / "ativos_resolvidos.json",
        {"total_ativos": 1, "ativos": {"A-CLI": ativo.model_dump(mode="json")}},
    )

    runner = CliRunner()
    result = runner.invoke(app, ["promover", "--projeto", str(proj.raiz), "--ativo", "A-CLI"])
    assert result.exit_code == 0
    assert "ativo(s) promovido(s) para a Pasta Global" in result.stdout
    assert (pasta_global_tmp / "imagens" / "A-CLI.jpg").is_file()
    assert (pasta_global_tmp / "imagens" / "A-CLI.json").is_file()
