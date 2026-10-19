"""Teste de aceitação do Marco 4 (M4): Planejamento completo do Vesúvio.

Valida:
1. Cobertura de 100% da narração (116 segmentos em 9 blocos).
2. Uso exclusivo do catálogo fechado (T00-T14 e O1-O4).
3. Verificador de dosagem aprova o plano (D1-D17).
4. Estimativa de tempo dentro do orçamento do preset Padrão (<= 120 min).
5. Geração completa de todos os artefatos em 01_plano/ (plano.json, plano.md,
   verificacao.md, estimativa.md, numeros_na_tela.md).
"""

import json
from pathlib import Path

from docforja.esquemas import Plano
from docforja.planejamento.planejador import PlanejadorVideo
from docforja.planejamento.shots import TEMPLATES_CATALOGO


def test_planejamento_m4_vesuvio_completo(tmp_path: Path):
    """Executa o planejamento completo do Vesúvio e valida todos os critérios de aceitação."""
    caminho_roteiro = Path("docs/pipeline/04-roteiro.md")
    assert caminho_roteiro.is_file(), "Roteiro docs/pipeline/04-roteiro.md não encontrado"

    roteiro_texto = caminho_roteiro.read_text(encoding="utf-8")
    pasta_plano = tmp_path / "01_plano"

    planejador = PlanejadorVideo()
    plano, res_verif, rel_est, relatorios = planejador.planejar_projeto(
        slug_projeto="vesuvio",
        roteiro_texto=roteiro_texto,
        diretorio_saida=pasta_plano,
        preset="padrao",
        kit="cinza-e-brasa@1.0",
        idiomas={"principal": "pt-BR", "extras": ["en", "es"]},
    )

    # 1. Estrutura de blocos
    assert len(plano.blocos) == 9, f"Esperado 9 blocos (B0 a B8), obtido {len(plano.blocos)}"
    blocos_ids = [b.id for b in plano.blocos]
    assert blocos_ids == ["B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]

    # 2. Cobertura de 100% dos segmentos da narração
    todos_segmentos_no_plano: set[str] = set()
    for b in plano.blocos:
        for s in b.shots:
            todos_segmentos_no_plano.update(s.segmentos)

    assert len(todos_segmentos_no_plano) == 116, (
        f"Esperado exatamente 116 segmentos cobertos, obtido {len(todos_segmentos_no_plano)}"
    )
    # Valida segmentos inicial e final
    assert "B0-S01" in todos_segmentos_no_plano
    assert "B8-S13" in todos_segmentos_no_plano

    # 3. Catálogo fechado de templates (T00 a T14) e sobreposições (O1 a O4)
    for b in plano.blocos:
        for s in b.shots:
            assert s.template in TEMPLATES_CATALOGO, (
                f"Template inválido fora do catálogo: {s.template}"
            )
            for o in s.sobreposicoes:
                tipo_o = o.get("tipo")
                assert tipo_o in {"O1", "O2", "O3", "O4"}, f"Sobreposição inválida: {tipo_o}"

    # 4. Verificador de dosagem aprova o plano
    pendencias = res_verif.total_violacoes - res_verif.violacoes_corrigidas
    assert res_verif.aprovado is True, f"Plano reprovado com {pendencias} pendências"
    assert plano.verificacao.get("aprovado") is True

    # 5. Estimativa de produção respeita o orçamento do preset Padrão (<= 120 min)
    assert rel_est.orcamento_minutos == 120
    assert rel_est.tempo_total_minutos <= 120, (
        f"Estimativa ({rel_est.tempo_total_minutos} min) estourou o orçamento de 120 min"
    )
    assert rel_est.aprovado is True

    # 6. Gravação e integridade de todos os artefatos
    assert relatorios is not None
    assert pasta_plano.joinpath("plano.json").is_file()
    assert pasta_plano.joinpath("plano.md").is_file()
    assert pasta_plano.joinpath("verificacao.md").is_file()
    assert pasta_plano.joinpath("estimativa.md").is_file()
    assert pasta_plano.joinpath("numeros_na_tela.md").is_file()

    # Validação do plano.json via Pydantic
    conteudo_json = pasta_plano.joinpath("plano.json").read_text(encoding="utf-8")
    dados_plano = json.loads(conteudo_json)
    plano_recarregado = Plano.model_validate(dados_plano)
    assert plano_recarregado.projeto == "vesuvio"
    assert plano_recarregado.preset == "padrao"
    assert len(plano_recarregado.blocos) == 9

    # Validação do plano.md
    conteudo_md = pasta_plano.joinpath("plano.md").read_text(encoding="utf-8")
    assert "## B0 -" in conteudo_md
    assert "## B3 -" in conteudo_md
    assert "| Shot | Tempo | Narração | Template | Imagem | Texto na tela | Som |" in conteudo_md
    assert "Ativos do bloco:" in conteudo_md

    # Validação do verificacao.md
    conteudo_verif = pasta_plano.joinpath("verificacao.md").read_text(encoding="utf-8")
    assert "[OK] APROVADO" in conteudo_verif
    assert "Relatório de Verificação de Dosagem (D1 a D17)" in conteudo_verif

    # Validação do estimativa.md
    conteudo_est = pasta_plano.joinpath("estimativa.md").read_text(encoding="utf-8")
    assert "[DENTRO DO ORÇAMENTO]" in conteudo_est
    assert "Narração e alinhamento" in conteudo_est
    assert "Geração de imagens" in conteudo_est
    assert "Renderização Remotion" in conteudo_est

    # Validação do numeros_na_tela.md
    conteudo_nums = pasta_plano.joinpath("numeros_na_tela.md").read_text(encoding="utf-8")
    assert "Conferência de Números e Dados na Tela" in conteudo_nums
    assert "| Shot | Item na Tela | Constar no Roteiro? | Status |" in conteudo_nums
