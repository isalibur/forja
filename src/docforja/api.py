"""Servidor FastAPI e endpoints SSE da interface web local do DocForja."""

from __future__ import annotations

import asyncio
import contextlib
import json
import mimetypes
import re
from collections.abc import AsyncIterator
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from docforja.audio.trilha import resolver_trilha_provisoria
from docforja.esquemas import Ativo
from docforja.global_assets.promocao import (
    avaliar_ativos_para_promocao,
    promover_itens_para_global,
)
from docforja.midia.licenca import (
    carregar_ficha_licenca,
    classificar_licenca,
    detectar_patrimonio_restrito,
)
from docforja.midia.pasta_manual import EXTENSOES_IMAGEM, identificar_ativo_por_nome
from docforja.midia.selecoes import hash_resolvidos, registrar_selecao, selecoes_atuais
from docforja.nucleo.banco import BancoProjeto
from docforja.nucleo.cotas import gerenciador_cotas
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.nucleo.eventos import barramento_global
from docforja.nucleo.gpu import semaforo_gpu
from docforja.nucleo.handlers import criar_executor_projeto
from docforja.nucleo.projeto import Projeto
from docforja.settings import load_settings

app = FastAPI(title="DocForja API", version="0.1.0")
EXTENSOES_PREVIA = {".jpg", ".jpeg", ".png", ".webp"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173", "http://localhost:5173",
        "http://127.0.0.1:7860", "http://localhost:7860",
    ],
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
    codigo: str | None = None


class PromoverGlobalPayload(BaseModel):
    itens: list[str]


class SelecionarCandidataPayload(BaseModel):
    candidata: str | None
    hash_resolvidos: str


