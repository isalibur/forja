import json
import wave
from pathlib import Path

import pytest

from docforja.audio.adaptadores.base import AdaptadorTTS
from docforja.audio.narracao import OrquestradorNarracao
from docforja.nucleo.executor import ExecutorPipeline
from docforja.nucleo.handlers import criar_executor_projeto, registrar_handlers_disponiveis
from docforja.nucleo.projeto import Projeto

ROTEIRO_VALIDO = """## B1 — Abertura\n\n**B1-S01** {calmo}\nA história começa aqui.\n"""


@pytest.mark.anyio
async def test_handlers_integrados_validam_entrada_e_salvam_leitura(tmp_path):
    projeto = Projeto.criar(
        nome="teste_handlers", roteiro=ROTEIRO_VALIDO, raiz_projetos=tmp_path
    )
    executor = criar_executor_projeto(projeto)

    status = await executor.executar(ate_etapa="P3_estrategia")

    assert status["E00_entrada"] == "concluida"
    assert status["P1_leitura"] == "concluida"
    assert status["P3_estrategia"] == "concluida"
    assert "P4_shots" not in status
    assert "P2_narracao" not in status
    leitura = json.loads((projeto.pastas.plano / "leitura.json").read_text(encoding="utf-8"))
    assert leitura["total_segmentos"] == 1
    assert leitura["blocos"][0]["segmentos"][0]["texto_limpo"] == "A história começa aqui."
    estrategia = json.loads(
        (projeto.pastas.plano / "estrategia.json").read_text(encoding="utf-8")
    )
    assert estrategia["blocos"][0]["bloco_id"] == "B1"
    assert estrategia["blocos"][0]["modo_visual"] == "reconstituição"

    status_ate_p4 = await executor.executar(ate_etapa="P4_shots")
    assert status_ate_p4["P4_shots"] == "concluida"
    shots = json.loads((projeto.pastas.plano / "shots.json").read_text(encoding="utf-8"))
    assert shots["tempos"] == "estimados"
    assert [sid for shot in shots["blocos"][0]["shots"] for sid in shot["segmentos"]] == [
        "B1-S01"
    ]


@pytest.mark.anyio
async def test_handler_p4_cobre_blocos_e_refaz_saida_corrompida(tmp_path):
    roteiro = (
        "## B1 — Primeiro\n\n**B1-S01**\nUma abertura.\n"
        "## B2 — Segundo\n\n**B2-S01**\nUm detalhe.\n"
    )
    projeto = Projeto.criar(nome="teste_p4_blocos", roteiro=roteiro, raiz_projetos=tmp_path)
    executor = criar_executor_projeto(projeto)
    status = await executor.executar(ate_etapa="P4_shots")
    assert status["P4_shots"] == "concluida"

    caminho = projeto.pastas.plano / "shots.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert [item["bloco_id"] for item in dados["blocos"]] == ["B1", "B2"]
    assert [
        sid for bloco in dados["blocos"] for shot in bloco["shots"] for sid in shot["segmentos"]
    ] == ["B1-S01", "B2-S01"]
    dados["blocos"][1]["shots"][0]["segmentos"] = []
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    status_retomado = await executor.executar(ate_etapa="P4_shots")
    assert status_retomado["P4_shots"] == "concluida"
    corrigido = json.loads(caminho.read_text(encoding="utf-8"))
    assert [
        sid for shot in corrigido["blocos"][1]["shots"] for sid in shot["segmentos"]
    ] == ["B2-S01"]


