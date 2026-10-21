"""Gera amostras de voz para avaliação do usuário (motor Kokoro, qualidade final).

Sintetiza um trecho curto em cada voz escolhida, aplica a mesma cadeia de voz
usada na produção e grava os WAVs fora do repositório, com um índice em
Markdown. Nenhuma mídia entra no Git.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from docforja.audio.adaptadores.kokoro import AdaptadorKokoro  # noqa: E402
from docforja.audio.cadeia import aplicar_cadeia_voz  # noqa: E402

TEXTOS = {
    "p": (
        "A primeira hipótese estava errada. O que eles achavam que era um acidente "
        "era, na verdade, o começo de uma descoberta. E tudo por causa de uma "
        "rachadura na parede."
    ),
    "a": (
        "The first hypothesis was wrong. What they took for an accident was, in fact, "
        "the beginning of a discovery. And it all started with a crack in the wall."
    ),
    "b": (
        "The first hypothesis was wrong. What they took for an accident was, in fact, "
        "the beginning of a discovery. And it all started with a crack in the wall."
    ),
    "e": (
        "La primera hipótesis estaba equivocada. Lo que tomaban por un accidente era, "
        "en realidad, el comienzo de un descubrimiento. Y todo empezó con una grieta "
        "en la pared."
    ),
    "f": (
        "La première hypothèse était fausse. Ce qu'ils prenaient pour un accident "
        "était en réalité le début d'une découverte. Et tout a commencé par une "
        "fissure dans le mur."
    ),
    "i": (
        "La prima ipotesi era sbagliata. Ciò che scambiavano per un incidente era, "
        "in realtà, l'inizio di una scoperta. E tutto è cominciato con una crepa "
        "nel muro."
    ),
    "j": (
        "最初の仮説は間違っていた。彼らが事故だと思っていたものが、実は発見の始まりだった。"
        "すべては壁のひび割れから始まっていた。"
    ),
    "z": (
        "第一个假设是错的。他们以为是事故的东西, 其实是发现的开始。"
        "一切都从墙上的一道裂缝开始。"
    ),
    "h": (
        "पहला अनुमान गलत था। जिसे उन्होंने दुर्घटना समझा था, वह वास्तव में एक खोज की शुरुआत थी।"
        "और सब कुछ दीवार की दरार से शुरू हुआ।"
    ),
}

# Vozes escolhidas pela qualidade conhecida do modelo, priorizando pt-BR.
# A lista oficial do repositório hexgrad/Kokoro-82M tem 51 vozes; em português
# brasileiro existem apenas pm_alex, pm_santa e pf_dora.
VOZES = [
    ("pm_alex", "p", "Português (BR) · masculina"),
    ("pm_santa", "p", "Português (BR) · feminina"),
    ("pf_dora", "p", "Português (BR) · feminina"),
    ("af_heart", "a", "Inglês (EUA) · feminina"),
    ("af_bella", "a", "Inglês (EUA) · feminina"),
    ("af_nicole", "a", "Inglês (EUA) · feminina"),
    ("af_sarah", "a", "Inglês (EUA) · feminina"),
    ("am_michael", "a", "Inglês (EUA) · masculina"),
    ("bf_emma", "b", "Inglês (Reino Unido) · feminina"),
    ("ef_dora", "e", "Espanhol · feminina"),
    ("em_alex", "e", "Espanhol · masculina"),
    ("em_santa", "e", "Espanhol · feminina"),
    ("ff_siwis", "f", "Francês · feminina"),
    ("if_sara", "i", "Italiano · feminina"),
    ("jf_alpha", "j", "Japonês · feminina"),
    ("zf_xiaobei", "z", "Mandarim · feminina"),
    ("hf_alpha", "h", "Hindi · feminina"),
]


def gerar(destino: Path, voz: str, idioma: str) -> dict[str, object]:
    """Sintetiza a amostra e devolve os dados medidos do arquivo."""
    bruto = destino / "brutos" / f"{voz}.wav"
    final = destino / "amostras" / f"{voz}.wav"
    bruto.parent.mkdir(parents=True, exist_ok=True)
    final.parent.mkdir(parents=True, exist_ok=True)
    AdaptadorKokoro().gerar(
        TEXTOS[idioma], bruto, voz=voz, idioma=idioma, velocidade=1.0
    )
    aplicar_cadeia_voz(bruto, final)
    info = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(final),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    duracao = 0.0
    if info.returncode == 0:
        duracao = round(float(json.loads(info.stdout)["format"]["duration"]), 2)
    return {"voz": voz, "idioma": idioma, "duracao_s": duracao, "arquivo": final.name}


def main() -> int:
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument(
        "--destino",
        type=Path,
        default=Path("E:/05_PROJETOS/forja/estudos-voz"),
        help="Pasta de destino (fora do repositório).",
    )
    analisador.add_argument("--somente", nargs="*", help="Gera apenas estas vozes.")
    argumentos = analisador.parse_args()
    destino: Path = argumentos.destino
    destino.mkdir(parents=True, exist_ok=True)

    resultados: list[dict[str, object]] = []
    for voz, idioma, descricao in VOZES:
        if argumentos.somente and voz not in argumentos.somente:
            continue
        inicio = time.monotonic()
        try:
            registro = gerar(destino, voz, idioma)
        except Exception as erro:
            registro = {"voz": voz, "idioma": idioma, "erro": str(erro)[:300]}
        registro["descricao"] = descricao
        registro["segundos"] = round(time.monotonic() - inicio, 1)
        resultados.append(registro)
        print(json.dumps(registro, ensure_ascii=False), flush=True)

    linhas = [
        "# Amostras de voz — Kokoro 82M",
        "",
        "Trecho curto em cada voz, com a mesma cadeia de voz da produção "
        "(passa-alta, presença, compressão e redução leve de ruído). "
        "Velocidade natural (1.0), saída em 24 kHz mono.",
        "",
        "| Arquivo | Voz | Idioma | Duração |",
        "|---|---|---|---|",
    ]
    for registro in resultados:
        if "erro" in registro:
            linhas.append(
                f"| — | `{registro['voz']}` | {registro['idioma']} | "
                f"falhou: {registro['erro']} |"
            )
            continue
        linhas.append(
            f"| `{registro['arquivo']}` | `{registro['voz']}` | {registro['descricao']} | "
            f"{registro['duracao_s']} s |"
        )
    linhas.extend(
        [
            "",
            "A pasta `brutos/` traz a síntese antes da cadeia de voz, para comparação.",
            "As amostras em japonês e mandarim saem mais longas porque o fonemizador "
            "do Kokoro lê os ideogramas de forma literal.",
            "",
            "## Texto usado",
            "",
            "**Português (BR):** " + TEXTOS["p"],
            "",
            "**Inglês:** " + TEXTOS["a"],
            "",
            "**Espanhol:** " + TEXTOS["e"],
            "",
            "Ouça, escolha a voz do canal e registre em `00_entrada/opcoes.yaml` "
            "(`motor_tts`, `voz`).",
        ]
    )
    (destino / "LEIA-ME.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    (destino / "amostras.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    falhas = [item for item in resultados if "erro" in item]
    print(f"\n{len(resultados) - len(falhas)} amostras geradas, {len(falhas)} falhas.")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
