"""Narração e retime dos idiomas adicionais."""

from __future__ import annotations

import json
from pathlib import Path

from docforja.audio.narracao import OrquestradorNarracao
from docforja.esquemas import Plano
from docforja.idiomas.retime import retimar_plano
from docforja.idiomas.traducao import RoteiroTraduzido
from docforja.io import atomic_write_json
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.nucleo.projeto import Projeto
from docforja.planejamento.entidades import SegmentoProcessado
from docforja.planejamento.leitura import ler_roteiro_formatado


def carregar_traducao_atual(projeto: Projeto, idioma: str) -> tuple[RoteiroTraduzido, Path]:
    pasta = projeto.pastas.plano / "idiomas" / idioma
    indice_path = pasta / "atual.json"
    if not indice_path.is_file():
        raise FileNotFoundError(f"Tradução validada ausente para {idioma}.")
    indice = json.loads(indice_path.read_text(encoding="utf-8"))
    nome = str(indice.get("versao", ""))
    if not nome.startswith("roteiro_") or Path(nome).name != nome:
        raise ValueError(f"Índice de tradução inválido para {idioma}.")
    caminho = pasta / nome
    if not caminho.is_file():
        raise FileNotFoundError(f"Versão da tradução ausente para {idioma}.")
    return RoteiroTraduzido.model_validate_json(caminho.read_text(encoding="utf-8")), caminho


def _segmentos_traduzidos(projeto: Projeto, traducao: RoteiroTraduzido) -> list[SegmentoProcessado]:
    origem = {
        segmento.id: segmento
        for bloco in ler_roteiro_formatado(projeto.obter_roteiro())
        for segmento in bloco.segmentos
    }
    if list(origem) != [item.id for item in traducao.segmentos]:
        raise ValueError("A tradução não corresponde ao roteiro atual.")
    return [
        SegmentoProcessado(
            id=item.id,
            texto_original=item.texto_original,
            texto_limpo=item.texto_limpo,
            direcao_voz=origem[item.id].direcao_voz,
            batida=origem[item.id].batida,
            intensidade=origem[item.id].intensidade,
            silencio_apos_s=origem[item.id].silencio_apos_s,
            pausas=origem[item.id].pausas,
        )
        for item in traducao.segmentos
    ]


def eh_modo_so_legendas(projeto: Projeto, idioma: str) -> bool:
    """Verifica se um idioma extra está configurado no modo 'só legendas'."""
    opcoes = projeto.obter_opcoes()
    if opcoes.get("modo_legendas", False):
        return True
    idiomas_cfg = opcoes.get("idiomas", {})
    if not isinstance(idiomas_cfg, dict):
        return False
    if idiomas_cfg.get("modo_legendas", False):
        return True
    so_leg = idiomas_cfg.get("so_legendas", [])
    if isinstance(so_leg, list) and idioma in so_leg:
        return True
    modos = idiomas_cfg.get("modos", {})
    return bool(isinstance(modos, dict) and modos.get(idioma) in ("so_legendas", "legendas"))


def _manifesto_valido(projeto: Projeto, idioma: str, hash_traducao: str) -> bool:
    pasta = projeto.pastas.audio / idioma
    manifesto_path = pasta / "narracao_idioma.json"
    if not manifesto_path.is_file():
        return False
    try:
        manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
        if manifesto.get("hash_traducao") != hash_traducao:
            return False
        if eh_modo_so_legendas(projeto, idioma):
            segmentos_path = pasta / "segmentos.json"
            if not segmentos_path.is_file():
                return False
            segmentos = json.loads(segmentos_path.read_text(encoding="utf-8"))
            return [item["id"] for item in segmentos] == manifesto.get("segmentos")
        for nome, hash_esperado in manifesto.get("hash_saidas", {}).items():
            caminho = pasta / nome
            if not caminho.is_file() or calcular_hash_dados(caminho) != hash_esperado:
                return False
        segmentos = json.loads((pasta / "segmentos.json").read_text(encoding="utf-8"))
        return [item["id"] for item in segmentos] == manifesto.get("segmentos")
    except (OSError, ValueError, KeyError, TypeError):
        return False


def narracoes_extras_validas(projeto: Projeto) -> bool:
    extras = projeto.obter_opcoes().get("idiomas", {}).get("extras", [])
    try:
        return all(
            _manifesto_valido(
                projeto, idioma, carregar_traducao_atual(projeto, idioma)[0].hash_traducao
            )
            for idioma in extras
        )
    except (OSError, ValueError):
        return False


