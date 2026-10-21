"""Produção versionada de um short derivado nos idiomas disponíveis no projeto."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import unicodedata
from itertools import pairwise
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from docforja.audio.mixagem import exigir_medidas, extrair_medidas_loudnorm
from docforja.esquemas import Ativo, Plano
from docforja.idiomas.narracao import carregar_traducao_atual, eh_modo_so_legendas
from docforja.io import atomic_write_json, atomic_write_text
from docforja.midia.licenca import (
    caminho_sidecar_licenca,
    carregar_ficha_licenca,
    classificar_licenca,
    detectar_patrimonio_restrito,
)
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.nucleo.gpu import semaforo_gpu
from docforja.nucleo.handlers import _criar_orquestrador
from docforja.nucleo.projeto import Projeto, slugificar
from docforja.planejamento.entidades import SegmentoProcessado
from docforja.planejamento.previa import KIT_REMOTION
from docforja.shorts.candidatos import pontuar_candidatos_do_plano
from docforja.shorts.modelos import (
    CandidatoShort,
    ElementoTelaShort,
    IntervaloLegendaShort,
    ManifestoVertical,
    ShortParaVerificar,
)
from docforja.shorts.verificador import verificar_short

FPS = 30
MAX_CHARS_LEGENDA = 42
MAX_CHARS_LINHA_LEGENDA = 21
GANHO_TRILHA_SHORT = 0.0648


class CaptionRemotion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    startMs: float = Field(ge=0)
    endMs: float = Field(gt=0)
    timestampMs: float | None = None
    confidence: float | None = None


class PropsCenaShort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variante: str
    titulo: str = ""
    subtitulo: str = ""
    texto: str = ""
    imagem: str = ""
    imagem_antes: str = ""
    imagem_depois: str = ""
    clipe: str = ""
    itens: list[str] = Field(default_factory=list)
    opcao_a: str = ""
    opcao_b: str = ""
    preco: str = ""
    condicao: str = ""
    aviso_publicidade: str = ""
    prova: str = ""
    fonte_prova: str = ""
    cta: str = ""
    marca: str = ""
    foco_x: float = Field(default=0.5, ge=0, le=1)
    foco_y: float = Field(default=0.5, ge=0, le=1)
    usar_fundo_desfocado: bool = False
    legendas: list[CaptionRemotion] = Field(default_factory=list)


class CenaRenderShort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    inicio_frame: int = Field(ge=0)
    duracao_frames: int = Field(gt=0)
    props: PropsCenaShort


class PropsRenderShort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duracao_frames: int = Field(gt=0)
    audio: str = Field(min_length=1)
    cenas: list[CenaRenderShort] = Field(min_length=1)


class ResultadoProducaoShort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    idioma: str
    revisao: str
    caminho_video: str
    caminho_capa: str
    caminho_legendas: str
    duracao_s: float
    qa_aprovado: bool
    falhas_qa: list[str] = Field(default_factory=list)
    cache: bool = False


def _executar(comando: list[str], *, cwd: Path, timeout: int = 3600) -> str:
    resultado = subprocess.run(
        comando, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
    )
    if resultado.returncode:
        raise RuntimeError((resultado.stderr or resultado.stdout)[-1800:])
    return resultado.stderr + "\n" + resultado.stdout


def _traducao_atual_validada(projeto: Projeto, idioma: str) -> tuple[Any, Path]:
    traducao, caminho = carregar_traducao_atual(projeto, idioma)
    hash_roteiro_atual = hashlib.sha256(projeto.obter_roteiro().encode("utf-8")).hexdigest()
    if traducao.hash_roteiro_origem != hash_roteiro_atual:
        raise ValueError(f"A tradução em {idioma} está desatualizada em relação ao roteiro atual.")
    return traducao, caminho


def _carregar_aprovacao_manifesto(
    projeto: Projeto, referencia: str
) -> tuple[dict[str, Any], CandidatoShort, ManifestoVertical, str, str]:
    pasta = projeto.pastas.montagem / "shorts" / "derivados" / referencia
    atual_path = pasta / "aprovacao_atual.json"
    if not atual_path.is_file():
        raise ValueError("Aprove uma frase-ponte antes de produzir o short.")
    atual = json.loads(atual_path.read_text(encoding="utf-8"))
    aprovacao_id = str(atual.get("versao", ""))
    if not re.fullmatch(r"[a-f0-9]{64}", aprovacao_id):
        raise ValueError("A versão da aprovação é inválida.")
    aprovacao_path = pasta / f"aprovacao-{aprovacao_id}.json"
    if not aprovacao_path.is_file():
        raise ValueError("A versão aprovada não está disponível.")
    aprovacao = json.loads(aprovacao_path.read_text(encoding="utf-8"))
    candidato = CandidatoShort.model_validate(aprovacao["candidato"])
    if not any(frase.aprovada for frase in candidato.frases_ponte):
        raise ValueError("A frase-ponte ainda não foi aprovada.")
    manifesto_pointer_path = pasta / "manifesto_atual.json"
    if not manifesto_pointer_path.is_file():
        raise ValueError("Gere novamente o manifesto vertical antes de produzir o short.")
    pointer = json.loads(manifesto_pointer_path.read_text(encoding="utf-8"))
    manifesto_id = str(pointer.get("versao", ""))
    if not re.fullmatch(r"[a-f0-9]{64}", manifesto_id):
        raise ValueError("A versão do manifesto vertical é inválida.")
    if pointer.get("aprovacao_versao") != aprovacao_id:
        raise ValueError("A frase-ponte mudou; gere novamente o manifesto vertical.")
    if pointer.get("fonte_hash") != aprovacao.get("fonte_hash"):
        raise ValueError("O manifesto vertical foi criado para outra versão do plano.")
    manifesto_path = pasta / f"manifesto-vertical-{manifesto_id}.json"
    if not manifesto_path.is_file():
        raise ValueError("A versão do manifesto vertical não está disponível.")
    manifesto = ManifestoVertical.model_validate_json(manifesto_path.read_text(encoding="utf-8"))
    return aprovacao, candidato, manifesto, aprovacao_id, manifesto_id


def _opcoes_projeto(
    projeto: Projeto, idioma_solicitado: str | None = None
) -> tuple[dict[str, Any], str, str, str]:
    opcoes = projeto.obter_opcoes()
    idiomas_cfg = opcoes.get("idiomas", {})
    principal = str(idiomas_cfg.get("principal", "pt-BR"))
    idioma = idioma_solicitado or principal
    if not re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", idioma):
        raise ValueError("O código de idioma do projeto é inválido.")
    extras = idiomas_cfg.get("extras", []) if isinstance(idiomas_cfg, dict) else []
    if idioma != principal and idioma not in extras:
        raise ValueError(f"{idioma} não está configurado como idioma extra do projeto.")
    motor = str(opcoes.get("tts", {}).get("motor") or opcoes.get("motor_tts") or "kokoro")
    vozes = opcoes.get("vozes", {})
    voz = str(vozes.get(idioma) or (opcoes.get("voz") if idioma == principal else "") or "")
    if opcoes.get("narracao_pronta") or any(
        (projeto.pastas.entrada / f"narracao{suffix}").is_file()
        for suffix in (".wav", ".mp3", f"_{idioma}.wav", f"_{idioma}.mp3")
    ):
        raise ValueError(
            "Este projeto usa narração gravada. Para preservar a mesma voz, grave a frase-ponte; "
            "não vamos sintetizar uma voz diferente automaticamente."
        )
    return opcoes, idioma, motor, voz


def obter_ponte_idioma_aprovada(
    projeto: Projeto, referencia: str, idioma: str, candidato: CandidatoShort
) -> tuple[str, str]:
    """Carrega uma frase localizada somente quando há aprovação humana vigente."""
    if not re.fullmatch(r"[a-f0-9]{24}", referencia) or not re.fullmatch(
        r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", idioma
    ):
        raise ValueError("Referência ou idioma da ponte localizada inválido.")
    pasta = (
        projeto.pastas.montagem / "shorts" / "derivados" / referencia / "pontes_idiomas" / idioma
    )
    indice_path = pasta / "aprovacao_atual.json"
    if not indice_path.is_file():
        raise ValueError(f"A frase-ponte localizada para {idioma} precisa de aprovação.")
    indice = json.loads(indice_path.read_text(encoding="utf-8"))
    versao = str(indice.get("versao", ""))
    if not re.fullmatch(r"[a-f0-9]{64}", versao):
        raise ValueError(f"A aprovação da frase-ponte em {idioma} é inválida.")
    arquivo = pasta / f"aprovacao-{versao}.json"
    if not arquivo.is_file():
        raise ValueError(f"A aprovação da frase-ponte em {idioma} não está disponível.")
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    if calcular_hash_dados(dados) != versao:
        raise ValueError(f"A revisão da frase-ponte em {idioma} foi alterada.")
    base_atual_path = pasta.parent.parent / "aprovacao_atual.json"
    if not base_atual_path.is_file():
        raise ValueError("A aprovação base do candidato não está disponível.")
    base_versao = json.loads(base_atual_path.read_text(encoding="utf-8")).get("versao")
    traducao, _ = _traducao_atual_validada(projeto, idioma)
    if (
        dados.get("idioma") != idioma
        or dados.get("candidato_id") != candidato.id
        or dados.get("aprovacao_base") != base_versao
        or dados.get("hash_traducao") != traducao.hash_traducao
        or not dados.get("aprovada")
        or not isinstance(dados.get("texto"), str)
    ):
        raise ValueError(f"A frase-ponte em {idioma} não está aprovada para este trecho.")
    texto = " ".join(dados["texto"].split())
    if not texto or len(texto) > 240:
        raise ValueError(f"A frase-ponte em {idioma} está vazia ou excede 240 caracteres.")
    return texto, versao


def aprovar_ponte_short_idioma(
    projeto: Projeto, referencia: str, idioma: str, texto: str
) -> dict[str, Any]:
    """Persiste a tradução manual da ponte como revisão imutável por idioma."""
    if not re.fullmatch(r"[a-f0-9]{24}", referencia):
        raise ValueError("Referência de short inválida.")
    opcoes = projeto.obter_opcoes()
    idiomas_cfg = opcoes.get("idiomas", {})
    extras = idiomas_cfg.get("extras", []) if isinstance(idiomas_cfg, dict) else []
    principal = (
        str(idiomas_cfg.get("principal", "pt-BR")) if isinstance(idiomas_cfg, dict) else "pt-BR"
    )
    if (
        idioma == principal
        or idioma not in extras
        or not re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", idioma)
    ):
        raise ValueError("O idioma deve ser um idioma extra configurado no projeto.")
    _aprovacao, candidato, _, aprovacao_id, _ = _carregar_aprovacao_manifesto(projeto, referencia)
    traducao, _ = _traducao_atual_validada(projeto, idioma)
    ids_traduzidos = {item.id for item in traducao.segmentos}
    if not set(candidato.segmento_ids).issubset(ids_traduzidos):
        raise ValueError(f"A tradução em {idioma} não contém os segmentos deste short.")
    texto_limpo = " ".join(texto.split())
    if not texto_limpo or len(texto_limpo) > 240:
        raise ValueError("A frase-ponte localizada deve ter entre 1 e 240 caracteres.")
    conteudo = {
        "referencia": referencia,
        "idioma": idioma,
        "candidato_id": candidato.id,
        "aprovacao_base": aprovacao_id,
        "hash_traducao": traducao.hash_traducao,
        "texto": texto_limpo,
        "aprovada": True,
    }
    versao = calcular_hash_dados(conteudo)
    pasta = (
        projeto.pastas.montagem / "shorts" / "derivados" / referencia / "pontes_idiomas" / idioma
    )
    atomic_write_json(pasta / f"aprovacao-{versao}.json", conteudo)
    atomic_write_json(pasta / "aprovacao_atual.json", {"versao": versao})
    return {"versao": versao, "aprovacao": conteudo}


def _localizar_dados_short(
    projeto: Projeto,
    idioma: str,
    candidato: CandidatoShort,
    plano: Plano,
    manifesto: ManifestoVertical,
) -> tuple[CandidatoShort, ManifestoVertical, Path, Path, Path, dict[str, str]]:
    """Resolve narração, tempos, palavras e shots retimados para um idioma extra."""
    traducao, _ = _traducao_atual_validada(projeto, idioma)
    if eh_modo_so_legendas(projeto, idioma):
        raise ValueError(
            f"{idioma} está em 'só legendas'; falta narração localizada para renderizar."
        )
    pasta_audio = projeto.pastas.audio / idioma
    audio = pasta_audio / "narracao_completa.wav"
    segmentos_path = pasta_audio / "segmentos.json"
    palavras_path = pasta_audio / "palavras.json"
    manifesto_audio_path = pasta_audio / "narracao_idioma.json"
    if not all(
        path.is_file() for path in (audio, segmentos_path, palavras_path, manifesto_audio_path)
    ):
        raise ValueError(f"Narração alinhada e palavras são necessárias para {idioma}.")
    manifesto_audio = json.loads(manifesto_audio_path.read_text(encoding="utf-8"))
    if manifesto_audio.get("hash_traducao") != traducao.hash_traducao:
        raise ValueError(f"A narração em {idioma} está desatualizada em relação à tradução.")
    for nome in ("narracao_completa.wav", "segmentos.json", "palavras.json"):
        esperado = manifesto_audio.get("hash_saidas", {}).get(nome)
        caminho = pasta_audio / nome
        if not esperado or calcular_hash_dados(caminho) != esperado:
            raise ValueError(f"O arquivo {nome} em {idioma} mudou; regenere a narração localizada.")

    dados_segmentos = json.loads(segmentos_path.read_text(encoding="utf-8"))
    por_id = {str(item.get("id")): item for item in dados_segmentos if item.get("id")}
    textos = {item.id: item.texto_limpo for item in traducao.segmentos}
    if not set(candidato.segmento_ids).issubset(por_id) or not set(candidato.segmento_ids).issubset(
        textos
    ):
        raise ValueError(f"Segmentos traduzidos ou alinhados ausentes em {idioma}.")
    inicio = min(float(por_id[sid]["inicio_s"]) for sid in candidato.segmento_ids)
    fim = max(float(por_id[sid]["fim_s"]) for sid in candidato.segmento_ids)
    texto = " ".join(textos[sid] for sid in candidato.segmento_ids).strip()
    candidato_localizado = candidato.model_copy(
        update={"inicio_s": inicio, "fim_s": fim, "texto": texto}
    )

    shot_por_id = {shot.id: shot for bloco in plano.blocos for shot in bloco.shots}
    shots_localizados = []
    ids_candidato = set(candidato.segmento_ids)
    for shot_v in manifesto.shots:
        shot = shot_por_id.get(shot_v.shot_id)
        if not shot:
            raise ValueError(f"Shot {shot_v.shot_id} não existe mais no plano mestre.")
        ids_shot = ids_candidato.intersection(shot.segmentos)
        if not ids_shot:
            continue
        inicio_shot = min(float(por_id[sid]["inicio_s"]) for sid in ids_shot)
        fim_shot = max(float(por_id[sid]["fim_s"]) for sid in ids_shot)
        shots_localizados.append(
            shot_v.model_copy(
                update={
                    "inicio_s": max(inicio, inicio_shot),
                    "fim_s": min(fim, fim_shot),
                }
            )
        )
    if not shots_localizados:
        raise ValueError(f"O manifesto não contém shots associados aos segmentos de {idioma}.")
    manifesto_localizado = manifesto.model_copy(update={"shots": shots_localizados})
    hashes_localizados = {
        "traducao": traducao.hash_traducao,
        "narracao": calcular_hash_dados(audio),
        "segmentos": calcular_hash_dados(segmentos_path),
        "palavras": calcular_hash_dados(palavras_path),
        "manifesto_narracao": calcular_hash_dados(manifesto_audio_path),
    }
    return (
        candidato_localizado,
        manifesto_localizado,
        audio,
        segmentos_path,
        palavras_path,
        hashes_localizados,
    )


def _ativos_resolvidos(projeto: Projeto, plano: Plano) -> dict[str, Ativo]:
    saida = dict(plano.ativos)
    caminho = projeto.pastas.plano / "ativos_resolvidos.json"
    if caminho.is_file():
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        saida.update(
            {aid: Ativo.model_validate(item) for aid, item in dados.get("ativos", {}).items()}
        )
    escolhas = projeto.pastas.midias / "escolhas.json"
    if escolhas.is_file():
        dados = json.loads(escolhas.read_text(encoding="utf-8")).get("ativos", {})
        for aid, escolha in dados.items():
            if aid in saida and isinstance(escolha, dict) and escolha.get("caminho"):
                saida[aid].caminho = Path(escolha["caminho"])
    return saida


def _licenca_comercial(ativo: Ativo) -> bool:
    caminho = ativo.caminho
    if not caminho or not caminho.is_file():
        return False
    ficha = carregar_ficha_licenca(caminho)
    dados = ficha.model_dump() if ficha else (ativo.licenca or {})
    permitido, _ = classificar_licenca(str(dados.get("licenca", "")))
    return (
        permitido
        and dados.get("comercial") is True
        and not dados.get("patrimonio_restrito", False)
        and not detectar_patrimonio_restrito(ativo.id, ativo.descricao)
    )


def _palavras(path: Path, ids: set[str], inicio: float, fim: float) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValueError("Alinhamento palavra a palavra ausente para este idioma.")
    dados = json.loads(path.read_text(encoding="utf-8"))
    resultado = []
    for item in dados:
        sid = str(item.get("segmento_id", ""))
        texto = str(item.get("palavra", item.get("word", ""))).strip()
        inicio_palavra = float(item.get("inicio_s", item.get("start", 0)))
        fim_palavra = float(item.get("fim_s", item.get("end", 0)))
        if sid in ids and texto and fim_palavra > inicio and inicio_palavra < fim:
            resultado.append(
                {
                    "text": texto,
                    "start": max(0.0, inicio_palavra - inicio),
                    "end": min(fim - inicio, fim_palavra - inicio),
                }
            )
    resultado.sort(key=lambda item: item["start"])
    if not resultado:
        raise ValueError("Não há palavras alinhadas no intervalo aprovado.")
    resultado[0]["start"] = 0.0
    for anterior, atual in pairwise(resultado):
        if atual["start"] - anterior["end"] <= 0.1:
            anterior["end"] = max(anterior["end"], atual["start"])
    resultado[-1]["end"] = fim - inicio
    return resultado


def _captions_remotion(
    palavras: list[dict[str, Any]], inicio: float, fim: float
) -> list[CaptionRemotion]:
    saida = []
    for grupo in _agrupar_palavras(palavras):
        a = max(inicio, float(grupo["start"]))
        b = min(fim, float(grupo["end"]))
        if b <= a:
            continue
        texto = " ".join(str(grupo["text"]).split())
        saida.append(
            CaptionRemotion(
                text="\n".join(
                    textwrap.wrap(
                        texto,
                        width=MAX_CHARS_LINHA_LEGENDA,
                        break_long_words=False,
                    )[:2]
                ),
                startMs=(a - inicio) * 1000,
                endMs=(b - inicio) * 1000,
            )
        )
    return saida


def _agrupar_palavras(palavras: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa palavras em frases curtas, sincronizadas e legíveis em tela pequena."""
    grupos: list[dict[str, Any]] = []
    atual: list[dict[str, Any]] = []

    def finalizar() -> None:
        if not atual:
            return
        grupos.append(
            {
                "text": " ".join(str(item["text"]).strip() for item in atual),
                "start": float(atual[0]["start"]),
                "end": float(atual[-1]["end"]),
                "palavras": atual.copy(),
            }
        )
        atual.clear()

    for palavra in sorted(palavras, key=lambda item: float(item["start"])):
        texto = str(palavra["text"]).strip()
        if not texto:
            continue
        candidata = [*atual, palavra]
        texto_candidato = " ".join(str(item["text"]).strip() for item in candidata)
        duracao = float(candidata[-1]["end"]) - float(candidata[0]["start"])
        excede_limites = len(texto_candidato) > MAX_CHARS_LEGENDA or duracao > 6
        if atual and excede_limites:
            finalizar()
        atual.append(palavra)
        if texto.endswith((".", "!", "?", "…", ";", ":", ",")):
            finalizar()
    finalizar()
    indice = 1
    while indice < len(grupos):
        anterior, atual_grupo = grupos[indice - 1], grupos[indice]
        if len(atual_grupo["palavras"]) == 1:
            ultima_palavra_anterior = str(anterior["palavras"][-1]["text"]).rstrip()
            combinada = f"{anterior['text']} {atual_grupo['text']}"
            duracao_combinada = float(atual_grupo["end"]) - float(anterior["start"])
            if (
                len(combinada) <= MAX_CHARS_LEGENDA
                and duracao_combinada <= 6
                and not ultima_palavra_anterior.endswith((".", "!", "?", "…"))
            ):
                grupos[indice - 1 : indice + 1] = [
                    {
                        "text": combinada,
                        "start": anterior["start"],
                        "end": atual_grupo["end"],
                        "palavras": [*anterior["palavras"], *atual_grupo["palavras"]],
                    }
                ]
                indice = max(1, indice - 1)
                continue
        indice += 1
    return grupos