@pytest.mark.anyio
async def test_handler_p5_consolida_ativos_e_refaz_saida_alterada(tmp_path):
    roteiro = (
        "## B1 — Primeiro\n\n**B1-S01**\nUma abertura.\n"
        "**B1-S02**\nMais um detalhe.\n"
    )
    projeto = Projeto.criar(nome="teste_p5_ativos", roteiro=roteiro, raiz_projetos=tmp_path)
    executor = criar_executor_projeto(projeto)
    status = await executor.executar(ate_etapa="P5_ativos")
    assert status["P5_ativos"] == "concluida"

    shots = json.loads((projeto.pastas.plano / "shots.json").read_text(encoding="utf-8"))
    usos = {}
    for bloco in shots["blocos"]:
        for shot in bloco["shots"]:
            for aid in shot["ativos"]:
                usos.setdefault(aid, []).append(shot["id"])
    caminho = projeto.pastas.plano / "ativos.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert dados["versao"] == 1
    assert {aid: item["usado_em"] for aid, item in dados["ativos"].items()} == usos
    assert all(item["caminho"] is None for item in dados["ativos"].values())

    primeiro = next(iter(dados["ativos"]))
    dados["ativos"][primeiro]["usado_em"] = []
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    status_retomado = await executor.executar(ate_etapa="P5_ativos")
    assert status_retomado["P5_ativos"] == "concluida"
    corrigido = json.loads(caminho.read_text(encoding="utf-8"))
    assert corrigido["ativos"][primeiro]["usado_em"] == usos[primeiro]


@pytest.mark.anyio
async def test_handler_p3_recria_estrategia_ausente_na_retomada(tmp_path):
    projeto = Projeto.criar(
        nome="teste_retomada_p3", roteiro=ROTEIRO_VALIDO, raiz_projetos=tmp_path
    )
    executor = criar_executor_projeto(projeto)
    status = await executor.executar(ate_etapa="P3_estrategia")
    assert status["P3_estrategia"] == "concluida"

    caminho = projeto.pastas.plano / "estrategia.json"
    caminho.unlink()
    status = await executor.executar(ate_etapa="P3_estrategia")
    assert status["P3_estrategia"] == "concluida"
    assert caminho.is_file()


@pytest.mark.anyio
async def test_handler_p3_rejeita_leitura_alterada(tmp_path):
    projeto = Projeto.criar(
        nome="teste_leitura_alterada", roteiro=ROTEIRO_VALIDO, raiz_projetos=tmp_path
    )
    executor = criar_executor_projeto(projeto)
    await executor.executar(ate_etapa="P1_leitura")
    caminho = projeto.pastas.plano / "leitura.json"
    leitura = json.loads(caminho.read_text(encoding="utf-8"))
    leitura["blocos"][0]["segmentos"][0]["texto_limpo"] = "Outro texto."
    caminho.write_text(json.dumps(leitura, ensure_ascii=False), encoding="utf-8")

    status = await executor.executar(ate_etapa="P3_estrategia")
    assert status["P3_estrategia"] == "falhou"
    assert not (projeto.pastas.plano / "estrategia.json").exists()


@pytest.mark.anyio
async def test_handler_p1_rejeita_roteiro_sem_segmentos(tmp_path):
    projeto = Projeto.criar(
        nome="teste_roteiro_invalido", roteiro="Texto sem estrutura.", raiz_projetos=tmp_path
    )
    executor = criar_executor_projeto(projeto)

    status = await executor.executar()

    assert status["E00_entrada"] == "concluida"
    assert status["P1_leitura"] == "falhou"
    assert "Nenhum segmento reconhecido" in executor.banco.obter_etapa("P1_leitura")["erro"]
    assert not (projeto.pastas.plano / "leitura.json").exists()


@pytest.mark.anyio
async def test_handler_e00_rejeita_roteiro_vazio(tmp_path):
    projeto = Projeto.criar(nome="teste_sem_roteiro", raiz_projetos=tmp_path)
    executor = criar_executor_projeto(projeto)

    status = await executor.executar()

    assert status["E00_entrada"] == "falhou"
    assert "não possui roteiro" in executor.banco.obter_etapa("E00_entrada")["erro"]
    assert "P1_leitura" not in status


