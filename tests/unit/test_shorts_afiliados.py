"""Shorts de afiliado: planilha de produtos, cartão V11 e agenda, sem rede ou GPU."""

from __future__ import annotations

import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from docforja.api import app
from docforja.shorts.afiliados import (
    gerar_agenda_csv,
    gerar_textos_plataforma,
    ler_planilha_produtos,
    linha_agenda,
    roteiro_sugerido,
)
from docforja.shorts.avulsos import ler_lote_afiliados
from docforja.shorts.producao_avulsos import _criar_cenas, preparar_producao, produzir_avulso

CSV_PRODUTOS = (
    "nome,descricao,beneficios,preco,fonte_preco,condicao,link_afiliado,imagens,nicho,plataforma,marca\n"
    "Furadeira Leve,Furadeira compacta para uso doméstico.,"
    "Peso leve|Motor silencioso,\"149,90\",https://loja.exemplo.com/furadeira,,"
    "https://loja.exemplo.com/a?ref=docforja,"
    "global:imagens:produto-furadeira,ferramentas,youtube_shorts,Loja Exemplo\n"
)


def _planilha(invalida: str = "") -> str:
    return CSV_PRODUTOS.replace("Furadeira Leve", invalida) if invalida else CSV_PRODUTOS


def test_planilha_exige_preco_com_fonte_e_recusa_promessa_inventada() -> None:
    produtos = ler_planilha_produtos(CSV_PRODUTOS)
    assert len(produtos) == 1
    assert produtos[0].beneficios == ["Peso leve", "Motor silencioso"]
    assert produtos[0].preco == "149,90"
    assert produtos[0].link_afiliado.startswith("https://")

    sem_fonte = CSV_PRODUTOS.replace(
        "\"149,90\",https://loja.exemplo.com/furadeira,,", "\"149,90\",,,"
    )
    with pytest.raises(ValueError, match="fonte do preço"):
        ler_planilha_produtos(sem_fonte)

    with pytest.raises(ValueError, match="não permitida"):
        ler_planilha_produtos(_planilha("Furadeira o melhor"))

    with pytest.raises(ValueError, match="https"):
        ler_planilha_produtos(
            CSV_PRODUTOS.replace("https://loja.exemplo.com/a?ref=docforja", "http://x.com/a")
        )

    with pytest.raises(ValueError, match="Pasta Global"):
        ler_planilha_produtos(
            CSV_PRODUTOS.replace("global:imagens:produto-furadeira", "produto-furadeira")
        )


def test_roteiro_sugerido_nao_inventa_preco_nem_link() -> None:
    produto = ler_planilha_produtos(CSV_PRODUTOS)[0]
    texto = roteiro_sugerido(produto)

    assert produto.link_afiliado not in texto
    assert "149,90" in texto
    assert texto.lower().count(produto.cta.lower()) == 1


def test_lote_afiliado_cria_pedido_com_produto_e_roteiro_sugerido() -> None:
    pedidos = ler_lote_afiliados(CSV_PRODUTOS)

    assert len(pedidos) == 1
    pedido = pedidos[0]
    assert pedido.formula_id == "produto_afiliado"
    assert pedido.objetivo == "vendas"
    assert pedido.produto is not None
    assert pedido.produto.nome == "Furadeira Leve"
    assert pedido.roteiro_sugerido
    assert pedido.roteiro is None


def test_planilha_com_dez_produtos_gera_dez_pedidos_e_uma_agenda() -> None:
    linhas = ["nome,descricao,beneficios,preco,fonte_preco,link_afiliado,imagens,plataforma,marca"]
    for indice in range(1, 11):
        linhas.append(
            f"Produto {indice},Descricao do produto {indice}.,"
            f"Beneficio um|Beneficio dois,\"1{indice},00\",https://loja.exemplo.com/p{indice},"
            f"https://loja.exemplo.com/p{indice}?ref=docforja,"
            f"global:imagens:produto-{indice},ambas,Loja Exemplo"
        )
    pedidos = ler_lote_afiliados("\n".join(linhas))

    assert len(pedidos) == 10
    assert [pedido.id for pedido in pedidos] == [f"A{indice:03d}" for indice in range(1, 11)]
    assert all(pedido.produto is not None for pedido in pedidos)
    assert all(pedido.produto.link_afiliado.startswith("https://") for pedido in pedidos)


