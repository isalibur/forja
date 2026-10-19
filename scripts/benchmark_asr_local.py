"""Compara um modelo ASR local com o roteiro de um projeto de teste.

Uso manual; não integra a suíte unitária e não baixa modelos.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from docforja.audio.alinhamento import AlinhadorWhisperX
from docforja.audio.metricas import calcular_wer
from docforja.io import atomic_write_json
from docforja.nucleo.gpu import semaforo_gpu
from docforja.nucleo.projeto import Projeto
from docforja.planejamento.leitura import ler_roteiro_formatado
from docforja.settings import load_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projeto", type=Path, required=True)
    parser.add_argument("--modelo", required=True)
    args = parser.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    projeto = Projeto.carregar(args.projeto)
    idioma = projeto.obter_opcoes().get("idiomas", {}).get("principal", "pt-BR")
    wav = projeto.pastas.audio / idioma / "narracao_completa.wav"
    if not wav.is_file():
        raise FileNotFoundError(wav)
    segmentos = [
        segmento
        for bloco in ler_roteiro_formatado(projeto.obter_roteiro())
        for segmento in bloco.segmentos
    ]
    referencia = " ".join(item.texto_limpo for item in segmentos)
    nome_modelo = Path(args.modelo).name
    pasta = projeto.pastas.sistema / "benchmark_asr" / nome_modelo
    pasta.mkdir(parents=True, exist_ok=True)
    alinhador = AlinhadorWhisperX(
        python_path=load_settings().python_environments.get("whisperx"),
        modelo=args.modelo,
    )
    inicio = time.perf_counter()
    with semaforo_gpu.adquirir_sync(modelo="whisper", tarefa="benchmark_asr", projeto=projeto.slug):
        alinhador.alinhar(
            audio_wav=wav,
            saida_palavras=pasta / "palavras.json",
            saida_segmentos=pasta / "segmentos.json",
            idioma=idioma.split("-")[0].lower(),
        )
    duracao = round(time.perf_counter() - inicio, 2)
    hipotese = " ".join(
        item.get("texto", "")
        for item in json.loads((pasta / "segmentos.json").read_text(encoding="utf-8"))
    )
    resultado = {
        "modelo": args.modelo,
        "duracao_s": duracao,
        "palavras_referencia": len(referencia.split()),
        "wer_bruto": calcular_wer(referencia, hipotese),
        "wer_normalizado": calcular_wer(referencia, hipotese, idioma=idioma),
        "transcricao": hipotese,
    }
    atomic_write_json(pasta / "resultado.json", resultado)
    print(
        f"{nome_modelo}: WER {resultado['wer_normalizado']:.2%}, "
        f"bruto {resultado['wer_bruto']:.2%}, {duracao:.1f} s; {pasta}",
        flush=True,
    )


if __name__ == "__main__":
    main()