def _intervalos_legenda(palavras: list[dict[str, Any]]) -> list[IntervaloLegendaShort]:
    """Converte os blocos de legenda efetivamente renderizados em intervalos de verificação."""
    return [
        IntervaloLegendaShort(
            inicio_s=float(bloco["start"]), fim_s=float(bloco["end"]), texto=str(bloco["text"])
        )
        for bloco in _agrupar_palavras(palavras)
        if float(bloco["end"]) > float(bloco["start"])
    ]


def _srt(palavras: list[dict[str, Any]]) -> str:
    def timestamp(segundos: float) -> str:
        total_ms = max(0, round(segundos * 1000))
        horas, restante = divmod(total_ms, 3_600_000)
        minutos, restante = divmod(restante, 60_000)
        segundos_i, ms = divmod(restante, 1000)
        return f"{horas:02d}:{minutos:02d}:{segundos_i:02d},{ms:03d}"

    grupos = _agrupar_palavras(palavras)
    entradas = []
    for idx, item in enumerate(grupos, 1):
        linhas = textwrap.wrap(str(item["text"]), width=42, break_long_words=False)
        entradas.append(
            f"{idx}\n{timestamp(item['start'])} --> {timestamp(item['end'])}\n"
            + "\n".join(linhas)
        )
    return "\n\n".join(entradas) + "\n"


