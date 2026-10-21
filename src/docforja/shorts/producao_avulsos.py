"""Rascunhos verticais educativos a partir de campanhas avulsas aprovadas."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from docforja.io import atomic_write_json, atomic_write_text
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.nucleo.gpu import semaforo_gpu
from docforja.nucleo.handlers import _criar_orquestrador
from docforja.planejamento.entidades import SegmentoProcessado
from docforja.planejamento.previa import KIT_REMOTION
from docforja.shorts.alegacoes_avulsas import documentacao_vigente, obter_documentacao
from docforja.shorts.campanhas import obter_aprovacao_roteiro, obter_campanha
from docforja.shorts.midias_avulsas import (
    obter_selecao_midias,
    resolver_imagem_global,
    selecao_vigente,
)
from docforja.shorts.modelos import (
    ElementoTelaShort,
    ShortParaVerificar,
)
from docforja.shorts.producao import (
    FPS,
    CenaRenderShort,
    PropsCenaShort,
    PropsRenderShort,
    _captions_remotion,
    _intervalos_legenda,
    _medir_lufs,
    _mixar_audio,
    _palavras,
    _renderizar,
    _srt,
)
from docforja.shorts.verificador import verificar_short

MODELOS_CONFIG = Path(__file__).resolve().parents[3] / "config" / "modelos.yaml"
ARTEFATOS = {
    "video.mp4", "capa.jpg", "legendas.srt", "metadados.json",
    "youtube.md", "instagram.md",
}


class PreparacaoAvulsa(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    campanha_id: str
    pedido_id: str
    hash_campanha: str
    revisao_roteiro: str
    revisao_midias: str
    revisao_alegacoes: str
    revisao: str
    texto: str
    tema: str
    cta: str
    duracao_alvo_s: int
    ids_imagens: list[str]
    voz: str


def _voz_ptbr() -> str:
    catalogo = yaml.safe_load(MODELOS_CONFIG.read_text(encoding="utf-8"))
    for candidato in catalogo["tts"]["candidatos"]:
        if candidato.get("adaptador") != "kokoro":
            continue
        for voz in candidato.get("benchmark", {}).get("voices", []):
            if voz.get("language") == "pt-BR" and Path(voz.get("path", "")).is_file():
                return str(voz["id"])
    raise ValueError("Nenhuma voz Kokoro pt-BR instalada no catálogo.")


def _pasta_saida(raiz_projetos: Path, campanha_id: str, pedido_id: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{24}", campanha_id) or not re.fullmatch(
        r"A[0-9]{3,}", pedido_id
    ):
        raise ValueError("Identificador de short avulso inválido.")
    return raiz_projetos / "_campanhas_avulsas" / campanha_id / "saidas" / pedido_id


def preparar_producao(
    raiz_projetos: Path, raiz_global: Path, campanha_id: str, pedido_id: str
) -> PreparacaoAvulsa:
    """Recusa entrada obsoleta e conteúdo comercial ainda sem template/prova verificada."""
    campanha = obter_campanha(raiz_projetos, campanha_id)
    pedido = next((item for item in campanha.pedidos if item.id == pedido_id), None)
    if pedido is None:
        raise ValueError("Pedido não pertence à campanha.")
    aprovacao = obter_aprovacao_roteiro(raiz_projetos, campanha_id, pedido_id)
    selecao = obter_selecao_midias(raiz_projetos, campanha_id, pedido_id)
    documentacao = obter_documentacao(raiz_projetos, campanha_id, pedido_id)
    if aprovacao is None or aprovacao.hash_campanha != campanha.hash_conteudo:
        raise ValueError("Aprove o roteiro atual antes de produzir.")
    if selecao is None or not selecao_vigente(raiz_global, selecao, aprovacao.revisao):
        raise ValueError("Confirme novamente as imagens e suas licenças.")
    if documentacao is None or not documentacao_vigente(
        documentacao, aprovacao.revisao, selecao.revisao
    ):
        raise ValueError("Registre a ficha de alegações para as revisões atuais.")
    if pedido.objetivo != "educativo" or documentacao.dados.relacao_comercial != "nenhuma":
        raise ValueError(
            "Esta primeira produção aceita apenas avulsos educativos sem relação comercial."
        )
    cta = " ".join((pedido.cta or "").split())
    texto = " ".join(aprovacao.texto.split())
    if not cta or len(cta.split()) > 6 or len(re.findall(re.escape(cta), texto, re.I)) != 1:
        raise ValueError(
            "Informe um CTA de até seis palavras que apareça uma vez no roteiro aprovado."
        )
    voz = _voz_ptbr()
    fontes = {
        "campanha": campanha.hash_conteudo,
        "roteiro": aprovacao.revisao,
        "midias": selecao.revisao,
        "alegacoes": documentacao.revisao,
        "voz": voz,
        "catalogo_tts": calcular_hash_dados(MODELOS_CONFIG),
        "producao": calcular_hash_dados(Path(__file__)),
        "templates": calcular_hash_dados(
            KIT_REMOTION / "src" / "composicoes" / "ShortVertical.tsx"
        ),
        "timeline": calcular_hash_dados(
            KIT_REMOTION / "src" / "composicoes" / "ShortTimeline.tsx"
        ),
    }
    return PreparacaoAvulsa(
        campanha_id=campanha_id,
        pedido_id=pedido_id,
        hash_campanha=campanha.hash_conteudo,
        revisao_roteiro=aprovacao.revisao,
        revisao_midias=selecao.revisao,
        revisao_alegacoes=documentacao.revisao,
        revisao=calcular_hash_dados(fontes),
        texto=texto,
        tema=pedido.tema,
        cta=cta,
        duracao_alvo_s=pedido.duracao_s,
        ids_imagens=[item.id_global for item in selecao.midias],
        voz=voz,
    )


def obter_estado(raiz_projetos: Path, campanha_id: str, pedido_id: str) -> dict[str, Any]:
    caminho = _pasta_saida(raiz_projetos, campanha_id, pedido_id) / "producao_atual.json"
    if not caminho.is_file():
        return {"status": "nao_iniciada"}
    return json.loads(caminho.read_text(encoding="utf-8"))


def obter_artefato(
    raiz_projetos: Path, raiz_global: Path, campanha_id: str, pedido_id: str, nome: str
) -> Path:
    if nome not in ARTEFATOS:
        raise ValueError("Artefato não permitido.")
    estado = obter_estado(raiz_projetos, campanha_id, pedido_id)
    revisao = estado.get("revisao")
    if estado.get("status") != "concluido" or not isinstance(revisao, str):
        raise FileNotFoundError("Não há rascunho concluído.")
    if not re.fullmatch(r"[a-f0-9]{64}", revisao):
        raise ValueError("Revisão inválida.")
    if preparar_producao(raiz_projetos, raiz_global, campanha_id, pedido_id).revisao != revisao:
        raise FileNotFoundError("Rascunho desatualizado; confirme novamente as aprovações.")
    arquivo = _pasta_saida(raiz_projetos, campanha_id, pedido_id) / "revisoes" / revisao / nome
    if not arquivo.is_file():
        raise FileNotFoundError("Artefato não encontrado.")
    return arquivo


def _gancho(texto: str) -> str:
    """Usa a primeira frase completa quando cabe em seis palavras."""
    primeira = re.split(r"(?<=[.!?…])\s+", texto.strip(), maxsplit=1)[0]
    if len(primeira.split()) <= 6:
        return primeira.rstrip(".,;:!?—- ")
    return " ".join(texto.split()[:6]).rstrip(".,;:!?—- ")


def _criar_cenas(
    preparacao: PreparacaoAvulsa, palavras: list[dict[str, Any]], imagens: list[str], duracao: float
) -> list[CenaRenderShort]:
    frames = max(1, round(duracao * FPS))
    hook = _gancho(preparacao.texto)
    cenas: list[CenaRenderShort] = []
    inicio = 0
    numero = 0
    while inicio < frames:
        fim = min(frames, inicio + (2 * FPS if inicio == 0 else 75))
        a, b = inicio / FPS, fim / FPS
        cenas.append(CenaRenderShort(
            id=f"cena-{numero:03d}",
            inicio_frame=inicio,
            duracao_frames=fim - inicio,
            props=PropsCenaShort(
                variante="V01" if numero == 0 else "V02",
                titulo=hook if numero == 0 else "",
                imagem=imagens[numero % len(imagens)],
                legendas=_captions_remotion(palavras, a, b),
            ),
        ))
        inicio = fim
        numero += 1
    return cenas


def produzir_avulso(
    raiz_projetos: Path, raiz_global: Path, preparacao: PreparacaoAvulsa
) -> dict[str, Any]:
    pasta = _pasta_saida(raiz_projetos, preparacao.campanha_id, preparacao.pedido_id)
    saida = pasta / "revisoes" / preparacao.revisao
    if saida.is_dir() and all((saida / nome).is_file() for nome in ARTEFATOS):
        return {"status": "concluido", "revisao": preparacao.revisao, "cache": True}
    if saida.exists():
        raise RuntimeError("Revisão incompleta existente; nada será sobrescrito.")
    orquestrador = _criar_orquestrador("kokoro")
    if not orquestrador.tts.disponivel() or not orquestrador.alinhador.disponivel():
        raise RuntimeError("Kokoro e WhisperX locais são necessários para legendas verificadas.")
    saida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="avulso-", dir=saida.parent) as temporario:
        work = Path(temporario)
        public = work / "public"
        ativos = public / "ativos"
        ativos.mkdir(parents=True)
        imagens = []
        for indice, id_global in enumerate(preparacao.ids_imagens):
            origem, _ = resolver_imagem_global(raiz_global, id_global)
            destino = ativos / f"imagem-{indice:02d}{origem.suffix.lower()}"
            shutil.copy2(origem, destino)
            imagens.append(f"ativos/{destino.name}")
        segmento = SegmentoProcessado(
            id="avulso", texto_original=preparacao.texto, texto_limpo=preparacao.texto
        )
        with semaforo_gpu.adquirir_sync(
            modelo="kokoro", tarefa=f"M8 avulso {preparacao.pedido_id}",
            projeto=preparacao.campanha_id,
        ):
            narracao = orquestrador.processar_projeto_completo(
                [segmento], work / "audio", idioma="pt-BR", voz=preparacao.voz,
                gerar_timestamps_estimados=False,
            )
        if narracao.wer_medio is None or narracao.wer_medio > 0.02:
            raise ValueError("A narração divergiu do roteiro; revise antes de renderizar.")
        duracao = narracao.duracao_total_s
        palavras = _palavras(narracao.arquivo_palavras_json, {"avulso"}, 0, duracao)
        loudness, _ = _mixar_audio(
            narracao.arquivo_completo_wav, public / "audio.wav", None,
            work / "sem_relatorio_longo.json",
        )
        cenas = _criar_cenas(preparacao, palavras, imagens, duracao)
        props = PropsRenderShort(
            duracao_frames=max(1, round(duracao * FPS)), audio="audio.wav", cenas=cenas
        )
        props_path = work / "props.json"
        atomic_write_json(props_path, props.model_dump(mode="json"))
        _renderizar("Short-Derivado", props_path, public, work / "video.mp4")
        _renderizar("Short-Derivado", props_path, public, work / "capa.jpg", still=True)
        atomic_write_text(work / "legendas.srt", _srt(palavras))
        hook = _gancho(preparacao.texto)
        loudness_entregue = _medir_lufs(work / "video.mp4")
        qa = verificar_short(ShortParaVerificar(
            duracao_s=duracao,
            duracao_alvo_s=float(preparacao.duracao_alvo_s),
            inicio_gancho_visual_s=0,
            inicio_gancho_textual_s=0,
            inicio_gancho_falado_s=float(palavras[0]["start"]),
            mudancas_visuais_s=[c.inicio_frame / FPS for c in cenas[1:]],
            elementos=[
                ElementoTelaShort(id="gancho", x=0.08, y=0.18, largura=0.78, altura=0.35),
                ElementoTelaShort(id="legenda", x=0.08, y=0.67, largura=0.78, altura=0.06),
            ],
            legendas=_intervalos_legenda(palavras),
            textos_tela=[hook],
            quantidade_ctas_principais=len(
                re.findall(re.escape(preparacao.cta), preparacao.texto, re.I)
            ),
            audio_lufs_integrado=loudness_entregue if loudness_entregue is not None else loudness,
            musica_cobre_voz=False,
        ))
        selecao = obter_selecao_midias(
            raiz_projetos, preparacao.campanha_id, preparacao.pedido_id
        )
        assert selecao is not None
        metadados = {
            "status": "rascunho", "publicacao_autorizada": False,
            "motivo_publicacao_bloqueada": (
                "Alegações sem verificação externa e revisão humana final pendente."
            ),
            "campanha_id": preparacao.campanha_id,
            "pedido_id": preparacao.pedido_id,
            "revisao": preparacao.revisao,
            "tema": preparacao.tema,
            "cta": preparacao.cta,
            "duracao_s": duracao,
            "wer": narracao.wer_medio,
            "qa": qa.model_dump(mode="json"),
            "creditos_imagens": [
                {"id": item.id_global, "credito": item.credito, "licenca": item.licenca}
                for item in selecao.midias
            ],
            "fontes": {
                "roteiro": preparacao.revisao_roteiro,
                "midias": preparacao.revisao_midias,
                "alegacoes": preparacao.revisao_alegacoes,
            },
        }
        atomic_write_json(work / "metadados.json", metadados)
        titulo = preparacao.tema.strip()[:40]
        atomic_write_text(
            work / "youtube.md",
            f"# {titulo}\n\n{preparacao.texto}\n\n#Shorts #DocForja\n"
            "\nRASCUNHO — não publicar sem revisão factual, visual, sonora e do QA.\n",
        )
        atomic_write_text(
            work / "instagram.md",
            f"{preparacao.tema}\n\n{preparacao.texto}\n\n#Reels #DocForja\n"
            "\nRASCUNHO — não publicar sem revisão factual, visual, sonora e do QA.\n",
        )
        atual = preparar_producao(
            raiz_projetos, raiz_global, preparacao.campanha_id, preparacao.pedido_id
        )
        if atual != preparacao:
            raise ValueError("As aprovações mudaram durante o render; descarte o rascunho.")
        for auxiliar in (public, work / "audio"):
            shutil.rmtree(auxiliar)
        props_path.unlink()
        work.rename(saida)
    return {"status": "concluido", "revisao": preparacao.revisao, "cache": False}


def executar_producao_background(
    raiz_projetos: Path, raiz_global: Path, preparacao: PreparacaoAvulsa
) -> None:
    estado = _pasta_saida(
        raiz_projetos, preparacao.campanha_id, preparacao.pedido_id
    ) / "producao_atual.json"
    try:
        if preparar_producao(
            raiz_projetos, raiz_global, preparacao.campanha_id, preparacao.pedido_id
        ) != preparacao:
            raise ValueError("As aprovações mudaram antes de iniciar; recarregue a campanha.")
        atomic_write_json(estado, {"status": "executando", "revisao": preparacao.revisao})
        resultado = produzir_avulso(raiz_projetos, raiz_global, preparacao)
        atomic_write_json(estado, resultado)
    except Exception as exc:
        atomic_write_json(estado, {
            "status": "falhou", "revisao": preparacao.revisao, "erro": str(exc)
        })