def salvar_retime_se_disponivel(projeto: Projeto, idioma: str) -> Path | None:
    plano_path = projeto.pastas.plano / "plano_verificado.json"
    principal = projeto.obter_opcoes().get("idiomas", {}).get("principal", "pt-BR")
    origem_path = projeto.pastas.audio / principal / "segmentos.json"
    destino_path = projeto.pastas.audio / idioma / "segmentos.json"
    if not plano_path.is_file() or not origem_path.is_file() or not destino_path.is_file():
        return None
    plano = Plano.model_validate_json(plano_path.read_text(encoding="utf-8"))
    retimado = retimar_plano(
        plano,
        json.loads(origem_path.read_text(encoding="utf-8")),
        json.loads(destino_path.read_text(encoding="utf-8")),
    )
    destino = projeto.pastas.plano / "idiomas" / idioma / "plano_retimado.json"
    atomic_write_json(destino, retimado.model_dump(mode="json"))
    return destino


def executar_narracoes_extras(projeto: Projeto, motor: OrquestradorNarracao) -> None:
    """Gera uma narração por idioma extra e registra hashes para retomada segura."""
    opcoes = projeto.obter_opcoes()
    extras = opcoes.get("idiomas", {}).get("extras", [])
    vozes = opcoes.get("vozes", {})
    if not extras:
        return
    for idioma in extras:
        traducao, _ = carregar_traducao_atual(projeto, idioma)
        if _manifesto_valido(projeto, idioma, traducao.hash_traducao):
            salvar_retime_se_disponivel(projeto, idioma)
            continue
        if eh_modo_so_legendas(projeto, idioma):
            principal = opcoes.get("idiomas", {}).get("principal", "pt-BR")
            origem_segs = projeto.pastas.audio / principal / "segmentos.json"
            if not origem_segs.is_file():
                raise FileNotFoundError(
                    f"Tempos de áudio base ausentes para legendas em {idioma}."
                )
            dados_base = json.loads(origem_segs.read_text(encoding="utf-8"))
            mapa_trad = {s.id: s.texto_limpo for s in traducao.segmentos}
            segmentos_loc = [
                {
                    "id": item["id"],
                    "inicio_s": item["inicio_s"],
                    "fim_s": item["fim_s"],
                    "texto": mapa_trad.get(item["id"], item.get("texto", "")),
                }
                for item in dados_base
            ]
            pasta = projeto.pastas.audio / idioma
            pasta.mkdir(parents=True, exist_ok=True)
            atomic_write_json(pasta / "segmentos.json", segmentos_loc)
            duracao_total = float(dados_base[-1]["fim_s"]) if dados_base else 0.0
            atomic_write_json(
                pasta / "narracao_idioma.json",
                {
                    "idioma": idioma,
                    "modo": "so_legendas",
                    "hash_traducao": traducao.hash_traducao,
                    "duracao_total_s": duracao_total,
                    "segmentos": [item.id for item in traducao.segmentos],
                    "hash_saidas": {
                        "segmentos.json": calcular_hash_dados(pasta / "segmentos.json"),
                    },
                },
            )
            salvar_retime_se_disponivel(projeto, idioma)
            continue

        if not motor.tts.disponivel():
            raise RuntimeError("Motor de narração configurado não está disponível.")
        segmentos = _segmentos_traduzidos(projeto, traducao)
        relatorio = motor.processar_projeto_completo(
            segmentos=segmentos,
            pasta_audio=projeto.pastas.audio,
            idioma=idioma,
            voz=vozes.get(idioma),
            executar_alinhamento=False,
            gerar_timestamps_estimados=True,
        )
        if not relatorio.arquivo_completo_wav.is_file() or relatorio.duracao_total_s <= 0:
            raise RuntimeError(f"A narração em {idioma} não produziu um WAV válido.")
        pasta = projeto.pastas.audio / idioma
        saidas = ["narracao_completa.wav", "segmentos.json", "palavras.json"]
        atomic_write_json(
            pasta / "narracao_idioma.json",
            {
                "idioma": idioma,
                "hash_traducao": traducao.hash_traducao,
                "duracao_total_s": relatorio.duracao_total_s,
                "segmentos": [item.id for item in traducao.segmentos],
                "hash_saidas": {nome: calcular_hash_dados(pasta / nome) for nome in saidas},
            },
        )
        salvar_retime_se_disponivel(projeto, idioma)
