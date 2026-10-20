"""Testes unitários dos módulos de estratégia, otio, saída e promoção global (Marco M6)."""

import json
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from docforja.esquemas import Ativo, Bloco, Plano, Shot
from docforja.estrategia.capitulos import (
    extrair_capitulos_plano,
    formatar_capitulos_txt,
)
from docforja.estrategia.descricao import gerar_descricao_md
from docforja.estrategia.thumbnails import (
    formatar_thumbs_briefing_md,
    gerar_conceitos_thumbnails,
)
from docforja.estrategia.titulos import (
    formatar_titulos_md,
    gerar_titulos_estrategicos,
)
from docforja.global_assets.promocao import (
    avaliar_ativos_para_promocao,
    promover_itens_para_global,
)
from docforja.io import atomic_write_json
from docforja.nucleo.projeto import Projeto
from docforja.producao.execucao import executar_r4_trilha_sfx
from docforja.producao.otio import exportar_projeto_otio, gerar_timeline_otio_dict
from docforja.producao.saida import montar_pacote_saida_completo


def test_r4_preserva_ficha_licenca_na_trilha_do_video_longo(tmp_path: Path, monkeypatch) -> None:
    projeto = Projeto.criar(nome="Com trilha licenciada", roteiro="Teste", raiz_projetos=tmp_path)
    origem = tmp_path / "trilha_origem.wav"
    origem.write_bytes(b"audio licenciado")
    ficha = {"licenca": "CC0-1.0", "comercial": True, "credito": "Livre de direitos"}
    atomic_write_json(origem.with_name(f"{origem.stem}.licenca.json"), ficha)
    monkeypatch.setattr("docforja.producao.execucao.resolver_trilha_provisoria", lambda _: origem)

    executar_r4_trilha_sfx(SimpleNamespace(projeto=projeto))

    destino = projeto.pastas.audio / "trilha" / "trilha_definitiva.wav"
    sidecar = destino.with_name(f"{destino.name}.licenca.json")
    assert destino.read_bytes() == origem.read_bytes()
    assert json.loads(sidecar.read_text(encoding="utf-8")) == ficha


def _criar_plano_amostra() -> Plano:
    return Plano(
        projeto="vesuvio-revelado",
        kit="cinza-e-brasa@1.0",
        preset="padrao",
        blocos=[
            Bloco(
                id="B0",
                titulo="A Inscrição de Pompeia",
                shots=[
                    Shot(
                        id="B0-01", duracao_s=4.0, inicio_s=0.0, fim_s=4.0,
                        template="T01", ativos=["A-01"],
                    ),
                    Shot(id="B0-02", duracao_s=5.0, inicio_s=4.0, fim_s=9.0, template="T08"),
                ],
            ),
            Bloco(
                id="B1",
                titulo="O Colapso da Montanha",
                shots=[
                    Shot(
                        id="B1-01", duracao_s=6.0, inicio_s=9.0, fim_s=15.0,
                        template="T02", ativos=["A-02"],
                    ),
                ],
            ),
        ],
    )


def test_gerar_titulos_estrategicos():
    plano = _criar_plano_amostra()
    titulos = gerar_titulos_estrategicos(plano)

    assert len(titulos) == 10
    assert all(len(t.titulo) <= 60 for t in titulos)
    assert all(0.0 <= t.nota <= 10.0 for t in titulos)

    top_ab = [t for t in titulos if t.recomendado_ab]
    assert len(top_ab) == 3

    md = formatar_titulos_md(titulos)
    assert "# Ideias de Títulos para CTR" in md
    assert "Top 3 Recomendados para Teste A/B" in md
    assert "| 10 |" in md


def test_capitulos_extraem_tempos_reais_com_zero_inicial():
    plano = _criar_plano_amostra()
    caps = extrair_capitulos_plano(plano)

    assert len(caps) == 2
    assert caps[0].timestamp == "00:00"
    assert caps[0].tempo_s == 0.0
    assert caps[1].timestamp == "00:09"
    assert caps[1].tempo_s == 9.0

    txt = formatar_capitulos_txt(caps)
    assert "00:00 A Inscrição de Pompeia\n" in txt
    assert "00:09 O Colapso da Montanha\n" in txt


