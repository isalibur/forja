"""Gerenciamento da estrutura de pastas e metadados de projetos DocForja."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from docforja.esquemas import TipoProjeto
from docforja.io import atomic_write_json
from docforja.settings import AppSettings, load_settings


def slugificar(texto: str) -> str:
    """Gera um slug seguro para pastas a partir do nome/tema."""
    normalizado = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in normalizado if not unicodedata.combining(c))
    slug = re.sub(r"[^\w\s-]", "", sem_acento.lower()).strip()
    return re.sub(r"[-\s]+", "-", slug) or "projeto"


@dataclass
class PastasProjeto:
    raiz: Path
    entrada: Path
    plano: Path
    midias: Path
    audio: Path
    montagem: Path
    saida: Path
    sistema: Path


class Projeto:
    """Instância de projeto local do DocForja."""

    def __init__(self, raiz: Path, slug: str) -> None:
        self.slug = slug
        self.raiz = raiz.resolve()
        self.pastas = PastasProjeto(
            raiz=self.raiz,
            entrada=self.raiz / "00_entrada",
            plano=self.raiz / "01_plano",
            midias=self.raiz / "02_midias",
            audio=self.raiz / "03_audio",
            montagem=self.raiz / "04_montagem",
            saida=self.raiz / "05_saida",
            sistema=self.raiz / "sistema",
        )
        self.opcoes_file = self.pastas.entrada / "opcoes.yaml"
        self.banco_file = self.pastas.sistema / "banco.db"
        self.eventos_file = self.pastas.sistema / "eventos.jsonl"

    @classmethod
    def criar(
        cls,
        nome: str,
        tipo: TipoProjeto | str = TipoProjeto.LONGO,
        roteiro: str = "",
        idioma_principal: str = "pt-BR",
        idiomas_extras: list[str] | None = None,
        preset: str = "padrao",
        kit: str = "cinza-e-brasa@1.0",
        opcoes_adicionais: dict[str, Any] | None = None,
        raiz_projetos: Path | None = None,
        settings: AppSettings | None = None,
    ) -> Projeto:
        """Cria e inicializa toda a estrutura de diretórios do projeto (07 §4)."""
        app_settings = settings or load_settings()
        base_dir = raiz_projetos or app_settings.paths.projects
        slug = slugificar(nome)
        raiz = (base_dir / slug).resolve()

        projeto = cls(raiz, slug)
        # Cria diretórios estruturais
        for subpasta in [
            projeto.pastas.entrada,
            projeto.pastas.entrada / "documentos",
            projeto.pastas.plano,
            projeto.pastas.plano / "pesquisa",
            projeto.pastas.midias / "biblioteca",
            projeto.pastas.midias / "pesquisadas",
            projeto.pastas.midias / "geradas",
            projeto.pastas.midias / "manual",
            projeto.pastas.midias / "nao_atribuidas",
            projeto.pastas.midias / "tratadas",
            projeto.pastas.audio / idioma_principal,
            projeto.pastas.audio / "trilha",
            projeto.pastas.audio / "sfx",
            projeto.pastas.montagem / idioma_principal / "blocos",
            projeto.pastas.saida / idioma_principal,
            projeto.pastas.saida / "elementos",
            projeto.pastas.sistema / "logs",
            projeto.pastas.sistema / "cache",
        ]:
            subpasta.mkdir(parents=True, exist_ok=True)

        extras = idiomas_extras or []
        for extra in extras:
            (projeto.pastas.audio / extra).mkdir(parents=True, exist_ok=True)
            (projeto.pastas.montagem / extra / "blocos").mkdir(parents=True, exist_ok=True)
            (projeto.pastas.saida / extra).mkdir(parents=True, exist_ok=True)

        opcoes = {
            "nome": nome,
            "slug": slug,
            "tipo": str(tipo),
            "preset": preset,
            "kit": kit,
            "idiomas": {"principal": idioma_principal, "extras": extras},
            "monetizado": True,
            **(opcoes_adicionais or {}),
        }
        with projeto.opcoes_file.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(opcoes, handle, allow_unicode=True, sort_keys=False)

        if roteiro:
            (projeto.pastas.entrada / "roteiro.md").write_text(roteiro, encoding="utf-8")

        glossario = {"termos": {}}
        with (projeto.pastas.entrada / "glossario.yaml").open("w", encoding="utf-8") as handle:
            yaml.safe_dump(glossario, handle, allow_unicode=True)

        # Inicializa arquivo de escolhas de mídia
        atomic_write_json(projeto.pastas.midias / "escolhas.json", {"ativos": {}})

        # O banco também faz parte da estrutura inicial do projeto (M1).
        from docforja.nucleo.banco import BancoProjeto

        BancoProjeto(projeto.banco_file)

        return projeto

    @classmethod
    def carregar(cls, caminho_ou_slug: str | Path, raiz_projetos: Path | None = None) -> Projeto:
        """Carrega um projeto existente a partir de seu caminho ou slug."""
        caminho = Path(caminho_ou_slug)
        if not caminho.is_dir():
            app_settings = load_settings()
            base_dir = raiz_projetos or app_settings.paths.projects
            caminho = (base_dir / str(caminho_ou_slug)).resolve()
        if not caminho.is_dir():
            raise FileNotFoundError(f"Projeto não encontrado em: {caminho}")
        return cls(caminho, caminho.name)

    def obter_opcoes(self) -> dict[str, Any]:
        if not self.opcoes_file.is_file():
            return {}
        with self.opcoes_file.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def obter_roteiro(self) -> str:
        roteiro_file = self.pastas.entrada / "roteiro.md"
        if roteiro_file.is_file():
            return roteiro_file.read_text(encoding="utf-8")
        return ""

    def artefatos_m3_m4_ausentes(self) -> list[Path]:
        """Lista saídas de aceitação de M3/M4 que ainda não existem no projeto."""
        opcoes = self.obter_opcoes()
        idioma = opcoes.get("idiomas", {}).get("principal", "pt-BR")
        obrigatorios = [
            self.pastas.audio / idioma / "narracao_completa.wav",
            self.pastas.audio / idioma / "palavras.json",
            self.pastas.plano / "plano.json",
            self.pastas.plano / "plano.md",
            self.pastas.plano / "verificacao.md",
            self.pastas.plano / "estimativa.md",
        ]
        return [caminho for caminho in obrigatorios if not caminho.is_file()]
