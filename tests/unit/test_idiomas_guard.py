"""O M7 não pode declarar versões extras concluídas sem produzi-las."""

import pytest

from docforja.nucleo.banco import BancoProjeto
from docforja.nucleo.etapas import DefinicaoEtapa
from docforja.nucleo.executor import ContextoEtapa
from docforja.nucleo.projeto import Projeto
from docforja.producao.execucao import executar_noop_idioma_extra


@pytest.mark.parametrize("etapa_id", ["T1_traducao", "T2_narracao_idiomas"])
def test_idiomas_extras_nao_sao_marcados_como_concluidos(tmp_path, etapa_id):
    projeto = Projeto.criar(
        "Idiomas pendentes", idiomas_extras=["en", "es"], raiz_projetos=tmp_path
    )
    contexto = ContextoEtapa(
        projeto=projeto,
        etapa=DefinicaoEtapa(id=etapa_id),
        banco=BancoProjeto(projeto.banco_file),
    )
    with pytest.raises(NotImplementedError, match=etapa_id):
        executar_noop_idioma_extra(contexto)


def test_sem_idiomas_extras_o_noop_permanece_valido(tmp_path):
    projeto = Projeto.criar("Só idioma principal", raiz_projetos=tmp_path)
    contexto = ContextoEtapa(
        projeto=projeto,
        etapa=DefinicaoEtapa(id="T1_traducao"),
        banco=BancoProjeto(projeto.banco_file),
    )
    assert executar_noop_idioma_extra(contexto) is None
