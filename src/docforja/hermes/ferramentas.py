"""Ferramentas operacionais do Hermes Agent para DocForja.

Executa comandos estritamente delimitados sobre a API/CLI local,
com validação de slug contra travessia de caminho e proteção
inviolável do código de confirmação humana PRODUZIR.
"""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from typing import Any

from docforja.nucleo.banco import BancoProjeto
from docforja.nucleo.cotas import gerenciador_cotas
from docforja.nucleo.gpu import semaforo_gpu
from docforja.nucleo.handlers import criar_executor_projeto
from docforja.nucleo.projeto import Projeto
from docforja.settings import load_settings


def validar_slug(slug: str) -> str:
    """Valida o slug contra caracteres inválidos e travessia de diretório."""
    limpo = slug.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,99}", limpo):
        raise ValueError(
            f"Slug inválido: '{slug}'. Use apenas letras minúsculas, números e hífens."
        )
    if ".." in limpo or "/" in limpo or "\\" in limpo:
        raise ValueError("Tentativa de travessia de diretório bloqueada.")
    return limpo


def obter_projeto_seguro(slug: str, raiz_projetos: Path | None = None) -> Projeto:
    """Localiza o projeto garantindo que ele resida estritamente dentro da raiz configurada."""
    slug_valido = validar_slug(slug)
    settings = load_settings()
    raiz = (raiz_projetos or settings.paths.projects).resolve()
    caminho = (raiz / slug_valido).resolve()
    if caminho.parent != raiz:
        raise PermissionError(f"Acesso negado: caminho fora da raiz autorizada: {caminho}")
    if not caminho.is_dir() or not (caminho / "sistema" / "banco.db").is_file():
        raise FileNotFoundError(f"Projeto '{slug_valido}' não encontrado em {raiz}.")
    return Projeto(caminho, slug_valido)


def docforja_novo(
    nome: str,
    tipo: str = "longo",
    roteiro: str = "",
    idioma_principal: str = "pt-BR",
    idiomas_extras: list[str] | None = None,
    preset: str = "padrao",
    kit: str = "cinza-e-brasa@1.0",
    raiz_projetos: Path | None = None,
) -> dict[str, Any]:
    """Cria um novo projeto DocForja com estrutura oficial."""
    projeto = Projeto.criar(
        nome=nome,
        tipo=tipo,
        roteiro=roteiro,
        idioma_principal=idioma_principal,
        idiomas_extras=idiomas_extras,
        preset=preset,
        kit=kit,
        raiz_projetos=raiz_projetos,
    )
    return {
        "status": "criado",
        "slug": projeto.slug,
        "caminho": str(projeto.raiz),
        "idiomas": {"principal": idioma_principal, "extras": idiomas_extras or []},
    }


def docforja_status(slug: str, raiz_projetos: Path | None = None) -> dict[str, Any]:
    """Retorna estado das etapas, semáforo de GPU e cotas de forma resumida."""
    projeto = obter_projeto_seguro(slug, raiz_projetos=raiz_projetos)
    banco = BancoProjeto(projeto.banco_file)
    etapas = banco.listar_etapas()

    gpu_info = semaforo_gpu.obter_status()
    cotas_info = gerenciador_cotas.obter_resumo()

    return {
        "slug": projeto.slug,
        "etapas": [
            {
                "id": e["id"],
                "status": e["status"],
                "duracao_s": round(e["duracao_s"], 2) if e.get("duracao_s") else None,
            }
            for e in etapas
        ],
        "gpu": {
            "ocupada": gpu_info["ocupada"],
            "modelo_atual": gpu_info["modelo_atual"] or "nenhum",
        },
        "cotas": {"requisicoes_hoje": cotas_info["requisicoes"]},
    }


def docforja_resumo_plano(slug: str, raiz_projetos: Path | None = None) -> dict[str, Any]:
    """Retorna resumo do plano gerado e itens pendentes na lista de busca."""
    projeto = obter_projeto_seguro(slug, raiz_projetos=raiz_projetos)
    banco = BancoProjeto(projeto.banco_file)
    p8_status = banco.obter_etapa("P8_estimativa_previa")
    plano_pronto = bool(p8_status and p8_status.get("status") == "concluida")

    lista_busca_path = projeto.pastas.plano / "lista_de_busca.md"
    itens_pendentes: list[str] = []
    if lista_busca_path.is_file():
        conteudo = lista_busca_path.read_text(encoding="utf-8")
        for linha in conteudo.splitlines():
            if linha.strip().startswith("- [ ]") or linha.strip().startswith("- [x]"):
                itens_pendentes.append(linha.strip())

    estimativa_min: int | None = None
    estimativa_md = projeto.pastas.plano / "estimativa.md"
    if estimativa_md.is_file():
        match = re.search(r"(\d+)\s*min", estimativa_md.read_text(encoding="utf-8"))
        if match:
            estimativa_min = int(match.group(1))

    return {
        "slug": projeto.slug,
        "plano_pronto": plano_pronto,
        "estimativa_minutos": estimativa_min,
        "total_buscas": len(itens_pendentes),
        "buscas_pendentes": [it for it in itens_pendentes if it.startswith("- [ ]")][:10],
    }


