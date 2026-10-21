from itertools import pairwise
from pathlib import Path

import pytest

from docforja.esquemas import Plano
from docforja.shorts.candidatos import (
    aprovar_frase_ponte,
    gerar_frases_ponte,
    pontuar_candidatos,
    pontuar_candidatos_do_plano,
)
from docforja.shorts.formulas import carregar_formulas
from docforja.shorts.modelos import (
    ElementoTelaShort,
    IntervaloLegendaShort,
    SegmentoShort,
    ShortParaVerificar,
)
from docforja.shorts.verificador import verificar_short
from docforja.shorts.verticalizar import calcular_recorte_vertical, verticalizar_plano


def _segmentos() -> list[SegmentoShort]:
    return [
        SegmentoShort(
            id=f"S{indice}",
            inicio_s=(indice - 1) * 10,
            fim_s=indice * 10,
            texto=f"Trecho narrado {indice}.",
            batida="gancho" if indice == 1 else "contexto",
            autonomia_solo=8,
            curiosidade_para_longo=9,
            forca_visual_vertical=7,
        )
        for indice in range(1, 6)
    ]


def test_pontuar_candidatos_gera_trechos_na_faixa_sem_sobreposicao() -> None:
    candidatos = pontuar_candidatos(_segmentos(), limite=5)

    assert candidatos
    assert all(20 <= item.fim_s - item.inicio_s <= 55 for item in candidatos)
    assert candidatos[0].pontuacao > 0
    assert all(
        anterior.fim_s <= atual.inicio_s
        for anterior, atual in pairwise(candidatos)
    )


def test_candidatos_nao_edita_segmentos_origem() -> None:
    segmentos = _segmentos()
    antes = [item.model_dump() for item in segmentos]

    pontuar_candidatos(segmentos)

    assert [item.model_dump() for item in segmentos] == antes


def test_pontuar_candidatos_do_plano_usa_tempo_real_sem_mudar_plano() -> None:
    plano = Plano.model_validate(
        {
            "projeto": "longo",
            "tipo": "longo",
            "blocos": [
                {
                    "id": "B0",
                    "titulo": "A descoberta",
                    "shots": [
                        {
                            "id": f"SHOT-{indice}",
                            "segmentos": [f"S{indice}"],
                            "duracao_s": 10,
                            "inicio_s": (indice - 1) * 10,
                            "fim_s": indice * 10,
                            "template": "T01",
                            "params": {"batida": "gancho" if indice == 1 else "contexto"},
                        }
                        for indice in range(1, 6)
                    ],
                }
            ],
        }
    )
    antes = plano.model_dump(mode="json")
    audio = [
        {"id": f"S{indice}", "inicio_s": (indice - 1) * 10, "fim_s": indice * 10,
         "texto": f"Fala {indice}."}
        for indice in range(1, 6)
    ]

    candidatos = pontuar_candidatos_do_plano(plano, audio)

    assert candidatos
    assert candidatos[0].segmento_ids[0] == "S1"
    assert plano.model_dump(mode="json") == antes


def test_frases_ponte_requerem_aprovacao_explicita() -> None:
    candidata = pontuar_candidatos(_segmentos(), limite=1)[0]
    candidata.frases_ponte = gerar_frases_ponte("A história do Vesúvio")

    aprovada = aprovar_frase_ponte(candidata, 1)

    assert [item.aprovada for item in aprovada.frases_ponte] == [False, True, False]
    assert not any(item.aprovada for item in candidata.frases_ponte)


def test_aprovar_frase_ponte_rejeita_indice_invalido() -> None:
    candidata = pontuar_candidatos(_segmentos(), limite=1)[0]
    candidata.frases_ponte = gerar_frases_ponte("Longo")

    with pytest.raises(IndexError):
        aprovar_frase_ponte(candidata, 3)


def test_calcular_recorte_vertical_respeita_foco_e_proporcao() -> None:
    recorte = calcular_recorte_vertical(1920, 1080, foco_x=0.8, foco_y=0.5)

    assert recorte.largura == pytest.approx(0.316406)
    assert recorte.x <= 0.8 <= recorte.x + recorte.largura


def test_calcular_recorte_vertical_valida_entrada() -> None:
    with pytest.raises(ValueError):
        calcular_recorte_vertical(0, 1080)
    with pytest.raises(ValueError):
        calcular_recorte_vertical(1920, 1080, foco_x=1.5)


def test_verticalizar_plano_preserva_origem_e_exige_licenca_comercial(tmp_path: Path) -> None:
    imagem = tmp_path / "imagem.png"
    imagem.write_bytes(b"conteudo de teste")
    plano = Plano.model_validate(
        {
            "projeto": "longo",
            "tipo": "longo",
            "blocos": [
                {
                    "id": "B0",
                    "titulo": "Teste",
                    "shots": [
                        {
                            "id": "SHOT-1",
                            "segmentos": ["S1"],
                            "duracao_s": 10,
                            "inicio_s": 0,
                            "fim_s": 10,
                            "template": "T01",
                            "ativos": ["A1"],
                        }
                    ],
                }
            ],
            "ativos": {
                "A1": {
                    "id": "A1",
                    "descricao": "Paisagem de teste",
                    "caminho": str(imagem),
                    "licenca": {"licenca": "CC0", "comercial": True},
                }
            },
        }
    )
    antes = plano.model_dump(mode="json")

    manifesto = verticalizar_plano(plano, {"A1": (1920, 1080)}, focos={"A1": (0.8, 0.5)})

    assert manifesto.proporcao == "9:16"
    assert manifesto.shots[0].ativos[0].hash_origem
    assert plano.model_dump(mode="json") == antes
    plano.ativos["A1"].licenca = {"licenca": "CC BY-NC 4.0", "comercial": False}
    with pytest.raises(ValueError, match="licença liberada"):
        verticalizar_plano(plano, {"A1": (1920, 1080)})