def _licenca_trilha_comercial(trilha: Path) -> bool:
    sidecar = _sidecar_trilha(trilha)
    if not sidecar:
        return False
    dados = json.loads(sidecar.read_text(encoding="utf-8"))
    permitido, _ = classificar_licenca(str(dados.get("licenca", "")))
    return (
        permitido and dados.get("comercial") is True and not dados.get("patrimonio_restrito", False)
    )


def _resolver_trilha_short(projeto: Projeto) -> Path | None:
    """Usa somente trilha escolhida explicitamente, nunca o drone de fallback do kit."""
    pasta_trilha = projeto.pastas.audio / "trilha"
    for nome in (
        "trilha_definitiva.wav",
        "trilha_definitiva.mp3",
        "trilha.wav",
        "trilha.mp3",
        "provisoria.wav",
        "provisoria.mp3",
        "trilha_provisoria.wav",
        "trilha_provisoria.mp3",
    ):
        candidata = pasta_trilha / nome
        if candidata.is_file():
            return candidata

    opcoes_audio = projeto.obter_opcoes().get("audio", {})
    trilha_configurada = (
        opcoes_audio.get("trilha") if isinstance(opcoes_audio, dict) else None
    )
    if not trilha_configurada:
        return None

    from docforja.global_assets.resolucao import buscar_trilha_global, obter_pasta_global

    resultado = buscar_trilha_global(
        str(trilha_configurada), pasta_global=obter_pasta_global()
    )
    return resultado[0] if resultado else None


