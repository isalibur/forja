"""Traduções manuais preservam segmentos e nunca modificam arquivos de entrada."""

import json

import pytest

from docforja.idiomas.traducao import executar_traducao_projeto, validar_traducao
from docforja.nucleo.projeto import Projeto

ORIGEM = """## B0 — Introdução
**B0-S01** O Vesúvio desperta. [PAUSA-C]
**B0-S02** A cidade observa.

## B1 — A erupção
**B1-S01** A cinza cobre as ruas.
"""

INGLES = """## B0 — Introduction
**B0-S01** Vesuvius wakes. [PAUSA-C]
**B0-S02** The city watches.

## B1 — The eruption
**B1-S01** Ash covers the streets.
"""


def test_validar_ids_e_ordem():
    resultado = validar_traducao(ORIGEM, INGLES, "en")
    assert [item.id for item in resultado.segmentos] == [
        "B0-S01", "B0-S02", "B1-S01"
    ]
    assert resultado.segmentos[0].texto_limpo.startswith("Vesuvius wakes")
    for texto in [
        INGLES.replace("B0-S02", "B0-S03"),
        INGLES.replace("B0-S02", "B0-S01"),
        INGLES.replace("**B0-S02** The city watches.\n", ""),
        INGLES.replace("## B1 — The eruption", "## B2 — The eruption"),
    ]:
        with pytest.raises(ValueError, match="IDs"):
            validar_traducao(ORIGEM, texto, "en")


def test_validar_preserva_marcas_tecnicas():
    with pytest.raises(ValueError, match="pausas"):
        validar_traducao(ORIGEM, INGLES.replace(" [PAUSA-C]", ""), "en")
    origem = ORIGEM.replace("A cidade observa.", "A cidade observa. [SILÊNCIO 2 s]")
    traducao = INGLES.replace("The city watches.", "The city watches. [SILÊNCIO 3 s]")
    with pytest.raises(ValueError, match="silêncios"):
        validar_traducao(origem, traducao, "en")


def test_modo_manual_exporta_modelo_e_importa_sem_alterar_entrada(tmp_path):
    projeto = Projeto.criar(
        "Traducao manual", roteiro=ORIGEM, idiomas_extras=["en"], raiz_projetos=tmp_path
    )
    with pytest.raises(FileNotFoundError, match=r"traducao_en\.md"):
        executar_traducao_projeto(projeto)
    modelos = list((projeto.pastas.plano / "idiomas").glob("modelo_en_*.md"))
    assert len(modelos) == 1
    assert "B0-S01" in modelos[0].read_text(encoding="utf-8")
    entrada = projeto.pastas.entrada / "traducao_en.md"
    entrada.write_text(INGLES, encoding="utf-8")
    resultado = executar_traducao_projeto(projeto)
    assert len(resultado["en"].segmentos) == 3
    indice = json.loads(
        (projeto.pastas.plano / "idiomas" / "en" / "atual.json").read_text(encoding="utf-8")
    )
    assert (projeto.pastas.plano / "idiomas" / "en" / indice["versao"]).is_file()
    assert entrada.read_text(encoding="utf-8") == INGLES


def test_modo_automatico_falha_sem_saida_falsa(tmp_path):
    projeto = Projeto.criar(
        "Traducao automatica", roteiro=ORIGEM, idiomas_extras=["en"],
        opcoes_adicionais={"traducao": {"modos": {"en": "automatico"}}},
        raiz_projetos=tmp_path,
    )
    with pytest.raises(NotImplementedError, match="automática"):
        executar_traducao_projeto(projeto)
    assert not (projeto.pastas.plano / "idiomas" / "en" / "atual.json").exists()


def test_modo_arquivo_importa_sem_criar_modelo(tmp_path):
    projeto = Projeto.criar(
        "Arquivo traduzido", roteiro=ORIGEM, idiomas_extras=["en"],
        opcoes_adicionais={"traducao": {"modos": {"en": "arquivo"}}},
        raiz_projetos=tmp_path,
    )
    (projeto.pastas.entrada / "traducao_en.md").write_text(INGLES, encoding="utf-8")
    assert len(executar_traducao_projeto(projeto)["en"].segmentos) == 3
    assert not list((projeto.pastas.plano / "idiomas").glob("modelo_*.md"))


def test_sem_idiomas_extras_nao_cria_saida(tmp_path):
    projeto = Projeto.criar("Sem extras", roteiro=ORIGEM, raiz_projetos=tmp_path)
    assert executar_traducao_projeto(projeto) == {}
    assert not (projeto.pastas.plano / "idiomas").exists()
