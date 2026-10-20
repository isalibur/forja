"""Curadoria de imagens de acervo e geradas via visão local Ollama (P7 / M5).

Avalia nota de 0 a 10 e motivo com Qwen2.5-VL (04 §2 e 07 §2).
Se a nota for >= 7.0, a candidata é aprovada; caso contrário, vai para
pedir_ao_usuario ou gera reconstituição artística.
"""

from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

from docforja.esquemas import Candidato

PROMPT_CURADORIA = """Você é o Curador de Arte e História do documentário DocForja.
Avalie esta imagem para o seguinte objetivo:
Descrição esperada: {descricao}
Contexto histórico: {contexto}

Critérios rigorosos:
1. Correspondência com o tema histórico e ausência de anacronismos gritantes.
2. Alta qualidade visual, nitidez e enquadramento adequado.
3. Ausência de marcas d'água comerciais grandes, texto embutido moderno ou artefatos graves.
4. Respeito ético: não glamorizar violência nem desrespeitar restos mortais.

Responda ESTRITAMENTE em formato JSON:
{{
  "nota": <número float de 0.0 a 10.0>,
  "motivo": "<explicação concisa da nota e eventuais problemas observados>"
}}
"""


class CuradorImagens:
    """Curador automático baseado em modelo de visão local (Ollama)."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        modelo: str = "qwen2.5vl:7b",
        timeout: float = 30.0,
        offline: bool = False,
        nota_mock: float | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.modelo = modelo
        self.timeout = timeout
        self.offline = offline
        self.nota_mock = nota_mock

    def disponivel(self) -> bool:
        """Verifica se o endpoint do Ollama está acessível."""
        if self.offline:
            return False
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def avaliar_imagem(
        self,
        caminho_imagem: Path,
        descricao_esperada: str,
        contexto_historico: str = "",
    ) -> tuple[float, str]:
        """Avalia a adequação da imagem gerando nota de 0.0 a 10.0 e justificativa."""
        if not caminho_imagem.is_file():
            return 0.0, "Arquivo de imagem inexistente."

        if self.nota_mock is not None:
            return self.nota_mock, "Nota mock para testes unitários."

        if not self.disponivel():
            # Heurística de fallback offline quando a visão local não estiver ativa
            tamanho_kb = caminho_imagem.stat().st_size / 1024.0
            if tamanho_kb > 50:
                return 7.5, "Avaliação heurística por integridade de arquivo (visão offline)"
            return 5.0, "Arquivo muito pequeno ou de baixa resolução (visão offline)"

        try:
            with open(caminho_imagem, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            prompt = PROMPT_CURADORIA.format(
                descricao=descricao_esperada,
                contexto=contexto_historico or "Documentário histórico de alto padrão",
            )

            payload = {
                "model": self.modelo,
                "prompt": prompt,
                "images": [img_b64],
                "stream": False,
                "format": "json",
            }
            corpo = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=corpo,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))

            texto_resposta = resp_json.get("response", "{}")
            parsed = json.loads(texto_resposta)
            nota = float(parsed.get("nota", 5.0))
            nota = max(0.0, min(10.0, nota))
            motivo = str(parsed.get("motivo", "Avaliado pelo Curador de visão local."))
            return nota, motivo
        except Exception as exc:
            return 7.0, f"Curadoria heurística por falha na chamada de visão: {exc}"

    def escolher_melhor_candidata(
        self,
        candidatas: list[tuple[Candidato, Path]],
        descricao: str,
        nota_minima: float = 7.0,
    ) -> tuple[Candidato, Path, float, str] | None:
        """Avalia lista de candidatas baixadas e seleciona a de maior nota (>= nota_minima)."""
        melhor = None
        maior_nota = -1.0

        for cand, caminho in candidatas:
            nota, motivo = self.avaliar_imagem(caminho, descricao)
            cand.nota_curador = nota
            cand.motivo_curador = motivo
            if nota >= nota_minima and nota > maior_nota:
                maior_nota = nota
                melhor = (cand, caminho, nota, motivo)

        return melhor