def _sidecar_trilha(trilha: Path) -> Path | None:
    for sidecar in (
        trilha.with_name(f"{trilha.name}.licenca.json"),
        trilha.with_name(f"{trilha.stem}.licenca.json"),
    ):
        if not sidecar.is_file():
            continue
        return sidecar
    return None


def _medir_lufs(caminho: Path) -> float | None:
    """Mede o loudness integrado do arquivo entregue, no mesmo layout do vídeo final."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not caminho.is_file():
        return None
    medicao = _executar(
        [ffmpeg, "-i", str(caminho), "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
        cwd=KIT_REMOTION,
        timeout=900,
    )
    medido = re.search(r"\bI:\s*(-?[\d.]+)\s*LUFS", medicao)
    return float(medido.group(1)) if medido else None


def _mixar_audio(
    voz: Path, destino: Path, trilha: Path | None, relatorio_longo: Path
) -> tuple[float | None, bool | None]:
    """Normaliza a mix do short em 48 kHz estéreo e mede o arquivo entregue."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg não está instalado ou não está no PATH.")
    volume_trilha_short = GANHO_TRILHA_SHORT
    entradas = ["-i", str(voz)]
    if trilha and trilha.is_file():
        if not _licenca_trilha_comercial(trilha):
            raise ValueError(
                "A trilha não tem ficha comercial vigente; o short não será renderizado."
            )
        entradas.extend(["-stream_loop", "-1", "-i", str(trilha)])
        grafo = (
            "[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[voz];"
            f"[1:a]volume={volume_trilha_short},"
            "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[musica];"
            "[musica][voz]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=350[duck];"
            "[voz][duck]amix=inputs=2:duration=first:normalize=0[mix]"
        )
    else:
        grafo = "[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[mix]"

    medicao = f"{grafo};[mix]loudnorm=I=-14:TP=-1:LRA=11:print_format=json[out]"
    primeira_passagem = [
        ffmpeg,
        "-hide_banner",
        "-nostats",
        *entradas,
        "-filter_complex",
        medicao,
        "-map",
        "[out]",
        "-f",
        "null",
        "-",
    ]
    medidas = exigir_medidas(
        extrair_medidas_loudnorm(_executar(primeira_passagem, cwd=KIT_REMOTION, timeout=900)),
        ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset"),
    )
    normalizacao = (
        "loudnorm=I=-14:TP=-1:LRA=11:linear=true:"
        f"measured_I={medidas['input_i']}:"
        f"measured_TP={medidas['input_tp']}:"
        f"measured_LRA={medidas['input_lra']}:"
        f"measured_thresh={medidas['input_thresh']}:"
        f"offset={medidas['target_offset']}:print_format=json"
    )
    saida = f"{grafo};[mix]{normalizacao}[out]"
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_name(f"{destino.stem}.tmp{destino.suffix}")
    comando = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-nostats",
        *entradas,
        "-filter_complex",
        saida,
        "-map",
        "[out]",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-c:a",
        "pcm_s16le",
        str(temporario),
    ]
    try:
        _executar(comando, cwd=KIT_REMOTION, timeout=900)
        if not temporario.is_file() or temporario.stat().st_size == 0:
            raise RuntimeError("FFmpeg não criou a mix esperada do short.")
        os.replace(temporario, destino)
    finally:
        temporario.unlink(missing_ok=True)

    lufs = _medir_lufs(destino)
    musica_mais_presente: bool | None = None
    if trilha and trilha.is_file() and relatorio_longo.is_file():
        relatorio = json.loads(relatorio_longo.read_text(encoding="utf-8"))
        ganho_longo = relatorio.get("ganho_trilha_sob_fala")
        if isinstance(ganho_longo, (int, float)) and not isinstance(ganho_longo, bool):
            musica_mais_presente = volume_trilha_short > float(ganho_longo)
        else:
            volume_longo = re.search(
                r"(0[.,]\d+)", str(relatorio.get("sidechain_ducking", ""))
            )
            if volume_longo:
                volume_referencia = float(volume_longo.group(1).replace(",", "."))
                musica_mais_presente = volume_trilha_short > volume_referencia
    return lufs, musica_mais_presente


def _renderizar(
    composicao: str, props: Path, public: Path, destino: Path, *, still: bool = False
) -> None:
    npm = shutil.which("npm") or shutil.which("npm.cmd") or "npm"
    if still:
        comando = [
            npm,
            "exec",
            "--offline",
            "--",
            "remotion",
            "still",
            "src/index.ts",
            composicao,
            str(destino),
            "--frame=1",
            f"--props={props}",
            f"--public-dir={public}",
        ]
    else:
        comando = [
            npm,
            "exec",
            "--offline",
            "--",
            "remotion",
            "render",
            "src/index.ts",
            composicao,
            str(destino),
            f"--props={props}",
            f"--public-dir={public}",
            "--concurrency=2",
            "--log=error",
        ]
    _executar(comando, cwd=KIT_REMOTION)
    if not destino.is_file():
        raise RuntimeError(f"O Remotion não criou {destino.name}.")


