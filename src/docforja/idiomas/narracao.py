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


def _manifesto_valido(projeto: Projeto, idioma: str, hash_traducao: str) -> bool:
    pasta = projeto.pastas.audio / idioma
    manifesto_path = pasta / "narracao_idioma.json"
    if not manifesto_path.is_file():
        return False
    try:
        manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
        if manifesto.get("hash_traducao") != hash_traducao:
            return False
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
    if not motor.tts.disponivel():
        raise RuntimeError("Motor de narração configurado não está disponível.")
    for idioma in extras:
        traducao, _ = carregar_traducao_atual(projeto, idioma)
        if _manifesto_valido(projeto, idioma, traducao.hash_traducao):
            salvar_retime_se_disponivel(projeto, idioma)
            continue
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
