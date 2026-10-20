"""Teste manual da cadeia real E00-P6 com três segmentos do roteiro oficial.

Não faz parte da suíte unitária: usa Kokoro, WhisperX, GPU e deixa artefatos
numa pasta temporária sob E:/05_PROJETOS/forja para diagnóstico.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path

from docforja.audio.adaptadores.kokoro import AdaptadorKokoro
from docforja.audio.alinhamento import AlinhadorWhisperX
from docforja.audio.narracao import OrquestradorNarracao
from docforja.nucleo.executor import ExecutorPipeline
from docforja.nucleo.handlers import criar_executor_projeto, registrar_handlers_disponiveis
from docforja.nucleo.projeto import Projeto
from docforja.planejamento.leitura import ler_roteiro_formatado
from docforja.settings import load_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projeto", type=Path, help="Retoma um projeto de teste existente")
    parser.add_argument("--modelo-asr", help="Modelo ASR local para o teste")
    parser.add_argument(
        "--completo",
        action="store_true",
        help="Usa o roteiro oficial completo (116 segmentos em 9 blocos)",
    )
    parser.add_argument(
        "--ate",
        default="P6_verificador",
        help="Etapa alvo de execução (padrão: P6_verificador)",
    )
    args = parser.parse_args()
    if args.projeto:
        projeto = Projeto.carregar(args.projeto)
    else:
        origem = Path("docs/pipeline/04-roteiro.md")
        if args.completo:
            roteiro = origem.read_text(encoding="utf-8")
            nome = "p6-real-completo"
            prefix = "smoke-p6-completo-"
        else:
            bloco = ler_roteiro_formatado(origem.read_text(encoding="utf-8"))[0]
            segmentos = bloco.segmentos[:3]
            roteiro = f"## {bloco.id} — {bloco.nome}\n\n" + "\n\n".join(
                f"**{segmento.id}**\n{segmento.texto_original}" for segmento in segmentos
            )
            nome = "p6-real"
            prefix = "smoke-p6-"
        raiz = Path(tempfile.mkdtemp(prefix=prefix, dir="E:/05_PROJETOS/forja"))
        projeto = Projeto.criar(nome=nome, roteiro=roteiro, raiz_projetos=raiz)
    print(f"Projeto de teste: {projeto.raiz}", flush=True)
    if args.modelo_asr:
        ambientes = load_settings().python_environments
        orquestrador = OrquestradorNarracao(
            adaptador_tts=AdaptadorKokoro(python_path=ambientes.get("kokoro")),
            alinhador=AlinhadorWhisperX(
                python_path=ambientes.get("whisperx"), modelo=args.modelo_asr
            ),
        )
        executor = registrar_handlers_disponiveis(
            ExecutorPipeline(projeto), orquestrador=orquestrador
        )
    else:
        executor = criar_executor_projeto(projeto)
    status = asyncio.run(executor.executar(ate_etapa=args.ate))
    print(f"Etapas: {json.dumps(status, ensure_ascii=False)}", flush=True)
    qualidade = projeto.pastas.audio / "pt-BR" / "qualidade.json"
    if qualidade.is_file():
        dados = json.loads(qualidade.read_text(encoding="utf-8"))
        print(
            f"Qualidade: {dados['status']}, WER {dados['wer']:.2%} "
            f"(limite {dados['limite_wer']:.2%})",
            flush=True,
        )
    verificacao = projeto.pastas.plano / "verificacao.json"
    if verificacao.is_file():
        dados = json.loads(verificacao.read_text(encoding="utf-8"))
        print(f"Dosagem aprovada: {dados['aprovado']}", flush=True)
    resolvidos = projeto.pastas.plano / "ativos_resolvidos.json"
    if resolvidos.is_file():
        dados = json.loads(resolvidos.read_text(encoding="utf-8"))
        print(f"Ativos resolvidos: {dados.get('total_ativos', 0)}", flush=True)
    if status.get(args.ate) != "concluida":
        sys.exit(1)


if __name__ == "__main__":
    main()
