"""Artefatos localizados usados pelas etapas de produção multilíngue."""

from __future__ import annotations

import json
from pathlib import Path

from docforja.esquemas import Plano
from docforja.idiomas.narracao import carregar_traducao_atual, salvar_retime_se_disponivel
from docforja.io import atomic_write_json, atomic_write_text
from docforja.nucleo.projeto import Projeto


def idiomas_do_projeto(projeto: Projeto) -> list[str]:
    idiomas = projeto.obter_opcoes().get("idiomas", {})
    return [idiomas.get("principal", "pt-BR"), *idiomas.get("extras", [])]


def plano_do_idioma(projeto: Projeto, idioma: str) -> tuple[Plano, Path]:
    principal = idiomas_do_projeto(projeto)[0]
    if idioma == principal:
        caminho = projeto.pastas.plano / "plano.json"
        if not caminho.is_file():
            caminho = projeto.pastas.plano / "plano_verificado.json"
    else:
        caminho = salvar_retime_se_disponivel(projeto, idioma)
        if caminho is None:
            raise FileNotFoundError(f"Plano ou áudio ausente para retime em {idioma}.")
        traducao, _ = carregar_traducao_atual(projeto, idioma)
        plano = Plano.model_validate_json(caminho.read_text(encoding="utf-8"))
        textos = {item.id: item.texto_limpo for item in traducao.segmentos}
        for bloco in plano.blocos:
            for shot in bloco.shots:
                localizados = [textos[sid] for sid in shot.segmentos if sid in textos]
                if not localizados:
                    continue
                texto = " ".join(localizados)
                if shot.textos:
                    shot.textos = [texto]
                for chave in ("texto", "titulo", "subtitulo", "legenda", "traducao"):
                    if isinstance(shot.params.get(chave), str) and shot.params[chave].strip():
                        shot.params[chave] = texto
        atomic_write_json(caminho, plano.model_dump(mode="json"))
        atomic_write_json(
            projeto.pastas.plano / "i18n" / f"{idioma}.json",
            {"idioma": idioma, "segmentos": textos},
        )
    if not caminho.is_file():
        raise FileNotFoundError(f"Plano de produção ausente para {idioma}.")
    return Plano.model_validate_json(caminho.read_text(encoding="utf-8")), caminho


def gerar_legendas_srt(projeto: Projeto, idioma: str) -> Path:
    segmentos_path = projeto.pastas.audio / idioma / "segmentos.json"
    if not segmentos_path.is_file():
        raise FileNotFoundError(f"Tempos de áudio ausentes para legendas em {idioma}.")
    segmentos = json.loads(segmentos_path.read_text(encoding="utf-8"))

    def tempo_srt(segundos: float) -> str:
        milissegundos = round(segundos * 1000)
        horas, resto = divmod(milissegundos, 3_600_000)
        minutos, resto = divmod(resto, 60_000)
        secs, millis = divmod(resto, 1000)
        return f"{horas:02d}:{minutos:02d}:{secs:02d},{millis:03d}"

    blocos = []
    for indice, item in enumerate(segmentos, start=1):
        blocos.append(
            f"{indice}\n{tempo_srt(float(item['inicio_s']))} --> "
            f"{tempo_srt(float(item['fim_s']))}\n{item['texto']}"
        )
    destino = projeto.pastas.saida / idioma / "legendas" / "legendas.srt"
    atomic_write_text(destino, "\n\n".join(blocos) + "\n")
    return destino
