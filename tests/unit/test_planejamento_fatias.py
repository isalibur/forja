"""Shots múltiplos por segmento preservam a linha do tempo real."""

import pytest

from docforja.esquemas import Bloco, Plano, Shot
from docforja.planejamento.dosagem import VerificadorDosagem
from docforja.planejamento.entidades import BlocoProcessado, SegmentoProcessado
from docforja.planejamento.estrategia import EstrategiaBloco
from docforja.planejamento.previa import montar_manifesto_previa
from docforja.planejamento.shots import gerar_shots_bloco
from docforja.planejamento.tempos import intervalos_narrados, segmentos_em_ordem


def _shots() -> tuple[list[Shot], BlocoProcessado]:
    segmento = SegmentoProcessado(
        id="B1-S01", texto_original="Uma narrativa longa.",
        texto_limpo="Uma narrativa longa.", intensidade=8,
    )
    bloco = BlocoProcessado(id="B1", nome="Teste", segmentos=[segmento])
    estrategia = EstrategiaBloco(
        bloco_id="B1", titulo="Teste", modo_visual="misto",
        lut="quente", clima_musical="calmo",
    )
    shots = gerar_shots_bloco(bloco, estrategia, tempos_reais={"B1-S01": 11.0})
    return shots, bloco


def test_p4_divide_fala_longa_sem_perder_tempo():
    shots, bloco = _shots()
    assert len(shots) == 3
    assert segmentos_em_ordem(shots) == ["B1-S01"]
    assert len({shot.id for shot in shots}) == 3
    assert sum(shot.duracao_s for shot in shots) == pytest.approx(11.0)
    assert all(2 <= shot.duracao_s <= 4 for shot in shots)
    audio = [{"id": "B1-S01", "inicio_s": 2.0, "fim_s": 13.0}]
    assert list(intervalos_narrados(shots, audio).values()) == pytest.approx(
        [(2.0, 5.667), (5.667, 9.333), (9.333, 13.0)]
    )
    plano = Plano(projeto="teste", blocos=[Bloco(id="B1", titulo="Teste", shots=shots)])
    resultado = VerificadorDosagem().verificar_e_corrigir(
        plano, blocos_processados=[bloco], tempos_reais={"B1-S01": 11.0}
    )
    assert not any(v.regra in {"D1", "D14"} and not v.corrigida for v in resultado.violacoes)


def test_p8_mostra_cada_fatia_sem_duplicar_audio():
    shots, _ = _shots()
    plano = Plano(projeto="teste", blocos=[Bloco(id="B1", titulo="Teste", shots=shots)])
    manifesto = montar_manifesto_previa(
        plano, [{"id": "B1-S01", "inicio_s": 0, "fim_s": 11}], {}
    )
    assert len(manifesto["shots"]) == 3
    assert manifesto["shots"][0]["inicio_frame"] == 0
    assert manifesto["shots"][-1]["fim_frame"] == 264
    assert all(
        atual["fim_frame"] == seguinte["inicio_frame"]
        for atual, seguinte in zip(manifesto["shots"], manifesto["shots"][1:], strict=False)
    )


def test_fatia_com_lacuna_ou_sobreposicao_falha():
    shots, _ = _shots()
    shots[1].inicio_segmento_s += 0.2
    with pytest.raises(ValueError, match="descontínua"):
        intervalos_narrados(shots, [{"id": "B1-S01", "inicio_s": 0, "fim_s": 11}])
