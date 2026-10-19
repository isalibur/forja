"""Testes do motor de dosagem com planos sintéticos violando cada regra D1 a D17."""

from docforja.esquemas import Ativo, Bloco, OrigemAtivo, Plano, Shot
from docforja.planejamento.dosagem import VerificadorDosagem
from docforja.planejamento.entidades import BlocoProcessado, SegmentoProcessado


def criar_plano_base() -> Plano:
    """Cria um plano sintético básico para testes de regras isoladas."""
    return Plano(
        versao=3,
        projeto="teste_sintetico",
        kit="cinza-e-brasa@1.0",
        preset="padrao",
        orcamento_producao_min=120,
        estimativa_producao_min=50,
        blocos=[
            Bloco(
                id="B1",
                titulo="Bloco de Teste",
                modo_visual="misto",
                clima_musical="tenso",
                shots=[
                    Shot(
                        id="B1-01",
                        segmentos=["B1-S01"],
                        duracao_s=4.0,
                        template="T01",
                        params={"movimento": "push_in", "amplitude": 0.03},
                        sobreposicoes=[],
                        ativos=["A-001"],
                        textos=["Texto Curto"],
                        sfx=[],
                        transicao="corte",
                    )
                ],
            )
        ],
        ativos={
            "A-001": Ativo(
                id="A-001",
                descricao="Foto histórica de acervo real da Campânia",
                origem=OrigemAtivo.PESQUISAR,
                usado_em=["B1-01"],
            )
        },
    )