def _projeto_da_interface(slug: str) -> Projeto:
    """Restringe leitura da UI aos projetos cadastrados na pasta configurada."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,99}", slug):
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    raiz = load_settings().paths.projects.resolve()
    caminho = (raiz / slug).resolve()
    if caminho.parent != raiz or not (caminho / "sistema" / "banco.db").is_file():
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return Projeto(caminho, slug)


@lru_cache(maxsize=32)
def _hash_audio_em_cache(caminho: Path, tamanho: int, modificado_ns: int) -> str:
    """Evita reler todo o WAV a cada atualização da tela."""
    return calcular_hash_dados(caminho)


def _manifesto_atual(projeto: Projeto) -> dict[str, Any] | None:
    plano = projeto.pastas.plano
    meta = plano / "previa.json"
    props = projeto.pastas.sistema / "previa" / "props.json"
    entradas = {
        "hash_verificacao": plano / "verificacao.json",
        "hash_resolvidos": plano / "ativos_resolvidos.json",
    }
    idioma = projeto.obter_opcoes().get("idiomas", {}).get("principal", "pt-BR")
    entradas["hash_audio"] = projeto.pastas.audio / idioma / "narracao_completa.wav"
    entradas["hash_segmentos"] = projeto.pastas.audio / idioma / "segmentos.json"
    if not meta.is_file() or not props.is_file() or any(
        not caminho.is_file() for caminho in entradas.values()
    ):
        return None
    dados = json.loads(meta.read_text(encoding="utf-8"))
    hashes_atuais = {
        chave: (
            _hash_audio_em_cache(caminho, caminho.stat().st_size, caminho.stat().st_mtime_ns)
            if chave == "hash_audio" else calcular_hash_dados(caminho)
        )
        for chave, caminho in entradas.items()
    }
    if any(dados.get(chave) != hash_atual for chave, hash_atual in hashes_atuais.items()):
        return None
    return json.loads(props.read_text(encoding="utf-8"))


def _imagens_licenciadas(projeto: Projeto, ativos: dict[str, Ativo]) -> dict[str, Path]:
    """Seleciona somente imagens internas com ficha explicitamente permissiva."""
    raiz = projeto.raiz.resolve()
    mapa_shots = {shot_id: aid for aid, ativo in ativos.items() for shot_id in ativo.usado_em}
    manual = projeto.pastas.midias / "manual"
    manuais: dict[str, Path] = {}
    if manual.is_dir():
        for arquivo in sorted(manual.iterdir()):
            if arquivo.is_file() and arquivo.suffix.lower() in EXTENSOES_IMAGEM:
                aid = identificar_ativo_por_nome(arquivo.name, ativos, mapa_shots)
                if aid:
                    manuais[aid] = arquivo
    aprovadas: dict[str, Path] = {}
    for aid, ativo in ativos.items():
        candidatos = [manuais[aid]] if aid in manuais else []
        if ativo.caminho:
            candidatos.append(ativo.caminho)
        for candidato in candidatos:
            caminho = candidato.resolve()
            if not caminho.is_relative_to(raiz) or not caminho.is_file():
                continue
            if caminho.suffix.lower() not in EXTENSOES_PREVIA:
                continue
            ficha = carregar_ficha_licenca(caminho)
            if not ficha or not ficha.comercial or ficha.patrimonio_restrito:
                continue
            if detectar_patrimonio_restrito(ficha.url_origem, ativo.descricao):
                continue
            if not classificar_licenca(ficha.licenca)[0]:
                continue
            aprovadas[aid] = caminho
            break
    for aid, selecao in selecoes_atuais(projeto).items():
        if aid not in ativos or not selecao.candidata:
            continue
        if any(
            item["nome"] == selecao.candidata
            for item in _candidatas_publicas(projeto, aid, ativos[aid])
        ):
            aprovadas[aid] = projeto.pastas.midias / "pesquisadas" / aid / selecao.candidata
    return aprovadas


def _ficha_publica(projeto: Projeto, ativo: Ativo, caminho: Path) -> dict[str, Any] | None:
    """Dados de crédito de imagem interna cuja licença permite a prévia."""
    arquivo = caminho.resolve()
    if not arquivo.is_relative_to(projeto.raiz.resolve()) or not arquivo.is_file():
        return None
    if arquivo.suffix.lower() not in EXTENSOES_PREVIA:
        return None
    ficha = carregar_ficha_licenca(arquivo)
    if not ficha or not ficha.comercial or ficha.patrimonio_restrito:
        return None
    if not classificar_licenca(ficha.licenca)[0]:
        return None
    if detectar_patrimonio_restrito(ficha.url_origem, ativo.descricao):
        return None
    nota = ficha.detalhes.get("nota_curador")
    nota_publica = (
        float(nota) if isinstance(nota, (int, float)) and not isinstance(nota, bool) else None
    )
    motivo = ficha.detalhes.get("motivo_curador")
    return {
        "autor": ficha.autor,
        "licenca": ficha.licenca,
        "credito": ficha.texto_credito,
        "fonte": ficha.url_origem if ficha.url_origem.startswith(("https://", "http://")) else None,
        "nota": nota_publica,
        "motivo": motivo if isinstance(motivo, str) else None,
    }


def _candidatas_publicas(projeto: Projeto, aid: str, ativo: Ativo) -> list[dict[str, Any]]:
    """Lista apenas candidatas de pesquisa com ficha válida e caminho fixo."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", aid):
        return []
    pasta = projeto.pastas.midias / "pesquisadas" / aid
    if not pasta.is_dir():
        return []
    candidatas = []
    for arquivo in sorted(pasta.glob("cand_*")):
        nome_valido = re.fullmatch(
            r"cand_[A-Za-z0-9_-]+_[1-9][0-9]*\.(jpg|jpeg|png|webp)", arquivo.name
        )
        if not arquivo.is_file() or not nome_valido:
            continue
        ficha = _ficha_publica(projeto, ativo, arquivo)
        if ficha:
            candidatas.append({
                "nome": arquivo.name,
                "imagem_url": (
                    f"/api/projetos/{projeto.slug}/ativos/{aid}"
                    f"/candidatas/{arquivo.name}/imagem"
                ),
                **ficha,
            })
        if len(candidatas) >= 5:
            break
    return candidatas