def _escrever_ponteiro_saida(pasta_saida: Path, resultado: ResultadoProducaoShort) -> None:
    raiz_short = pasta_saida.parent.parent
    atomic_write_json(
        raiz_short / "atual.json",
        {
            "revisao": resultado.revisao,
            "idioma": resultado.idioma,
            "video": resultado.caminho_video,
            "capa": resultado.caminho_capa,
            "legendas": resultado.caminho_legendas,
        },
    )


def produzir_short_derivado(
    projeto: Projeto, referencia: str, idioma_solicitado: str | None = None
) -> ResultadoProducaoShort:
    """Renderiza em staging isolado e publica uma revisão imutável do short derivado."""
    if not re.fullmatch(r"[a-f0-9]{24}", referencia):
        raise ValueError("Referência de short inválida.")
    opcoes, idioma_principal, motor_nome, voz_principal = _opcoes_projeto(projeto)
    idioma = idioma_solicitado or idioma_principal
    _rotulos_cta(idioma)
    voz = voz_principal
    pasta_aprovacao = projeto.pastas.montagem / "shorts" / "derivados" / referencia
    aprovacao, candidato, manifesto, aprovacao_id, manifesto_id = _carregar_aprovacao_manifesto(
        projeto, referencia
    )
    plano = Plano.model_validate_json(
        (projeto.pastas.plano / "plano.json").read_text(encoding="utf-8")
    )
    ativos = _ativos_resolvidos(projeto, plano)
    audio = projeto.pastas.audio / idioma_principal / "narracao_completa.wav"
    segmentos_path = projeto.pastas.audio / idioma_principal / "segmentos.json"
    palavras_path = projeto.pastas.audio / idioma_principal / "palavras.json"
    if not audio.is_file() or not segmentos_path.is_file():
        raise ValueError(f"Áudio e tempos narrados são necessários para {idioma}.")
    segmentos_principal = json.loads(segmentos_path.read_text(encoding="utf-8"))
    plano_path = projeto.pastas.plano / "plano.json"
    fonte_hash_atual = calcular_hash_dados(
        {
            "plano": calcular_hash_dados(plano_path),
            "segmentos": calcular_hash_dados(segmentos_path),
        }
    )
    if fonte_hash_atual != aprovacao.get("fonte_hash"):
        raise ValueError("O plano ou a narração mudou; atualize os candidatos e aprove novamente.")
    por_id = {str(item.get("id")): item for item in segmentos_principal}
    if any(sid not in por_id for sid in candidato.segmento_ids):
        raise ValueError("Os segmentos do candidato não correspondem mais à narração.")
    inicio = min(float(por_id[sid]["inicio_s"]) for sid in candidato.segmento_ids)
    fim = max(float(por_id[sid]["fim_s"]) for sid in candidato.segmento_ids)
    ponte = next(frase.texto for frase in candidato.frases_ponte if frase.aprovada)
    hashes_localizados: dict[str, str] = {}
    ponte_idioma_versao = aprovacao_id
    if idioma != idioma_principal:
        candidato_original = candidato
        candidato, manifesto, audio, segmentos_path, palavras_path, hashes_localizados = (
            _localizar_dados_short(projeto, idioma, candidato, plano, manifesto)
        )
        segmentos_localizados = json.loads(segmentos_path.read_text(encoding="utf-8"))
        por_id = {str(item.get("id")): item for item in segmentos_localizados}
        inicio, fim = candidato.inicio_s, candidato.fim_s
        ponte, ponte_idioma_versao = obter_ponte_idioma_aprovada(
            projeto, referencia, idioma, candidato_original
        )
        opcoes, _, motor_nome, voz = _opcoes_projeto(projeto, idioma)
        if not voz:
            raise ValueError(f"Configure uma voz TTS aprovada para o idioma {idioma}.")
    palavras = _palavras(palavras_path, set(candidato.segmento_ids), inicio, fim)
    incluir_ponte = not _trecho_ja_tem_cta_video(candidato.texto)
    trilha = _resolver_trilha_short(projeto)
    if trilha and not _licenca_trilha_comercial(trilha):
        raise ValueError("A trilha não tem ficha comercial vigente para uso no short.")

    fontes: dict[str, str] = {
        "audio": calcular_hash_dados(audio),
        "palavras": calcular_hash_dados(palavras_path),
        "fonte": str(aprovacao["fonte_hash"]),
        "trilha": calcular_hash_dados(trilha) if trilha and trilha.is_file() else "",
    }
    fontes.update(hashes_localizados)
    sidecar_trilha = _sidecar_trilha(trilha) if trilha else None
    if sidecar_trilha:
        fontes["trilha_licenca"] = calcular_hash_dados(sidecar_trilha)
    imagens: dict[str, tuple[Path, str]] = {}
    shot_por_id = {shot.id: shot for bloco in plano.blocos for shot in bloco.shots}
    for shot_v in manifesto.shots:
        shot = shot_por_id.get(shot_v.shot_id)
        if shot is None:
            raise ValueError(f"Shot {shot_v.shot_id} não existe mais no plano mestre.")
        if not shot_v.ativos:
            raise ValueError(f"Shot {shot_v.shot_id} ainda não tem imagem liberada para o short.")
        ativo_v = shot_v.ativos[0]
        ativo = ativos.get(ativo_v.ativo_id)
        if not ativo or not _licenca_comercial(ativo):
            raise ValueError(f"O ativo {ativo_v.ativo_id} não tem licença comercial vigente.")
        if ativo.caminho.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise ValueError(
                f"O ativo {ativo_v.ativo_id} não é uma imagem suportada para Remotion."
            )
        hash_imagem = calcular_hash_dados(ativo.caminho)
        if hash_imagem != ativo_v.hash_origem:
            raise ValueError(
                f"O ativo {ativo_v.ativo_id} mudou; gere novamente o manifesto vertical."
            )
        fontes[ativo_v.ativo_id] = hash_imagem
        sidecar = caminho_sidecar_licenca(ativo.caminho)
        fontes[f"licenca:{ativo_v.ativo_id}"] = (
            calcular_hash_dados(sidecar)
            if sidecar.is_file()
            else calcular_hash_dados(ativo.licenca or {})
        )
        imagens[shot_v.shot_id] = (ativo.caminho, hash_imagem)

    motor_id = {
        "motor": motor_nome,
        "voz": voz,
        "idioma": idioma,
        "velocidade": 1.0,
        "configuracao": opcoes.get("tts", {}),
    }
    hash_ponte = calcular_hash_dados({"texto": ponte, "tts": motor_id})
    revisao = calcular_hash_dados(
        {
            "fonte": fontes,
            "aprovacao": aprovacao_id,
            "aprovacao_ponte_idioma": ponte_idioma_versao,
            "manifesto": manifesto_id,
            "tts": motor_id,
            "candidato": candidato.model_dump(mode="json"),
            "mix": {
                "ganho_trilha": GANHO_TRILHA_SHORT,
                "incluir_ponte": incluir_ponte,
            },
        }
    )
    ordenados = pontuar_candidatos_do_plano(plano, segmentos_principal, limite=5)
    try:
        indice_short = next(
            indice for indice, item in enumerate(ordenados, start=1) if item.id == candidato.id
        )
    except StopIteration as exc:
        raise ValueError("O candidato aprovado não consta mais na lista atual.") from exc
    slug_trecho = slugificar(candidato.texto[:54])[:48]
    pasta_saida = (
        projeto.pastas.saida
        / idioma
        / "shorts"
        / f"S{indice_short:02d}-{slug_trecho}"
        / "revisoes"
        / revisao
    )
    registro = pasta_saida / "short.json"
    if registro.is_file():
        dados = json.loads(registro.read_text(encoding="utf-8"))
        cached = ResultadoProducaoShort.model_validate({**dados["resultado"], "cache": True})
        if all(
            Path(item).is_file()
            for item in (cached.caminho_video, cached.caminho_capa, cached.caminho_legendas)
        ):
            return cached
        raise RuntimeError(
            "A revisão em cache está incompleta; preserve-a e verifique a pasta de saída."
        )

    bridge_path = pasta_aprovacao / "cache" / f"ponte-{hash_ponte}.wav"
    if incluir_ponte and not bridge_path.is_file():
        orquestrador = _criar_orquestrador(motor_tts=motor_nome, projeto=projeto)
        if not orquestrador.tts.disponivel():
            raise RuntimeError(
                f"O motor de narração configurado ({motor_nome}) não está disponível."
            )
        bridge_path.parent.mkdir(parents=True, exist_ok=True)
        modelo_gpu = motor_nome if motor_nome in {"kokoro", "chatterbox", "voicestudio"} else None
        with tempfile.TemporaryDirectory(
            prefix=f"ponte-{hash_ponte[:8]}-", dir=bridge_path.parent
        ) as pasta_temporaria:
            with semaforo_gpu.adquirir_sync(
                modelo=modelo_gpu,
                tarefa=f"M8 ponte de short {referencia[:8]} ({idioma})",
                projeto=projeto.slug,
            ):
                orquestrador.processar_segmento(
                    SegmentoProcessado(id="ponte-short", texto_original=ponte, texto_limpo=ponte),
                    Path(pasta_temporaria),
                    idioma=idioma,
                    voz=voz or None,
                )
            gerado = Path(pasta_temporaria) / "ponte-short.wav"
            if not gerado.is_file():
                raise RuntimeError("O TTS não gerou o áudio da frase-ponte.")
            gerado.replace(bridge_path)

    pasta_saida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="short-render-", dir=pasta_saida.parent) as temp_dir:
        work = Path(temp_dir)
        public = work / "public"
        (public / "ativos").mkdir(parents=True)
        for shot_id, (origem, _) in imagens.items():
            destino = public / "ativos" / f"{slugificar(shot_id)}{origem.suffix.lower()}"
            shutil.copy2(origem, destino)
        trim = work / "trecho.wav"
        concat = work / "voz.wav"
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("FFmpeg não está instalado ou não está no PATH.")
        _executar(
            [
                ffmpeg,
                "-y",
                "-ss",
                f"{inicio:.3f}",
                "-i",
                str(audio),
                "-t",
                f"{fim - inicio:.3f}",
                "-c:a",
                "pcm_s16le",
                str(trim),
            ],
            cwd=KIT_REMOTION,
            timeout=900,
        )
        if incluir_ponte:
            _executar(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(trim),
                    "-i",
                    str(bridge_path),
                    "-filter_complex",
                    "[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a0];"
                    "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a1];"
                    "[a0][a1]concat=n=2:v=0:a=1[out]",
                    "-map",
                    "[out]",
                    "-c:a",
                    "pcm_s16le",
                    str(concat),
                ],
                cwd=KIT_REMOTION,
                timeout=900,
            )
        else:
            shutil.copy2(trim, concat)
        voz_mix = public / "audio.wav"
        loudness, musica_mais_presente = _mixar_audio(
            concat,
            voz_mix,
            trilha,
            projeto.pastas.audio / idioma / "relatorio_mix.json",
        )

        duracao_base = fim - inicio
        duracao_ponte = _duracao_wav(bridge_path) if incluir_ponte else 0.0
        duracao_total = duracao_base + duracao_ponte
        if not 15 <= duracao_total <= 60:
            raise ValueError(
                "A ponte aprovada deixa o short fora da faixa de 15 a 60 segundos. "
                "Edite a ponte e gere novo manifesto."
            )
        hook = " ".join(candidato.texto.split()[:6])
        cenas: list[CenaRenderShort] = []
        primeira = next((shot for shot in manifesto.shots if shot.fim_s > inicio), None)
        if primeira is None:
            raise ValueError("O manifesto vertical não contém cenas dentro do trecho.")
        primeira_origem, _ = imagens[primeira.shot_id]
        primeiro_recorte = primeira.ativos[0].recorte
        cenas.append(
            CenaRenderShort(
                id="gancho",
                inicio_frame=0,
                duracao_frames=min(FPS * 2, round(duracao_base * FPS)),
                props=PropsCenaShort(
                    variante="V01",
                    titulo=hook,
                    imagem=f"ativos/{slugificar(primeira.shot_id)}{primeira_origem.suffix.lower()}",
                    foco_x=min(0.98, max(0.02, primeiro_recorte.x + primeiro_recorte.largura / 2)),
                    foco_y=min(0.98, max(0.02, primeiro_recorte.y + primeiro_recorte.altura / 2)),
                    usar_fundo_desfocado=primeiro_recorte.usar_fundo_desfocado,
                    legendas=_captions_remotion(palavras, 0, min(2.0, duracao_base)),
                ),
            )
        )
        for shot_v in manifesto.shots:
            a = max(2.0, shot_v.inicio_s - inicio)
            b = min(duracao_base, shot_v.fim_s - inicio)
            if b <= a:
                continue
            origem, _ = imagens[shot_v.shot_id]
            img_rel = f"ativos/{slugificar(shot_v.shot_id)}{origem.suffix.lower()}"
            foco_x = 0.5
            foco_y = 0.5
            recorte = next(item.recorte for item in shot_v.ativos if item.ativo_id in ativos)
            foco_x = min(0.98, max(0.02, recorte.x + recorte.largura / 2))
            foco_y = min(0.98, max(0.02, recorte.y + recorte.altura / 2))
            cursor = a
            parte = 0
            while cursor < b:
                fim_cena = min(b, cursor + 2.5)
                duracao_frames = max(1, round((fim_cena - cursor) * FPS))
                palavras_cena = _captions_remotion(palavras, cursor, fim_cena)
                cena_props = PropsCenaShort(
                    variante="V02",
                    imagem=img_rel,
                    foco_x=foco_x,
                    foco_y=foco_y,
                    usar_fundo_desfocado=recorte.usar_fundo_desfocado,
                    legendas=palavras_cena,
                )
                cenas.append(
                    CenaRenderShort(
                        id=f"{shot_v.shot_id}-{parte}",
                        inicio_frame=round(cursor * FPS),
                        duracao_frames=duracao_frames,
                        props=cena_props,
                    )
                )
                cursor = fim_cena
                parte += 1
        if incluir_ponte:
            palavras_ponte = ponte.split()
            for idx, palavra in enumerate(palavras_ponte):
                a = duracao_base + duracao_ponte * idx / len(palavras_ponte)
                b = duracao_base + duracao_ponte * (idx + 1) / len(palavras_ponte)
                palavras.append({"text": palavra, "start": a, "end": b})
        bridge_captions = (
            _captions_remotion(palavras, duracao_base, duracao_total) if incluir_ponte else []
        )
        texto_completo, texto_assista = _rotulos_cta(idioma)
        if incluir_ponte:
            cenas.append(
                CenaRenderShort(
                    id="cta",
                    inicio_frame=round(duracao_base * FPS),
                    duracao_frames=max(1, round(duracao_ponte * FPS)),
                    props=PropsCenaShort(
                        variante="V07",
                        titulo=texto_completo,
                        cta=texto_assista,
                        legendas=bridge_captions,
                    ),
                )
            )
        duracao_frames = max(1, round(duracao_total * FPS))
        props = PropsRenderShort(duracao_frames=duracao_frames, audio="audio.wav", cenas=cenas)
        props_path = work / "props.json"
        atomic_write_json(props_path, props.model_dump(mode="json", by_alias=True))
        video_tmp = work / "video.mp4"
        capa_tmp = work / "capa.jpg"
        _renderizar("Short-Derivado", props_path, public, video_tmp)
        _renderizar("Short-Derivado", props_path, public, capa_tmp, still=True)

        captions_path = work / "legendas.srt"
        atomic_write_text(captions_path, _srt(palavras))
        elementos = [
            ElementoTelaShort(id="gancho", x=0.08, y=0.18, largura=0.78, altura=0.35, texto=hook),
            ElementoTelaShort(id="legenda", x=0.08, y=0.67, largura=0.78, altura=0.06),
        ]
        if incluir_ponte:
            elementos.append(
                ElementoTelaShort(
                    id="cta", x=0.08, y=0.2, largura=0.78, altura=0.4, texto=texto_completo
                )
            )
        intervalos = _intervalos_legenda(palavras)
        verificacao = verificar_short(
            ShortParaVerificar(
                duracao_s=duracao_total,
                duracao_alvo_s=duracao_total,
                inicio_gancho_visual_s=0,
                inicio_gancho_textual_s=0,
                inicio_gancho_falado_s=palavras[0]["start"],
                mudancas_visuais_s=[
                    cena.inicio_frame / FPS for cena in cenas if cena.inicio_frame > 0
                ],
                elementos=elementos,
                legendas=intervalos,
                textos_tela=[hook, texto_completo, texto_assista],
                quantidade_ctas_principais=1,
                derivado=True,
                frase_ponte_aprovada=True,
                video_longo_id=projeto.slug,
                audio_lufs_integrado=loudness,
                musica_mais_presente_que_longo=musica_mais_presente,
                # O ducking está ativo, mas ainda não há medição objetiva de mascaramento.
                musica_cobre_voz=None,
            )
        )
        ativos_metadados: dict[str, Any] = {}
        for shot_v in manifesto.shots:
            ativo_id = shot_v.ativos[0].ativo_id
            ativo = ativos[ativo_id]
            ficha = carregar_ficha_licenca(ativo.caminho)
            ativos_metadados[ativo_id] = {
                "hash": imagens[shot_v.shot_id][1],
                "descricao": ativo.descricao,
                "licenca": ficha.model_dump(mode="json") if ficha else ativo.licenca,
            }
        opcoes_metadados = _metadados(
            projeto, candidato, ponte if incluir_ponte else "", idioma
        )
        metadados_dir = work / "metadados"
        metadados_dir.mkdir()
        atomic_write_json(
            metadados_dir / "metadados.json",
            {
                **opcoes_metadados,
                "revisao": revisao,
                "ativos": ativos_metadados,
                "qa_aprovado": verificacao.aprovado,
                "falhas_qa": [item.regra for item in verificacao.violacoes if not item.aprovada],
            },
        )
        for nome, texto in opcoes_metadados["arquivos"].items():
            atomic_write_text(metadados_dir / nome, texto)
        pasta_saida.parent.mkdir(parents=True, exist_ok=True)
        resultado = ResultadoProducaoShort(
            status="concluido",
            idioma=idioma,
            revisao=revisao,
            caminho_video=str(pasta_saida / "video.mp4"),
            caminho_capa=str(pasta_saida / "capa.jpg"),
            caminho_legendas=str(pasta_saida / "legendas.srt"),
            duracao_s=duracao_total,
            qa_aprovado=verificacao.aprovado,
            falhas_qa=[item.regra for item in verificacao.violacoes if not item.aprovada],
        )
        atomic_write_json(work / "short.json", {"resultado": resultado.model_dump(mode="json")})
        shutil.rmtree(public)
        for temporario in (props_path, trim, concat):
            temporario.unlink(missing_ok=True)
        work.rename(pasta_saida)
        _escrever_ponteiro_saida(pasta_saida, resultado)
    return resultado


