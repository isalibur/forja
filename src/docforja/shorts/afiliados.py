"""Produtos de afiliado lidos de planilha, com as regras de honestidade de 15 §2.1."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

COLUNAS = {
    "nome",
    "descricao",
    "beneficios",
    "preco",
    "fonte_preco",
    "condicao",
    "link_afiliado",
    "imagens",
    "nicho",
    "plataforma",
    "marca",
    "cta",
    "duracao_s",
}
COLUNAS_OBRIGATORIAS = {"nome", "descricao", "beneficios", "link_afiliado"}
DURACOES = (15, 30, 45, 60)

TERMOS_PROIBIDOS = (
    "melhor do mundo",
    "o melhor",
    "melhor de todos",
    "garantido",
    "garantia vitalícia",
    "garantia vitalicia",
    "milagroso",
    "resultado garantido",
    "número um",
    "numero um",
    "imperdível",
    "imperdivel",
    "aprovado por médicos",
    "resultados reais garantidos",
)

Plataforma = Literal["youtube_shorts", "instagram_reels", "ambas"]
MAX_PALAVRAS_TELA = 6
MAX_BENEFICIOS = 3
CTA_PADRAO = "link na bio"
PADRAO_PRECO = re.compile(
    r"R\$|US\$|€|£|\bpre[cç]os?\b|\b\d+[.,]\d{2}\b|\b\d+\s*%|"
    r"\b(?:reais|dólares|dolares|euros)\b|\b(?:por|a partir de)\s+\d+(?:[.,]\d+)?\b",
    flags=re.IGNORECASE,
)


class ProdutoAfiliado(BaseModel):
    """Produto pronto para virar short; o link nunca é queimado no vídeo."""

    model_config = ConfigDict(extra="forbid", strict=True)

    nome: str = Field(min_length=1, max_length=120)
    descricao: str = Field(min_length=1, max_length=2000)
    beneficios: list[str] = Field(min_length=1, max_length=MAX_BENEFICIOS)
    preco: str | None = Field(default=None, max_length=60)
    fonte_preco: str | None = Field(default=None, max_length=1000)
    condicao: str | None = Field(default=None, max_length=60)
    link_afiliado: str = Field(min_length=8, max_length=1000)
    imagens: list[str] = Field(default_factory=list, max_length=20)
    nicho: str | None = Field(default=None, max_length=120)
    plataforma: Plataforma = "ambas"
    marca: str | None = Field(default=None, max_length=120)
    cta: str = CTA_PADRAO
    duracao_s: int = 30

    @model_validator(mode="after")
    def validar_honestidade(self) -> ProdutoAfiliado:
        if self.duracao_s not in DURACOES:
            raise ValueError("A duração do short deve ser 15, 30, 45 ou 60 segundos.")
        if not re.fullmatch(r"https://\S+", self.link_afiliado):
            raise ValueError("O link de afiliado precisa ser uma URL https válida.")
        if self.preco and not (self.fonte_preco or "").strip():
            raise ValueError("Preço na planilha exige fonte do preço.")
        if self.preco and not re.search(
            r"R\$|US\$|€|£|\d+", self.preco, flags=re.IGNORECASE
        ):
            raise ValueError("O preço informado não tem formato de valor reconhecido.")
        if self.condicao and not (self.fonte_preco or "").strip():
            raise ValueError("Condição comercial exige a fonte do preço na planilha.")
        for texto in (
            self.nome,
            *self.beneficios,
            self.preco or "",
            self.condicao or "",
        ):
            if texto and len(texto.split()) > MAX_PALAVRAS_TELA:
                raise ValueError(
                    f"Texto com mais de {MAX_PALAVRAS_TELA} palavras não cabe na tela: {texto!r}."
                )
        proibidos = [
            termo
            for termo in TERMOS_PROIBIDOS
            if termo in self.nome.lower()
            or termo in self.descricao.lower()
            or any(termo in beneficio.lower() for beneficio in self.beneficios)
        ]
        if proibidos:
            raise ValueError(
                "Expressão não permitida em conteúdo de afiliado: "
                + ", ".join(sorted(set(proibidos)))
            )
        if not self.imagens:
            raise ValueError("Informe ao menos uma imagem autorizada do produto.")
        for identificador in self.imagens:
            if not identificador.startswith("global:"):
                raise ValueError("As imagens do produto devem vir da Pasta Global.")
        return self


def _dividir(valor: str) -> list[str]:
    return [item.strip() for item in valor.split("|") if item.strip()]


def validar_sem_preco(produto: ProdutoAfiliado, roteiro: str | None = None) -> None:
    """Impede valores voláteis em entradas novas e em campanhas antigas ao produzir."""
    if (produto.preco or "").strip():
        raise ValueError("Retire o preço da planilha; a oferta será consultada pelo link.")
    textos = [
        produto.nome,
        produto.descricao,
        *produto.beneficios,
        produto.condicao or "",
        produto.cta,
        roteiro or "",
    ]
    if any(PADRAO_PRECO.search(texto) for texto in textos):
        raise ValueError("Retire preços e descontos numéricos do texto; use o link da oferta.")


def ler_planilha_produtos(texto_csv: str) -> list[ProdutoAfiliado]:
    """Lê a planilha de produtos e recusa linhas que quebrar as regras de honestidade."""
    leitor = csv.DictReader(io.StringIO(texto_csv.lstrip("\ufeff")))
    cabecalho = leitor.fieldnames or []
    if len(cabecalho) != len(set(cabecalho)):
        raise ValueError("Cabeçalho da planilha contém colunas duplicadas.")
    if COLUNAS_OBRIGATORIAS - set(cabecalho):
        raise ValueError(
            "A planilha exige as colunas " + ", ".join(sorted(COLUNAS_OBRIGATORIAS)) + "."
        )
    desconhecidas = set(cabecalho) - COLUNAS
    if desconhecidas:
        raise ValueError("Colunas desconhecidas na planilha: " + ", ".join(sorted(desconhecidas)))
    produtos: list[ProdutoAfiliado] = []
    for numero, linha in enumerate(leitor, start=2):
        if None in linha:
            raise ValueError(f"Linha {numero} da planilha tem mais valores que colunas.")
        if not any((valor or "").strip() for valor in linha.values()):
            continue
        dados = {chave: (valor or "").strip() for chave, valor in linha.items()}
        try:
            if dados.get("preco"):
                raise ValueError("Retire o preço da planilha; a oferta será consultada pelo link.")
            produto = ProdutoAfiliado.model_validate(
                {
                    "nome": dados["nome"],
                    "descricao": dados["descricao"],
                    "beneficios": _dividir(dados["beneficios"]),
                    "preco": dados.get("preco") or None,
                    "fonte_preco": dados.get("fonte_preco") or None,
                    "condicao": dados.get("condicao") or None,
                    "link_afiliado": dados["link_afiliado"],
                    "imagens": _dividir(dados.get("imagens", "")),
                    "nicho": dados.get("nicho") or None,
                    "plataforma": dados.get("plataforma") or "ambas",
                    "marca": dados.get("marca") or None,
                    "cta": dados.get("cta") or CTA_PADRAO,
                    "duracao_s": int(dados.get("duracao_s") or 30),
                }
            )
            validar_sem_preco(produto)
            produtos.append(produto)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Linha {numero} da planilha: {exc}") from exc
    if not produtos:
        raise ValueError("A planilha não contém produtos.")
    return produtos


def roteiro_sugerido(produto: ProdutoAfiliado) -> str:
    """Roteiro sem promessa inventada; serve de rascunho para a aprovação do usuário."""
    validar_sem_preco(produto)
    partes = [produto.descricao.strip()]
    for beneficio in produto.beneficios:
        partes.append(f"Em resumo, {beneficio}.")
    partes.append(f"Confira a oferta e as condições atuais: {produto.cta}.")
    return " ".join(partes)


def gerar_agenda_csv(linhas: list[dict[str, str]]) -> str:
    """Planilha de publicação no formato genérico de 15 §2.3."""
    buffer = io.StringIO()
    escritor = csv.writer(buffer, quoting=csv.QUOTE_ALL, lineterminator="\n")
    escritor.writerow(
        [
            "Plataforma",
            "Data",
            "Hora",
            "Arquivo_Video",
            "Arquivo_Capa",
            "Titulo",
            "Legenda",
            "Hashtags",
            "Link",
            "Aviso_Publicidade",
            "Status",
        ]
    )
    for linha in linhas:
        escritor.writerow(
            [
                linha.get("plataforma", ""),
                linha.get("data", ""),
                linha.get("hora", ""),
                linha.get("arquivo_video", ""),
                linha.get("arquivo_capa", ""),
                linha.get("titulo", ""),
                linha.get("legenda", "").replace("\n", " ").strip(),
                linha.get("hashtags", ""),
                linha.get("link", ""),
                linha.get("aviso_publicidade", ""),
                linha.get("status", "rascunho"),
            ]
        )
    return buffer.getvalue()


def caminho_planilha_padrao(raiz: Path) -> Path:
    """Caminho sugerido para a planilha de produtos na pasta do usuário."""
    return raiz / "planilha_produtos.csv"


def titulos_sugeridos(produto: ProdutoAfiliado) -> list[str]:
    """Títulos curtos para Shorts e Reels, sem promessa fora da planilha."""
    beneficio = produto.beneficios[0] if produto.beneficios else produto.nome
    candidatos = [
        f"{produto.nome}: {beneficio}",
        f"{beneficio} com {produto.nome}",
        f"{produto.nome} em uso",
    ]
    titulos: list[str] = []
    for candidato in candidatos:
        titulo = " ".join(candidato.split())[:40].rstrip(" ,;:-")
        if titulo and titulo not in titulos:
            titulos.append(titulo)
    return titulos


def hashtags_sugeridas(produto: ProdutoAfiliado) -> list[str]:
    """Hashtags do nicho, sem inventar programa de afiliados."""
    etiquetas = ["#Shorts", "#Reels", "#DocForja"]
    if produto.nicho:
        marca = "".join(caractere for caractere in produto.nicho if caractere.isalnum())
        if marca:
            etiquetas.insert(0, f"#{marca}")
    return etiquetas


def gerar_textos_plataforma(
    produto: ProdutoAfiliado, cta: str, gancho: str
) -> dict[str, str]:
    """Textos de publicação por plataforma; o link vai só aqui e na agenda."""
    hashtags = " ".join(hashtags_sugeridas(produto))
    titulos = titulos_sugeridos(produto)
    titulo = titulos[0] if titulos else produto.nome
    beneficios = "\n".join(f"· {item}" for item in produto.beneficios)
    validar_sem_preco(produto, gancho)
    condicao = f"\n\nCondição: {produto.condicao}" if produto.condicao else ""
    aviso = f"\n\n{AVISO_PUBLICIDADE} — {produto.marca or 'marca declarada'}."
    youtube = (
        f"# {titulo}\n\n{gancho}\n\n{beneficios}{condicao}{aviso}\n\n"
        "Confira a oferta e as condições atuais pelo link de afiliado:\n"
        f"{produto.link_afiliado}\n\n"
        f"{cta.capitalize()}.\n\n{hashtags}\n"
        "\nRASCUNHO — não publicar sem revisão factual, visual, sonora e do QA.\n"
    )
    instagram = (
        f"{gancho}\n\n{beneficios}{condicao}{aviso}\n\n"
        "Confira a oferta e as condições atuais pelo link de afiliado:\n"
        f"{produto.link_afiliado}\n\n{cta.capitalize()}.\n\n{hashtags}\n"
        "\nRASCUNHO — não publicar sem revisão factual, visual, sonora e do QA.\n"
    )
    return {
        "titulo": titulo,
        "titulos": "\n".join(f"{indice + 1}. {item}" for indice, item in enumerate(titulos)),
        "hashtags": hashtags,
        "youtube": youtube,
        "instagram": instagram,
    }


def linha_agenda(
    produto: ProdutoAfiliado,
    titulo: str,
    legenda: str,
    hashtags: str,
    data: str,
    hora: str,
    arquivos: dict[str, str],
) -> dict[str, str]:
    """Linha da planilha de publicação de 15 §2.3 para o short de afiliado."""
    return {
        "plataforma": produto.plataforma,
        "data": data,
        "hora": hora,
        "arquivo_video": arquivos.get("video", ""),
        "arquivo_capa": arquivos.get("capa", ""),
        "titulo": titulo,
        "legenda": legenda,
        "hashtags": hashtags,
        "link": produto.link_afiliado,
        "aviso_publicidade": f"{AVISO_PUBLICIDADE} — {produto.marca or 'marca declarada'}.",
        "status": "rascunho",
    }


AVISO_PUBLICIDADE = "Publicidade · link de afiliado"


__all__ = [
    "AVISO_PUBLICIDADE",
    "COLUNAS",
    "MAX_BENEFICIOS",
    "MAX_PALAVRAS_TELA",
    "ProdutoAfiliado",
    "caminho_planilha_padrao",
    "gerar_agenda_csv",
    "gerar_textos_plataforma",
    "hashtags_sugeridas",
    "ler_planilha_produtos",
    "linha_agenda",
    "roteiro_sugerido",
    "titulos_sugeridos",
    "validar_sem_preco",
]
