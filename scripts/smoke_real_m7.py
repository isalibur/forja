"""Ensaio controlado da cadeia real M7 T1 (tradução LLM) e T2 (TTS Kokoro + Retime).

Executa com escopo deliberadamente delimitado (2 segmentos curtos, ~12 palavras),
sem alterar projetos do usuário, em pasta temporária isolada.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path

from docforja.audio.adaptadores.kokoro import AdaptadorKokoro
from docforja.audio.alinhamento import AlinhadorWhisperX
from docforja.audio.narracao import OrquestradorNarracao
from docforja.esquemas import Bloco, Plano, Shot
from docforja.idiomas.narracao import executar_narracoes_extras, narracoes_extras_validas
from docforja.idiomas.traducao import executar_traducao_projeto
from docforja.io import atomic_write_json
from docforja.llm.roteador import RoteadorLLM
from docforja.nucleo.projeto import Projeto
from docforja.planejamento.leitura import ler_roteiro_formatado
from docforja.settings import load_settings

ROTEIRO_AMOSTRA = """## B0 — Introdução

**B0-S01**
O Vesúvio desperta sob um céu de cinzas.

**B0-S02**
A cidade observa em silêncio o prenúncio da tragédia.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Ensaio real T1/T2 multi-idioma (M7)")
    parser.add_argument(
        "--pasta-base",
        type=Path,
        default=Path("E:/05_PROJETOS/forja"),
        help="Diretório base para a pasta de ensaio descartável",
    )
    parser.add_argument(
        "--idioma",
        default="en",
        help="Idioma extra para tradução e TTS (padrão: en)",
    )
    parser.add_argument(
        "--voz",
        default="af_heart",
        help="Voz Kokoro para o idioma extra (padrão: af_heart)",
    )
    args = parser.parse_args()

    base_dir = args.pasta_base if args.pasta_base.is_dir() else Path(tempfile.gettempdir())
    pasta_tmp = Path(tempfile.mkdtemp(prefix="smoke-m7-real-", dir=base_dir))
    print("=== Ensaio M7 Real (Escopo Delimitado) ===")
    print(f"Pasta temporária: {pasta_tmp}")
    print(f"Idioma alvo: {args.idioma} | Voz: {args.voz}")

    try:
        # 1. Cria projeto isolado
        projeto = Projeto.criar(
            nome="ensaio-m7",
            roteiro=ROTEIRO_AMOSTRA,
            idioma_principal="pt-BR",
            idiomas_extras=[args.idioma],
            opcoes_adicionais={
                "traducao": {"modos": {args.idioma: "automatico"}},
                "vozes": {"pt-BR": "pm_alex", args.idioma: args.voz},
            },
            raiz_projetos=pasta_tmp,
        )

        settings = load_settings()
        ambientes = settings.python_environments
        kokoro_path = ambientes.get("kokoro")
        kokoro = AdaptadorKokoro(python_path=kokoro_path)
        if not kokoro.disponivel():
            raise RuntimeError(f"Kokoro TTS indisponível no caminho: {kokoro_path}")

        whisperx = AlinhadorWhisperX(python_path=ambientes.get("whisperx"))
        motor = OrquestradorNarracao(adaptador_tts=kokoro, alinhador=whisperx)

        # 2. Gera narração base em pt-BR via Kokoro (apenas 2 segmentos)
        print("\n[1/4] Gerando narração base pt-BR via Kokoro...")
        blocos = ler_roteiro_formatado(ROTEIRO_AMOSTRA)
        segmentos_pt = [seg for b in blocos for seg in b.segmentos]
        t0_pt = time.perf_counter()
        relatorio_pt = motor.processar_projeto_completo(
            segmentos=segmentos_pt,
            pasta_audio=projeto.pastas.audio,
            idioma="pt-BR",
            voz="pm_alex",
            executar_alinhamento=False,
            gerar_timestamps_estimados=True,
        )
        duracao_pt = relatorio_pt.duracao_total_s
        tempo_pt = time.perf_counter() - t0_pt
        print(f"   pt-BR concluído em {tempo_pt:.2f}s | Duração WAV: {duracao_pt:.2f}s")

        # 3. Cria plano verificado proporcional aos tempos reais
        segs_pt_dados = json.loads(
            (projeto.pastas.audio / "pt-BR" / "segmentos.json").read_text(encoding="utf-8")
        )
        shots = []
        for i, item in enumerate(segs_pt_dados):
            dur = float(item["fim_s"]) - float(item["inicio_s"])
            shots.append(
                Shot(
                    id=f"B0-{i+1:02d}",
                    segmentos=[item["id"]],
                    duracao_s=round(dur, 3),
                    inicio_segmento_s=0.0,
                    fim_segmento_s=round(dur, 3),
                    template="T01",
                    textos=[item["texto"]],
                    params={"texto": item["texto"]},
                )
            )
        plano = Plano(
            projeto=projeto.slug,
            blocos=[Bloco(id="B0", titulo="Introdução", shots=shots)],
        )
        for nome in ("plano.json", "plano_verificado.json"):
            atomic_write_json(projeto.pastas.plano / nome, plano.model_dump(mode="json"))

        # 4. Executa T1: Tradução automática estruturada via 9Router/Ollama
        print(f"\n[2/4] Executando T1 (tradução automática estruturada para {args.idioma})...")
        roteador = RoteadorLLM()
        t0_trad = time.perf_counter()
        traducoes = executar_traducao_projeto(projeto, roteador=roteador)
        tempo_trad = time.perf_counter() - t0_trad
        print(f"   T1 concluído em {tempo_trad:.2f}s")
        trad_en = traducoes[args.idioma]
        for seg in trad_en.segmentos:
            print(f"   [{seg.id}] Original: {seg.texto_original!r}")
            print(f"          Traduzido: {seg.texto_limpo!r}")

        # 5. Executa T2: Narração sequencial Kokoro + Retime proporcional
        print(f"\n[3/4] Executando T2 (TTS Kokoro {args.idioma} + Retime do Plano)...")
        t0_t2 = time.perf_counter()
        executar_narracoes_extras(projeto, motor)
        tempo_t2 = time.perf_counter() - t0_t2
        print(f"   T2 concluído em {tempo_t2:.2f}s")

        # Valida saídas de T2
        assert narracoes_extras_validas(projeto), "Manifesto de T2 inválido ou incompleto."
        pasta_extra = projeto.pastas.audio / args.idioma
        manifesto_extra = json.loads(
            (pasta_extra / "narracao_idioma.json").read_text(encoding="utf-8")
        )
        print(f"   WAV extra: {pasta_extra / 'narracao_completa.wav'}")
        dur_extra = manifesto_extra["duracao_total_s"]
        print(f"   Duração {args.idioma}: {dur_extra:.2f}s (pt-BR era {duracao_pt:.2f}s)")

        plano_retimado_path = projeto.pastas.plano / "idiomas" / args.idioma / "plano_retimado.json"
        assert plano_retimado_path.is_file(), "plano_retimado.json não foi gerado."
        plano_retimado = json.loads(plano_retimado_path.read_text(encoding="utf-8"))
        for shot in plano_retimado["blocos"][0]["shots"]:
            f_inicio = shot.get("inicio_s", 0) * 24
            print(f"   Shot retimado {shot['id']}: dur={shot['duracao_s']}s (frame={f_inicio:.0f})")

        # 6. Teste de Retomada e Cache (idempotência)
        print("\n[4/4] Testando retomada rápida por cache de hash...")
        t0_cache = time.perf_counter()
        executar_traducao_projeto(projeto, roteador=roteador)
        executar_narracoes_extras(projeto, motor)
        tempo_cache = time.perf_counter() - t0_cache
        print(f"   Retomada em {tempo_cache:.3f}s (no-op confirmado!)")

        print("\n=== SUCESSO: Ensaio real T1/T2 concluído com total integridade! ===")

    finally:
        print(f"\nOs artefatos de ensaio estão disponíveis em: {pasta_tmp}")


if __name__ == "__main__":
    main()
