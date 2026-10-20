"""Testes de invalidação seletiva multilíngue por bloco na produção (07 §1, 08 §M7)."""

from __future__ import annotations

import json
from pathlib import Path

from docforja.esquemas import Ativo, Bloco, OrigemAtivo, Plano, Shot
from docforja.idiomas.traducao import executar_traducao_projeto
from docforja.io import atomic_write_json
from docforja.nucleo.banco import BancoProjeto
from docforja.nucleo.etapas import DefinicaoEtapa, calcular_hash_dados
from docforja.nucleo.executor import ContextoEtapa
from docforja.nucleo.projeto import Projeto
from docforja.producao.execucao import executar_r2_tratamento, executar_r7_render


def _preparar_projeto_multilingue_dois_blocos(tmp_path: Path) -> tuple[Projeto, Path, Path]:
    """Cria um projeto estruturado com 2 blocos e 2 idiomas (pt-BR e en)."""
    proj = Projeto.criar(
        nome="proj_invalidacao_seletiva",
        roteiro="## B0\n\n**B0-S01**\nTexto 1.\n\n## B1\n\n**B1-S01**\nTexto 2.",
        raiz_projetos=tmp_path / "projetos",
        opcoes_adicionais={"idiomas": {"principal": "pt-BR", "extras": ["en"]}},
    )

    # Imagens dos ativos
    img_a1 = proj.pastas.midias / "pesquisadas" / "A-01" / "escolhida.jpg"
    img_a1.parent.mkdir(parents=True, exist_ok=True)
    img_a1.write_bytes(b"\xFF\xD8\xFF\xE0" + b"IMG_A01_V1" * 8)

    img_a2 = proj.pastas.midias / "pesquisadas" / "A-02" / "escolhida.jpg"
    img_a2.parent.mkdir(parents=True, exist_ok=True)
    img_a2.write_bytes(b"\xFF\xD8\xFF\xE0" + b"IMG_A02_V1" * 8)

    ativo1 = Ativo(
        id="A-01",
        descricao="Cena do Vesúvio",
        origem=OrigemAtivo.PESQUISAR,
        caminho=img_a1,
        licenca={"licenca": "CC0", "comercial": True},
        usado_em=["B0-01"],
    )
    ativo2 = Ativo(
        id="A-02",
        descricao="Rua de Pompeia",
        origem=OrigemAtivo.PESQUISAR,
        caminho=img_a2,
        licenca={"licenca": "CC0", "comercial": True},
        usado_em=["B1-01"],
    )

    shot0_pt = Shot(
        id="B0-01",
        segmentos=["B0-S01"],
        duracao_s=4.0,
        template="KenBurns",
        ativos=["A-01"],
    )
    shot1_pt = Shot(
        id="B1-01",
        segmentos=["B1-S01"],
        duracao_s=4.0,
        template="KenBurns",
        ativos=["A-02"],
    )

    plano_pt = Plano(
        versao=1,
        projeto=proj.slug,
        idiomas={"principal": "pt-BR", "extras": ["en"]},
        blocos=[
            Bloco(id="B0", titulo="A Ameaça", shots=[shot0_pt]),
            Bloco(id="B1", titulo="A Fuga", shots=[shot1_pt]),
        ],
        ativos={"A-01": ativo1, "A-02": ativo2},
    )

    shot0_en = Shot(
        id="B0-01",
        segmentos=["B0-S01"],
        duracao_s=4.5,
        template="KenBurns",
        ativos=["A-01"],
    )
    shot1_en = Shot(
        id="B1-01",
        segmentos=["B1-S01"],
        duracao_s=4.2,
        template="KenBurns",
        ativos=["A-02"],
    )

    plano_en = Plano(
        versao=1,
        projeto=proj.slug,
        idiomas={"principal": "pt-BR", "extras": ["en"]},
        blocos=[
            Bloco(id="B0", titulo="The Threat", shots=[shot0_en]),
            Bloco(id="B1", titulo="The Escape", shots=[shot1_en]),
        ],
        ativos={"A-01": ativo1, "A-02": ativo2},
    )

    for nome in ("plano.json", "plano_verificado.json"):
        atomic_write_json(proj.pastas.plano / nome, plano_pt.model_dump(mode="json"))

    atomic_write_json(
        proj.pastas.plano / "ativos_resolvidos.json",
        {
            "total_ativos": 2,
            "ativos": {
                "A-01": ativo1.model_dump(mode="json"),
                "A-02": ativo2.model_dump(mode="json"),
            },
        },
    )
    atomic_write_json(
        proj.pastas.midias / "escolhas.json",
        {
            "A-01": {"caminho": str(img_a1), "origem": "pesquisar", "aprovado": True},
            "A-02": {"caminho": str(img_a2), "origem": "pesquisar", "aprovado": True},
        },
    )

    # Tradução validada para en
    (proj.pastas.entrada / "traducao_en.md").write_text(
        "## B0\n\n**B0-S01**\nThreat in English.\n\n## B1\n\n**B1-S01**\nEscape in English.",
        encoding="utf-8",
    )
    executar_traducao_projeto(proj)

    pasta_retimado_en = proj.pastas.plano / "idiomas" / "en"
    pasta_retimado_en.mkdir(parents=True, exist_ok=True)
    atomic_write_json(pasta_retimado_en / "plano_retimado.json", plano_en.model_dump(mode="json"))

    # Áudio simulado por idioma
    for idioma, dur1, dur2 in [("pt-BR", 4.0, 8.0), ("en", 4.5, 8.7)]:
        pasta_audio = proj.pastas.audio / idioma
        pasta_audio.mkdir(parents=True, exist_ok=True)
        wav = pasta_audio / "narracao_completa.wav"
        wav.write_bytes(b"RIFF" + b"\x00" * 44)
        segs = [
            {
                "id": "B0-S01",
                "texto": "Texto do bloco zero.",
                "inicio_s": 0.0,
                "fim_s": dur1,
                "palavras": [{"p": "teste", "inicio": 0.0, "fim": dur1}],
            },
            {
                "id": "B1-S01",
                "texto": "Texto do bloco um.",
                "inicio_s": dur1,
                "fim_s": dur2,
                "palavras": [{"p": "fim", "inicio": dur1, "fim": dur2}],
            },
        ]
        atomic_write_json(pasta_audio / "segmentos.json", segs)

    return proj, img_a1, img_a2


