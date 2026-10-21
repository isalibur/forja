"""Servidor FastAPI e endpoints SSE da interface web local do DocForja."""

from __future__ import annotations

import asyncio
import contextlib
import json
import mimetypes
import re
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from docforja.audio.trilha import resolver_trilha_provisoria
from docforja.esquemas import Ativo, Plano
from docforja.global_assets import (
    avaliar_ativos_para_promocao,
    obter_pasta_global,
    promover_itens_para_global,
)
from docforja.io import atomic_write_json
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
from docforja.shorts.alegacoes_avulsas import (
    DadosAlegacoes,
    documentacao_vigente,
    obter_documentacao,
    registrar_documentacao,
)
from docforja.shorts.avulsos import PASTA_FORMULAS_PADRAO, ler_lote_avulsos_texto
from docforja.shorts.campanhas import (
    CampanhaAvulsa,
    aprovacoes_da_campanha,
    aprovar_roteiro,
    listar_campanhas,
    obter_campanha,
    salvar_campanha,
)
from docforja.shorts.candidatos import (
    aprovar_frase_ponte,
    gerar_frases_ponte,
    pontuar_candidatos_do_plano,
)
from docforja.shorts.formulas import carregar_formulas
from docforja.shorts.midias_avulsas import (
    listar_imagens_globais,
    obter_selecao_midias,
    resolver_imagem_global,
    selecao_vigente,
    selecionar_midias,
)
from docforja.shorts.modelos import CandidatoShort, FrasePonte
from docforja.shorts.producao import (
    aprovar_ponte_short_idioma,
    executar_producao_background,
    obter_ponte_idioma_aprovada,
)
from docforja.shorts.verticalizar import verticalizar_plano

