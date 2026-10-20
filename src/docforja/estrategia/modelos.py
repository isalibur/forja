"""Modelos de dados para metadados estratégicos de publicação."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ItemTitulo(BaseModel):
    """Ideia de título para teste de CTR com nota multicritério."""

    titulo: str
    angulo: str
    gatilho: str
    palavra_chave: str
    nota: float
    criterios: dict[str, float] = Field(default_factory=dict)
    recomendado_ab: bool = False


class ConceitoThumbnail(BaseModel):
    """Briefing de conceito de thumbnail."""

    id: str  # "A", "B", "C"
    nome: str
    ideia: str
    elemento_central: str
    texto_tela: str
    contraste: str
    cores: list[str] = Field(default_factory=list)
    legibilidade_120px: bool = True
    arquivo_rascunho: str | None = None


class Capitulo(BaseModel):
    """Marcador de capítulo de vídeo."""

    tempo_s: float
    timestamp: str  # "00:00"
    titulo: str


class PacoteEstrategico(BaseModel):
    """Pacote completo de metadados estratégicos para publicação."""

    projeto: str
    idioma: str = "pt-BR"
    duracao_s: float
    titulos: list[ItemTitulo] = Field(default_factory=list)
    top_titulos_ab: list[str] = Field(default_factory=list)
    descricao: str = ""
    capitulos: list[Capitulo] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    palavras_chave: list[str] = Field(default_factory=list)
    comentario_fixado: str = ""
    post_comunidade: str = ""
    checklist_publicacao: list[str] = Field(default_factory=list)
    thumbnails: list[ConceitoThumbnail] = Field(default_factory=list)
