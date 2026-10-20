"""Gerenciamento da pasta manual do usuário (02_midias/manual/).

Identifica arquivos pelo ID do ativo (A-xxx) ou ID do shot (Bx-yy), atribui
ao plano e direciona arquivos não reconhecidos para 02_midias/nao_atribuidas/.
Preserva os arquivos originais e cria sidecars de licença e crédito.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from docforja.esquemas import Ativo
from docforja.midia.licenca import FichaLicenca, salvar_ficha_licenca

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def identificar_ativo_por_nome(
    nome_arquivo: str,
    ativos: dict[str, Ativo],
    mapa_shots: dict[str, str] | None = None,
) -> str | None:
    """Extrai o ID do ativo a partir do nome do arquivo.

    Suporta:
    - ID direto: A-017.jpg, A-017_v2.png, A-017-detalhe.jpg
    - ID de shot: B1-05.jpg (mapeado para o primeiro ativo do shot)
    """
    stem = Path(nome_arquivo).stem.upper()

    # Busca padrão A-\d+ (seguido de fim, underline ou delimitador)
    match_ativo = re.search(r"(A-\d+)(?:[_\W]|$)", stem)
    if match_ativo:
        aid = match_ativo.group(1)
        if aid in ativos:
            return aid

    # Busca padrão de shot B\d+-\d+ (seguido de fim, underline ou delimitador)
    match_shot = re.search(r"(B\d+-\d+)(?:[_\W]|$)", stem)
    if match_shot and mapa_shots:
        shot_id = match_shot.group(1)
        if shot_id in mapa_shots:
            return mapa_shots[shot_id]

    # Busca correspondência exata de nome_arquivo configurado no ativo
    for aid, ativo in ativos.items():
        if ativo.nome_arquivo and ativo.nome_arquivo.lower() == nome_arquivo.lower():
            return aid

    return None


def escanear_pasta_manual(
    pasta_manual: Path,
    pasta_nao_atribuidas: Path,
    ativos: dict[str, Ativo],
    mapa_shots: dict[str, str] | None = None,
) -> tuple[dict[str, Path], list[Path]]:
    """Analisa arquivos na pasta manual, atribuindo-os aos IDs conhecidos.

    Retorna:
        (atribuidos: dict[aid, caminho_final], nao_atribuidos: list[caminho_final])
    """
    pasta_manual.mkdir(parents=True, exist_ok=True)
    pasta_nao_atribuidas.mkdir(parents=True, exist_ok=True)

    atribuidos: dict[str, Path] = {}
    nao_atribuidos: list[Path] = []

    for item in pasta_manual.iterdir():
        if not item.is_file() or item.suffix.lower() not in EXTENSOES_IMAGEM:
            continue
        # Ignora arquivos de sistema ou sidecars
        if item.name.endswith(".licenca.json"):
            continue

        aid = identificar_ativo_por_nome(item.name, ativos, mapa_shots=mapa_shots)
        if aid:
            atribuidos[aid] = item
            # Garante que sidecar básico exista se o usuário não forneceu
            sidecar = item.with_name(f"{item.name}.licenca.json")
            if not sidecar.is_file():
                salvar_ficha_licenca(
                    item,
                    FichaLicenca(
                        url_origem="pasta_manual",
                        autor="fornecido pelo produtor",
                        licenca="manual_autorizado",
                        comercial=True,
                        patrimonio_restrito=False,
                        credito_obrigatorio=False,
                        texto_credito="Arquivo fornecido pelo produtor",
                    ),
                )
        else:
            # Copia para não atribuídas se ainda não estiver lá
            destino_nao_atribuido = pasta_nao_atribuidas / item.name
            if not destino_nao_atribuido.exists():
                shutil.copy2(item, destino_nao_atribuido)
            nao_atribuidos.append(destino_nao_atribuido)

    return atribuidos, nao_atribuidos