class TTSFalso(AdaptadorTTS):
    def disponivel(self) -> bool:
        return True

    def gerar(
        self,
        texto: str,
        saida_wav: Path,
        voz: str | None = None,
        idioma: str = "pt-BR",
        velocidade: float = 1.0,
    ) -> Path:
        saida_wav.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(saida_wav), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(24000)
            audio.writeframes(b"\x00\x00" * 12000)
        return saida_wav


class AlinhadorFalso:
    def __init__(
        self, disponivel: bool = True, texto_asr: str | list[str] = "A história começa aqui."
    ) -> None:
        self._disponivel = disponivel
        self.texto_asr = texto_asr
        self.modelo = "modelo-a"
        self.chamadas = 0

    def disponivel(self) -> bool:
        return self._disponivel

    def alinhar(
        self,
        audio_wav: Path,
        saida_palavras: Path,
        saida_segmentos: Path,
        segmentos_info: list[dict] | None = None,
        idioma: str = "pt",
        device: str | None = None,
        timeout: float = 300,
    ) -> tuple[Path, Path]:
        self.chamadas += 1
        if segmentos_info is None:
            textos = self.texto_asr if isinstance(self.texto_asr, list) else [self.texto_asr]
            segmentos = [
                {"texto": texto, "inicio_s": i * 0.5, "fim_s": (i + 1) * 0.5}
                for i, texto in enumerate(textos)
            ]
            palavras = []
        else:
            segmentos = segmentos_info
            if isinstance(self.texto_asr, list):
                palavras = [
                    {"palavra": "teste", "inicio_s": 0, "fim_s": 0.1, "segmento_id": item["id"]}
                    for item in segmentos_info
                ]
            else:
                palavras = [
                    {"palavra": palavra, "inicio_s": 0, "fim_s": 0.1, "segmento_id": "B1-S01"}
                    for palavra in ["A", "história", "começa", "aqui"]
                ]
        saida_palavras.write_text(json.dumps(palavras, ensure_ascii=False), encoding="utf-8")
        saida_segmentos.write_text(json.dumps(segmentos, ensure_ascii=False), encoding="utf-8")
        return saida_palavras, saida_segmentos


@pytest.mark.anyio
async def test_pipeline_narracao_e_alinhamento_reais_com_adaptadores_falsos(tmp_path):
    projeto = Projeto.criar(
        nome="teste_audio_pipeline", roteiro=ROTEIRO_VALIDO, raiz_projetos=tmp_path
    )
    executor = ExecutorPipeline(projeto)
    registrar_handlers_disponiveis(
        executor,
        orquestrador=OrquestradorNarracao(
            adaptador_tts=TTSFalso(), alinhador=AlinhadorFalso()
        ),
    )

    status = await executor.executar(ate_etapa="P2b_alinhamento")

    assert status["P2_narracao"] == "concluida"
    assert status["P2b_alinhamento"] == "concluida"
    assert "P3_estrategia" not in status
    pasta_audio = projeto.pastas.audio / "pt-BR"
    assert (pasta_audio / "narracao_completa.wav").is_file()
    assert json.loads((pasta_audio / "qualidade.json").read_text(encoding="utf-8"))["wer"] == 0
    assert len(json.loads((pasta_audio / "palavras.json").read_text(encoding="utf-8"))) == 4

    (pasta_audio / "qualidade.json").unlink()
    status_retomado = await executor.executar(ate_etapa="P2b_alinhamento")
    assert status_retomado["P2b_alinhamento"] == "concluida"
    assert (pasta_audio / "qualidade.json").is_file()


