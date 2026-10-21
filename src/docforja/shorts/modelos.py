"""Modelos validados para seleção, edição e verificação de shorts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ModeloShort(BaseModel):
    """Base stricta dos dados intercambiados pelos módulos de shorts."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class SegmentoShort(ModeloShort):
    """Segmento do vídeo longo com tempos reais e sinais editoriais revisáveis."""

    id: str = Field(min_length=1)
    inicio_s: float = Field(ge=0)
    fim_s: float = Field(gt=0)
    texto: str = Field(min_length=1)
    batida: str = "contexto"
    autonomia_solo: int = Field(default=5, ge=0, le=10)
    curiosidade_para_longo: int = Field(default=5, ge=0, le=10)
    forca_visual_vertical: int = Field(default=5, ge=0, le=10)

    @model_validator(mode="after")
    def validar_intervalo(self) -> SegmentoShort:
        if self.fim_s <= self.inicio_s:
            raise ValueError("fim_s deve ser maior que inicio_s")
        return self


class FrasePonte(ModeloShort):
    """Frase nova aprovada explicitamente pelo usuário para um short derivado."""

    texto: str = Field(min_length=1)
    aprovada: bool = False


class CandidatoShort(ModeloShort):
    """Trecho proposto do vídeo longo; não modifica o Plano mestre."""

    id: str
    inicio_s: float = Field(ge=0)
    fim_s: float = Field(gt=0)
    segmento_ids: list[str] = Field(min_length=1)
    texto: str
    pontuacao: float = Field(ge=0, le=100)
    componentes: dict[str, float]
    motivos: list[str] = Field(default_factory=list)
    frases_ponte: list[FrasePonte] = Field(default_factory=list)


class ElementoTelaShort(ModeloShort):
    """Elemento visual em coordenadas normalizadas de 0 a 1."""

    id: str
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    largura: float = Field(gt=0, le=1)
    altura: float = Field(gt=0, le=1)
    texto: str = ""
    importante: bool = True


class IntervaloLegendaShort(ModeloShort):
    inicio_s: float = Field(ge=0)
    fim_s: float = Field(gt=0)
    texto: str = Field(min_length=1)


class ShortParaVerificar(ModeloShort):
    """Dados mensuráveis necessários ao verificador DS1-DS9."""

    duracao_s: float = Field(gt=0)
    duracao_alvo_s: float = Field(gt=0)
    possui_fala: bool = True
    inicio_gancho_visual_s: float | None = Field(default=None, ge=0)
    inicio_gancho_textual_s: float | None = Field(default=None, ge=0)
    inicio_gancho_falado_s: float | None = Field(default=None, ge=0)
    mudancas_visuais_s: list[float] = Field(default_factory=list)
    elementos: list[ElementoTelaShort] = Field(default_factory=list)
    legendas: list[IntervaloLegendaShort] = Field(default_factory=list)
    textos_tela: list[str] = Field(default_factory=list)
    quantidade_ctas_principais: int = Field(default=0, ge=0)
    derivado: bool = False
    frase_ponte_aprovada: bool = False
    video_longo_id: str | None = None
    audio_lufs_integrado: float | None = None
    musica_mais_presente_que_longo: bool | None = None
    musica_cobre_voz: bool | None = None
    musica_ausente: bool = False


class ViolacaoDosagemShort(ModeloShort):
    regra: str
    aprovada: bool
    descricao: str
    detalhes: str = ""


class ResultadoDosagemShort(ModeloShort):
    aprovado: bool
    violacoes: list[ViolacaoDosagemShort] = Field(default_factory=list)


class FormulaShort(ModeloShort):
    """Fórmula editorial de short armazenada como YAML versionável."""

    id: str
    nome: str
    estrutura: list[str] = Field(min_length=1)
    objetivos: list[str] = Field(min_length=1)
    templates: list[str] = Field(min_length=1)
    duracao_min_s: int = Field(default=15, ge=15)
    duracao_max_s: int = Field(default=60, le=90)
    regras: list[str] = Field(default_factory=list)
    exige_prova_real: bool = False
    exige_fonte_preco: bool = False

    @model_validator(mode="after")
    def validar_faixa_duracao(self) -> FormulaShort:
        if self.duracao_max_s < self.duracao_min_s:
            raise ValueError("duracao_max_s deve ser maior ou igual a duracao_min_s")
        return self


class CropVertical(ModeloShort):
    """Janela de recorte normalizada para adaptar um ativo ao formato vertical."""

    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    largura: float = Field(gt=0, le=1)
    altura: float = Field(gt=0, le=1)
    usar_fundo_desfocado: bool = False


class AtivoReenquadrado(ModeloShort):
    ativo_id: str
    recorte: CropVertical
    hash_origem: str


class ShotVerticalizado(ModeloShort):
    shot_id: str
    inicio_s: float = Field(ge=0)
    fim_s: float = Field(gt=0)
    template_origem: str
    ativos: list[AtivoReenquadrado] = Field(default_factory=list)


class ManifestoVertical(ModeloShort):
    projeto: str
    proporcao: str = "9:16"
    hash_entrada: str
    shots: list[ShotVerticalizado] = Field(default_factory=list)


__all__ = [
    "AtivoReenquadrado",
    "CandidatoShort",
    "CropVertical",
    "ElementoTelaShort",
    "FormulaShort",
    "FrasePonte",
    "IntervaloLegendaShort",
    "ManifestoVertical",
    "ModeloShort",
    "ResultadoDosagemShort",
    "SegmentoShort",
    "ShortParaVerificar",
    "ShotVerticalizado",
    "ViolacaoDosagemShort",
]
