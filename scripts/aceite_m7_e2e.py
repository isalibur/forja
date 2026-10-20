"""Ensaio E2E de Validação de Aceite do Marco M7.

Executa os 3 critérios de aceite final definidos em docs/construtor/08-marcos-de-construcao.md §M7:
1. Vídeo completo e localizado nos 3 idiomas (pt-BR + en + es), com narração, SRT e metadados.
2. Invalidação seletiva por bloco: alteração de uma imagem em escolhas.json re-renderiza
   exclusivamente os blocos afetados nos 3 idiomas, reaproveitando os blocos intactos do cache.
3. Reaproveitamento por ID da Pasta Global: promoção assistida com verificação de licença
   comercial e consumo automático em um segundo projeto.

Execução isolada em pasta temporária descartável, sem modificar projetos reais.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import struct
import sys
import tempfile
import time
import wave
import zlib
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from docforja.audio.trilha import resolver_trilha_provisoria
from docforja.esquemas import Ativo, Bloco, OrigemAtivo, Plano, Shot
from docforja.global_assets.promocao import ItemPromocao, promover_itens_para_global
from docforja.idiomas.traducao import validar_traducao
from docforja.io import atomic_write_json
from docforja.midia.resolucao import resolver_ativos_projeto
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.nucleo.executor import ContextoEtapa, ExecutorPipeline
from docforja.nucleo.handlers import registrar_handlers_disponiveis
from docforja.nucleo.projeto import Projeto
from docforja.producao.execucao import (
    executar_r1_imagens,
    executar_r2_tratamento,
    executar_r3_mapas,
    executar_r4_trilha_sfx,
    executar_r5_montagem,
    executar_r6_mix,
    executar_r7_render,
    executar_r8_qa,
    executar_r9_pacote,
)

ROTEIRO_VESUVIO = """## B0 — O Prenúncio

**B0-S01**
O Vesúvio ergue-se imponente sobre a baía de Nápoles.

## B1 — A Catástrofe

**B1-S01**
Cinzas ardentes sepultaram as cidades romanas em silêncio.
"""


def _criar_wav(caminho: Path, duracao_s: float = 3.0, sample_rate: int = 24000) -> Path:
    """Gera arquivo WAV mono 24 kHz válido."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(caminho), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * int(sample_rate * duracao_s))
    return caminho


