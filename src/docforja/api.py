"""Servidor FastAPI e endpoints SSE da interface web local do DocForja."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from docforja.nucleo.banco import BancoProjeto
from docforja.nucleo.cotas import gerenciador_cotas
from docforja.nucleo.eventos import barramento_global
from docforja.nucleo.gpu import semaforo_gpu
from docforja.nucleo.handlers import criar_executor_projeto
from docforja.nucleo.projeto import Projeto
from docforja.settings import load_settings

app = FastAPI(title="DocForja API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CriarProjetoPayload(BaseModel):
    nome: str
    tipo: str = "longo"
    roteiro: str = ""
    idioma_principal: str = "pt-BR"
    idiomas_extras: list[str] = Field(default_factory=list)
    preset: str = "padrao"
    kit: str = "cinza-e-brasa@1.0"
    opcoes_adicionais: dict[str, Any] = Field(default_factory=dict)


class AprovarGatePayload(BaseModel):
    gate: str = "REVISAO"


@app.get("/api/saude")
def obter_saude() -> dict[str, Any]:
    gpu_info = semaforo_gpu.obter_status()
    cotas_info = gerenciador_cotas.obter_resumo()
    return {
        "status": "online",
        "gpu": gpu_info,
        "cotas": cotas_info,
    }


@app.get("/api/projetos")
def listar_projetos() -> list[dict[str, Any]]:
    settings = load_settings()
    raiz = settings.paths.projects
    if not raiz.is_dir():
        return []
    projetos = []
    for item in sorted(raiz.iterdir()):
        if item.is_dir() and (item / "sistema" / "banco.db").is_file():
            try:
                proj = Projeto.carregar(item)
                opcoes = proj.obter_opcoes()
                banco = BancoProjeto(proj.banco_file)
                etapas = banco.listar_etapas()
                etapa_atual = "Aguardando início"
                for e in etapas:
                    if e["status"] == "falhou":
                        etapa_atual = f"Falha: {e['id']}"
                        break
                    if e["status"] in ("executando", "pausada_revisao"):
                        etapa_atual = f"{e['id']} ({e['status']})"
                        break
                    if e["status"] == "pendente":
                        etapa_atual = f"{e['id']} (aguardando)"
                        break
                else:
                    status_por_id = {e["id"]: e["status"] for e in etapas}
                    gate_m3_m4 = {
                        "P2_narracao",
                        "P4_shots",
                        "P6_verificador",
                        "P8_estimativa_previa",
                        "REVISAO",
                    }
                    if gate_m3_m4.issubset(status_por_id) and all(
                        status_por_id[etapa] == "concluida" for etapa in gate_m3_m4
                    ):
                        ausentes = proj.artefatos_m3_m4_ausentes()
                        etapa_atual = (
                            "Saídas pendentes de M3/M4"
                            if ausentes
                            else "Concluído"
                        )
                    elif etapas and all(e["status"] == "concluida" for e in etapas):
                        etapa_atual = "Concluído"

                projetos.append(
                    {
                        "slug": proj.slug,
                        "nome": opcoes.get("nome", proj.slug),
                        "tipo": opcoes.get("tipo", "longo"),
                        "preset": opcoes.get("preset", "padrao"),
                        "etapa_atual": etapa_atual,
                        "caminho": str(proj.raiz),
                    }
                )
            except Exception:
                continue
    return projetos


@app.post("/api/projetos")
def criar_projeto(payload: CriarProjetoPayload) -> dict[str, Any]:
    projeto = Projeto.criar(
        nome=payload.nome,
        tipo=payload.tipo,
        roteiro=payload.roteiro,
        idioma_principal=payload.idioma_principal,
        idiomas_extras=payload.idiomas_extras,
        preset=payload.preset,
        kit=payload.kit,
        opcoes_adicionais=payload.opcoes_adicionais,
    )
    return {
        "sucesso": True,
        "slug": projeto.slug,
        "caminho": str(projeto.raiz),
    }


@app.get("/api/projetos/{slug}")
def obter_projeto(slug: str) -> dict[str, Any]:
    try:
        projeto = Projeto.carregar(slug)
    except FileNotFoundError as err:
        raise HTTPException(status_code=404, detail="Projeto não encontrado") from err

    opcoes = projeto.obter_opcoes()
    banco = BancoProjeto(projeto.banco_file)
    etapas = banco.listar_etapas()
    return {
        "slug": projeto.slug,
        "opcoes": opcoes,
        "etapas": etapas,
        "roteiro": projeto.obter_roteiro(),
    }


@app.post("/api/projetos/{slug}/executar")
def acionar_execucao(
    slug: str, background_tasks: BackgroundTasks, ate: str | None = None
) -> dict[str, Any]:
    try:
        projeto = Projeto.carregar(slug)
    except FileNotFoundError as err:
        raise HTTPException(status_code=404, detail="Projeto não encontrado") from err

    executor = criar_executor_projeto(projeto)
    if ate is not None and ate not in executor.grafo.etapas:
        raise HTTPException(status_code=400, detail=f"Etapa desconhecida: {ate}")

    async def _rodar():
        await executor.executar(ate_etapa=ate)

    background_tasks.add_task(asyncio.run, _rodar())
    return {"status": "iniciado", "slug": slug}


@app.post("/api/projetos/{slug}/aprovar_gate")
def aprovar_gate(
    slug: str, payload: AprovarGatePayload, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    try:
        projeto = Projeto.carregar(slug)
    except FileNotFoundError as err:
        raise HTTPException(status_code=404, detail="Projeto não encontrado") from err

    executor = criar_executor_projeto(projeto)
    executor.aprovar_gate(payload.gate)

    async def _rodar():
        await executor.executar()

    background_tasks.add_task(asyncio.run, _rodar())
    return {"status": "aprovado", "gate": payload.gate}


@app.get("/api/eventos")
async def fluxo_eventos() -> StreamingResponse:
    """Stream de eventos em tempo real via Server-Sent Events (SSE)."""
    fila = barramento_global.registrar_ouvinte()

    async def gerador() -> AsyncIterator[str]:
        try:
            while True:
                try:
                    evento = await asyncio.wait_for(fila.get(), timeout=20.0)
                    yield f"data: {evento.model_dump_json()}\n\n"
                except TimeoutError:
                    # Heartbeat para manter a conexão ativa
                    yield ": ping\n\n"
        finally:
            barramento_global.remover_ouvinte(fila)

    return StreamingResponse(
        gerador(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Servir frontend estático de src/docforja/web_dist/ se existir
web_dist = Path(__file__).parent / "web_dist"
if web_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=str(web_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def catch_all(full_path: str):
        arquivo = web_dist / full_path
        if arquivo.is_file():
            return FileResponse(str(arquivo))
        return FileResponse(str(web_dist / "index.html"))