@pytest.mark.anyio
async def test_troca_modelo_asr_invalida_alinhamento_aprovado(tmp_path):
    projeto = Projeto.criar(
        nome="teste_troca_modelo_asr", roteiro=ROTEIRO_VALIDO, raiz_projetos=tmp_path
    )
    alinhador = AlinhadorFalso()
    executor = registrar_handlers_disponiveis(
        ExecutorPipeline(projeto),
        orquestrador=OrquestradorNarracao(
            adaptador_tts=TTSFalso(), alinhador=alinhador
        ),
    )
    await executor.executar(ate_etapa="P2b_alinhamento")
    pasta = projeto.pastas.audio / "pt-BR"
    qualidade = pasta / "qualidade.json"
    assert json.loads(qualidade.read_text(encoding="utf-8"))["modelo_asr"] == "modelo-a"
    chamadas_iniciais = alinhador.chamadas

    await executor.executar(ate_etapa="P2b_alinhamento")
    assert alinhador.chamadas == chamadas_iniciais

    alinhador.modelo = "modelo-b"
    status = await executor.executar(ate_etapa="P2b_alinhamento")
    assert status["P2b_alinhamento"] == "concluida"
    assert alinhador.chamadas > chamadas_iniciais
    assert json.loads(qualidade.read_text(encoding="utf-8"))["modelo_asr"] == "modelo-b"


@pytest.mark.anyio
async def test_pipeline_registra_wer_reprovado_sem_concluir_alinhamento(tmp_path):
    projeto = Projeto.criar(
        nome="teste_wer_reprovado", roteiro=ROTEIRO_VALIDO, raiz_projetos=tmp_path
    )
    executor = ExecutorPipeline(projeto)
    registrar_handlers_disponiveis(
        executor,
        orquestrador=OrquestradorNarracao(
            adaptador_tts=TTSFalso(),
            alinhador=AlinhadorFalso(texto_asr="A história com Mesa Raki."),
        ),
    )

    status = await executor.executar(ate_etapa="P2b_alinhamento")

    assert status["P2b_alinhamento"] == "falhou"
    qualidade = json.loads(
        (projeto.pastas.audio / "pt-BR" / "qualidade.json").read_text(encoding="utf-8")
    )
    assert qualidade["status"] == "reprovado"
    assert qualidade["wer"] > qualidade["limite_wer"]
    assert qualidade["transcricao_primeira_passagem"] == "A história com Mesa Raki."


@pytest.mark.anyio
async def test_pipeline_refaz_apenas_segmento_reprovado(tmp_path):
    class TTSContador(TTSFalso):
        def __init__(self):
            self.chamadas = 0

        def gerar(self, texto, saida_wav, voz=None, idioma="pt-BR", velocidade=1.0):
            self.chamadas += 1
            return super().gerar(texto, saida_wav, voz, idioma, velocidade)

    roteiro = (
        "## B1 — Abertura\n\n**B1-S01**\nA história começa aqui.\n"
        "**B1-S02**\nA cidade desapareceu ontem.\n"
    )
    projeto = Projeto.criar(nome="teste_refacao", roteiro=roteiro, raiz_projetos=tmp_path)
    tts = TTSContador()
    executor = ExecutorPipeline(projeto)
    registrar_handlers_disponiveis(
        executor,
        orquestrador=OrquestradorNarracao(
            adaptador_tts=tts,
            alinhador=AlinhadorFalso(
                texto_asr=["A história começa aqui.", "A cidade apareceu ontem."]
            ),
        ),
    )

    status = await executor.executar(ate_etapa="P2b_alinhamento")

    assert status["P2b_alinhamento"] == "falhou"
    assert tts.chamadas == 3  # dois takes iniciais e só um segmento refeito


@pytest.mark.anyio
async def test_pipeline_aceita_numero_equivalente_no_asr(tmp_path):
    roteiro = "## B1 — Abertura\n\n**B1-S01**\nDezesseis dias antes de novembro.\n"
    projeto = Projeto.criar(
        nome="teste_numero_asr", roteiro=roteiro, raiz_projetos=tmp_path
    )
    executor = ExecutorPipeline(projeto)
    registrar_handlers_disponiveis(
        executor,
        orquestrador=OrquestradorNarracao(
            adaptador_tts=TTSFalso(),
            alinhador=AlinhadorFalso(texto_asr="16 dias antes de novembro."),
        ),
    )

    status = await executor.executar(ate_etapa="P2b_alinhamento")

    assert status["P2b_alinhamento"] == "concluida"
    qualidade = json.loads(
        (projeto.pastas.audio / "pt-BR" / "qualidade.json").read_text(encoding="utf-8")
    )
    assert qualidade["wer"] == 0.0
    assert qualidade["wer_bruto_primeira_passagem"] > 0