def test_d1_duracao_intensidade():
    """Valida D1: Duração fora dos limites da intensidade é detectada e corrigida."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    # Intensidade 8 (faixa 2.0 a 4.0s), mas shot com 7.0s
    seg = SegmentoProcessado(
        id="B1-S01", texto_original="Texto", texto_limpo="Texto", intensidade=8.0
    )
    bloco_proc = BlocoProcessado(id="B1", nome="Bloco de Teste", segmentos=[seg])
    plano.blocos[0].shots[0].duracao_s = 7.0

    res = verificador.verificar_e_corrigir(
        plano, blocos_processados=[bloco_proc], autocorrige=False
    )
    assert any(v.regra == "D1" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(
        plano, blocos_processados=[bloco_proc], autocorrige=True
    )
    assert res_corr.aprovado is True
    assert plano.blocos[0].shots[0].duracao_s <= 4.0


def test_d2_movimento_max_estatico():
    """Valida D2: Shot estático por mais de 4s é detectado e recebe push_in 2%."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    shot = plano.blocos[0].shots[0]
    shot.duracao_s = 5.0
    shot.params = {"movimento": "estático"}

    res = verificador.verificar_e_corrigir(plano, autocorrige=False)
    assert any(v.regra == "D2" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(plano, autocorrige=True)
    assert res_corr.aprovado is True
    assert shot.params["movimento"] == "push_in"
    assert shot.params["amplitude"] == 0.02


def test_d2_limite_e_correcao_veem_do_yaml(tmp_path):
    config = tmp_path / "dosagem.yaml"
    config.write_text(
        "regras:\n"
        "  D2_movimento_max_estatico:\n"
        "    max_segundos: 3.0\n"
        "    movimento_correcao: zoom_in\n"
        "    amplitude_correcao: 0.07\n",
        encoding="utf-8",
    )
    verificador = VerificadorDosagem(caminho_config=config)
    plano = criar_plano_base()
    shot = plano.blocos[0].shots[0]
    shot.params = {"movimento": "estático"}
    shot.textos = []

    resultado = verificador.verificar_e_corrigir(plano, autocorrige=True)

    assert any(v.regra == "D2" for v in resultado.violacoes)
    assert shot.params["movimento"] == "zoom_in"
    assert shot.params["amplitude"] == 0.07


def test_d3_sequencia_mesmo_template():
    """Valida D3: Mais de 4 shots T01 consecutivos são detectados e corrigidos."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    bloco = plano.blocos[0]
    # Cria 5 shots T01 seguidos
    bloco.shots = [
        Shot(
            id=f"B1-{i:02d}",
            segmentos=[f"B1-S{i:02d}"],
            duracao_s=3.5,
            template="T01",
            params={"movimento": "push_in"},
            ativos=["A-001"],
        )
        for i in range(1, 6)
    ]

    res = verificador.verificar_e_corrigir(plano, autocorrige=False)
    assert any(v.regra == "D3" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(plano, autocorrige=True)
    assert res_corr.aprovado is True
    # Pelo menos um template foi trocado para T02 para quebrar a sequência
    templates = [s.template for s in bloco.shots]
    assert "T02" in templates


def test_d4_templates_informacao_consecutivos():
    """Valida D4: Dois templates de informação seguidos (T08 e T09) são proibidos."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    bloco = plano.blocos[0]
    bloco.shots = [
        Shot(
            id="B1-01",
            segmentos=["B1-S01"],
            duracao_s=4.0,
            template="T08",
            params={"valor": "700.000"},
            textos=["700.000"],
        ),
        Shot(
            id="B1-02",
            segmentos=["B1-S02"],
            duracao_s=4.0,
            template="T09",
            params={"tipo": "escala"},
            textos=["Coluna eruptiva"],
        ),
    ]

    res = verificador.verificar_e_corrigir(plano, autocorrige=False)
    assert any(v.regra == "D4" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(plano, autocorrige=True)
    assert res_corr.aprovado is True
    assert bloco.shots[1].template == "T01"


def test_d5_texto_na_tela_palavras_e_duracao():
    """Valida D5: Texto com mais de 7 palavras ou duração insuficiente é corrigido."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    shot = plano.blocos[0].shots[0]
    shot.textos = ["Uma frase extremamente longa com mais de sete palavras na mesma tela"]
    shot.duracao_s = 2.0  # Muito curto para leitura

    res = verificador.verificar_e_corrigir(plano, autocorrige=False)
    assert any(v.regra == "D5" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(plano, autocorrige=True)
    assert res_corr.aprovado is True
    assert len(shot.textos[0].split()) <= 7


def test_d6_sobreposicoes_simultaneas():
    """Valida D6: Mais de duas sobreposições (fora O2) são limitadas por prioridade."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    shot = plano.blocos[0].shots[0]
    shot.sobreposicoes = [
        {"tipo": "O1", "texto": "PLÍNIO"},
        {"tipo": "O3", "texto": "13:00"},
        {"tipo": "O4", "texto": "Destaque"},
        {"tipo": "O2", "texto": "Crédito Automático"},  # O2 não conta no teto
    ]

    res = verificador.verificar_e_corrigir(plano, autocorrige=False)
    assert any(v.regra == "D6" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(plano, autocorrige=True)
    assert res_corr.aprovado is True
    sobres_reais = [o for o in shot.sobreposicoes if o.get("tipo") != "O2"]
    assert len(sobres_reais) <= 2


def test_d7_identificacao_o1_repetida():
    """Valida D7: Identificação O1 só é permitida na primeira aparição de cada entidade."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    bloco = plano.blocos[0]
    bloco.shots.append(
        Shot(
            id="B1-02",
            segmentos=["B1-S02"],
            duracao_s=4.0,
            template="T01",
            params={"movimento": "push_in"},
            sobreposicoes=[{"tipo": "O1", "texto": "PLÍNIO, O JOVEM"}],
            ativos=["A-001"],
        )
    )
    bloco.shots[0].sobreposicoes = [{"tipo": "O1", "texto": "PLÍNIO, O JOVEM"}]

    res = verificador.verificar_e_corrigir(plano, autocorrige=False)
    assert any(v.regra == "D7" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(plano, autocorrige=True)
    assert res_corr.aprovado is True
    # Segunda aparição teve O1 removido
    assert not any(o.get("tipo") == "O1" for o in bloco.shots[1].sobreposicoes)


def test_d8_respiro_apos_revelacao():
    """Valida D8: Após batida 'revelação', o shot seguinte não pode conter texto na tela."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    bloco = plano.blocos[0]

    seg1 = SegmentoProcessado(
        id="B1-S01", texto_original="T1", texto_limpo="T1", batida="revelação"
    )
    seg2 = SegmentoProcessado(
        id="B1-S02", texto_original="T2", texto_limpo="T2", batida="contexto"
    )
    bloco_proc = BlocoProcessado(id="B1", nome="Bloco", segmentos=[seg1, seg2])

    bloco.shots.append(
        Shot(
            id="B1-02",
            segmentos=["B1-S02"],
            duracao_s=3.0,
            template="T01",
            textos=["Texto que quebra o respiro"],
            ativos=["A-001"],
        )
    )

    res = verificador.verificar_e_corrigir(
        plano, blocos_processados=[bloco_proc], autocorrige=False
    )
    assert any(v.regra == "D8" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(
        plano, blocos_processados=[bloco_proc], autocorrige=True
    )
    assert res_corr.aprovado is True
    assert bloco.shots[1].textos == []


def test_d9_proporcao_geradas_excedida():
    """Valida D9: Proporção de imagens geradas acima do preset (30%) é corrigida."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    bloco = plano.blocos[0]
    # Cria 4 shots todos com imagem gerada (100% > 30%)
    for i in range(1, 5):
        aid = f"A-00{i}"
        plano.ativos[aid] = Ativo(
            id=aid,
            descricao="Cena gerada",
            origem=OrigemAtivo.GERAR,
            usado_em=[f"B1-{i:02d}"],
        )
    bloco.shots = [
        Shot(
            id=f"B1-{i:02d}",
            segmentos=[f"B1-S{i:02d}"],
            duracao_s=3.0,
            template="T01",
            ativos=[f"A-00{i}"],
        )
        for i in range(1, 5)
    ]

    res = verificador.verificar_e_corrigir(plano, autocorrige=False)
    assert any(v.regra == "D9" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(plano, autocorrige=True)
    assert res_corr.aprovado is True


def test_d10_ancora_real_por_bloco():
    """Valida D10: Bloco histórico sem nenhum ativo real de acervo é corrigido."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    # Troca o ativo do bloco para 'gerar' exclusivamente
    plano.ativos["A-001"].origem = OrigemAtivo.GERAR

    res = verificador.verificar_e_corrigir(plano, autocorrige=False)
    assert any(v.regra == "D10" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(plano, autocorrige=True)
    assert res_corr.aprovado is True
    assert plano.ativos["A-001"].origem == OrigemAtivo.PESQUISAR


def test_d11_reuso_mesmo_ativo():
    """Valida D11: Ativo usado em mais de 3 shots é duplicado em variante."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    bloco = plano.blocos[0]
    # Usa A-001 em 5 shots seguidos
    bloco.shots = [
        Shot(
            id=f"B1-{i:02d}",
            segmentos=[f"B1-S{i:02d}"],
            duracao_s=3.0,
            template="T01",
            ativos=["A-001"],
        )
        for i in range(1, 6)
    ]

    res = verificador.verificar_e_corrigir(plano, autocorrige=False)
    assert any(v.regra == "D11" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(plano, autocorrige=True)
    assert res_corr.aprovado is True
    assert "A-001_b" in plano.ativos


def test_d12_transicoes_fade_preto_e_dissolve():
    """Valida D12: fade_preto no meio de bloco e dissolve excessivo são convertidos para corte."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    bloco = plano.blocos[0]
    bloco.shots.append(
        Shot(
            id="B1-02",
            segmentos=["B1-S02"],
            duracao_s=3.0,
            template="T01",
            transicao="fade_preto",  # Ilegal no meio de bloco
            ativos=["A-001"],
        )
    )

    res = verificador.verificar_e_corrigir(plano, autocorrige=False)
    assert any(v.regra == "D12" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(plano, autocorrige=True)
    assert res_corr.aprovado is True
    assert bloco.shots[1].transicao == "corte"


def test_d13_numeros_na_tela_sem_respaldo():
    """Valida D13: Número exibido na tela que não existe no roteiro é corrigido."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    shot = plano.blocos[0].shots[0]
    shot.textos = ["999.000 pessoas"]  # Número inexistente no roteiro

    seg = SegmentoProcessado(
        id="B1-S01",
        texto_original="Havia cerca de vinte mil habitantes.",
        texto_limpo="Havia cerca de vinte mil habitantes.",
    )
    bloco_proc = BlocoProcessado(id="B1", nome="Bloco", segmentos=[seg])

    res = verificador.verificar_e_corrigir(
        plano, blocos_processados=[bloco_proc], autocorrige=False
    )
    assert any(v.regra == "D13" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(
        plano, blocos_processados=[bloco_proc], autocorrige=True
    )
    assert res_corr.aprovado is True
    assert "999.000 pessoas" not in shot.textos


def test_d14_cobertura_100_narra():
    """Valida D14: Segmento de narração omitido no plano é detectado e anexado."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()

    seg1 = SegmentoProcessado(id="B1-S01", texto_original="S1", texto_limpo="S1")
    seg2 = SegmentoProcessado(id="B1-S02", texto_original="S2", texto_limpo="S2")
    bloco_proc = BlocoProcessado(id="B1", nome="Bloco", segmentos=[seg1, seg2])

    res = verificador.verificar_e_corrigir(
        plano, blocos_processados=[bloco_proc], autocorrige=False
    )
    assert any(v.regra == "D14" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(
        plano, blocos_processados=[bloco_proc], autocorrige=True
    )
    assert res_corr.aprovado is True
    assert "B1-S02" in plano.blocos[0].shots[0].segmentos


def test_d15_orcamento_tempo():
    """Valida D15: não aprova orçamento usando economias que não mudaram o plano."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    plano.orcamento_producao_min = 10  # Orçamento que força redução
    # Insere vários shots com parallax T02
    bloco = plano.blocos[0]
    bloco.shots = [
        Shot(
            id=f"B1-{i:02d}",
            segmentos=[f"B1-S{i:02d}"],
            duracao_s=6.0,
            template="T02",
            ativos=["A-001"],
        )
        for i in range(1, 80)
    ]

    templates_antes = [shot.template for shot in bloco.shots]
    res = verificador.verificar_e_corrigir(plano, autocorrige=False)
    violacao_d15 = next(v for v in res.violacoes if v.regra == "D15")
    assert violacao_d15.corrigida is False
    assert res.aprovado is False
    assert [shot.template for shot in bloco.shots] == templates_antes


def test_d16_capitulos():
    """Valida D16: Vídeo com >= 4 blocos sem cartão T12 no início recebe capítulo."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    # Adiciona 4 blocos
    plano.blocos = [
        Bloco(
            id=f"B{i}",
            titulo=f"Capítulo {i}",
            shots=[
                Shot(
                    id=f"B{i}-01",
                    segmentos=[],
                    duracao_s=3.0,
                    template="T01",
                    ativos=["A-001"],
                )
            ],
        )
        for i in range(1, 5)
    ]

    res = verificador.verificar_e_corrigir(plano, autocorrige=False)
    assert any(v.regra == "D16" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(plano, autocorrige=True)
    assert res_corr.aprovado is True
    assert plano.blocos[1].shots[0].template == "T12"


def test_d17_vitimas_reais():
    """Valida D17: Imagem de vítima real com template não permitido ou SFX de impacto é ajustada."""
    verificador = VerificadorDosagem()
    plano = criar_plano_base()
    plano.ativos["A-MOLDE"] = Ativo(
        id="A-MOLDE",
        descricao="Molde de gesso de vítima humana de Pompeia",
        origem=OrigemAtivo.PESQUISAR,
        usado_em=["B1-01"],
    )
    shot = plano.blocos[0].shots[0]
    shot.ativos = ["A-MOLDE"]
    shot.template = "T03"  # FotoRecorte proibido para vítima
    shot.sfx = ["impacto_grave", "whoosh"]

    res = verificador.verificar_e_corrigir(plano, autocorrige=False)
    assert any(v.regra == "D17" for v in res.violacoes)

    res_corr = verificador.verificar_e_corrigir(plano, autocorrige=True)
    assert res_corr.aprovado is True
    assert shot.template == "T01"
    assert "impacto_grave" not in shot.sfx
