import json

from docforja.esquemas import (
    Ativo,
    Bloco,
    Candidato,
    Credito,
    OrigemAtivo,
    Plano,
    Segmento,
    Shot,
    Timeline,
    TipoProjeto,
)


def test_segmento_serializacao():
    seg = Segmento(
        id="B1-S01",
        texto="Durante séculos, a montanha parecia tranquila.",
        batida="contexto",
        intensidade=4,
        entidades=["Vesúvio"],
    )
    data = json.loads(seg.model_dump_json())
    assert data["id"] == "B1-S01"
    assert data["intensidade"] == 4
    assert "Vesúvio" in data["entidades"]


def test_ativo_e_candidato_schema():
    ativo = Ativo(
        id="A-041",
        descricao="Plínio, o Jovem, olhando o Vesúvio de Miseno",
        origem=OrigemAtivo.GERAR,
        personagem="plinio_jovem",
        usado_em=["B3-08"],
    )
    assert ativo.origem == "gerar"
    assert ativo.usado_em == ["B3-08"]

    candidato = Candidato(
        id="cand-1",
        origem="wikimedia",
        url_origem="http://example.com/item",
        comercial=True,
    )
    assert candidato.comercial is True


def test_plano_completo_validacao():
    shot = Shot(
        id="B1-01",
        segmentos=["B1-S01"],
        duracao_s=4.5,
        template="T01",
        params={"movimento": "push_in"},
    )
    bloco = Bloco(id="B1", titulo="Introdução", shots=[shot])
    plano = Plano(
        projeto="vesuvio",
        tipo=TipoProjeto.LONGO,
        blocos=[bloco],
        ativos={
            "A-001": Ativo(id="A-001", descricao="Vulcão distante", origem=OrigemAtivo.BIBLIOTECA)
        },
    )
    json_str = plano.model_dump_json()
    recarregado = Plano.model_validate_json(json_str)
    assert recarregado.projeto == "vesuvio"
    assert len(recarregado.blocos) == 1
    assert recarregado.blocos[0].shots[0].template == "T01"
    assert "A-001" in recarregado.ativos


def test_credito_e_timeline():
    cred = Credito(ativo_id="A-001", autor="Museu de Nápoles", licenca="CC BY-SA")
    assert cred.autor == "Museu de Nápoles"

    tl = Timeline(projeto="vesuvio", duracao_total_s=120.0)
    assert tl.fps == 30
    assert tl.largura == 1920
