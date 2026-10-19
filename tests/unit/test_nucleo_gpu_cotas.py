import asyncio

import pytest

from docforja.nucleo.cotas import GerenciadorCotas
from docforja.nucleo.gpu import SemaforoGPU


@pytest.mark.anyio
async def test_semaforo_gpu_exclusividade_e_agrupamento():
    semaforo = SemaforoGPU()
    descarregou = []

    def mock_descarregar():
        descarregou.append("flux")

    semaforo.registrar_descarregador("flux", mock_descarregar)

    # 1ª execução com modelo 'flux'
    async with semaforo.adquirir(modelo="flux", tarefa="gerar_1"):
        assert semaforo.modelo_atual == "flux"
        assert semaforo.tarefa_atual == "gerar_1"
        assert semaforo.obter_status()["ocupada"] is True

    # 2ª execução com o MESMO modelo 'flux' (não deve chamar descarregar)
    async with semaforo.adquirir(modelo="flux", tarefa="gerar_2"):
        assert len(descarregou) == 0

    # 3ª execução com NOVO modelo 'whisper' (deve descarregar 'flux' antes)
    async with semaforo.adquirir(modelo="whisper", tarefa="alinhar_1"):
        assert len(descarregou) == 1
        assert semaforo.modelo_atual == "whisper"

    assert semaforo.obter_status()["ocupada"] is False


@pytest.mark.anyio
async def test_semaforo_gpu_concorrencia():
    semaforo = SemaforoGPU()
    ordem = []

    async def worker(num: int, modelo: str):
        async with semaforo.adquirir(modelo=modelo, tarefa=f"task_{num}"):
            ordem.append(f"inicia_{num}")
            await asyncio.sleep(0.05)
            ordem.append(f"fim_{num}")

    await asyncio.gather(worker(1, "modA"), worker(2, "modA"))
    # Garante que uma terminou antes da outra iniciar
    assert (ordem == ["inicia_1", "fim_1", "inicia_2", "fim_2"]) or (
        ordem == ["inicia_2", "fim_2", "inicia_1", "fim_1"]
    )


def test_gerenciador_cotas_e_fallback():
    cotas = GerenciadorCotas()
    cotas.limites_diarios["openai_compat"] = 2

    prov, fallback = cotas.selecionar_ativo("openai_compat")
    assert prov == "openai_compat"
    assert fallback is False

    # Consome limite
    cotas.registrar_sucesso("openai_compat")
    cotas.registrar_sucesso("openai_compat")

    # Atingiu o limite -> fallback para Ollama
    assert cotas.esta_disponivel("openai_compat") is False
    prov_fb, fallback_ativo = cotas.selecionar_ativo("openai_compat")
    assert prov_fb == "ollama"
    assert fallback_ativo is True

    # Esgotamento manual
    cotas.registrar_esgotamento("openrouter", duracao_minutos=10)
    assert cotas.esta_disponivel("openrouter") is False
