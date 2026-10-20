"""Adaptadores de busca e download em acervos de imagens abertas (P7 / M5).

Implementa o protocolo AcervoAdapter (07 §2) para Wikimedia Commons, AIC, Met,
Openverse, etc., com filtros de resolução, licença comercial e patrimônio restrito.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Protocol, runtime_checkable

from docforja.esquemas import Candidato
from docforja.midia.licenca import (
    FichaLicenca,
    classificar_licenca,
    detectar_patrimonio_restrito,
    salvar_ficha_licenca,
)


@runtime_checkable
class AcervoAdapter(Protocol):
    """Protocolo oficial para adaptadores de acervos públicos e de arquivo."""

    nome: str

    def buscar(self, consulta: str, limite: int = 5) -> list[Candidato]:
        """Busca imagens correspondentes à consulta textual."""
        ...

    def baixar(self, candidato: Candidato, destino: Path) -> Path:
        """Faz o download da imagem em alta resolução e gera seu sidecar .licenca.json."""
        ...


class AdaptadorAcervoMock:
    """Adaptador de acervo sintético para testes unitários rápidos e determinísticos."""

    def __init__(self, candidatos: list[Candidato] | None = None, nome: str = "mock") -> None:
        self.nome = nome
        self._candidatos = candidatos or []

    def buscar(self, consulta: str, limite: int = 5) -> list[Candidato]:
        if not self._candidatos:
            # Retorna candidato sintético válido
            c = Candidato(
                id=f"{self.nome}-1",
                origem=self.nome,
                url_origem=f"https://acervo.local/{self.nome}/1",
                url_download=f"https://acervo.local/{self.nome}/1.jpg",
                autor="Acervo Histórico",
                licenca="CC BY-SA 4.0",
                comercial=True,
                patrimonio_restrito=detectar_patrimonio_restrito(consulta),
                largura=1920,
                altura=1080,
            )
            return [c][:limite]
        return self._candidatos[:limite]

    def baixar(self, candidato: Candidato, destino: Path) -> Path:
        destino.parent.mkdir(parents=True, exist_ok=True)
        # Cria arquivo de imagem mínimo ou placeholder
        destino.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
        salvar_ficha_licenca(
            destino,
            FichaLicenca(
                url_origem=candidato.url_origem,
                autor=candidato.autor,
                licenca=candidato.licenca,
                comercial=candidato.comercial,
                patrimonio_restrito=candidato.patrimonio_restrito,
                texto_credito=f"{candidato.autor} / {candidato.licenca}",
            ),
        )
        return destino


class AdaptadorWikimedia:
    """Adaptador de pesquisa e download na Wikimedia Commons via API oficial."""

    def __init__(
        self,
        user_agent: str = "DocForja/0.1 (contato: docforja@local.net)",
        timeout: float = 10.0,
    ) -> None:
        self.nome = "wikimedia"
        self.user_agent = user_agent
        self.timeout = timeout

    def buscar(self, consulta: str, limite: int = 5) -> list[Candidato]:
        base_url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"file:{consulta}",
            "gsrnamespace": "6",  # Espaço File
            "gsrlimit": str(limite * 2),
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata",
            "format": "json",
        }
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                dados = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return []

        paginas = dados.get("query", {}).get("pages", {})
        candidatos: list[Candidato] = []

        for pid, pagina in paginas.items():
            infos = pagina.get("imageinfo", [])
            if not infos:
                continue
            info = infos[0]
            largura = int(info.get("width", 0))
            altura = int(info.get("height", 0))

            # Exige lado maior >= 1600 px conforme regra 04 §2
            if max(largura, altura) < 1600:
                continue

            meta = info.get("extmetadata", {})
            licenca_nome = meta.get("LicenseShortName", {}).get("value", "")
            autor = meta.get("Artist", {}).get("value", "Desconhecido")
            # Remove tags HTML simples do autor
            autor_limpo = " ".join(autor.split())

            comercial, _ = classificar_licenca(licenca_nome)
            # Descarta NC e ND
            if not comercial:
                continue

            titulo = pagina.get("title", "")
            descricao = meta.get("ImageDescription", {}).get("value", "")
            restrito = detectar_patrimonio_restrito(consulta, titulo, descricao)

            url_download = info.get("url", "")
            url_origem = info.get("descriptionurl", url_download)

            candidatos.append(
                Candidato(
                    id=f"wiki-{pid}",
                    origem=self.nome,
                    url_origem=url_origem,
                    url_download=url_download,
                    autor=autor_limpo,
                    licenca=licenca_nome,
                    comercial=comercial,
                    patrimonio_restrito=restrito,
                    largura=largura,
                    altura=altura,
                )
            )
            if len(candidatos) >= limite:
                break

        return candidatos

    def baixar(self, candidato: Candidato, destino: Path) -> Path:
        destino.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(
            candidato.url_download, headers={"User-Agent": self.user_agent}
        )
        with urllib.request.urlopen(req, timeout=self.timeout * 2) as resp:
            conteudo = resp.read()

        destino.write_bytes(conteudo)
        salvar_ficha_licenca(
            destino,
            FichaLicenca(
                url_origem=candidato.url_origem,
                autor=candidato.autor,
                licenca=candidato.licenca,
                comercial=candidato.comercial,
                patrimonio_restrito=candidato.patrimonio_restrito,
                texto_credito=f"{candidato.autor} / {candidato.licenca} (via Wikimedia Commons)",
            ),
        )
        return destino