def test_invalidacao_seletiva_multilingue(tmp_path: Path):
    """Garante que alterar a imagem do Bloco 0 refaz apenas o Bloco 0 nos dois idiomas."""
    proj, _img_a1, img_a2 = _preparar_projeto_multilingue_dois_blocos(tmp_path)
    ctx = ContextoEtapa(
        projeto=proj,
        etapa=DefinicaoEtapa(id="R7_render"),
        banco=BancoProjeto(proj.banco_file),
    )

    # 1. Primeira execução: R2 e R7
    executar_r2_tratamento(ctx)
    manif_r2_file = proj.pastas.midias / "tratadas" / "manifesto_r2.json"
    manif_r2 = json.loads(manif_r2_file.read_text(encoding="utf-8"))
    assert set(manif_r2["ativos_reprocessados"]) == {"A-01", "A-02"}

    executar_r7_render(ctx)

    # Confere chunks gerados nos dois idiomas
    for idioma in ["pt-BR", "en"]:
        pasta_blocos = proj.pastas.sistema / "render" / idioma / "blocos"
        assert (pasta_blocos / "B0.mp4").is_file()
        assert (pasta_blocos / "B1.mp4").is_file()

        manif_r7_file = proj.pastas.saida / idioma / "manifesto_r7.json"
        manif_r7 = json.loads(manif_r7_file.read_text(encoding="utf-8"))
        assert set(manif_r7["blocos_re_renderizados"]) == {"B0", "B1"}
        assert manif_r7["blocos_reaproveitados"] == []

    # Guarda hashes do Bloco 1 (que NÃO deve mudar)
    chunk_b1_pt = proj.pastas.sistema / "render" / "pt-BR" / "blocos" / "B1.mp4"
    chunk_b1_en = proj.pastas.sistema / "render" / "en" / "blocos" / "B1.mp4"
    hash_b1_pt_inicial = calcular_hash_dados(chunk_b1_pt)
    hash_b1_en_inicial = calcular_hash_dados(chunk_b1_en)
    video_pt_inicial = calcular_hash_dados(proj.pastas.saida / "pt-BR" / "video.mp4")
    video_en_inicial = calcular_hash_dados(proj.pastas.saida / "en" / "video.mp4")

    # 2. Re-execução imediata sem mudanças: 100% de reaproveitamento de cache
    executar_r7_render(ctx)
    for idioma in ["pt-BR", "en"]:
        manif_r7_file = proj.pastas.saida / idioma / "manifesto_r7.json"
        manif_r7 = json.loads(manif_r7_file.read_text(encoding="utf-8"))
        assert manif_r7["blocos_re_renderizados"] == []
        assert set(manif_r7["blocos_reaproveitados"]) == {"B0", "B1"}

    # 3. Altera a imagem do ativo A-01 (pertencente apenas ao Bloco B0)
    nova_img_a1 = proj.pastas.midias / "pesquisadas" / "A-01" / "nova_escolhida.jpg"
    nova_img_a1.write_bytes(b"\xFF\xD8\xFF\xE0" + b"NOVA_IMAGEM_A01_V2" * 12)

    # Atualiza escolhas.json para a nova imagem
    atomic_write_json(
        proj.pastas.midias / "escolhas.json",
        {
            "A-01": {"caminho": str(nova_img_a1), "origem": "pesquisar", "aprovado": True},
            "A-02": {"caminho": str(img_a2), "origem": "pesquisar", "aprovado": True},
        },
    )

    # 4. Executa R2: invalida SOMENTE A-01
    executar_r2_tratamento(ctx)
    manif_r2_file = proj.pastas.midias / "tratadas" / "manifesto_r2.json"
    manif_r2_pos = json.loads(manif_r2_file.read_text(encoding="utf-8"))
    assert manif_r2_pos["ativos_reprocessados"] == ["A-01"]

    # 5. Executa R7: invalida SOMENTE Bloco B0 nos dois idiomas
    executar_r7_render(ctx)

    for idioma in ["pt-BR", "en"]:
        manif_r7_file = proj.pastas.saida / idioma / "manifesto_r7.json"
        manif_r7_pos = json.loads(manif_r7_file.read_text(encoding="utf-8"))
        # Bloco B0 foi re-renderizado
        assert manif_r7_pos["blocos_re_renderizados"] == ["B0"]
        # Bloco B1 foi integralmente REAPROVEITADO do cache!
        assert manif_r7_pos["blocos_reaproveitados"] == ["B1"]

    # Verifica integridade dos chunks: B1 permaneceu idêntico byte a byte
    assert calcular_hash_dados(chunk_b1_pt) == hash_b1_pt_inicial
    assert calcular_hash_dados(chunk_b1_en) == hash_b1_en_inicial

    # Verifica que os vídeos finais de ambos os idiomas foram remontados com sucesso
    assert calcular_hash_dados(proj.pastas.saida / "pt-BR" / "video.mp4") != video_pt_inicial
    assert calcular_hash_dados(proj.pastas.saida / "en" / "video.mp4") != video_en_inicial

    # Garante preservação dos áudios e sincronismo (não foram tocados)
    assert (proj.pastas.audio / "pt-BR" / "narracao_completa.wav").is_file()
    assert (proj.pastas.audio / "en" / "narracao_completa.wav").is_file()