def _duracao_wav(caminho: Path) -> float:
    import wave

    with wave.open(str(caminho), "rb") as wav:
        return wav.getnframes() / wav.getframerate()


def _rotulos_cta(idioma: str) -> tuple[str, str]:
    base = idioma.split("-", maxsplit=1)[0].lower()
    rotulos = {
        "pt": ("VÍDEO COMPLETO", "ASSISTA"),
        "en": ("FULL VIDEO", "WATCH"),
        "es": ("VIDEO COMPLETO", "VER"),
    }.get(base)
    if not rotulos:
        raise ValueError(f"Os textos de CTA para {idioma} ainda não estão localizados.")
    return rotulos


def _trecho_ja_tem_cta_video(texto: str) -> bool:
    """Detecta convite explícito ao vídeo completo no fecho do trecho narrado."""
    normalizado = unicodedata.normalize("NFKD", texto.lower())
    normalizado = "".join(char for char in normalizado if not unicodedata.combining(char))
    final = " ".join(normalizado.split())[-140:].rstrip(" .,!?:;—-")
    return any(
        convite in final
        for convite in (
            "video completo",
            "assista ao video",
            "veja o video",
            "watch the full video",
            "mira el video completo",
        )
    )


def _metadados(
    projeto: Projeto,
    candidato: CandidatoShort,
    ponte: str,
    idioma: str,
) -> dict[str, Any]:
    opcoes = projeto.obter_opcoes()
    idioma_base = idioma.split("-", maxsplit=1)[0].lower()
    textos_por_idioma = {
        "pt": {
            "video_completo": "Vídeo completo",
            "instruir_relacionado": "vincular como vídeo relacionado",
            "relacionado": "Vídeo relacionado: selecione o vídeo longo na plataforma.",
            "alt": "Texto alternativo",
            "capa": "Capa sugerida",
            "comentario": "Assista ao vídeo completo",
            "placeholder_link": "adicionar link",
            "titulo": "Título",
            "descricao": "Descrição",
            "titulos_header": "# Títulos sugeridos (máximo 40 caracteres)",
            "legenda_palavra": "com legendas palavra a palavra",
            "hashtags_ig": "#Shorts #Reels #Documentario #VideoCurto #DocForja",
            "hashtags_yt": "#Shorts #Documentario #VideoCurto",
        },
        "en": {
            "video_completo": "Full video",
            "instruir_relacionado": "Link as the related video",
            "relacionado": "Related video: select the full-length video on the platform.",
            "alt": "Alt text",
            "capa": "Suggested cover",
            "comentario": "Watch the full video",
            "placeholder_link": "add link",
            "titulo": "Title",
            "descricao": "Description",
            "titulos_header": "# Suggested titles (maximum 40 characters)",
            "legenda_palavra": "with word-by-word captions",
            "hashtags_ig": "#Shorts #Reels #Documentary #ShortVideo #DocForja",
            "hashtags_yt": "#Shorts #Documentary #ShortVideo",
        },
        "es": {
            "video_completo": "Video completo",
            "instruir_relacionado": "vincular como video relacionado",
            "relacionado": "Video relacionado: selecciona el video largo en la plataforma.",
            "alt": "Texto alternativo",
            "capa": "Portada sugerida",
            "comentario": "Mira el video completo",
            "placeholder_link": "añade el enlace",
            "titulo": "Título",
            "descricao": "Descripción",
            "titulos_header": "# Títulos sugeridos (máximo 40 caracteres)",
            "legenda_palavra": "con subtítulos palabra por palabra",
            "hashtags_ig": "#Shorts #Reels #Documental #VideoCorto #DocForja",
            "hashtags_yt": "#Shorts #Documental #VideoCorto",
        },
    }
    textos = textos_por_idioma.get(idioma_base)
    if not textos:
        raise ValueError(f"Os metadados de Shorts para {idioma} ainda não estão localizados.")
    titulo_longo = str(opcoes.get("nome", projeto.slug))
    hook = " ".join(candidato.texto.split()[:7])
    titulos: list[str] = []
    palavras = candidato.texto.split()
    for inicio in range(min(6, len(palavras))):
        for limite in range(min(10, len(palavras) - inicio), 2, -1):
            titulo = " ".join(palavras[inicio : inicio + limite]).rstrip(".,;:!?—- ")
            if titulo and len(titulo) <= 40 and titulo not in titulos:
                titulos.append(titulo)
            if len(titulos) == 8:
                break
        if len(titulos) == 8:
            break
    descricao = (
        f"{candidato.texto.strip()}\n\n{textos['video_completo']}: {titulo_longo}. "
        f"({textos['instruir_relacionado']})."
    )
    alt = {
        "pt": f"Vídeo vertical com narração: {candidato.texto.strip()}.",
        "en": f"Vertical video with narration: {candidato.texto.strip()}.",
        "es": f"Video vertical con narración: {candidato.texto.strip()}.",
    }[idioma_base]
    texto_ponte = f"\n\n{ponte}" if ponte else ""
    instagram = (
        f"{hook}{texto_ponte}\n\n{textos['hashtags_ig']}\n\n"
        f"{textos['alt']}: {alt} {textos['legenda_palavra']}."
    )
    youtube = (
        f"{textos['titulo']}: {titulos[0] if titulos else titulo_longo[:40]}\n\n"
        f"{textos['descricao']}:\n{descricao}\n\n"
        f"{textos['relacionado']}"
    )
    instagram += f"\n{textos['capa']}: capa.jpg."
    youtube += f"\n\n{textos['hashtags_yt']}"
    return {
        "projeto": projeto.slug,
        "titulo_longo": titulo_longo,
        "idioma": idioma,
        "gancho": hook,
        "frase_ponte": ponte,
        "video_relacionado": projeto.slug,
        "requer_vinculo_manual": True,
        "arquivos": {
            "titulos.md": f"{textos['titulos_header']}\n\n"
            + "\n".join(f"{idx}. {titulo}" for idx, titulo in enumerate(titulos, 1))
            + "\n",
            "youtube.md": youtube + "\n",
            "instagram.md": instagram + "\n",
            "comentario_fixado.md": (
                f"{textos['comentario']}: [{textos['placeholder_link']}: {titulo_longo}]\n"
            ),
        },
    }