def test_textos_e_agenda_mantem_o_link_fora_do_video() -> None:
    produto = ler_planilha_produtos(CSV_PRODUTOS)[0]
    textos = gerar_textos_plataforma(produto, produto.cta, "Furadeira leve para casa")
    linha = linha_agenda(
        produto,
        textos["titulo"],
        textos["youtube"],
        textos["hashtags"],
        data="2026-10-25",
        hora="18:00",
        arquivos={"video": "video.mp4", "capa": "capa.jpg"},
    )
    agenda = gerar_agenda_csv([linha])

    assert produto.link_afiliado in textos["youtube"]
    assert produto.link_afiliado in agenda
    assert "Publicidade" in textos["youtube"]
    assert "Publicidade" in linha["aviso_publicidade"]
    assert "Furadeira leve para casa" in textos["instagram"]


def _campanha_afiliada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[TestClient, Path, Path, str, str]:
    projetos = tmp_path / "projetos"
    global_ = tmp_path / "global"
    imagens = global_ / "imagens"
    imagens.mkdir(parents=True)
    (imagens / "produto.png").write_bytes(b"imagem-de-teste")
    (imagens / "produto.json").write_text(json.dumps({
        "arquivo": "produto.png", "descricao": "Produto de teste", "licenca": "CC0-1.0",
        "comercial": True,
    }), encoding="utf-8")

    def settings() -> object:
        return type("Settings", (), {"paths": type("Paths", (), {"projects": projetos})()})()

    monkeypatch.setattr("docforja.api.load_settings", settings)
    monkeypatch.setattr("docforja.api.obter_pasta_global", lambda: global_)
    monkeypatch.setattr("docforja.shorts.producao_avulsos._voz_ptbr", lambda: "pm_alex")
    client = TestClient(app)
    planilha = CSV_PRODUTOS.replace("global:imagens:produto-furadeira", "global:imagens:produto")
    previa = client.post("/api/shorts/afiliados/planilhas/planejar", json={"csv_texto": planilha})
    assert previa.status_code == 200
    assert previa.json()["quantidade"] == 1
    criacao = client.post(
        "/api/shorts/afiliados/campanhas", json={"nome": "Afiliados", "csv_texto": planilha}
    )
    assert criacao.status_code == 201
    campanha = criacao.json()
    base = f"/api/shorts/avulsos/campanhas/{campanha['id']}/pedidos/A001"
    resposta = client.post(f"{base}/roteiro/aprovar", json={
        "texto": (
            "Furadeira leve para casa. Peso leve e motor silencioso. "
            "Hoje sai por 149,90. Link na bio para ver o detalhe."
        ),
        "hash_campanha": campanha["hash_conteudo"],
    })
    assert resposta.status_code == 200
    revisao_roteiro = resposta.json()["revisao"]
    selecao = client.post(f"{base}/midias/selecionar", json={
        "ids_globais": ["global:imagens:produto"],
        "hash_campanha": campanha["hash_conteudo"],
        "revisao_roteiro": revisao_roteiro,
    })
    assert selecao.status_code == 200
    revisao_midias = selecao.json()["revisao"]
    ficha = client.post(f"{base}/alegacoes/registrar", json={
        "hash_campanha": campanha["hash_conteudo"],
        "revisao_roteiro": revisao_roteiro,
        "revisao_midias": revisao_midias,
        "dados": {
            "fontes": [{
                "alegacao": "Preço de 149,90 na página do produto.",
                "fonte": "https://loja.exemplo.com/furadeira",
            }],
            "fonte_preco": "https://loja.exemplo.com/furadeira",
            "relacao_comercial": "afiliado",
            "marca": "Loja Exemplo",
            "aviso_publicidade": True,
            "revisado_pelo_usuario": True,
        },
    })
    assert ficha.status_code == 200
    return client, projetos, global_, campanha["id"], base