def test_descricao_md_contem_secoes_obrigatorias():
    plano = _criar_plano_amostra()
    caps = extrair_capitulos_plano(plano)
    desc = gerar_descricao_md(plano, caps)

    assert "## Capítulos" in desc
    assert "00:00 A Inscrição de Pompeia" in desc
    assert "## Fontes e Documentação" in desc
    assert "RECONSTITUIÇÃO ARTÍSTICA" in desc
    assert "#Documentario" in desc


def test_thumbnails_briefing():
    plano = _criar_plano_amostra()
    conceitos = gerar_conceitos_thumbnails(plano)

    assert len(conceitos) == 3
    assert [c.id for c in conceitos] == ["A", "B", "C"]
    assert all(c.legibilidade_120px for c in conceitos)

    md = formatar_thumbs_briefing_md(conceitos)
    assert "## Conceito A" in md
    assert "120 px" in md


def test_timeline_otio_gera_schema_valido(tmp_path: Path):
    plano = _criar_plano_amostra()
    dados_otio = gerar_timeline_otio_dict(plano, fps=24)

    assert dados_otio["OTIO_SCHEMA"] == "Timeline.1"
    assert dados_otio["name"] == plano.projeto
    assert len(dados_otio["tracks"]["children"]) == 2  # Video e Audio

    track_video = dados_otio["tracks"]["children"][0]
    assert track_video["kind"] == "Video"
    assert len(track_video["children"]) == 3  # 3 shots no plano

    arquivo_otio = tmp_path / "projeto.otio"
    exportar_projeto_otio(plano, arquivo_otio)
    assert arquivo_otio.is_file()
    assert '"OTIO_SCHEMA": "Timeline.1"' in arquivo_otio.read_text(encoding="utf-8")


def test_pacote_saida_completo_e_promocao_global(tmp_path: Path):
    proj = Projeto.criar(
        nome="saida_completa_teste",
        roteiro="## B0\n\n**B0-S01**\nTexto.",
        raiz_projetos=tmp_path / "projetos",
    )
    plano = _criar_plano_amostra()

    # Cria fake imagem com licença comercial
    img_path = proj.pastas.midias / "pesquisadas" / "A-01.jpg"
    img_path.write_bytes(b"JPEG_TESTE_IMAGEM")
    img_ficha = img_path.with_name("A-01.jpg.licenca.json")
    img_ficha.write_text('{"licenca": "CC-BY-4.0", "comercial": true}', encoding="utf-8")

    ativo = Ativo(
        id="A-01",
        descricao="Inscrição em Pompeia",
        origem="pesquisar",
        caminho=img_path,
        usado_em=["B0-01"],
        licenca={"licenca": "CC-BY-4.0", "comercial": True, "autor": "Museu MANN"},
    )

    import docforja.io as io_mod

    io_mod.atomic_write_json(
        proj.pastas.plano / "ativos_resolvidos.json",
        {"ativos": {"A-01": ativo.model_dump(mode="json")}},
    )
    io_mod.atomic_write_json(
        proj.pastas.plano / "plano.json",
        plano.model_dump(mode="json"),
    )

    resultado = montar_pacote_saida_completo(proj, duracao_real_s=15.0)
    assert resultado["total_titulos"] == 10
    assert resultado["total_capitulos"] == 2

    # Confere arquivos gerados em 05_saida
    saida = proj.pastas.saida
    meta = saida / "pt-BR" / "metadados"
    assert (meta / "titulos.md").is_file()
    assert (meta / "descricao.md").is_file()
    assert (meta / "capitulos.txt").is_file()
    assert (meta / "tags.txt").is_file()
    assert (meta / "hashtags.txt").is_file()
    assert (meta / "palavras_chave.md").is_file()
    assert (meta / "thumbs_briefing.md").is_file()
    assert (meta / "comentario_fixado.md").is_file()
    assert (meta / "checklist_publicacao.md").is_file()
    assert (meta / "metadados.json").is_file()

    pub = saida / "pt-BR" / "publicacao"
    assert (pub / "agenda.csv").is_file()

    elem = saida / "elementos"
    assert (elem / "projeto.otio").is_file()
    assert (elem / "plano" / "plano.json").is_file()
    assert (elem / "imagens" / "A-01.jpg").is_file()

    assert (saida / "creditos.txt").is_file()
    assert (saida / "relatorio.md").is_file()
    assert (saida / "promover_para_global.md").is_file()

    # Testa promoção para a pasta global
    pasta_global = tmp_path / "global"
    itens_promo = avaliar_ativos_para_promocao(proj.slug, {"A-01": ativo})
    assert len(itens_promo) == 1
    promovidos = promover_itens_para_global(itens_promo, pasta_global)
    assert promovidos == ["A-01"]
    assert (pasta_global / "imagens" / "A-01.jpg").is_file()
    assert (pasta_global / "imagens" / "A-01.json").is_file()