@pytest.mark.anyio
async def test_pipeline_usa_wer_global_sem_reprovar_segmento_curto(tmp_path):
    texto_1 = (
        "A história começa aqui com detalhes sobre a cidade e as pessoas daquele tempo antigo."
    )
    texto_2 = "O dia era claro e o caminho seguia pela região. " * 5
    roteiro = f"## B1 — Abertura\n\n**B1-S01**\n{texto_1}\n\n**B1-S02**\n{texto_2}\n"

    class AlinhadorDoisSegmentos(AlinhadorFalso):
        def alinhar(self, audio_wav, saida_palavras, saida_segmentos, segmentos_info=None,
                    idioma="pt", device=None, timeout=300):
            if segmentos_info is None:
                segmentos = [
                    {"texto": texto_1.replace("cidade", "aldeia"), "inicio_s": 0, "fim_s": 0.5},
                    {"texto": texto_2, "inicio_s": 0.5, "fim_s": 1.0},
                ]
                palavras = []
            else:
                segmentos = segmentos_info
                palavras = [
                    {"palavra": "teste", "inicio_s": 0, "fim_s": 0.1, "segmento_id": item["id"]}
                    for item in segmentos_info
                ]
            saida_palavras.write_text(json.dumps(palavras), encoding="utf-8")
            saida_segmentos.write_text(
                json.dumps(segmentos, ensure_ascii=False), encoding="utf-8"
            )
            return saida_palavras, saida_segmentos

    projeto = Projeto.criar(nome="teste_wer_global", roteiro=roteiro, raiz_projetos=tmp_path)
    executor = ExecutorPipeline(projeto)
    registrar_handlers_disponiveis(
        executor,
        orquestrador=OrquestradorNarracao(
            adaptador_tts=TTSFalso(), alinhador=AlinhadorDoisSegmentos()
        ),
    )
    status = await executor.executar(ate_etapa="P2b_alinhamento")

    assert status["P2b_alinhamento"] == "concluida"
    qualidade = json.loads(
        (projeto.pastas.audio / "pt-BR" / "qualidade.json").read_text(encoding="utf-8")
    )
    assert 0 < qualidade["wer"] <= qualidade["limite_wer"]
    assert qualidade["wer_segmentos_primeira_passagem"]["B1-S01"] > 0.02