@app.get("/api/projetos/{slug}/plano")
def obter_plano_ui(slug: str) -> dict[str, Any]:
    projeto = _projeto_da_interface(slug)
    pasta = projeto.pastas.plano
    plano_path = pasta / "plano.json"
    if not plano_path.is_file():
        return {"pronto": False, "slug": slug}
    plano = json.loads(plano_path.read_text(encoding="utf-8"))
    resolvidos_path = pasta / "ativos_resolvidos.json"
    ativos_dados = (
        json.loads(resolvidos_path.read_text(encoding="utf-8")).get("ativos", {})
        if resolvidos_path.is_file() else plano.get("ativos", {})
    )
    ativos = {aid: Ativo.model_validate(item) for aid, item in ativos_dados.items()}
    imagens = _imagens_licenciadas(projeto, ativos)
    selecoes = {
        aid: selecao
        for aid, selecao in selecoes_atuais(projeto).items()
        if aid in ativos and (
            selecao.candidata is None
            or any(
                item["nome"] == selecao.candidata
                for item in _candidatas_publicas(projeto, aid, ativos[aid])
            )
        )
    }
    urls_imagens = {
        aid: (
            f"/api/projetos/{slug}/ativos/{aid}/imagem"
            + (f"?revisao={selecoes[aid].criada_em}" if aid in selecoes else "")
        )
        for aid in imagens
    }
    mapa_shots = {shot_id: aid for aid, ativo in ativos.items() for shot_id in ativo.usado_em}
    recebidos: set[str] = set()
    manual = projeto.pastas.midias / "manual"
    if manual.is_dir():
        for arquivo in manual.iterdir():
            if arquivo.is_file() and arquivo.suffix.lower() in EXTENSOES_IMAGEM:
                aid = identificar_ativo_por_nome(arquivo.name, ativos, mapa_shots)
                if aid:
                    recebidos.add(aid)
    pedidos = [
        {
            "id": aid,
            "descricao": ativo.descricao,
            "motivo": ativo.motivo,
            "busca": ativo.busca or {},
            "nome_arquivo": ativo.nome_arquivo or f"{aid}.jpg",
            "plano_b": ativo.plano_b,
            "usado_em": ativo.usado_em,
            "recebido": aid in recebidos,
            "resolvido": bool(ativo.caminho and ativo.caminho.is_file()),
        }
        for aid, ativo in sorted(ativos.items())
        if str(ativo.origem) == "pedir_ao_usuario"
    ]
    verificacao = pasta / "verificacao.json"
    return {
        "pronto": True,
        "slug": slug,
        "plano": plano,
        "ativos": {
            aid: {
                **ativo.model_dump(mode="json"),
                "imagem_url": urls_imagens.get(aid),
                "licenca_previa": (
                    carregar_ficha_licenca(imagens[aid]).licenca if aid in imagens else None
                ),
                "credito_imagem": (
                    _ficha_publica(projeto, ativo, imagens[aid]) if aid in imagens else None
                ),
                "candidatas": _candidatas_publicas(projeto, aid, ativo),
                "candidata_selecionada": (
                    selecoes[aid].candidata if aid in selecoes else None
                ),
            }
            for aid, ativo in ativos.items()
        },
        "pedidos": pedidos,
        "verificacao": json.loads(verificacao.read_text(encoding="utf-8"))
        if verificacao.is_file() else None,
        "manifesto": _manifesto_atual(projeto),
        "imagens_por_shot": {
            shot_id: urls_imagens[aid]
            for aid, ativo in ativos.items() if aid in imagens for shot_id in ativo.usado_em
        },
        "pasta_manual": str(manual),
        "hash_resolvidos": hash_resolvidos(projeto),
        "previa_mp4_desatualizada": any(
            selecao.candidata for selecao in selecoes.values()
        ),
    }