def test_verificador_aplica_regras_ds1_a_ds9() -> None:
    short = ShortParaVerificar(
        duracao_s=30,
        duracao_alvo_s=30,
        inicio_gancho_visual_s=0,
        inicio_gancho_textual_s=0,
        inicio_gancho_falado_s=0.2,
        mudancas_visuais_s=list(range(3, 30, 3)),
        elementos=[ElementoTelaShort(id="titulo", x=0.1, y=0.2, largura=0.7, altura=0.1)],
        legendas=[
            IntervaloLegendaShort(inicio_s=0, fim_s=15, texto="palavra"),
            IntervaloLegendaShort(inicio_s=15, fim_s=30, texto=" palavra"),
        ],
        textos_tela=["Três palavras na tela"],
        quantidade_ctas_principais=1,
        derivado=True,
        frase_ponte_aprovada=True,
        video_longo_id="longo-vesuvio",
        audio_lufs_integrado=-14,
        musica_mais_presente_que_longo=True,
        musica_cobre_voz=False,
    )

    resultado = verificar_short(short)

    assert resultado.aprovado
    assert [item.regra for item in resultado.violacoes] == [f"DS{i}" for i in range(1, 10)]


def test_verificador_reprova_cta_ponte_e_elemento_fora_safe_area() -> None:
    short = ShortParaVerificar(
        duracao_s=30,
        duracao_alvo_s=30,
        inicio_gancho_visual_s=0,
        inicio_gancho_textual_s=2.5,
        inicio_gancho_falado_s=0,
        mudancas_visuais_s=list(range(3, 30, 3)),
        elementos=[ElementoTelaShort(id="cta", x=0.2, y=0.8, largura=0.6, altura=0.1)],
        quantidade_ctas_principais=0,
        derivado=True,
    )

    resultado = verificar_short(short)
    falhas = {item.regra for item in resultado.violacoes if not item.aprovada}

    assert not resultado.aprovado
    assert {"DS1", "DS2", "DS4", "DS5", "DS8", "DS9"} <= falhas


def test_ds9_informa_quando_mascaramento_da_voz_nao_foi_medido() -> None:
    short = ShortParaVerificar(
        duracao_s=30,
        duracao_alvo_s=30,
        inicio_gancho_visual_s=0,
        inicio_gancho_textual_s=0,
        inicio_gancho_falado_s=0,
        mudancas_visuais_s=list(range(3, 30, 3)),
        elementos=[ElementoTelaShort(id="titulo", x=0.1, y=0.2, largura=0.7, altura=0.1)],
        legendas=[
            IntervaloLegendaShort(inicio_s=0, fim_s=30, texto="legenda de teste"),
        ],
        textos_tela=["Texto de teste"],
        quantidade_ctas_principais=1,
        audio_lufs_integrado=-14.0,
        musica_mais_presente_que_longo=False,
        musica_cobre_voz=None,
    )

    resultado = verificar_short(short)
    ds9 = next(item for item in resultado.violacoes if item.regra == "DS9")

    assert not ds9.aprovada
    assert ds9.detalhes == "Mascaramento da voz ainda não foi medido."


def test_ds4_aceita_pausa_natural_entre_blocos_e_reprova_lacuna_real() -> None:
    base = {
        "duracao_s": 22.625,
        "duracao_alvo_s": 22.625,
        "inicio_gancho_visual_s": 0,
        "inicio_gancho_textual_s": 0,
        "inicio_gancho_falado_s": 0.0,
        "mudancas_visuais_s": list(range(3, 22, 3)),
        "quantidade_ctas_principais": 1,
        "audio_lufs_integrado": -14.0,
        "musica_cobre_voz": False,
    }
    com_pausa = verificar_short(
        ShortParaVerificar(
            **base,
            legendas=[
                IntervaloLegendaShort(inicio_s=0, fim_s=1.52, texto="Um rio pode mudar de nome."),
                IntervaloLegendaShort(inicio_s=1.82, fim_s=22.625, texto="O mesmo curso de água."),
            ],
        )
    )
    com_lacuna = verificar_short(
        ShortParaVerificar(
            **base,
            legendas=[
                IntervaloLegendaShort(inicio_s=0, fim_s=1.52, texto="Um rio pode mudar de nome."),
                IntervaloLegendaShort(inicio_s=4.52, fim_s=22.625, texto="O mesmo curso de água."),
            ],
        )
    )

    ds4_pausa = next(item for item in com_pausa.violacoes if item.regra == "DS4")
    ds4_lacuna = next(item for item in com_lacuna.violacoes if item.regra == "DS4")

    assert ds4_pausa.aprovada
    assert not ds4_lacuna.aprovada
    assert "3.00" in ds4_lacuna.detalhes


def test_catalogo_de_formulas_tem_ids_unicos_e_conteudo_afiliado() -> None:
    catalogo = carregar_formulas(Path("global/formulas_shorts"))

    assert len(catalogo) == 11
    assert catalogo["produto_afiliado"].exige_fonte_preco
    assert "V11" in catalogo["produto_afiliado"].templates