def _criar_png_real(
    caminho: Path, r: int, g: int, b: int, largura: int = 120, altura: int = 120
) -> Path:
    """Gera arquivo PNG 100% válido (W3C standard) com cor sólida para render Remotion."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    linha = b"\x00" + bytes([r, g, b]) * largura
    raw_data = linha * altura
    compressed = zlib.compress(raw_data)

    def _chunk(tipo: bytes, dados: bytes) -> bytes:
        crc = zlib.crc32(tipo + dados) & 0xFFFFFFFF
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", compressed)
        + _chunk(b"IEND", b"")
    )
    caminho.write_bytes(png_bytes)
    return caminho


async def executar_cenario_1_multilingue(projeto: Projeto, executor: ExecutorPipeline) -> dict:
    """Cenário 1: Produção Completa em 3 Idiomas (pt-BR, en, es)."""
    print("\n" + "=" * 60)
    print(">>> CENÁRIO 1: Produção Completa em 3 Idiomas (pt-BR + en + es)")
    print("=" * 60)

    # 1. Configura áudios e segmentos para os 3 idiomas
    textos_idiomas = {
        "pt-BR": {
            "B0-S01": ("O Vesúvio ergue-se imponente sobre a baía de Nápoles.", 3.0),
            "B1-S01": ("Cinzas ardentes sepultaram as cidades romanas em silêncio.", 4.0),
        },
        "en": {
            "B0-S01": ("Mount Vesuvius rises majestically over the Bay of Naples.", 2.8),
            "B1-S01": ("Burning ashes buried the Roman cities in silence.", 3.8),
        },
        "es": {
            "B0-S01": ("El Vesubio se alza imponente sobre la bahía de Nápoles.", 3.2),
            "B1-S01": ("Cenizas ardientes sepultaron las ciudades romanas en silencio.", 4.2),
        },
    }

    for idioma, segs in textos_idiomas.items():
        pasta_audio = projeto.pastas.audio / idioma
        pasta_audio.mkdir(parents=True, exist_ok=True)
        segs_lista = []
        cur_t = 0.0
        for sid, (txt, dur) in segs.items():
            segs_lista.append({
                "id": sid,
                "texto": txt,
                "inicio_s": round(cur_t, 3),
                "fim_s": round(cur_t + dur, 3),
                "duracao_s": round(dur, 3),
            })
            cur_t += dur
        atomic_write_json(pasta_audio / "segmentos.json", segs_lista)
        _criar_wav(pasta_audio / "narracao_completa.wav", duracao_s=cur_t)

    # 2. Configura planos (mestre pt-BR e retimados en/es)
    def _montar_plano(idioma: str) -> Plano:
        dur_b0 = textos_idiomas[idioma]["B0-S01"][1]
        dur_b1 = textos_idiomas[idioma]["B1-S01"][1]
        return Plano(
            versao=1,
            projeto=projeto.slug,
            kit="cinza-e-brasa@1.0",
            blocos=[
                Bloco(
                    id="B0",
                    titulo="O Prenúncio",
                    modo_visual="reconstituição",
                    shots=[
                        Shot(
                            id="B0-01",
                            segmentos=["B0-S01"],
                            duracao_s=dur_b0,
                            inicio_s=0.0,
                            fim_s=dur_b0,
                            template="T01",
                            ativos=["A-001"],
                            textos=[textos_idiomas[idioma]["B0-S01"][0]],
                        )
                    ],
                ),
                Bloco(
                    id="B1",
                    titulo="A Catástrofe",
                    modo_visual="reconstituição",
                    shots=[
                        Shot(
                            id="B1-01",
                            segmentos=["B1-S01"],
                            duracao_s=dur_b1,
                            inicio_s=dur_b0,
                            fim_s=dur_b0 + dur_b1,
                            template="T02",
                            ativos=["A-002"],
                            textos=[textos_idiomas[idioma]["B1-S01"][0]],
                        )
                    ],
                ),
            ],
        )

    plano_pt = _montar_plano("pt-BR")
    atomic_write_json(projeto.pastas.plano / "plano.json", plano_pt.model_dump(mode="json"))
    atomic_write_json(
        projeto.pastas.plano / "plano_verificado.json", plano_pt.model_dump(mode="json")
    )

    traducoes_texto = {
        "en": (
            "## B0 — O Prenúncio\n\n"
            "**B0-S01**\n"
            "Mount Vesuvius rises majestically over the Bay of Naples.\n\n"
            "## B1 — A Catástrofe\n\n"
            "**B1-S01**\n"
            "Burning ashes buried the Roman cities in silence.\n"
        ),
        "es": (
            "## B0 — O Prenúncio\n\n"
            "**B0-S01**\n"
            "El Vesubio se alza imponente sobre la bahía de Nápoles.\n\n"
            "## B1 — A Catástrofe\n\n"
            "**B1-S01**\n"
            "Cenizas ardientes sepultaron las ciudades romanas en silencio.\n"
        ),
    }

    for idioma in ("en", "es"):
        plano_ret = _montar_plano(idioma)
        pasta_ret = projeto.pastas.plano / "idiomas" / idioma
        pasta_ret.mkdir(parents=True, exist_ok=True)
        atomic_write_json(pasta_ret / "plano_retimado.json", plano_ret.model_dump(mode="json"))

        traduzido = validar_traducao(ROTEIRO_VESUVIO, traducoes_texto[idioma], idioma)
        versao_nome = f"roteiro_{traduzido.hash_traducao[:16]}.json"
        atomic_write_json(pasta_ret / versao_nome, traduzido.model_dump(mode="json"))
        atomic_write_json(pasta_ret / "atual.json", {"versao": versao_nome, "modo": "arquivo"})

    # 3. Cria imagens reais dos ativos A-001 e A-002 com fichas de licença comercial
    img_a001 = _criar_png_real(
        projeto.pastas.midias / "manual" / "napoles_v1.png", 30, 60, 200
    )
    img_a002 = _criar_png_real(
        projeto.pastas.midias / "manual" / "erupcao_v1.png", 220, 80, 20
    )

    ativos_resolvidos = {
        "versao": 1,
        "ativos": {
            "A-001": Ativo(
                id="A-001",
                tipo="imagem",
                descricao="Vista da baía de Nápoles",
                origem=OrigemAtivo.PEDIR_AO_USUARIO,
                caminho=img_a001,
                usado_em=["B0-01"],
                licenca={"licenca": "CC0", "comercial": True, "autor": "Acervo Histórico"},
            ).model_dump(mode="json"),
            "A-002": Ativo(
                id="A-002",
                tipo="imagem",
                descricao="Erupção do Vesúvio cinzas",
                origem=OrigemAtivo.PEDIR_AO_USUARIO,
                caminho=img_a002,
                usado_em=["B1-01"],
                licenca={"licenca": "CC-BY", "comercial": True, "autor": "Museu Arqueológico"},
            ).model_dump(mode="json"),
        },
    }
    atomic_write_json(projeto.pastas.plano / "ativos_resolvidos.json", ativos_resolvidos)

    # 4. Executa pipeline de produção R1 a R9
    ctx = ContextoEtapa(
        projeto=projeto, etapa=executor.grafo.etapas["R7_render"], banco=executor.banco
    )
    t0 = time.perf_counter()
    executar_r1_imagens(ctx)
    executar_r2_tratamento(ctx)
    executar_r3_mapas(ctx)
    executar_r4_trilha_sfx(ctx)
    executar_r5_montagem(ctx)
    executar_r6_mix(ctx)
    executar_r7_render(ctx)
    executar_r8_qa(ctx)
    executar_r9_pacote(ctx)
    duracao_cenario1 = time.perf_counter() - t0

    print(f"✔ Produção R1-R9 concluída em {duracao_cenario1:.2f}s")

    # Verificações obrigatórias nos 3 idiomas
    for idioma in ("pt-BR", "en", "es"):
        pasta_saida = projeto.pastas.saida / idioma
        assert (pasta_saida / "video.mp4").is_file(), f"video.mp4 ausente em {idioma}"
        srt_path = pasta_saida / "legendas" / "legendas.srt"
        if not srt_path.is_file():
            srt_path = pasta_saida / "legendas" / "legenda.srt"
        assert srt_path.is_file(), f"Arquivo de legenda ausente em {pasta_saida / 'legendas'}"
        srt_content = srt_path.read_text(encoding="utf-8")
        assert len(srt_content.strip()) > 0, f"Arquivo de legenda vazio em {idioma}"

        pasta_meta = pasta_saida / "metadados"
        assert pasta_meta.is_dir(), f"metadados ausente em {idioma}"
        arquivos_esperados = [
            "titulos.md",
            "descricao.md",
            "capitulos.txt",
            "thumbs_briefing.md",
            "tags.txt",
            "hashtags.txt",
            "palavras_chave.md",
            "comentario_fixado.md",
            "post_comunidade.md",
            "checklist_publicacao.md",
            "metadados.json",
        ]
        for arq in arquivos_esperados:
            assert (pasta_meta / arq).is_file(), f"Artefato {arq} ausente em {idioma}"

        print(f"   [{idioma}] Vídeo, SRT e 11 metadados estratégicos verificados com sucesso.")

    return {"status": "sucesso", "tempo_s": duracao_cenario1}


async def executar_cenario_2_invalidacao_seletiva(
    projeto: Projeto, executor: ExecutorPipeline
) -> dict:
    """Cenário 2: Invalidação Seletiva por Bloco nos 3 Idiomas."""
    print("\n" + "=" * 60)
    print(">>> CENÁRIO 2: Invalidação Seletiva por Bloco (pt-BR + en + es)")
    print("=" * 60)

    # 1. Captura hashes e estados pré-invalidação
    hashes_pre = {}
    for idioma in ("pt-BR", "en", "es"):
        pasta_blocos = projeto.pastas.sistema / "render" / idioma / "blocos"
        hashes_pre[idioma] = {
            "B0": calcular_hash_dados(pasta_blocos / "B0.mp4"),
            "B1": calcular_hash_dados(pasta_blocos / "B1.mp4"),
            "video": calcular_hash_dados(projeto.pastas.saida / idioma / "video.mp4"),
        }

    # 2. Usuário troca a imagem do ativo A-001 (usado exclusivamente no bloco B0)
    print("-> Simulando troca da imagem do ativo A-001 (bloco B0) via escolhas.json...")
    nova_img_a001 = _criar_png_real(
        projeto.pastas.midias / "manual" / "napoles_v2_noturna.png", 10, 10, 50
    )

    escolhas = {
        "A-001": {
            "arquivo": nova_img_a001.name,
            "caminho": str(nova_img_a001),
            "origem": "manual",
            "motivo": "Substituição por pintura noturna com melhor contraste",
            "licenca": {"licenca": "CC0", "comercial": True},
        }
    }
    atomic_write_json(projeto.pastas.midias / "escolhas.json", escolhas)

    # 3. Reexecuta R2 (tratamento) e R7 (renderização por blocos)
    ctx = ContextoEtapa(
        projeto=projeto, etapa=executor.grafo.etapas["R7_render"], banco=executor.banco
    )
    t0 = time.perf_counter()
    executar_r2_tratamento(ctx)
    executar_r7_render(ctx)
    duracao_reexecucao = time.perf_counter() - t0

    print(f"✔ Re-render seletivo concluído em {duracao_reexecucao:.2f}s")

    # 4. Auditoria de invalidação seletiva nos 3 idiomas
    for idioma in ("pt-BR", "en", "es"):
        pasta_blocos = projeto.pastas.sistema / "render" / idioma / "blocos"
        manifesto_r7 = json.loads(
            (projeto.pastas.saida / idioma / "manifesto_r7.json").read_text(encoding="utf-8")
        )

        hash_b0_pos = calcular_hash_dados(pasta_blocos / "B0.mp4")
        hash_b1_pos = calcular_hash_dados(pasta_blocos / "B1.mp4")
        hash_video_pos = calcular_hash_dados(projeto.pastas.saida / idioma / "video.mp4")

        # Comprova que B0 foi re-renderizado
        assert manifesto_r7.get("blocos_re_renderizados") == ["B0"], (
            f"[{idioma}] B0 não consta nos re-renderizados: {manifesto_r7}"
        )

        # Comprova que B1 foi REAPROVEITADO DO CACHE (hash idêntico)
        assert hash_b1_pos == hashes_pre[idioma]["B1"], (
            f"[{idioma}] B1 foi indevidamente modificado! Esperado cache hit."
        )
        assert manifesto_r7.get("blocos_reaproveitados") == ["B1"], (
            f"[{idioma}] B1 não consta nos reaproveitados: {manifesto_r7}"
        )

        print(f"   [{idioma}] Invalidação Seletiva Confirmada:")
        print(f"       - Bloco B0: RE-RENDERIZADO (novo hash {hash_b0_pos[:8]})")
        print(f"       - Bloco B1: REAPROVEITADO DO CACHE (hash intacto {hash_b1_pos[:8]})")
        print(f"       - Vídeo final: Concatenado com sucesso ({hash_video_pos[:8]})")

    return {"status": "sucesso", "tempo_s": duracao_reexecucao}


async def executar_cenario_3_pasta_global(pasta_tmp: Path) -> dict:
    """Cenário 3: Reaproveitamento da Pasta Global por ID em um Segundo Projeto."""
    print("\n" + "=" * 60)
    print(">>> CENÁRIO 3: Reaproveitamento da Pasta Global por ID")
    print("=" * 60)

    pasta_global = pasta_tmp / "biblioteca_global"
    pasta_global.mkdir(parents=True, exist_ok=True)

    # 1. Cria e promove um ativo de Mapa e uma Trilha para a Pasta Global
    mapa_origem = _criar_png_real(pasta_tmp / "mapa_vesuvio_relevo.png", 50, 180, 70)
    trilha_origem = _criar_wav(pasta_tmp / "trilha_cinematica.wav", duracao_s=5.0)

    itens_promover = [
        ItemPromocao(
            id="M-VESUVIO",
            tipo="mapas",
            origem_caminho=mapa_origem,
            descricao="Mapa topográfico do Monte Vesúvio e Pompeia",
            licenca="CC0",
            comercial=True,
            credito="Cartografia Histórica Italiana",
            motivo_sugestao="Relevo regional reaproveitável",
        ),
        ItemPromocao(
            id="T-EPICA",
            tipo="trilhas",
            origem_caminho=trilha_origem,
            descricao="Trilha instrumental épica cinza e brasa",
            licenca="CC-BY",
            comercial=True,
            credito="Compositor Oficial",
            motivo_sugestao="Tema orquestral dramático",
        ),
    ]

    promovidos = promover_itens_para_global(itens_promover, pasta_global)
    assert "M-VESUVIO" in promovidos and "T-EPICA" in promovidos, (
        "Falha na promoção para a pasta global."
    )
    print(f"✔ Ativos promovidos para a Pasta Global ({pasta_global}): {promovidos}")

    # 2. Cria o segundo projeto ("vesuvio_segundo_video")
    projeto2 = Projeto.criar(
        nome="vesuvio_segundo_video",
        roteiro="## B0\n\n**B0-S01**\nNovas escavações revelam a rota de fuga romana.",
        raiz_projetos=pasta_tmp / "projetos",
    )

    # 3. Configura o plano do segundo projeto referenciando o ativo global
    ativo_segundo = Ativo(
        id="M-001",
        tipo="mapa",
        descricao="Mapa da região do Vesúvio",
        origem=OrigemAtivo.BIBLIOTECA,
        id_global="global:mapas:M-VESUVIO",
        usado_em=["B0-01"],
    )
    plano2 = Plano(
        versao=1,
        projeto=projeto2.slug,
        kit="cinza-e-brasa@1.0",
        blocos=[
            Bloco(
                id="B0",
                titulo="Escavações",
                shots=[
                    Shot(
                        id="B0-01",
                        segmentos=["B0-S01"],
                        duracao_s=4.0,
                        template="T01",
                        ativos=["M-001"],
                    )
                ],
            )
        ],
        ativos={"M-001": ativo_segundo},
    )
    atomic_write_json(
        projeto2.pastas.plano / "plano_verificado.json", plano2.model_dump(mode="json")
    )

    # 4. Executa resolução de ativos no segundo projeto via resolver_ativos_projeto
    print("-> Resolvendo ativos no segundo projeto a partir da Pasta Global...")
    resolvidos = resolver_ativos_projeto(projeto2, plano2, pasta_global=pasta_global)
    assert "M-001" in resolvidos, "Ativo M-001 não foi resolvido."
    ativo_res = resolvidos["M-001"]

    assert ativo_res.caminho is not None and ativo_res.caminho.is_file(), (
        "Caminho do ativo global não resolvido."
    )
    assert "M-VESUVIO" in ativo_res.caminho.name, "Ativo resolvido não corresponde ao ID global."
    print(f"   ✔ Mapa resolvido por referência global: {ativo_res.caminho}")

    # 5. Executa resolução de trilha provisória consumindo a Pasta Global
    trilha_resolvida = resolver_trilha_provisoria(projeto2, pasta_global=pasta_global)
    assert trilha_resolvida is not None and trilha_resolvida.is_file(), "Trilha não resolvida."
    assert "T-EPICA" in trilha_resolvida.name, (
        "Trilha global não recebeu prioridade de resolução."
    )
    print(f"   ✔ Trilha resolvida da Pasta Global com prioridade: {trilha_resolvida}")

    return {"status": "sucesso", "promovidos": promovidos}


async def main_async() -> None:
    parser = argparse.ArgumentParser(description="Ensaio de Aceitação Final do Marco M7")
    parser.add_argument(
        "--pasta-base",
        type=Path,
        default=Path("E:/05_PROJETOS/forja"),
        help="Pasta base para ensaio isolado (padrão: E:/05_PROJETOS/forja)",
    )
    args = parser.parse_args()

    base_dir = args.pasta_base if args.pasta_base.is_dir() else Path(tempfile.gettempdir())
    pasta_ensaio = Path(tempfile.mkdtemp(prefix="aceite-m7-e2e-", dir=base_dir))
    print("============================================================")
    print("  ENSAIO DE ACEITE DO MARCO M7 (CRITÉRIO 'PRONTO')          ")
    print(f"  Diretório de ensaio: {pasta_ensaio}                       ")
    print("============================================================")

    t_inicio_total = time.perf_counter()

    try:
        # Projeto do Cenário 1 e 2
        projeto1 = Projeto.criar(
            nome="vesuvio_m7_aceite",
            roteiro=ROTEIRO_VESUVIO,
            idioma_principal="pt-BR",
            idiomas_extras=["en", "es"],
            raiz_projetos=pasta_ensaio / "projetos",
        )
        executor1 = ExecutorPipeline(projeto1)
        registrar_handlers_disponiveis(executor1)
        executor1.aprovar_gate("REVISAO")

        # Execução dos 3 Cenários
        res1 = await executar_cenario_1_multilingue(projeto1, executor1)
        res2 = await executar_cenario_2_invalidacao_seletiva(projeto1, executor1)
        res3 = await executar_cenario_3_pasta_global(pasta_ensaio)

        tempo_total = time.perf_counter() - t_inicio_total
        print("\n" + "=" * 60)
        print("  RESULTADO DO ENSAIO DE ACEITAÇÃO DO MARCO M7")
        print("=" * 60)
        print(f"✔ Cenário 1 (3 Idiomas pt-BR + en + es): APROVADO ({res1['tempo_s']:.2f}s)")
        print(f"✔ Cenário 2 (Invalidação Seletiva):     APROVADO ({res2['tempo_s']:.2f}s)")
        total_prom = len(res3['promovidos'])
        print(f"✔ Cenário 3 (Reaproveitamento Global):   APROVADO ({total_prom} ativos)")
        print("------------------------------------------------------------")
        print(f"Tempo total de execução: {tempo_total:.2f}s")
        print(f"Local dos artefatos produzidos: {pasta_ensaio}")
        print("=" * 60)

    except Exception as exc:
        print(f"\n❌ ERRO DURANTE O ENSAIO DE ACEITAÇÃO: {exc}")
        raise


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