@app.get("/api/projetos/{slug}/ativos/{aid}/imagem")
def obter_imagem_ativo(slug: str, aid: str) -> FileResponse:
    projeto = _projeto_da_interface(slug)
    resolvidos = projeto.pastas.plano / "ativos_resolvidos.json"
    if not resolvidos.is_file():
        raise HTTPException(status_code=404, detail="Imagem não disponível")
    dados = json.loads(resolvidos.read_text(encoding="utf-8")).get("ativos", {})
    if aid not in dados:
        raise HTTPException(status_code=404, detail="Imagem não disponível")
    caminho = _imagens_licenciadas(projeto, {aid: Ativo.model_validate(dados[aid])}).get(aid)
    if caminho is None:
        raise HTTPException(status_code=404, detail="Imagem sem licença confirmada")
    return FileResponse(
        caminho,
        media_type=mimetypes.guess_type(caminho.name)[0] or "application/octet-stream",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.get("/api/projetos/{slug}/ativos/{aid}/candidatas/{nome}/imagem")
def obter_imagem_candidata(slug: str, aid: str, nome: str) -> FileResponse:
    projeto = _projeto_da_interface(slug)
    resolvidos = projeto.pastas.plano / "ativos_resolvidos.json"
    if not resolvidos.is_file():
        raise HTTPException(status_code=404, detail="Candidata não disponível")
    dados = json.loads(resolvidos.read_text(encoding="utf-8")).get("ativos", {})
    if aid not in dados:
        raise HTTPException(status_code=404, detail="Candidata não disponível")
    ativo = Ativo.model_validate(dados[aid])
    candidata = next(
        (item for item in _candidatas_publicas(projeto, aid, ativo) if item["nome"] == nome),
        None,
    )
    if candidata is None:
        raise HTTPException(status_code=404, detail="Candidata sem licença confirmada")
    caminho = projeto.pastas.midias / "pesquisadas" / aid / nome
    return FileResponse(
        caminho,
        media_type=mimetypes.guess_type(nome)[0] or "application/octet-stream",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.post("/api/projetos/{slug}/ativos/{aid}/selecionar")
def selecionar_candidata(
    slug: str, aid: str, payload: SelecionarCandidataPayload
) -> dict[str, Any]:
    projeto = _projeto_da_interface(slug)
    resolvidos = projeto.pastas.plano / "ativos_resolvidos.json"
    if not resolvidos.is_file():
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    dados = json.loads(resolvidos.read_text(encoding="utf-8")).get("ativos", {})
    if aid not in dados:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    if payload.hash_resolvidos != hash_resolvidos(projeto):
        raise HTTPException(status_code=409, detail="O plano mudou; recarregue a página")
    ativo = Ativo.model_validate(dados[aid])
    if payload.candidata is not None and not any(
        item["nome"] == payload.candidata
        for item in _candidatas_publicas(projeto, aid, ativo)
    ):
        raise HTTPException(status_code=400, detail="Candidata sem licença confirmada")
    try:
        selecao = registrar_selecao(
            projeto, aid, payload.candidata, payload.hash_resolvidos
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return selecao.model_dump(mode="json")


@app.get("/api/projetos/{slug}/narracao.wav")
def obter_audio_previa(slug: str) -> FileResponse:
    projeto = _projeto_da_interface(slug)
    if _manifesto_atual(projeto) is None:
        raise HTTPException(status_code=404, detail="Prévia ainda não disponível")
    idioma = projeto.obter_opcoes().get("idiomas", {}).get("principal", "pt-BR")
    audio = projeto.pastas.audio / idioma / "narracao_completa.wav"
    if not audio.is_file():
        raise HTTPException(status_code=404, detail="Narração não encontrada")
    return FileResponse(audio, media_type="audio/wav", filename="narracao.wav")


@app.get("/api/projetos/{slug}/trilha_provisoria.wav")
def obter_trilha_provisoria(slug: str) -> FileResponse:
    projeto = _projeto_da_interface(slug)
    trilha = resolver_trilha_provisoria(projeto)
    if trilha is None or not trilha.is_file():
        raise HTTPException(status_code=404, detail="Trilha provisória não encontrada")
    return FileResponse(trilha, media_type="audio/wav", filename="trilha_provisoria.wav")


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

    if (
        payload.gate == "REVISAO"
        and payload.codigo is not None
        and payload.codigo.strip().upper() != "PRODUZIR"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Código de confirmação incorreto. "
                "Digite PRODUZIR para confirmar a produção."
            ),
        )

    executor = criar_executor_projeto(projeto)
    executor.aprovar_gate(payload.gate)

    async def _rodar():
        await executor.executar()

    background_tasks.add_task(asyncio.run, _rodar())
    return {"status": "aprovado", "gate": payload.gate}


@app.get("/api/projetos/{slug}/producao")
def obter_status_producao(slug: str) -> dict[str, Any]:
    projeto = _projeto_da_interface(slug)
    banco = BancoProjeto(projeto.banco_file)
    etapas = banco.listar_etapas()
    status_map = {e["id"]: e["status"] for e in etapas}

    etapas_producao = [
        "R1_imagens", "R2_tratamento", "R3_mapas", "R4_trilha_sfx",
        "R5_montagem", "R6_mix", "R7_render", "R8_qa", "R9_pacote", "R10_biblioteca",
    ]
    concluidas_prod = sum(1 for e in etapas_producao if status_map.get(e) == "concluida")
    em_execucao = [e for e in etapas if e["status"] == "executando"]

    plano_path = projeto.pastas.plano / "plano.json"
    estimativa_min = 30
    if plano_path.is_file():
        with contextlib.suppress(Exception):
            plano_dados = json.loads(plano_path.read_text(encoding="utf-8"))
            estimativa_min = plano_dados.get("estimativa_producao_min", 30)

    progresso = round((concluidas_prod / len(etapas_producao)) * 100)
    fracao_restante = max(0.0, 1.0 - (concluidas_prod / len(etapas_producao)))
    tempo_restante_min = round(estimativa_min * fracao_restante, 1)

    return {
        "slug": slug,
        "em_producao": bool(em_execucao),
        "concluida": concluidas_prod == len(etapas_producao),
        "progresso_percent": progresso,
        "etapa_ativa": em_execucao[0]["id"] if em_execucao else None,
        "tempo_restante_min": tempo_restante_min,
        "etapas": etapas,
        "gpu_status": semaforo_gpu.obter_status(),
    }


@app.get("/api/projetos/{slug}/saida")
def obter_saida_projeto(slug: str) -> dict[str, Any]:
    projeto = _projeto_da_interface(slug)
    idioma = projeto.obter_opcoes().get("idiomas", {}).get("principal", "pt-BR")
    pasta_saida = projeto.pastas.saida
    pasta_meta = pasta_saida / idioma / "metadados"

    meta_json_path = pasta_meta / "metadados.json"
    pronto = meta_json_path.is_file()

    metadados = {}
    if pronto:
        with contextlib.suppress(Exception):
            metadados = json.loads(meta_json_path.read_text(encoding="utf-8"))

    relatorio_txt = ""
    relatorio_path = pasta_saida / "relatorio.md"
    if relatorio_path.is_file():
        relatorio_txt = relatorio_path.read_text(encoding="utf-8")

    creditos_txt = ""
    creditos_path = pasta_saida / "creditos.txt"
    if creditos_path.is_file():
        creditos_txt = creditos_path.read_text(encoding="utf-8")

    promover_itens = []
    resolvidos_path = projeto.pastas.plano / "ativos_resolvidos.json"
    if resolvidos_path.is_file():
        with contextlib.suppress(Exception):
            dados_res = json.loads(resolvidos_path.read_text(encoding="utf-8"))
            ativos = {k: Ativo.model_validate(v) for k, v in dados_res.get("ativos", {}).items()}
            itens_promo = avaliar_ativos_para_promocao(slug, ativos)
            promover_itens = [item.model_dump(mode="json") for item in itens_promo]
            pass

    video_final = pasta_saida / idioma / "video.mp4"
    previa = projeto.pastas.plano / "previa.mp4"
    tem_video = video_final.is_file() or previa.is_file()
    video_url = f"/api/projetos/{slug}/video_final.mp4" if tem_video else None

    return {
        "slug": slug,
        "pronto": pronto,
        "idioma": idioma,
        "video_url": video_url,
        "metadados": metadados,
        "relatorio": relatorio_txt,
        "creditos": creditos_txt,
        "promover_itens": promover_itens,
    }


@app.post("/api/projetos/{slug}/promover_global")
def promover_ativos_global(slug: str, payload: PromoverGlobalPayload) -> dict[str, Any]:
    projeto = _projeto_da_interface(slug)
    resolvidos_path = projeto.pastas.plano / "ativos_resolvidos.json"
    if not resolvidos_path.is_file():
        raise HTTPException(status_code=404, detail="Ativos não encontrados")

    dados_res = json.loads(resolvidos_path.read_text(encoding="utf-8"))
    ativos = {k: Ativo.model_validate(v) for k, v in dados_res.get("ativos", {}).items()}
    itens_promo = avaliar_ativos_para_promocao(slug, ativos)
    itens_filtrados = [item for item in itens_promo if item.id in payload.itens]

    pasta_global = load_settings().paths.projects.parent / "global_assets"
    promovidos = promover_itens_para_global(itens_filtrados, pasta_global)
    return {"sucesso": True, "promovidos": promovidos}


@app.get("/api/projetos/{slug}/video_final.mp4")
def obter_video_final(slug: str) -> FileResponse:
    projeto = _projeto_da_interface(slug)
    idioma = projeto.obter_opcoes().get("idiomas", {}).get("principal", "pt-BR")
    video = projeto.pastas.saida / idioma / "video.mp4"
    if not video.is_file():
        video = projeto.pastas.plano / "previa.mp4"
    if not video.is_file():
        raise HTTPException(status_code=404, detail="Vídeo final não encontrado")
    return FileResponse(video, media_type="video/mp4", filename=f"{slug}.mp4")


@app.get("/api/global/itens")
def listar_itens_globais() -> dict[str, Any]:
    pasta_global = load_settings().paths.projects.parent / "global_assets"
    categorias: dict[str, list[dict[str, Any]]] = {
        "imagens": [], "personagens": [], "mapas": [], "loops": [], "trilhas": [], "sfx": [],
    }
    if pasta_global.is_dir():
        for cat in categorias:
            sub = pasta_global / cat
            if sub.is_dir():
                for f in sorted(sub.glob("*.json")):
                    try:
                        dados = json.loads(f.read_text(encoding="utf-8"))
                        categorias[cat].append(dados)
                    except Exception:
                        continue
    return {"categorias": categorias, "total": sum(len(v) for v in categorias.values())}


@app.get("/api/sistema/detalhes")
def obter_detalhes_sistema() -> dict[str, Any]:
    settings = load_settings()
    return {
        "gpu": semaforo_gpu.obter_status(),
        "cotas": gerenciador_cotas.obter_resumo(),
        "pastas": {
            "projetos": str(settings.paths.projects),
            "modelos": str(settings.paths.models),
            "temp": str(settings.paths.temp),
        },
        "ambientes_python": settings.python_environments,
        "adaptadores": {
            "whisper": settings.alinhamento.modelo_asr,
            "alinhador": settings.alinhamento.modelo_alinhador,
        },
    }


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