@pytest.mark.anyio
async def test_pipeline_p6_verifica_plano_com_alinhamento_aprovado(tmp_path):
    projeto = Projeto.criar(
        nome="teste_p6_integrado", roteiro=ROTEIRO_VALIDO, raiz_projetos=tmp_path
    )
    executor = ExecutorPipeline(projeto)
    registrar_handlers_disponiveis(
        executor,
        orquestrador=OrquestradorNarracao(
            adaptador_tts=TTSFalso(), alinhador=AlinhadorFalso()
        ),
    )

    status = await executor.executar(ate_etapa="P6_verificador")
    assert status["P2b_alinhamento"] == "concluida"
    assert status["P5_ativos"] == "concluida"
    assert status["P6_verificador"] == "concluida"

    pasta = projeto.pastas.plano
    plano = json.loads((pasta / "plano_verificado.json").read_text(encoding="utf-8"))
    verificacao = json.loads((pasta / "verificacao.json").read_text(encoding="utf-8"))
    assert plano["verificacao"]["aprovado"] is True
    assert verificacao["aprovado"] is True
    assert plano["verificacao"]["fase"] == "pre_resolucao_ativos"
    for nome in [
        "plano.json",
        "plano.md",
        "verificacao.md",
        "estimativa.md",
        "numeros_na_tela.md",
    ]:
        assert (pasta / nome).is_file()
    assert "Rascunho M4" in (pasta / "plano.md").read_text(encoding="utf-8")
    assert [
        sid for bloco in plano["blocos"] for shot in bloco["shots"] for sid in shot["segmentos"]
    ] == ["B1-S01"]

    verificacao["aprovado"] = False
    (pasta / "verificacao.json").write_text(
        json.dumps(verificacao, ensure_ascii=False), encoding="utf-8"
    )
    retomado = await executor.executar(ate_etapa="P6_verificador")
    assert retomado["P6_verificador"] == "concluida"
    corrigido = json.loads((pasta / "verificacao.json").read_text(encoding="utf-8"))
    assert corrigido["aprovado"] is True

    plano["blocos"][0]["shots"][0]["template"] = "T99"
    (pasta / "plano_verificado.json").write_text(
        json.dumps(plano, ensure_ascii=False), encoding="utf-8"
    )
    retomado = await executor.executar(ate_etapa="P6_verificador")
    assert retomado["P6_verificador"] == "concluida"
    plano_corrigido = json.loads(
        (pasta / "plano_verificado.json").read_text(encoding="utf-8")
    )
    assert plano_corrigido["blocos"][0]["shots"][0]["template"] != "T99"

    (pasta / "estimativa.md").write_text("alterado", encoding="utf-8")
    retomado = await executor.executar(ate_etapa="P6_verificador")
    assert retomado["P6_verificador"] == "concluida"
    assert "Rascunho M4" in (pasta / "estimativa.md").read_text(encoding="utf-8")


@pytest.mark.anyio
async def test_pipeline_p6_nao_avanca_sem_alinhamento_aprovado(tmp_path):
    projeto = Projeto.criar(
        nome="teste_p6_sem_alinhamento", roteiro=ROTEIRO_VALIDO, raiz_projetos=tmp_path
    )
    executor = ExecutorPipeline(projeto)
    registrar_handlers_disponiveis(
        executor,
        orquestrador=OrquestradorNarracao(
            adaptador_tts=TTSFalso(),
            alinhador=AlinhadorFalso(texto_asr="A história com Mesa Raki."),
        ),
    )

    status = await executor.executar(ate_etapa="P6_verificador")
    assert status["P2b_alinhamento"] == "falhou"
    assert "P6_verificador" not in status
    assert not (projeto.pastas.plano / "plano_verificado.json").exists()


@pytest.mark.anyio
async def test_pipeline_exige_whisperx_para_concluir_alinhamento(tmp_path):
    projeto = Projeto.criar(
        nome="teste_sem_whisperx", roteiro=ROTEIRO_VALIDO, raiz_projetos=tmp_path
    )
    executor = ExecutorPipeline(projeto)
    alinhador = AlinhadorFalso(disponivel=False)
    registrar_handlers_disponiveis(
        executor,
        orquestrador=OrquestradorNarracao(
            adaptador_tts=TTSFalso(), alinhador=alinhador
        ),
    )

    status = await executor.executar(ate_etapa="P2b_alinhamento")

    assert status["P2_narracao"] == "concluida"
    assert status["P2b_alinhamento"] == "falhou"
    pasta_audio = projeto.pastas.audio / "pt-BR"
    assert (pasta_audio / "narracao_completa.wav").is_file()
    assert not (pasta_audio / "palavras.json").exists()
    assert not (pasta_audio / "qualidade.json").exists()

    alinhador._disponivel = True
    status_retomado = await executor.executar(ate_etapa="P2b_alinhamento")
    assert status_retomado["P2b_alinhamento"] == "concluida"
    assert (pasta_audio / "qualidade.json").is_file()


