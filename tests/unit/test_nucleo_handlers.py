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
    assert status_ate_p4["P4_shots"] == "falhou"


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
    def __init__(self, disponivel: bool = True, texto_asr: str = "A história começa aqui.") -> None:
        self._disponivel = disponivel
        self.texto_asr = texto_asr

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
        if segmentos_info is None:
            segmentos = [{"texto": self.texto_asr, "inicio_s": 0, "fim_s": 0.5}]
            palavras = []
        else:
            segmentos = segmentos_info
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