def test_producao_afiliada_monta_cartao_v11_sem_queimar_o_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, projetos, global_, campanha_id, _ = _campanha_afiliada(tmp_path, monkeypatch)
    preparacao = preparar_producao(projetos, global_, campanha_id, "A001")
    assert preparacao.produto is not None
    assert preparacao.relacao_comercial == "afiliado"

    palavras = [{"text": "Furadeira", "start": 0.0, "end": 1.0}]
    cenas = _criar_cenas(preparacao, palavras, ["ativos/produto.png"], 30.0)
    variantes = [cena.props.variante for cena in cenas]

    assert variantes[0] == "V01"
    assert "V11" in variantes
    assert variantes[-1] == "V07"
    cartoes = [cena for cena in cenas if cena.props.variante == "V11"]
    assert len(cartoes) == 2
    assert cartoes[0].props.titulo == "Furadeira Leve"
    assert cartoes[0].props.itens == ["Peso leve", "Motor silencioso"]
    assert cartoes[1].props.preco == "149,90"
    assert "Publicidade" in cartoes[1].props.aviso_publicidade
    assert all(cena.duracao_frames <= 3 * 30 for cena in cenas)
    assert preparacao.produto.link_afiliado not in json.dumps(
        [cena.props.model_dump(mode="json") for cena in cenas]
    )


def test_producao_afiliada_publica_agenda_e_texto_com_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, projetos, global_, campanha_id, _ = _campanha_afiliada(tmp_path, monkeypatch)
    preparacao = preparar_producao(projetos, global_, campanha_id, "A001")

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
            palavras.write_text(json.dumps([
                {"segmento_id": "avulso", "palavra": "Furadeira", "inicio_s": 0, "fim_s": 30},
            ]), encoding="utf-8")
            return SimpleNamespace(
                wer_medio=0.0, duracao_total_s=30.0,
                arquivo_completo_wav=audio, arquivo_palavras_json=palavras,
            )

    def mixar(_voz: Path, destino: Path, _trilha: object, _relatorio: Path) -> tuple[float, None]:
        destino.write_bytes(b"mix-simulado")
        return -14.0, None

    def renderizar(_composicao: str, _props: Path, _public: Path, destino: Path,
                   *, still: bool = False) -> None:
        destino.write_bytes(b"capa" if still else b"video")

    monkeypatch.setattr(
        "docforja.shorts.producao_avulsos._criar_orquestrador", lambda _: Narrador()
    )
    monkeypatch.setattr(
        "docforja.shorts.producao_avulsos.semaforo_gpu.adquirir_sync", lambda **_: nullcontext()
    )
    monkeypatch.setattr("docforja.shorts.producao_avulsos._mixar_audio", mixar)
    monkeypatch.setattr("docforja.shorts.producao_avulsos._medir_lufs", lambda _caminho: -14.0)
    monkeypatch.setattr("docforja.shorts.producao_avulsos._renderizar", renderizar)

    resultado = produzir_avulso(projetos, global_, preparacao)
    assert resultado["status"] == "concluido"
    saida = (
        projetos / "_campanhas_avulsas" / campanha_id / "saidas" / "A001" / "revisoes"
        / preparacao.revisao
    )
    agenda = (saida / "agenda.csv").read_text(encoding="utf-8")
    youtube = (saida / "youtube.md").read_text(encoding="utf-8")
    metadados = json.loads((saida / "metadados.json").read_text(encoding="utf-8"))

    assert preparacao.produto.link_afiliado in agenda
    assert preparacao.produto.link_afiliado in youtube
    assert metadados["produto"]["link_queimado_no_video"] is False
    assert metadados["relacao_comercial"] == "afiliado"
    assert metadados["publicacao_autorizada"] is False
    assert "Link_Afiliado" in agenda or "Link" in agenda


def test_avulso_sem_aviso_de_publicidade_nao_produz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _projetos, _global, campanha_id, _base = _campanha_afiliada(tmp_path, monkeypatch)
    campanha = client.get(f"/api/shorts/avulsos/campanhas/{campanha_id}").json()
    base = f"/api/shorts/avulsos/campanhas/{campanha_id}/pedidos/A001"
    revisao_roteiro = campanha["aprovacoes_roteiro"]["A001"]["revisao"]
    selecao = campanha["selecoes_midias"]["A001"]
    resposta = client.post(f"{base}/alegacoes/registrar", json={
        "hash_campanha": campanha["hash_conteudo"],
        "revisao_roteiro": revisao_roteiro,
        "revisao_midias": selecao["revisao"],
        "dados": {
            "fontes": [{"alegacao": "Preço na página do produto.", "fonte": "loja.exemplo.com"}],
            "fonte_preco": "https://loja.exemplo.com/furadeira",
            "relacao_comercial": "afiliado",
            "marca": "Loja Exemplo",
            "aviso_publicidade": False,
            "revisado_pelo_usuario": True,
        },
    })
    assert resposta.status_code == 422
