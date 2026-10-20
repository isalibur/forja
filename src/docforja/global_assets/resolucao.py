"""Resolução e consumo de ativos da Pasta Global por ID estável (13 §3, Marco M7)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docforja.settings import AppSettings, load_settings

CATEGORIAS_GLOBAIS = ["imagens", "personagens", "mapas", "trilhas", "musica", "sfx", "loops"]


def obter_pasta_global(settings: AppSettings | None = None) -> Path:
    """Retorna o caminho raiz configurado para a pasta global de ativos."""
    st = settings or load_settings()
    configured = st.paths.global_assets
    if configured and configured.is_dir():
        return configured
    # Fallback para paths.projects.parent / "global_assets" ou "global"
    alt1 = st.paths.projects.parent / "global_assets"
    if alt1.is_dir():
        return alt1
    alt2 = st.paths.projects.parent / "global"
    if alt2.is_dir():
        return alt2
    return configured


def buscar_ativo_global(
    referencia_ou_id: str,
    pasta_global: Path | None = None,
    categoria: str | None = None,
) -> tuple[Path, dict[str, Any]] | None:
    """Busca um ativo na pasta global por ID estável ou referência global:<cat>:<id>.

    Verifica a existência do arquivo de mídia e da ficha de licença (.json),
    garantindo que o ativo possui licença comercial permissiva (sem NC/ND).
    """
    root = pasta_global or obter_pasta_global()
    if not root.is_dir():
        return None

    cat_alvo = categoria
    id_alvo = referencia_ou_id.strip()

    # Suporta prefixo global:<categoria>:<id>
    if id_alvo.startswith("global:"):
        partes = id_alvo.split(":")
        if len(partes) >= 3:
            cat_alvo = partes[1]
            id_alvo = ":".join(partes[2:])
        elif len(partes) == 2:
            id_alvo = partes[1]

    categorias_pesquisa = [cat_alvo] if cat_alvo else CATEGORIAS_GLOBAIS

    for cat in categorias_pesquisa:
        subpasta = root / cat
        if not subpasta.is_dir():
            continue

        ficha_path = subpasta / f"{id_alvo}.json"
        if not ficha_path.is_file():
            # Tenta buscar por licenca sidecar .licenca.json
            ficha_path = subpasta / f"{id_alvo}.licenca.json"

        if ficha_path.is_file():
            try:
                dados_ficha = json.loads(ficha_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            # Validação estrita de licença comercial (AGENTS.md e 13 §3)
            comercial = dados_ficha.get("comercial", True)
            licenca_str = str(dados_ficha.get("licenca", "")).lower()
            if not comercial or "nc" in licenca_str or "nd" in licenca_str:
                continue

            # Localiza arquivo de mídia correspondente
            arquivo_nome = dados_ficha.get("arquivo")
            caminho_midia: Path | None = None
            if arquivo_nome and (subpasta / arquivo_nome).is_file():
                caminho_midia = subpasta / arquivo_nome
            else:
                cands = [
                    f
                    for f in subpasta.glob(f"{id_alvo}.*")
                    if f.suffix.lower() not in (".json", ".md")
                ]
                if cands:
                    caminho_midia = cands[0]

            if caminho_midia and caminho_midia.is_file():
                dados_ficha.setdefault("id_global", f"global:{cat}:{id_alvo}")
                dados_ficha.setdefault("tipo", cat)
                return caminho_midia, dados_ficha

    return None


def buscar_mapa_global(
    termo_ou_regiao: str,
    pasta_global: Path | None = None,
) -> tuple[Path, dict[str, Any]] | None:
    """Busca um mapa reaproveitável na pasta global por correspondência de região ou termo."""
    root = pasta_global or obter_pasta_global()
    subpasta = root / "mapas"
    if not subpasta.is_dir():
        return None

    termo_norm = termo_ou_regiao.strip().lower()
    palavras_termo = set(termo_norm.split())

    for ficha_path in sorted(subpasta.glob("*.json")):
        if ficha_path.stem.endswith(".licenca"):
            continue
        try:
            dados = json.loads(ficha_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if not dados.get("comercial", True):
            continue
        lic = str(dados.get("licenca", "")).lower()
        if "nc" in lic or "nd" in lic:
            continue

        desc = str(dados.get("descricao", "")).lower()
        nome_id = str(dados.get("id", ficha_path.stem)).lower()
        tags = [str(t).lower() for t in dados.get("tags", [])]

        texto_busca = f"{desc} {nome_id} {' '.join(tags)}"
        # Correspondência por substring ou palavras-chave
        if termo_norm in texto_busca or any(p in texto_busca for p in palavras_termo if len(p) > 3):
            arquivo_nome = dados.get("arquivo")
            caminho: Path | None = None
            if arquivo_nome and (subpasta / arquivo_nome).is_file():
                caminho = subpasta / arquivo_nome
            else:
                cands = [
                    f
                    for f in subpasta.glob(f"{ficha_path.stem}.*")
                    if f.suffix.lower() not in (".json", ".md")
                ]
                if cands:
                    caminho = cands[0]

            if caminho and caminho.is_file():
                dados.setdefault("id_global", f"global:mapas:{dados.get('id', ficha_path.stem)}")
                return caminho, dados

    return None


def buscar_trilha_global(
    termo_ou_estilo: str | None = None,
    pasta_global: Path | None = None,
) -> tuple[Path, dict[str, Any]] | None:
    """Busca uma trilha sonora na pasta global com licença comercial permissiva."""
    root = pasta_global or obter_pasta_global()
    for cat in ["trilhas", "musica"]:
        subpasta = root / cat
        if not subpasta.is_dir():
            continue

        termo_norm = termo_ou_estilo.strip().lower() if termo_ou_estilo else None

        for ficha_path in sorted(subpasta.glob("*.json")):
            try:
                dados = json.loads(ficha_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            if not dados.get("comercial", True):
                continue
            lic = str(dados.get("licenca", "")).lower()
            if "nc" in lic or "nd" in lic:
                continue

            if termo_norm:
                desc = str(dados.get("descricao", "")).lower()
                nome_id = str(dados.get("id", ficha_path.stem)).lower()
                tags = [str(t).lower() for t in dados.get("tags", [])]
                texto_busca = f"{desc} {nome_id} {' '.join(tags)}"
                if termo_norm not in texto_busca:
                    continue

            arquivo_nome = dados.get("arquivo")
            caminho: Path | None = None
            if arquivo_nome and (subpasta / arquivo_nome).is_file():
                caminho = subpasta / arquivo_nome
            else:
                cands = [
                    f
                    for f in subpasta.glob(f"{ficha_path.stem}.*")
                    if f.suffix.lower() not in (".json", ".md")
                ]
                if cands:
                    caminho = cands[0]

            if caminho and caminho.is_file():
                dados.setdefault("id_global", f"global:{cat}:{dados.get('id', ficha_path.stem)}")
                return caminho, dados

    return None