@pytest.mark.anyio
async def test_pipeline_p4_adota_tempos_reais_quando_p2_conclui(tmp_path):
    projeto = Projeto.criar(
        nome="teste_p4_tempos_reais", roteiro=ROTEIRO_VALIDO, raiz_projetos=tmp_path
    )
    executor = ExecutorPipeline(projeto)
    registrar_handlers_disponiveis(
        executor,
        orquestrador=OrquestradorNarracao(
            adaptador_tts=TTSFalso(), alinhador=AlinhadorFalso()
        ),
    )

    status_p4 = await executor.executar(ate_etapa="P4_shots")
    assert status_p4["P4_shots"] == "concluida"
    caminho_shots = projeto.pastas.plano / "shots.json"
    dados_shots_estimados = json.loads(caminho_shots.read_text(encoding="utf-8"))
    assert dados_shots_estimados["tempos"] == "estimados"

    status_p2 = await executor.executar(ate_etapa="P2_narracao")
    assert status_p2["P2_narracao"] == "concluida"
    dados_shots_reais = json.loads(caminho_shots.read_text(encoding="utf-8"))
    assert dados_shots_reais["tempos"] == "reais"
    duracao_real_audio = dados_shots_reais["blocos"][0]["shots"][0]["duracao_s"]
    assert duracao_real_audio == 0.5


@pytest.mark.anyio
async def test_pipeline_p6_reenvia_ao_llm_bloco_reprovado(tmp_path, monkeypatch):
    from docforja.esquemas import Shot
    from docforja.planejamento.dosagem import ResultadoVerificacao, VerificadorDosagem, Violacao
    from docforja.planejamento.shots import ReparoShotsBloco

    class RoteadorMock:
        def __init__(self):
            self.chamadas = 0

        def completar_estruturado(self, prompt, schema, sistema="", **kwargs):
            self.chamadas += 1
            return ReparoShotsBloco(
                bloco_id="B1",
                shots=[
                    Shot(
                        id="B1-01",
                        segmentos=["B1-S01"],
                        duracao_s=4.0,
                        template="T01",
                        params={"movimento": "push_in", "amplitude": 0.02},
                        sobreposicoes=[],
                        ativos=["A-001"],
                        textos=[],
                        sfx=[],
                        transicao="corte",
                    )
                ],
            )

    chamadas_verif = 0
    orig_verificar = VerificadorDosagem.verificar_e_corrigir

    def mock_verificar(self, plano, blocos_processados=None, autocorrige=True):
        nonlocal chamadas_verif
        chamadas_verif += 1
        if chamadas_verif == 1:
            return ResultadoVerificacao(
                aprovado=False,
                total_violacoes=1,
                violacoes_corrigidas=0,
                violacoes=[
                    Violacao(
                        regra="D3",
                        descricao="Excesso de templates consecutivos iguais",
                        bloco_id="B1",
                        detalhes="Violação que exige intervenção do LLM",
                        corrigida=False,
                    )
                ],
                ajustes=[],
            )
        return orig_verificar(
            self, plano, blocos_processados=blocos_processados, autocorrige=autocorrige
        )

    monkeypatch.setattr(VerificadorDosagem, "verificar_e_corrigir", mock_verificar)

    projeto = Projeto.criar(
        nome="teste_p6_loop_llm", roteiro=ROTEIRO_VALIDO, raiz_projetos=tmp_path
    )
    roteador_mock = RoteadorMock()
    executor = ExecutorPipeline(projeto)
    registrar_handlers_disponiveis(
        executor,
        orquestrador=OrquestradorNarracao(
            adaptador_tts=TTSFalso(), alinhador=AlinhadorFalso()
        ),
        roteador_llm=roteador_mock,
    )

    status = await executor.executar(ate_etapa="P6_verificador")
    assert status["P6_verificador"] == "concluida"
    assert roteador_mock.chamadas == 1
    assert chamadas_verif >= 2