def docforja_imagens_nao_atribuidas(
    slug: str, raiz_projetos: Path | None = None
) -> dict[str, Any]:
    """Lista arquivos recebidos em 02_midias/manual/nao_atribuidas/ aguardando identificação."""
    projeto = obter_projeto_seguro(slug, raiz_projetos=raiz_projetos)
    arquivos: list[str] = []
    for pasta in (
        projeto.pastas.midias / "nao_atribuidas",
        projeto.pastas.midias / "manual" / "nao_atribuidas",
    ):
        if pasta.is_dir():
            arquivos.extend(f.name for f in pasta.iterdir() if f.is_file())

    arquivos = sorted(set(arquivos))

    return {
        "slug": projeto.slug,
        "quantidade": len(arquivos),
        "arquivos": sorted(arquivos),
    }


def docforja_planejar(slug: str, raiz_projetos: Path | None = None) -> dict[str, Any]:
    """Executa o pipeline de planejamento até P8_estimativa_previa."""
    projeto = obter_projeto_seguro(slug, raiz_projetos=raiz_projetos)
    executor = criar_executor_projeto(projeto)
    resultados = asyncio.run(executor.executar(ate_etapa="P8_estimativa_previa"))
    falhou = any(st == "falhou" for st in resultados.values())
    return {
        "slug": projeto.slug,
        "sucesso": not falhou,
        "etapas_executadas": resultados,
    }


def docforja_produzir(
    slug: str, codigo_confirmacao: str, raiz_projetos: Path | None = None
) -> dict[str, Any]:
    """Aprova o gate REVISAO somente com o código PRODUZIR e inicia a produção final."""
    if not codigo_confirmacao or codigo_confirmacao.strip().upper() != "PRODUZIR":
        raise ValueError(
            "Código de confirmação inválido ou ausente. "
            "É obrigatório que o usuário digite 'PRODUZIR' para autorizar a produção."
        )

    projeto = obter_projeto_seguro(slug, raiz_projetos=raiz_projetos)
    executor = criar_executor_projeto(projeto)
    executor.aprovar_gate("REVISAO")

    # Inicia execução de produção
    resultados = asyncio.run(executor.executar())
    falhou = any(st == "falhou" for st in resultados.values())
    return {
        "slug": projeto.slug,
        "sucesso": not falhou,
        "etapas_executadas": resultados,
    }


def docforja_status_producao(slug: str, raiz_projetos: Path | None = None) -> dict[str, Any]:
    """Retorna o progresso das etapas de produção e arquivos gerados em 05_saida/."""
    projeto = obter_projeto_seguro(slug, raiz_projetos=raiz_projetos)
    banco = BancoProjeto(projeto.banco_file)
    etapas_producao = [
        "R1_imagens", "R2_tratamento", "R3_mapas", "R4_trilha_sfx",
        "R5_montagem", "R6_mix", "R7_render", "R8_qa", "R9_pacote", "R10_biblioteca"
    ]
    concluidas = 0
    em_andamento = None
    falha = None

    for eid in etapas_producao:
        info = banco.obter_etapa(eid)
        if not info:
            continue
        status = info.get("status")
        if status == "concluida":
            concluidas += 1
        elif status == "executando":
            em_andamento = eid
        elif status == "falhou":
            falha = eid
            break

    progresso_pct = round((concluidas / len(etapas_producao)) * 100, 1)
    concluido = concluidas == len(etapas_producao)

    # Coleta saídas disponíveis se concluído
    saidas: dict[str, list[str]] = {}
    if concluido and projeto.pastas.saida.is_dir():
        for sub in projeto.pastas.saida.iterdir():
            if sub.is_dir() and sub.name != "elementos":
                saidas[sub.name] = [f.name for f in sub.iterdir() if f.is_file()]

    return {
        "slug": projeto.slug,
        "concluido": concluido,
        "progresso_percentual": progresso_pct,
        "etapa_ativa": em_andamento or falha or ("concluido" if concluido else "pendente"),
        "falha": falha,
        "saidas": saidas,
    }


def validar_chat_telegram(
    chat_id: str | int, chat_autorizado: str | int | None = None
) -> bool:
    """Valida se o chat_id que enviou a mensagem é o proprietário autorizado em TELEGRAM_CHAT_ID."""
    autorizado = chat_autorizado or os.getenv("TELEGRAM_CHAT_ID", "")
    if not str(autorizado).strip():
        return False
    return str(chat_id).strip() == str(autorizado).strip()