def executar_producao_background(
    projeto: Projeto, referencia: str, idioma_solicitado: str | None = None
) -> None:
    """Registra a conclusão/falha para consulta assíncrona pela interface."""
    pasta = projeto.pastas.montagem / "shorts" / "derivados" / referencia
    principal = str(projeto.obter_opcoes().get("idiomas", {}).get("principal", "pt-BR"))
    idioma = idioma_solicitado or principal
    estado = pasta / ("producao_atual.json" if idioma == principal else f"producao-{idioma}.json")
    solicitado = json.loads(estado.read_text(encoding="utf-8"))
    aprovado = json.loads((pasta / "aprovacao_atual.json").read_text(encoding="utf-8"))
    manifesto = json.loads((pasta / "manifesto_atual.json").read_text(encoding="utf-8"))
    versoes = {
        "fonte_hash": solicitado.get("fonte_hash"),
        "aprovacao_versao": solicitado.get("aprovacao_versao"),
        "manifesto_versao": solicitado.get("manifesto_versao"),
        "idioma": idioma,
    }
    if solicitado.get("idioma", idioma) != idioma:
        atomic_write_json(
            estado,
            {"status": "falhou", "erro": "O idioma do pedido mudou; atualize a tela.", **versoes},
        )
        return
    if idioma != principal:
        versoes["aprovacao_ponte_idioma"] = solicitado.get("aprovacao_ponte_idioma")
    if (
        aprovado.get("fonte_hash") != versoes["fonte_hash"]
        or aprovado.get("versao") != versoes["aprovacao_versao"]
        or manifesto.get("fonte_hash") != versoes["fonte_hash"]
        or manifesto.get("versao") != versoes["manifesto_versao"]
    ):
        atomic_write_json(
            estado,
            {
                "status": "falhou",
                "erro": "A aprovação mudou antes do início; atualize a tela.",
                **versoes,
            },
        )
        return
    if idioma != principal:
        try:
            aprovacao_path = pasta / f"aprovacao-{versoes['aprovacao_versao']}.json"
            candidato = CandidatoShort.model_validate(
                json.loads(aprovacao_path.read_text(encoding="utf-8"))["candidato"]
            )
            _, ponte_versao = obter_ponte_idioma_aprovada(projeto, referencia, idioma, candidato)
        except (OSError, ValueError, KeyError, TypeError):
            ponte_versao = None
        if ponte_versao != versoes["aprovacao_ponte_idioma"]:
            atomic_write_json(
                estado,
                {
                    "status": "falhou",
                    "erro": "A frase-ponte localizada mudou antes do início; atualize a tela.",
                    **versoes,
                },
            )
            return
    atomic_write_json(estado, {"status": "executando", "referencia": referencia, **versoes})
    try:
        resultado = produzir_short_derivado(
            projeto, referencia, None if idioma == principal else idioma
        )
        atomic_write_json(
            estado,
            {"status": "concluido", "resultado": resultado.model_dump(mode="json"), **versoes},
        )
    except Exception as exc:
        atomic_write_json(estado, {"status": "falhou", "erro": str(exc)[:1000], **versoes})


__all__ = [
    "ResultadoProducaoShort",
    "aprovar_ponte_short_idioma",
    "executar_producao_background",
    "obter_ponte_idioma_aprovada",
    "produzir_short_derivado",
]