@pytest.mark.anyio
async def test_producao_pipeline_handlers_e_execucao(tmp_path):
    """Verifica que o pipeline M6 avanca apos REVISAO e conclui R1-R10."""
    from docforja.nucleo.handlers import criar_executor_projeto

    proj = Projeto.criar(
        nome="teste_producao_m6",
        roteiro="## B0\n\n**B0-S01**\nTexto de teste narrado.",
        raiz_projetos=tmp_path,
    )

    plano = _criar_plano_amostra()
    atomic_write_json(
        proj.pastas.plano / "plano.json",
        plano.model_dump(mode="json"),
    )

    img_teste = tmp_path / "amostra.jpg"
    img_teste.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20)
    ativo = Ativo(
        id="A-01",
        tipo="imagem",
        descricao="Amostra de teste",
        caminho=img_teste,
        licenca={"licenca": "CC0", "credito": "Acervo", "comercial": True},
    )
    atomic_write_json(
        proj.pastas.plano / "ativos_resolvidos.json",
        {"ativos": {"A-01": ativo.model_dump(mode="json")}},
    )
    audio = proj.pastas.audio / "pt-BR"
    with wave.open(str(audio / "narracao_completa.wav"), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(8000)
        arquivo.writeframes(b"\x00\x00" * 8000)
    atomic_write_json(
        audio / "segmentos.json",
        [{"id": "B0-S01", "texto": "Texto de teste narrado.", "inicio_s": 0, "fim_s": 1}],
    )

    executor = criar_executor_projeto(proj)

    # Substitui etapas preliminares por no-op para isolar o teste das etapas R1-R10
    async def mock_ok(_ctx):
        pass

    for p_id in [
        "E00_entrada", "P1_leitura", "P3_estrategia", "P4_shots",
        "P5_ativos", "P6_verificador", "P7_resolucao", "P8_estimativa_previa",
        "P2_narracao", "P2b_alinhamento",
    ]:
        executor.registrar_handler(p_id, mock_ok)

    # REVISAO sem aprovação deve pausar o avanço da produção
    status_pausa = await executor.executar()
    assert status_pausa.get("REVISAO") == "pausada_revisao"
    assert "R1_imagens" not in status_pausa or status_pausa["R1_imagens"] != "concluida"

    # Libera o portão de revisão humana para produção
    executor.aprovar_gate("REVISAO")
    status_final = await executor.executar()

    assert status_final["REVISAO"] == "concluida"
    for etapa_m6 in [
        "R1_imagens", "R2_tratamento", "R3_mapas", "R4_trilha_sfx",
        "R5_montagem", "R6_mix", "R7_render", "R8_qa", "R9_pacote", "R10_biblioteca",
    ]:
        assert status_final[etapa_m6] == "concluida", f"Etapa {etapa_m6} não concluiu"

    # Confere que o pacote completo foi montado
    saida = proj.pastas.saida
    assert (saida / "relatorio.md").is_file()
    assert (saida / "creditos.txt").is_file()
    assert (saida / "pt-BR" / "metadados" / "metadados.json").is_file()
    assert (saida / "elementos" / "projeto.otio").is_file()

