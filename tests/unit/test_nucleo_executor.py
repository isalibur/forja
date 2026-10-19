import asyncio

import pytest

from docforja.nucleo.etapas import DefinicaoEtapa, PipelineGrafo
from docforja.nucleo.executor import ContextoEtapa, ExecutorPipeline
from docforja.nucleo.gpu import SemaforoGPU
from docforja.nucleo.projeto import Projeto


@pytest.fixture
def grafo_teste():
    etapas = {
        "E00": DefinicaoEtapa(id="E00", needs=[]),
        "P1": DefinicaoEtapa(id="P1", needs=["E00"]),
        "P2A": DefinicaoEtapa(id="P2A", needs=["P1"]),
        "P2B": DefinicaoEtapa(id="P2B", needs=["P1"]),
        "GATE": DefinicaoEtapa(id="GATE", needs=["P2A", "P2B"], gate=True),
        "R1": DefinicaoEtapa(id="R1", needs=["GATE"], gpu="imagem"),
        "R2": DefinicaoEtapa(id="R2", needs=["GATE"], gpu="audio"),
        "R3": DefinicaoEtapa(id="R3", needs=["R1", "R2"]),
    }
    return PipelineGrafo(etapas)


@pytest.mark.anyio
async def test_executor_paralelismo_e_dependencias(tmp_path, grafo_teste):
    projeto = Projeto.criar(nome="teste_paralelismo", raiz_projetos=tmp_path)
    executor = ExecutorPipeline(projeto, grafo=grafo_teste)
    concorrentes = set()
    max_concorrencia_atingida = 0

    async def mock_handler(ctx: ContextoEtapa):
        nonlocal max_concorrencia_atingida
        concorrentes.add(ctx.etapa.id)
        max_concorrencia_atingida = max(max_concorrencia_atingida, len(concorrentes))
        await asyncio.sleep(0.04)
        concorrentes.discard(ctx.etapa.id)

    for eid in grafo_teste.etapas:
        executor.registrar_handler(eid, mock_handler)

    # Executa até o GATE
    status = await executor.executar(max_concorrencia=4)
    assert status["E00"] == "concluida"
    assert status["P1"] == "concluida"
    assert status["P2A"] == "concluida"
    assert status["P2B"] == "concluida"
    assert status["GATE"] == "pausada_revisao"
    assert max_concorrencia_atingida >= 2  # P2A e P2B rodaram em paralelo


@pytest.mark.anyio
async def test_executor_exclusividade_gpu(tmp_path, grafo_teste):
    projeto = Projeto.criar(nome="teste_gpu", raiz_projetos=tmp_path)
    semaforo = SemaforoGPU()
    executor = ExecutorPipeline(projeto, grafo=grafo_teste, semaforo=semaforo)
    executor.aprovar_gate("GATE")

    simultaneos_gpu = 0
    max_gpu = 0

    async def mock_gpu_handler(ctx: ContextoEtapa):
        nonlocal simultaneos_gpu, max_gpu
        simultaneos_gpu += 1
        max_gpu = max(max_gpu, simultaneos_gpu)
        await asyncio.sleep(0.03)
        simultaneos_gpu -= 1

    executor.registrar_handler("R1", mock_gpu_handler)
    executor.registrar_handler("R2", mock_gpu_handler)

    await executor.executar(max_concorrencia=4)
    # Mesmo com concorrência geral 4, na GPU só pode 1 por vez
    assert max_gpu == 1


@pytest.mark.anyio
async def test_executor_gate_revisao(tmp_path, grafo_teste):
    projeto = Projeto.criar(nome="teste_gate", raiz_projetos=tmp_path)
    executor = ExecutorPipeline(projeto, grafo=grafo_teste)

    # 1ª rodada: para no GATE
    status1 = await executor.executar()
    assert status1["GATE"] == "pausada_revisao"
    assert "R1" not in status1

    # Libera o gate
    executor.aprovar_gate("GATE")

    # 2ª rodada: conclui tudo
    status2 = await executor.executar()
    assert status2["GATE"] == "concluida"
    assert status2["R1"] == "concluida"
    assert status2["R2"] == "concluida"
    assert status2["R3"] == "concluida"


@pytest.mark.anyio
async def test_executor_retomada_apos_kill(tmp_path, grafo_teste):
    projeto = Projeto.criar(nome="teste_retomada", raiz_projetos=tmp_path)

    # Simula estado em que P1 concluiu e P2A foi interrompido ('executando')
    executor1 = ExecutorPipeline(projeto, grafo=grafo_teste)
    executor1.banco.salvar_etapa("E00", status="concluida", hash_entrada="h0")
    executor1.banco.salvar_etapa("P1", status="concluida", hash_entrada="h1")
    executor1.banco.salvar_etapa("P2A", status="executando")

    # Novo executor simula processo reiniciado
    executor2 = ExecutorPipeline(projeto, grafo=grafo_teste)
    etapa_p2a = executor2.banco.obter_etapa("P2A")
    assert etapa_p2a["status"] == "pendente"  # Resetado para pendente

    executor2.aprovar_gate("GATE")
    status = await executor2.executar()
    assert status["P2A"] == "concluida"
    assert status["R3"] == "concluida"


@pytest.mark.anyio
async def test_executor_invalidacao_seletiva(tmp_path, grafo_teste):
    projeto = Projeto.criar(nome="teste_invalidacao", raiz_projetos=tmp_path)
    executor = ExecutorPipeline(projeto, grafo=grafo_teste)
    executor.aprovar_gate("GATE")

    await executor.executar()
    assert executor.banco.obter_etapa("R3")["status"] == "concluida"

    # Invalida R1: R1 e R3 devem ser invalidadas; R2 (independente) deve ser preservada
    invalidadas = executor.invalidar("R1")
    assert "R1" in invalidadas
    assert "R3" in invalidadas
    assert "R2" not in invalidadas

    assert executor.banco.obter_etapa("R1")["status"] == "pendente"
    assert executor.banco.obter_etapa("R3")["status"] == "pendente"
    assert executor.banco.obter_etapa("R2")["status"] == "concluida"


@pytest.mark.anyio
async def test_concorrencia_estabilidade_20_vezes(tmp_path):
    """Executa o pipeline 20 vezes seguidas para garantir ausência de deadlocks e estabilidade."""
    etapas = {
        "A": DefinicaoEtapa(id="A", needs=[]),
        "B1": DefinicaoEtapa(id="B1", needs=["A"], gpu="mod1"),
        "B2": DefinicaoEtapa(id="B2", needs=["A"], gpu="mod1"),
        "C": DefinicaoEtapa(id="C", needs=["B1", "B2"]),
    }
    grafo = PipelineGrafo(etapas)

    for i in range(20):
        proj = Projeto.criar(nome=f"run_estabilidade_{i}", raiz_projetos=tmp_path)
        ex = ExecutorPipeline(proj, grafo=grafo)
        res = await ex.executar(max_concorrencia=3)
        assert res["A"] == "concluida"
        assert res["B1"] == "concluida"
        assert res["B2"] == "concluida"
        assert res["C"] == "concluida"
