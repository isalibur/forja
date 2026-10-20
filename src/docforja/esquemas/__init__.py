"""Esquemas de dados Pydantic do DocForja."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class TipoProjeto(StrEnum):
    LONGO = "longo"
    SHORT_DERIVADO = "short_derivado"
    SHORT_AVULSO = "short_avulso"
    MUSICA = "musica"


class OrigemAtivo(StrEnum):
    BIBLIOTECA = "biblioteca"
    PESQUISAR = "pesquisar"
    GERAR = "gerar"
    PEDIR_AO_USUARIO = "pedir_ao_usuario"
    DADOS = "dados"


class BatidaSegmento(StrEnum):
    GANCHO = "gancho"
    CONTEXTO = "contexto"
    DADO = "dado"
    REVELACAO = "revelação"
    TENSAO = "tensão"
    RESPIRO = "respiro"
    TRANSICAO_LUGAR = "transição_lugar"
    TRANSICAO_TEMPO = "transição_tempo"
    CITACAO = "citação"
    FECHAMENTO = "fechamento"


class Segmento(BaseModel):
    """Segmento do roteiro extraído na leitura."""

    id: str
    texto: str
    batida: BatidaSegmento | str = BatidaSegmento.CONTEXTO
    intensidade: int = Field(default=5, ge=1, le=10)
    entidades: list[str] = Field(default_factory=list)
    duracao_estimada_s: float | None = None
    duracao_real_s: float | None = None


class Candidato(BaseModel):
    """Candidata de pesquisa em acervo."""

    id: str
    origem: str
    url_origem: str
    url_download: str = ""
    autor: str = ""
    licenca: str = ""
    comercial: bool = True
    patrimonio_restrito: bool = False
    nota_curador: float | None = None
    motivo_curador: str | None = None
    largura: int | None = None
    altura: int | None = None


class Ativo(BaseModel):
    """Ativo visual consolidado do projeto."""

    id: str
    descricao: str
    origem: OrigemAtivo | str = OrigemAtivo.BIBLIOTECA
    personagem: str | None = None
    prompt: str | None = None
    motivo: str | None = None
    busca: dict[str, Any] | None = None
    nome_arquivo: str | None = None
    usado_em: list[str] = Field(default_factory=list)
    proibicoes: list[str] = Field(default_factory=list)
    plano_b: str | None = None
    caminho: Path | None = None
    licenca: dict[str, Any] | None = None


class Credito(BaseModel):
    """Ficha de crédito de um ativo ou elemento."""

    ativo_id: str
    tipo: str = "imagem"
    titulo: str = ""
    autor: str = ""
    fonte: str = ""
    licenca: str = ""
    texto_credito: str = ""


class Shot(BaseModel):
    """Unidade audiovisual de cena no plano."""

    id: str
    segmentos: list[str] = Field(default_factory=list)
    ancora: dict[str, str] | None = None
    duracao_s: float
    inicio_s: float | None = None
    fim_s: float | None = None
    inicio_segmento_s: float | None = None
    fim_segmento_s: float | None = None
    template: str
    params: dict[str, Any] = Field(default_factory=dict)
    sobreposicoes: list[dict[str, Any]] = Field(default_factory=list)
    ativos: list[str] = Field(default_factory=list)
    textos: list[str] = Field(default_factory=list)
    sfx: list[str] = Field(default_factory=list)
    transicao: str = "corte"
    plano_b: dict[str, Any] | None = None
    motivo: str | None = None


class Bloco(BaseModel):
    """Bloco temático ou capítulo de vídeo."""

    id: str
    titulo: str
    modo_visual: str = "misto"
    clima_musical: str = ""
    contexto: dict[str, Any] | None = None
    shots: list[Shot] = Field(default_factory=list)


class Plano(BaseModel):
    """Plano de Vídeo mestre do DocForja."""

    versao: int = 1
    projeto: str
    kit: str = "cinza-e-brasa@1.0"
    preset: str = "padrao"
    tipo: TipoProjeto | str = TipoProjeto.LONGO
    idiomas: dict[str, Any] = Field(default_factory=lambda: {"principal": "pt-BR", "extras": []})
    orcamento_producao_min: int = 120
    estimativa_producao_min: int = 0
    blocos: list[Bloco] = Field(default_factory=list)
    ativos: dict[str, Ativo] = Field(default_factory=dict)
    musica: list[dict[str, Any]] = Field(default_factory=list)
    verificacao: dict[str, Any] = Field(default_factory=dict)


class ClipTimeline(BaseModel):
    id: str
    shot_id: str | None = None
    inicio_s: float
    duracao_s: float
    tipo: str = "video"
    origem: str = ""
    params: dict[str, Any] = Field(default_factory=dict)


class FaixaTimeline(BaseModel):
    id: str
    nome: str
    tipo: str = "video"
    clips: list[ClipTimeline] = Field(default_factory=list)


class Timeline(BaseModel):
    """Estrutura temporal para render e exportação OTIO/Remotion."""

    projeto: str
    idioma: str = "pt-BR"
    duracao_total_s: float
    fps: int = 30
    largura: int = 1920
    altura: int = 1080
    faixas: list[FaixaTimeline] = Field(default_factory=list)
    marcadores: list[dict[str, Any]] = Field(default_factory=list)
