"""Rascunhos verticais educativos a partir de campanhas avulsas aprovadas."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from datetime import date, timedelta
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
from docforja.shorts.afiliados import (
    AVISO_PUBLICIDADE as AVISO_AFILIADO,
)
from docforja.shorts.afiliados import (
    ProdutoAfiliado,
    gerar_agenda_csv,
    gerar_textos_plataforma,
    linha_agenda,
    validar_sem_preco,
)
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
    "youtube.md", "instagram.md", "agenda.csv",
}
AVISO_PUBLICIDADE = AVISO_AFILIADO


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
    produto: ProdutoAfiliado | None = None
    relacao_comercial: str = "nenhuma"


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
    if pedido.objetivo == "educativo":
        if documentacao.dados.relacao_comercial != "nenhuma":
            raise ValueError("Avulsos educativos não aceitam relação comercial declarada.")
    elif pedido.produto is not None and documentacao.dados.relacao_comercial == "afiliado":
        if not documentacao.dados.aviso_publicidade:
            raise ValueError("Short de afiliado exige aviso de publicidade na ficha.")
        if not (documentacao.dados.marca or "").strip():
            raise ValueError("Short de afiliado exige a marca da loja na ficha.")
    else:
        raise ValueError(
            "Esta produção aceita avulsos educativos sem relação comercial "
            "e shorts de afiliado com produto, aviso e marca confirmados."
        )
    cta = " ".join((pedido.cta or "").split())
    texto = " ".join(aprovacao.texto.split())
    if pedido.produto is not None:
        validar_sem_preco(pedido.produto, texto)
    if not cta or len(cta.split()) > 6 or len(re.findall(re.escape(cta), texto, re.I)) != 1:
        raise ValueError(
            "Informe um CTA de até seis palavras que apareça uma vez no roteiro aprovado."
        )
    voz = _voz_ptbr()
    produto = pedido.produto
    fontes = {
        "campanha": campanha.hash_conteudo,
        "roteiro": aprovacao.revisao,
        "midias": selecao.revisao,
        "alegacoes": documentacao.revisao,
        "voz": voz,
        "catalogo_tts": calcular_hash_dados(MODELOS_CONFIG),
        "producao": calcular_hash_dados(Path(__file__)),
        "produto": produto.model_dump(mode="json") if produto else "",
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
        produto=produto,
        relacao_comercial=documentacao.dados.relacao_comercial,
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


def _data_sugerida() -> str:
    """Sugere o dia seguinte para a planilha de publicação; o usuário confere a agenda."""
    return (date.today() + timedelta(days=1)).isoformat()


def _criar_cenas(
    preparacao: PreparacaoAvulsa, palavras: list[dict[str, Any]], imagens: list[str], duracao: float
) -> list[CenaRenderShort]:
    frames = max(1, round(duracao * FPS))
    hook = _gancho(preparacao.texto)
    if preparacao.produto is not None:
        return _cenas_afiliado(preparacao, palavras, imagens, duracao, hook)
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


def _cenas_afiliado(
    preparacao: PreparacaoAvulsa,
    palavras: list[dict[str, Any]],
    imagens: list[str],
    duracao: float,
    hook: str,
) -> list[CenaRenderShort]:
    """Estrutura da fórmula produto_afiliado: gancho, produto em uso, cartão V11 e CTA."""
    produto = preparacao.produto
    assert produto is not None
    duracao_cartao = min(5.6, max(4.0, duracao * 0.18))
    metade_cartao = duracao_cartao / 2
    duracao_cta = min(2.5, max(2.0, duracao * 0.08))
    inicio_cartao = min(max(2.5, duracao * 0.45), max(2.5, duracao - duracao_cartao - duracao_cta))
    fim_cartao = min(duracao - duracao_cta, inicio_cartao + duracao_cartao)
    inicio_cta = max(fim_cartao, duracao - duracao_cta)
    blocos: list[tuple[str, float, float, int, dict[str, Any]]] = [
        ("V01", 0.0, min(2.0, duracao), 0, {})
    ]
    cursor = min(2.0, duracao)
    indice = 0
    while cursor < inicio_cartao - 0.01:
        fim = min(inicio_cartao, cursor + 2.5)
        blocos.append(("V02", cursor, fim, indice, {}))
        cursor = fim
        indice += 1
    if fim_cartao > inicio_cartao:
        blocos.append((
            "V11",
            inicio_cartao,
            inicio_cartao + metade_cartao,
            indice,
            {"titulo": produto.nome, "itens": list(produto.beneficios[:2])},
        ))
        indice += 1
        blocos.append((
            "V11",
            inicio_cartao + metade_cartao,
            fim_cartao,
            indice,
            {
                "itens": list(produto.beneficios[2:]),
                "condicao": produto.condicao or "",
                "marca": produto.marca or "",
                "aviso_publicidade": AVISO_PUBLICIDADE,
            },
        ))
        indice += 1
        cursor = fim_cartao
    while cursor < inicio_cta - 0.01:
        fim = min(inicio_cta, cursor + 2.5)
        blocos.append(("V02", cursor, fim, indice, {}))
        cursor = fim
        indice += 1
    if duracao > inicio_cta + 0.01:
        blocos.append(("V07", inicio_cta, duracao, indice, {"cta": preparacao.cta}))
    cenas: list[CenaRenderShort] = []
    for numero, (variante, inicio, fim, indice_imagem, extra) in enumerate(blocos):
        frame_inicio = max(0, round(inicio * FPS))
        frame_fim = min(round(duracao * FPS), max(frame_inicio + 1, round(fim * FPS)))
        props = PropsCenaShort(
            variante=variante,
            titulo=hook if variante == "V01" else str(extra.get("titulo", "")),
            itens=list(extra.get("itens", [])),
            condicao=str(extra.get("condicao", "")),
            marca=str(extra.get("marca", "")),
            aviso_publicidade=str(extra.get("aviso_publicidade", "")),
            cta=str(extra.get("cta", "")),
            imagem=imagens[indice_imagem % len(imagens)],
            legendas=_captions_remotion(palavras, inicio, fim),
        )
        cenas.append(CenaRenderShort(
            id=f"cena-{numero:03d}",
            inicio_frame=frame_inicio,
            duracao_frames=frame_fim - frame_inicio,
            props=props,
        ))
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
            divergencia = (
                f"{narracao.wer_medio * 100:.2f}%"
                if narracao.wer_medio is not None
                else "desconhecido"
            )
            raise ValueError(
                f"A narração divergiu do roteiro (WER {divergencia}); revise antes de renderizar."
            )
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
        elementos = [
            ElementoTelaShort(id="gancho", x=0.08, y=0.18, largura=0.78, altura=0.35),
            ElementoTelaShort(id="legenda", x=0.08, y=0.67, largura=0.78, altura=0.06),
        ]
        textos_tela = [hook]
        if preparacao.produto is not None:
            produto = preparacao.produto
            elementos.append(
                ElementoTelaShort(id="cartao-produto", x=0.08, y=0.18, largura=0.78, altura=0.40)
            )
            elementos.append(
                ElementoTelaShort(id="cta", x=0.08, y=0.18, largura=0.78, altura=0.40)
            )
            textos_tela.extend(
                [produto.nome, *produto.beneficios, produto.condicao or ""]
            )
            textos_tela.extend([produto.marca or "", AVISO_PUBLICIDADE, preparacao.cta])
        qa = verificar_short(ShortParaVerificar(
            duracao_s=duracao,
            duracao_alvo_s=float(preparacao.duracao_alvo_s),
            inicio_gancho_visual_s=0,
            inicio_gancho_textual_s=0,
            inicio_gancho_falado_s=float(palavras[0]["start"]),
            mudancas_visuais_s=[c.inicio_frame / FPS for c in cenas[1:]],
            elementos=elementos,
            legendas=_intervalos_legenda(palavras),
            textos_tela=[texto for texto in textos_tela if texto],
            quantidade_ctas_principais=len(
                re.findall(re.escape(preparacao.cta), preparacao.texto, re.I)
            ),
            audio_lufs_integrado=loudness_entregue if loudness_entregue is not None else loudness,
            musica_cobre_voz=False,
            musica_ausente=True,
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
            "relacao_comercial": preparacao.relacao_comercial,
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
        if preparacao.produto is not None:
            produto = preparacao.produto
            metadados["produto"] = {
                "nome": produto.nome,
                "beneficios": list(produto.beneficios),
                "condicao": produto.condicao,
                "marca": produto.marca,
                "nicho": produto.nicho,
                "plataforma": produto.plataforma,
                "link_afiliado": produto.link_afiliado,
                "aviso_publicidade": AVISO_PUBLICIDADE,
                "link_queimado_no_video": False,
            }
        atomic_write_json(work / "metadados.json", metadados)
        if preparacao.produto is not None:
            produto = preparacao.produto
            textos = gerar_textos_plataforma(produto, preparacao.cta, hook)
            linha = linha_agenda(
                produto,
                textos["titulo"],
                textos["youtube"],
                textos["hashtags"],
                data=_data_sugerida(),
                hora="18:00",
                arquivos={"video": "video.mp4", "capa": "capa.jpg"},
            )
        else:
            titulo = " ".join(preparacao.tema.split())[:40]
            hashtags = "#Shorts #Reels #DocForja"
            youtube = (
                f"# {titulo}\n\n{preparacao.texto}\n\n{hashtags}\n"
                "\nRASCUNHO — não publicar sem revisão factual, visual, sonora e do QA.\n"
            )
            instagram = (
                f"{preparacao.tema}\n\n{preparacao.texto}\n\n{hashtags}\n"
                "\nRASCUNHO — não publicar sem revisão factual, visual, sonora e do QA.\n"
            )
            textos = {
                "titulo": titulo,
                "youtube": youtube,
                "instagram": instagram,
                "hashtags": hashtags,
            }
            linha = {
                "plataforma": "ambas",
                "data": _data_sugerida(),
                "hora": "18:00",
                "arquivo_video": "video.mp4",
                "arquivo_capa": "capa.jpg",
                "titulo": titulo,
                "legenda": youtube,
                "hashtags": hashtags,
                "link": "",
                "aviso_publicidade": "",
                "status": "rascunho",
            }
        atomic_write_text(work / "youtube.md", textos["youtube"])
        atomic_write_text(work / "instagram.md", textos["instagram"])
        atomic_write_text(work / "agenda.csv", gerar_agenda_csv([linha]))
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