app = FastAPI(title="DocForja API", version="0.1.0")
EXTENSOES_PREVIA = {".jpg", ".jpeg", ".png", ".webp"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:7860",
        "http://localhost:7860",
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


class AprovarShortPayload(BaseModel):
    indice_frase: int | None = Field(default=None, ge=0, le=2)
    frase_personalizada: str | None = Field(default=None, min_length=1, max_length=240)


class AprovarPonteIdiomaPayload(BaseModel):
    texto: str = Field(min_length=1, max_length=240)


class ManifestoShortPayload(BaseModel):
    dimensoes: dict[str, tuple[int, int]]
    focos: dict[str, tuple[float, float]] = Field(default_factory=dict)
    estrategia: Literal["recorte", "fundo_desfocado"] = "recorte"


class PlanejarLoteAvulsosPayload(BaseModel):
    csv_texto: str = Field(min_length=1, max_length=262144)


class SalvarLoteAvulsosPayload(PlanejarLoteAvulsosPayload):
    nome: str = Field(min_length=1, max_length=120)


class AprovarRoteiroAvulsoPayload(BaseModel):
    texto: str = Field(min_length=1, max_length=20000)
    hash_campanha: str = Field(pattern=r"^[a-f0-9]{64}$")


class SelecionarMidiasAvulsoPayload(BaseModel):
    ids_globais: list[str] = Field(min_length=1, max_length=20)
    hash_campanha: str = Field(pattern=r"^[a-f0-9]{64}$")
    revisao_roteiro: str = Field(pattern=r"^[a-f0-9]{64}$")


class RegistrarAlegacoesAvulsoPayload(BaseModel):
    hash_campanha: str = Field(pattern=r"^[a-f0-9]{64}$")
    revisao_roteiro: str = Field(pattern=r"^[a-f0-9]{64}$")
    revisao_midias: str = Field(pattern=r"^[a-f0-9]{64}$")
    dados: DadosAlegacoes


def _projeto_da_interface(slug: str) -> Projeto:
    """Restringe leitura da UI aos projetos cadastrados na pasta configurada."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,99}", slug):
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    raiz = load_settings().paths.projects.resolve()
    caminho = (raiz / slug).resolve()
    if caminho.parent != raiz or not (caminho / "sistema" / "banco.db").is_file():
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return Projeto(caminho, slug)


def _dados_shorts(projeto: Projeto) -> tuple[Plano, list[dict[str, Any]], str]:
    plano_path = projeto.pastas.plano / "plano.json"
    idioma = projeto.obter_opcoes().get("idiomas", {}).get("principal", "pt-BR")
    if not isinstance(idioma, str) or not re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", idioma):
        raise HTTPException(status_code=422, detail="Idioma principal inválido")
    segmentos_path = projeto.pastas.audio / idioma / "segmentos.json"
    if not plano_path.is_file() or not segmentos_path.is_file():
        raise HTTPException(status_code=409, detail="Plano e narração segmentada são necessários")
    try:
        plano = Plano.model_validate_json(plano_path.read_text(encoding="utf-8"))
        segmentos = json.loads(segmentos_path.read_text(encoding="utf-8"))
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=422, detail="Artefatos do plano/narração inválidos"
        ) from exc
    if not isinstance(segmentos, list):
        raise HTTPException(status_code=422, detail="Lista de segmentos da narração inválida")
    if plano.tipo != "longo":
        raise HTTPException(status_code=400, detail="Shorts derivados exigem projeto longo")
    fonte_hash = calcular_hash_dados(
        {
            "plano": calcular_hash_dados(plano_path),
            "segmentos": calcular_hash_dados(segmentos_path),
        }
    )
    return plano, segmentos, fonte_hash


def _candidatos_shorts(projeto: Projeto) -> tuple[Plano, str, list[tuple[str, CandidatoShort]]]:
    plano, segmentos, fonte_hash = _dados_shorts(projeto)
    candidatos = pontuar_candidatos_do_plano(plano, segmentos, limite=5)
    saida = []
    for candidato in candidatos:
        titulo = str(projeto.obter_opcoes().get("nome", plano.projeto))
        candidato = candidato.model_copy(update={"frases_ponte": gerar_frases_ponte(titulo)})
        referencia = calcular_hash_dados(
            {
                "fonte": fonte_hash,
                "candidato": candidato.model_dump(mode="json"),
            }
        )[:24]
        saida.append((referencia, candidato))
    return plano, fonte_hash, saida


def _pasta_short_derivado(projeto: Projeto, referencia: str) -> Path:
    return projeto.pastas.montagem / "shorts" / "derivados" / referencia


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
    if (
        not meta.is_file()
        or not props.is_file()
        or any(not caminho.is_file() for caminho in entradas.values())
    ):
        return None
    dados = json.loads(meta.read_text(encoding="utf-8"))
    hashes_atuais = {
        chave: (
            _hash_audio_em_cache(caminho, caminho.stat().st_size, caminho.stat().st_mtime_ns)
            if chave == "hash_audio"
            else calcular_hash_dados(caminho)
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
            candidatas.append(
                {
                    "nome": arquivo.name,
                    "imagem_url": (
                        f"/api/projetos/{projeto.slug}/ativos/{aid}"
                        f"/candidatas/{arquivo.name}/imagem"
                    ),
                    **ficha,
                }
            )
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
        if resolvidos_path.is_file()
        else plano.get("ativos", {})
    )
    ativos = {aid: Ativo.model_validate(item) for aid, item in ativos_dados.items()}
    imagens = _imagens_licenciadas(projeto, ativos)
    selecoes = {
        aid: selecao
        for aid, selecao in selecoes_atuais(projeto).items()
        if aid in ativos
        and (
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
                "candidata_selecionada": (selecoes[aid].candidata if aid in selecoes else None),
            }
            for aid, ativo in ativos.items()
        },
        "pedidos": pedidos,
        "verificacao": json.loads(verificacao.read_text(encoding="utf-8"))
        if verificacao.is_file()
        else None,
        "manifesto": _manifesto_atual(projeto),
        "imagens_por_shot": {
            shot_id: urls_imagens[aid]
            for aid, ativo in ativos.items()
            if aid in imagens
            for shot_id in ativo.usado_em
        },
        "pasta_manual": str(manual),
        "hash_resolvidos": hash_resolvidos(projeto),
        "previa_mp4_desatualizada": any(selecao.candidata for selecao in selecoes.values()),
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
        item["nome"] == payload.candidata for item in _candidatas_publicas(projeto, aid, ativo)
    ):
        raise HTTPException(status_code=400, detail="Candidata sem licença confirmada")
    try:
        selecao = registrar_selecao(projeto, aid, payload.candidata, payload.hash_resolvidos)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return selecao.model_dump(mode="json")


@app.post("/api/shorts/avulsos/planejar")
def planejar_lote_shorts_avulsos(payload: PlanejarLoteAvulsosPayload) -> dict[str, Any]:
    """Exibe um plano revisável; não cria projeto nem inicia produção."""
    try:
        pedidos = ler_lote_avulsos_texto(payload.csv_texto)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    formulas = carregar_formulas(PASTA_FORMULAS_PADRAO)
    return {
        "quantidade": len(pedidos),
        "pedidos": [pedido.model_dump(mode="json") for pedido in pedidos],
        "formulas": {
            id_: formulas[id_].model_dump(mode="json")
            for id_ in sorted({pedido.formula_id for pedido in pedidos})
        },
        "status": "aguardando_revisao",
    }


@app.post("/api/shorts/avulsos/campanhas", status_code=201)
def criar_campanha_avulsa(payload: SalvarLoteAvulsosPayload) -> dict[str, Any]:
    """Persiste somente o plano editorial; não aprova roteiro, mídia ou publicação."""
    try:
        pedidos = ler_lote_avulsos_texto(payload.csv_texto)
        campanha = salvar_campanha(
            load_settings().paths.projects,
            payload.nome,
            pedidos,
            carregar_formulas(PASTA_FORMULAS_PADRAO),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _resposta_campanha(campanha)


def _resposta_campanha(campanha: CampanhaAvulsa) -> dict[str, Any]:
    raiz = load_settings().paths.projects
    aprovacoes = aprovacoes_da_campanha(raiz, campanha)
    raiz_global = obter_pasta_global()
    selecoes: dict[str, Any] = {}
    midias_desatualizadas: list[str] = []
    documentacoes: dict[str, Any] = {}
    alegacoes_desatualizadas: list[str] = []
    for pedido in campanha.pedidos:
        selecao = obter_selecao_midias(raiz, campanha.id, pedido.id)
        documentacao = obter_documentacao(raiz, campanha.id, pedido.id)
        aprovacao = aprovacoes.get(pedido.id)
        if selecao is None:
            if documentacao is not None:
                alegacoes_desatualizadas.append(pedido.id)
            continue
        if aprovacao and selecao_vigente(raiz_global, selecao, aprovacao.revisao):
            selecoes[pedido.id] = selecao.model_dump(mode="json")
            if documentacao is not None:
                if documentacao_vigente(documentacao, aprovacao.revisao, selecao.revisao):
                    documentacoes[pedido.id] = documentacao.model_dump(mode="json")
                else:
                    alegacoes_desatualizadas.append(pedido.id)
        else:
            midias_desatualizadas.append(pedido.id)
            if documentacao is not None:
                alegacoes_desatualizadas.append(pedido.id)
    return {
        **campanha.model_dump(mode="json"),
        "quantidade": len(campanha.pedidos),
        "aprovacoes_roteiro": {
            pedido_id: aprovacao.model_dump(mode="json")
            for pedido_id, aprovacao in aprovacoes.items()
        },
        "selecoes_midias": selecoes,
        "midias_desatualizadas": midias_desatualizadas,
        "documentacoes_alegacoes": documentacoes,
        "alegacoes_desatualizadas": alegacoes_desatualizadas,
    }


@app.get("/api/shorts/avulsos/campanhas")
def consultar_campanhas_avulsas() -> list[dict[str, Any]]:
    campanhas = listar_campanhas(load_settings().paths.projects)
    return [_resposta_campanha(campanha) for campanha in campanhas]


@app.get("/api/shorts/avulsos/campanhas/{campanha_id}")
def consultar_campanha_avulsa(campanha_id: str) -> dict[str, Any]:
    try:
        campanha = obter_campanha(load_settings().paths.projects, campanha_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _resposta_campanha(campanha)


@app.post("/api/shorts/avulsos/campanhas/{campanha_id}/pedidos/{pedido_id}/roteiro/aprovar")
def aprovar_roteiro_short_avulso(
    campanha_id: str, pedido_id: str, payload: AprovarRoteiroAvulsoPayload
) -> dict[str, Any]:
    try:
        aprovacao = aprovar_roteiro(
            load_settings().paths.projects,
            campanha_id,
            pedido_id,
            payload.texto,
            payload.hash_campanha,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return aprovacao.model_dump(mode="json")


@app.get("/api/shorts/avulsos/midias-disponiveis")
def consultar_midias_avulsas_disponiveis() -> dict[str, Any]:
    return {
        "midias": [
            midia.model_dump(mode="json")
            for midia in listar_imagens_globais(obter_pasta_global())
        ]
    }


@app.get("/api/shorts/avulsos/midias/{categoria}/{item_id}/imagem")
def visualizar_midia_avulsa(categoria: str, item_id: str) -> FileResponse:
    try:
        arquivo, _ = resolver_imagem_global(
            obter_pasta_global(), f"global:{categoria}:{item_id}"
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(arquivo)


@app.post("/api/shorts/avulsos/campanhas/{campanha_id}/pedidos/{pedido_id}/midias/selecionar")
def selecionar_midias_short_avulso(
    campanha_id: str, pedido_id: str, payload: SelecionarMidiasAvulsoPayload
) -> dict[str, Any]:
    try:
        selecao = selecionar_midias(
            load_settings().paths.projects,
            obter_pasta_global(),
            campanha_id,
            pedido_id,
            payload.ids_globais,
            payload.hash_campanha,
            payload.revisao_roteiro,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return selecao.model_dump(mode="json")


@app.post(
    "/api/shorts/avulsos/campanhas/{campanha_id}/pedidos/{pedido_id}/alegacoes/registrar"
)
def registrar_alegacoes_short_avulso(
    campanha_id: str, pedido_id: str, payload: RegistrarAlegacoesAvulsoPayload
) -> dict[str, Any]:
    try:
        documentacao = registrar_documentacao(
            load_settings().paths.projects,
            obter_pasta_global(),
            campanha_id,
            pedido_id,
            payload.hash_campanha,
            payload.revisao_roteiro,
            payload.revisao_midias,
            payload.dados,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return documentacao.model_dump(mode="json")


@app.get("/api/projetos/{slug}/shorts/derivados")
def listar_shorts_derivados(slug: str) -> dict[str, Any]:
    projeto = _projeto_da_interface(slug)
    _, fonte_hash, candidatos = _candidatos_shorts(projeto)
    idiomas_cfg = projeto.obter_opcoes().get("idiomas", {})
    idioma_principal = str(idiomas_cfg.get("principal", "pt-BR"))
    idiomas_extras = idiomas_cfg.get("extras", []) if isinstance(idiomas_cfg, dict) else []
    idiomas_extras = [
        idioma
        for idioma in idiomas_extras
        if isinstance(idioma, str) and re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", idioma)
    ]
    idiomas_short_indisponiveis = [
        idioma
        for idioma in idiomas_extras
        if idioma.split("-", maxsplit=1)[0].lower() not in {"pt", "en", "es"}
    ]
    saida = []
    for referencia, candidato in candidatos:
        pasta = _pasta_short_derivado(projeto, referencia)
        atual_path = pasta / "aprovacao_atual.json"
        aprovacao = None
        if atual_path.is_file():
            with contextlib.suppress(ValueError, OSError, KeyError, TypeError):
                dados = json.loads(atual_path.read_text(encoding="utf-8"))
                if not re.fullmatch(r"[a-f0-9]{64}", str(dados.get("versao", ""))):
                    raise ValueError("Versão inválida")
                versao = pasta / f"aprovacao-{dados['versao']}.json"
                if dados.get("fonte_hash") == fonte_hash and versao.is_file():
                    aprovacao = json.loads(versao.read_text(encoding="utf-8"))
                    aprovacao["versao"] = dados["versao"]
        manifesto_atual = None
        manifesto_pointer_path = pasta / "manifesto_atual.json"
        if manifesto_pointer_path.is_file():
            with contextlib.suppress(ValueError, OSError, KeyError, TypeError):
                pointer = json.loads(manifesto_pointer_path.read_text(encoding="utf-8"))
                if (
                    pointer.get("fonte_hash") == fonte_hash
                    and aprovacao
                    and pointer.get("aprovacao_versao") == aprovacao.get("versao")
                ):
                    manifesto_path = pasta / f"manifesto-vertical-{pointer['versao']}.json"
                    if manifesto_path.is_file():
                        manifesto_atual = {
                            "versao": pointer["versao"],
                            "shots": len(
                                json.loads(manifesto_path.read_text(encoding="utf-8")).get(
                                    "shots", []
                                )
                            ),
                        }
        estado_producao = None
        estado_path = pasta / "producao_atual.json"
        if estado_path.is_file():
            with contextlib.suppress(ValueError, OSError, TypeError):
                estado = json.loads(estado_path.read_text(encoding="utf-8"))
                ponte_atual = (
                    json.loads((pasta / "aprovacao_atual.json").read_text(encoding="utf-8"))
                    if (pasta / "aprovacao_atual.json").is_file()
                    else {}
                )
                manifesto_pointer = (
                    json.loads((pasta / "manifesto_atual.json").read_text(encoding="utf-8"))
                    if (pasta / "manifesto_atual.json").is_file()
                    else {}
                )
                if (
                    aprovacao
                    and aprovacao.get("fonte_hash") == fonte_hash
                    and manifesto_pointer.get("fonte_hash") == fonte_hash
                    and estado.get("fonte_hash") == fonte_hash
                    and estado.get("aprovacao_versao") == ponte_atual.get("versao")
                    and estado.get("manifesto_versao") == manifesto_pointer.get("versao")
                ):
                    estado_producao = estado
        pontes_idiomas: dict[str, dict[str, str] | None] = {}
        producoes_idiomas: dict[str, dict[str, Any] | None] = {}
        for idioma in idiomas_extras:
            ponte_localizada = None
            try:
                texto, versao_ponte = obter_ponte_idioma_aprovada(
                    projeto, referencia, idioma, candidato
                )
                ponte_localizada = {"versao": versao_ponte, "texto": texto}
            except (OSError, ValueError, KeyError, TypeError):
                pass
            pontes_idiomas[idioma] = ponte_localizada
            estado_local_path = pasta / f"producao-{idioma}.json"
            producao_localizada = None
            if estado_local_path.is_file() and ponte_localizada:
                with contextlib.suppress(ValueError, OSError, TypeError):
                    estado_local = json.loads(estado_local_path.read_text(encoding="utf-8"))
                    if (
                        estado_local.get("idioma") == idioma
                        and estado_local.get("fonte_hash") == fonte_hash
                        and estado_local.get("aprovacao_versao") == (aprovacao or {}).get("versao")
                        and estado_local.get("manifesto_versao")
                        == (manifesto_atual or {}).get("versao")
                        and estado_local.get("aprovacao_ponte_idioma") == ponte_localizada["versao"]
                    ):
                        producao_localizada = estado_local
            producoes_idiomas[idioma] = producao_localizada
        saida.append(
            {
                "referencia": referencia,
                "candidato": candidato.model_dump(mode="json"),
                "aprovacao": aprovacao,
                "manifesto_atual": manifesto_atual,
                "producao": estado_producao,
                "pontes_idiomas": pontes_idiomas,
                "producoes_idiomas": producoes_idiomas,
            }
        )
    return {
        "slug": slug,
        "fonte_hash": fonte_hash,
        "idioma_principal": idioma_principal,
        "idiomas_extras": idiomas_extras,
        "idiomas_short_indisponiveis": idiomas_short_indisponiveis,
        "candidatos": saida,
    }


@app.post("/api/projetos/{slug}/shorts/derivados/{referencia}/aprovar")
def aprovar_short_derivado(
    slug: str, referencia: str, payload: AprovarShortPayload
) -> dict[str, Any]:
    projeto = _projeto_da_interface(slug)
    _, fonte_hash, candidatos = _candidatos_shorts(projeto)
    if not re.fullmatch(r"[a-f0-9]{24}", referencia):
        raise HTTPException(status_code=404, detail="Candidato não encontrado")
    encontrado = next((item for ref, item in candidatos if ref == referencia), None)
    if encontrado is None:
        raise HTTPException(status_code=409, detail="O plano mudou; recarregue os candidatos")
    if (payload.indice_frase is None) == (payload.frase_personalizada is None):
        raise HTTPException(
            status_code=400,
            detail="Escolha uma frase sugerida ou informe uma frase personalizada.",
        )
    if payload.frase_personalizada is not None:
        texto = " ".join(payload.frase_personalizada.split())
        aprovado = encontrado.model_copy(
            update={
                "frases_ponte": [*encontrado.frases_ponte, FrasePonte(texto=texto, aprovada=True)],
            }
        )
    else:
        try:
            aprovado = aprovar_frase_ponte(encontrado, payload.indice_frase or 0)
        except IndexError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    pasta = _pasta_short_derivado(projeto, referencia)
    conteudo = {
        "referencia": referencia,
        "fonte_hash": fonte_hash,
        "candidato": aprovado.model_dump(mode="json"),
        "aprovado_em": datetime.now(UTC).isoformat(),
    }
    versao = calcular_hash_dados(conteudo)
    atomic_write_json(pasta / f"aprovacao-{versao}.json", conteudo)
    atomic_write_json(
        pasta / "aprovacao_atual.json",
        {
            "versao": versao,
            "fonte_hash": fonte_hash,
        },
    )
    return {"versao": versao, "aprovacao": conteudo}


@app.post("/api/projetos/{slug}/shorts/derivados/{referencia}/idiomas/{idioma}/aprovar-ponte")
def aprovar_ponte_short_localizada(
    slug: str, referencia: str, idioma: str, payload: AprovarPonteIdiomaPayload
) -> dict[str, Any]:
    projeto = _projeto_da_interface(slug)
    if not re.fullmatch(r"[a-f0-9]{24}", referencia):
        raise HTTPException(status_code=404, detail="Candidato não encontrado")
    _, _, candidatos = _candidatos_shorts(projeto)
    if not any(ref == referencia for ref, _ in candidatos):
        raise HTTPException(status_code=409, detail="O plano mudou; recarregue os candidatos")
    try:
        return aprovar_ponte_short_idioma(projeto, referencia, idioma, payload.texto)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/projetos/{slug}/shorts/derivados/{referencia}/manifesto-vertical")
def criar_manifesto_vertical_short(
    slug: str, referencia: str, payload: ManifestoShortPayload
) -> dict[str, Any]:
    projeto = _projeto_da_interface(slug)
    plano, fonte_hash, candidatos = _candidatos_shorts(projeto)
    encontrado = next((item for ref, item in candidatos if ref == referencia), None)
    if encontrado is None:
        raise HTTPException(status_code=409, detail="O plano mudou; recarregue os candidatos")
    pasta = _pasta_short_derivado(projeto, referencia)
    atual_path = pasta / "aprovacao_atual.json"
    if not atual_path.is_file():
        raise HTTPException(
            status_code=409,
            detail="Aprove uma frase-ponte antes da verticalização",
        )
    atual = json.loads(atual_path.read_text(encoding="utf-8"))
    versao_aprovacao_id = str(atual.get("versao", ""))
    if not re.fullmatch(r"[a-f0-9]{64}", versao_aprovacao_id):
        raise HTTPException(status_code=409, detail="A aprovação está inválida")
    versao_aprovacao = pasta / f"aprovacao-{versao_aprovacao_id}.json"
    if atual.get("fonte_hash") != fonte_hash or not versao_aprovacao.is_file():
        raise HTTPException(status_code=409, detail="A aprovação está desatualizada")
    dados_aprovacao = json.loads(versao_aprovacao.read_text(encoding="utf-8"))
    aprovado = CandidatoShort.model_validate(dados_aprovacao["candidato"])
    if not any(frase.aprovada for frase in aprovado.frases_ponte):
        raise HTTPException(status_code=409, detail="A frase-ponte não está aprovada")

    ids_segmentos = set(encontrado.segmento_ids)
    blocos = []
    ativos_usados: set[str] = set()
    for bloco in plano.blocos:
        shots = []
        for shot in bloco.shots:
            if not ids_segmentos.intersection(shot.segmentos):
                continue
            inicio_shot = shot.inicio_s if shot.inicio_s is not None else encontrado.inicio_s
            fim_shot = shot.fim_s if shot.fim_s is not None else inicio_shot + shot.duracao_s
            inicio = max(inicio_shot, encontrado.inicio_s)
            fim = min(fim_shot, encontrado.fim_s)
            if fim <= inicio:
                continue
            shots.append(shot.model_copy(update={"inicio_s": inicio, "fim_s": fim}))
            ativos_usados.update(shot.ativos)
        if shots:
            blocos.append(bloco.model_copy(update={"shots": shots}))
    ativos_vertical = dict(plano.ativos)
    resolvidos_path = projeto.pastas.plano / "ativos_resolvidos.json"
    if resolvidos_path.is_file():
        try:
            resolvidos = json.loads(resolvidos_path.read_text(encoding="utf-8")).get("ativos", {})
            ativos_vertical.update(
                {aid: Ativo.model_validate(item) for aid, item in resolvidos.items()}
            )
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail="Ativos resolvidos inválidos") from exc
    escolhas_path = projeto.pastas.midias / "escolhas.json"
    if escolhas_path.is_file():
        try:
            escolhas = json.loads(escolhas_path.read_text(encoding="utf-8")).get("ativos", {})
            for aid, escolha in escolhas.items():
                if aid in ativos_vertical and isinstance(escolha, dict) and escolha.get("caminho"):
                    ativos_vertical[aid].caminho = Path(escolha["caminho"])
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail="Escolhas de mídia inválidas") from exc
    plano_derivado = plano.model_copy(
        update={
            "blocos": blocos,
            "ativos": {
                aid: ativos_vertical[aid] for aid in ativos_usados if aid in ativos_vertical
            },
        }
    )
    try:
        manifesto = verticalizar_plano(
            plano_derivado,
            payload.dimensoes,
            focos=payload.focos,
            estrategia=payload.estrategia,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    manifesto = manifesto.model_copy(
        update={
            "hash_entrada": calcular_hash_dados(
                {
                    "fonte": fonte_hash,
                    "aprovacao": atual["versao"],
                    "manifesto": manifesto.model_dump(mode="json"),
                }
            ),
        }
    )
    versao_manifesto = manifesto.hash_entrada
    atomic_write_json(
        pasta / f"manifesto-vertical-{versao_manifesto}.json", manifesto.model_dump(mode="json")
    )
    atomic_write_json(
        pasta / "manifesto_atual.json",
        {
            "versao": versao_manifesto,
            "aprovacao_versao": atual["versao"],
            "fonte_hash": fonte_hash,
        },
    )
    return {
        "versao": versao_manifesto,
        "manifesto": manifesto.model_dump(mode="json"),
        "aprovacao_versao": atual["versao"],
    }


@app.post("/api/projetos/{slug}/shorts/derivados/{referencia}/produzir", status_code=202)
def iniciar_producao_short_derivado(
    slug: str, referencia: str, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    projeto = _projeto_da_interface(slug)
    _, fonte_hash, candidatos = _candidatos_shorts(projeto)
    if not re.fullmatch(r"[a-f0-9]{24}", referencia):
        raise HTTPException(status_code=404, detail="Candidato não encontrado")
    if not any(ref == referencia for ref, _ in candidatos):
        raise HTTPException(status_code=409, detail="O plano mudou; recarregue os candidatos")
    pasta = _pasta_short_derivado(projeto, referencia)
    aprovacao_path = pasta / "aprovacao_atual.json"
    manifesto_path = pasta / "manifesto_atual.json"
    if not aprovacao_path.is_file() or not manifesto_path.is_file():
        raise HTTPException(
            status_code=409, detail="Aprove a ponte e gere o manifesto vertical primeiro"
        )
    aprovacao = json.loads(aprovacao_path.read_text(encoding="utf-8"))
    manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
    if (
        aprovacao.get("fonte_hash") != fonte_hash
        or manifesto.get("fonte_hash") != fonte_hash
        or manifesto.get("aprovacao_versao") != aprovacao.get("versao")
    ):
        raise HTTPException(status_code=409, detail="A aprovação ou o manifesto está desatualizado")
    estado_path = pasta / "producao_atual.json"
    if estado_path.is_file():
        with contextlib.suppress(ValueError, OSError, TypeError):
            estado_anterior = json.loads(estado_path.read_text(encoding="utf-8"))
            if (
                estado_anterior.get("status") in ("aguardando", "executando")
                and estado_anterior.get("aprovacao_versao") == aprovacao.get("versao")
                and estado_anterior.get("manifesto_versao") == manifesto.get("versao")
            ):
                return {"status": estado_anterior["status"], "referencia": referencia}
    atomic_write_json(
        estado_path,
        {
            "status": "aguardando",
            "referencia": referencia,
            "fonte_hash": fonte_hash,
            "aprovacao_versao": aprovacao.get("versao"),
            "manifesto_versao": manifesto.get("versao"),
        },
    )
    background_tasks.add_task(executar_producao_background, projeto, referencia)
    return {"status": "aguardando", "referencia": referencia}


@app.post(
    "/api/projetos/{slug}/shorts/derivados/{referencia}/idiomas/{idioma}/produzir",
    status_code=202,
)
def iniciar_producao_short_idioma(
    slug: str, referencia: str, idioma: str, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    projeto = _projeto_da_interface(slug)
    idiomas_cfg = projeto.obter_opcoes().get("idiomas", {})
    extras = idiomas_cfg.get("extras", []) if isinstance(idiomas_cfg, dict) else []
    if idioma not in extras or not re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", idioma):
        raise HTTPException(status_code=404, detail="Idioma extra não configurado")
    if idioma.split("-", maxsplit=1)[0].lower() not in {"pt", "en", "es"}:
        raise HTTPException(
            status_code=422,
            detail=(
                f"A produção de Shorts ainda não localiza textos de CTA e metadados para {idioma}."
            ),
        )
    _, fonte_hash, candidatos = _candidatos_shorts(projeto)
    candidato = next((item for ref, item in candidatos if ref == referencia), None)
    if not re.fullmatch(r"[a-f0-9]{24}", referencia) or candidato is None:
        raise HTTPException(status_code=409, detail="O plano mudou; recarregue os candidatos")
    pasta = _pasta_short_derivado(projeto, referencia)
    aprovacao_path = pasta / "aprovacao_atual.json"
    manifesto_path = pasta / "manifesto_atual.json"
    if not aprovacao_path.is_file() or not manifesto_path.is_file():
        raise HTTPException(status_code=409, detail="Aprove a ponte principal e gere o manifesto")
    aprovacao = json.loads(aprovacao_path.read_text(encoding="utf-8"))
    manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
    if (
        aprovacao.get("fonte_hash") != fonte_hash
        or manifesto.get("fonte_hash") != fonte_hash
        or manifesto.get("aprovacao_versao") != aprovacao.get("versao")
    ):
        raise HTTPException(
            status_code=409, detail="A aprovação base ou manifesto está desatualizado"
        )
    try:
        _, ponte_versao = obter_ponte_idioma_aprovada(projeto, referencia, idioma, candidato)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    estado_path = pasta / f"producao-{idioma}.json"
    if estado_path.is_file():
        with contextlib.suppress(ValueError, OSError, TypeError):
            anterior = json.loads(estado_path.read_text(encoding="utf-8"))
            if (
                anterior.get("status") in ("aguardando", "executando")
                and anterior.get("aprovacao_ponte_idioma") == ponte_versao
                and anterior.get("manifesto_versao") == manifesto.get("versao")
            ):
                return {"status": anterior["status"], "referencia": referencia, "idioma": idioma}
    atomic_write_json(
        estado_path,
        {
            "status": "aguardando",
            "referencia": referencia,
            "idioma": idioma,
            "fonte_hash": fonte_hash,
            "aprovacao_versao": aprovacao.get("versao"),
            "manifesto_versao": manifesto.get("versao"),
            "aprovacao_ponte_idioma": ponte_versao,
        },
    )
    background_tasks.add_task(executar_producao_background, projeto, referencia, idioma)
    return {"status": "aguardando", "referencia": referencia, "idioma": idioma}


@app.get("/api/projetos/{slug}/shorts/derivados/{referencia}/saida/{arquivo}")
def obter_arquivo_short_derivado(
    slug: str, referencia: str, arquivo: str, idioma: str | None = None
) -> FileResponse:
    projeto = _projeto_da_interface(slug)
    if not re.fullmatch(r"[a-f0-9]{24}", referencia):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    _, fonte_hash, candidatos = _candidatos_shorts(projeto)
    candidato = next((item for ref, item in candidatos if ref == referencia), None)
    if candidato is None:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    if arquivo not in {"video.mp4", "capa.jpg", "legendas.srt"}:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    idioma_principal = str(projeto.obter_opcoes().get("idiomas", {}).get("principal", "pt-BR"))
    idioma_saida = idioma or idioma_principal
    pasta_short = _pasta_short_derivado(projeto, referencia)
    if idioma_saida == idioma_principal:
        estado_path = pasta_short / "producao_atual.json"
        ponte_idioma_versao = None
    else:
        extras = projeto.obter_opcoes().get("idiomas", {}).get("extras", [])
        if idioma_saida not in extras or not re.fullmatch(
            r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", idioma_saida
        ):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        try:
            _, ponte_idioma_versao = obter_ponte_idioma_aprovada(
                projeto, referencia, idioma_saida, candidato
            )
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise HTTPException(status_code=404, detail="Saída localizada desatualizada") from exc
        estado_path = pasta_short / f"producao-{idioma_saida}.json"
    if not estado_path.is_file():
        raise HTTPException(status_code=404, detail="Produção ainda não disponível")
    with contextlib.suppress(ValueError, OSError, TypeError):
        estado = json.loads(estado_path.read_text(encoding="utf-8"))
        pasta = estado_path.parent
        if estado.get("fonte_hash") != fonte_hash or (
            ponte_idioma_versao and estado.get("aprovacao_ponte_idioma") != ponte_idioma_versao
        ):
            raise HTTPException(status_code=404, detail="Esta revisão de saída está desatualizada")
        ponte_atual = json.loads((pasta / "aprovacao_atual.json").read_text(encoding="utf-8"))
        manifesto_atual = json.loads((pasta / "manifesto_atual.json").read_text(encoding="utf-8"))
        if estado.get("aprovacao_versao") != ponte_atual.get("versao") or estado.get(
            "manifesto_versao"
        ) != manifesto_atual.get("versao"):
            raise HTTPException(status_code=404, detail="Esta revisão de saída está desatualizada")
        resultado = estado.get("resultado", {})
        caminho_base = Path(resultado.get("caminho_video", "")).resolve().parent
        raiz_saida = projeto.pastas.saida.resolve()
        caminho = (caminho_base / arquivo).resolve()
        if (
            caminho_base.is_relative_to(raiz_saida)
            and caminho.is_relative_to(raiz_saida)
            and caminho.is_file()
        ):
            tipo = {
                "video.mp4": "video/mp4",
                "capa.jpg": "image/jpeg",
                "legendas.srt": "text/plain",
            }[arquivo]
            return FileResponse(caminho, media_type=tipo, filename=arquivo)
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")


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
                        etapa_atual = "Saídas pendentes de M3/M4" if ausentes else "Concluído"
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
            detail=("Código de confirmação incorreto. Digite PRODUZIR para confirmar a produção."),
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
        "R1_imagens",
        "R2_tratamento",
        "R3_mapas",
        "R4_trilha_sfx",
        "R5_montagem",
        "R6_mix",
        "R7_render",
        "R8_qa",
        "R9_pacote",
        "R10_biblioteca",
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

    pasta_global = obter_pasta_global()
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
    pasta_global = obter_pasta_global()
    categorias: dict[str, list[dict[str, Any]]] = {
        "imagens": [],
        "personagens": [],
        "mapas": [],
        "loops": [],
        "trilhas": [],
        "sfx": [],
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