def test_selecao_ui_nao_altera_video_producao(tmp_path: Path):
    """Garante que seleções na prévia interativa da UI não alteram video.mp4 de produção."""
    proj, img_a1, _img_a2 = _preparar_projeto_multilingue_dois_blocos(tmp_path)
    ctx = ContextoEtapa(
        projeto=proj,
        etapa=DefinicaoEtapa(id="R7_render"),
        banco=BancoProjeto(proj.banco_file),
    )

    executar_r2_tratamento(ctx)
    executar_r7_render(ctx)

    video_pt_antes = calcular_hash_dados(proj.pastas.saida / "pt-BR" / "video.mp4")

    # Simula ação da UI registrando revisão em 02_midias/selecoes_ui/
    pasta_ui = proj.pastas.midias / "selecoes_ui"
    pasta_ui.mkdir(parents=True, exist_ok=True)
    atomic_write_json(
        pasta_ui / "rev_001.json",
        {"ativo_id": "A-01", "candidata": "cand_alternativa.jpg"},
    )

    # O arquivo oficial escolhas.json permanece intacto
    escolhas = json.loads((proj.pastas.midias / "escolhas.json").read_text(encoding="utf-8"))
    assert escolhas["A-01"]["caminho"] == str(img_a1)

    # Executar R7 não invalida nada
    executar_r7_render(ctx)
    assert calcular_hash_dados(proj.pastas.saida / "pt-BR" / "video.mp4") == video_pt_antes
