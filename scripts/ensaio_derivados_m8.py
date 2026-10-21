"""Ensaio isolado de três Shorts derivados, sem aprovação editorial ou publicação."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from docforja.io import atomic_write_json  # noqa: E402

SLUG = "vesuvio-teste-roteiro"


def preparar_copia(origem: Path, raiz: Path) -> Path:
    """Copia somente os insumos de leitura e substitui mídias pendentes por fundo de ensaio."""
    from ensaio_avulso_m8 import preparar_raiz

    if raiz.exists():
        raise ValueError(f"A raiz de ensaio já existe: {raiz}")
    preparar_raiz(raiz)
    projeto = raiz / "projetos" / SLUG
    for pasta in ("00_entrada", "01_plano", "03_audio", "sistema"):
        (projeto / pasta).mkdir(parents=True, exist_ok=True)
    for nome in ("opcoes.yaml", "roteiro.md"):
        fonte = origem / "00_entrada" / nome
        if fonte.is_file():
            shutil.copy2(fonte, projeto / "00_entrada" / nome)
    for nome in ("plano.json", "ativos_resolvidos.json"):
        shutil.copy2(origem / "01_plano" / nome, projeto / "01_plano" / nome)
    audio = projeto / "03_audio" / "pt-BR"
    audio.mkdir(parents=True)
    for nome in ("narracao_completa.wav", "segmentos.json", "palavras.json"):
        shutil.copy2(origem / "03_audio" / "pt-BR" / nome, audio / nome)
    shutil.copy2(origem / "sistema" / "banco.db", projeto / "sistema" / "banco.db")

    fundo = projeto / "02_midias" / "geradas" / "fundo-sintetico-ensaio.png"
    fundo.parent.mkdir(parents=True)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg não encontrado")
    comando = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "gradients=size=1080x1920:c0=0x12161d:c1=0x7a3a1c:"
        "x0=120:y0=240:x1=900:y1=1650:nb_colors=2:type=linear",
        "-frames:v",
        "1",
        str(fundo),
    ]
    resultado = subprocess.run(comando, capture_output=True, text=True, check=False)
    if resultado.returncode:
        raise RuntimeError(resultado.stderr[-1200:])
    resolvidos_path = projeto / "01_plano" / "ativos_resolvidos.json"
    resolvidos = json.loads(resolvidos_path.read_text(encoding="utf-8"))
    for ativo in resolvidos["ativos"].values():
        ativo["descricao"] = "Fundo abstrato sintético de ensaio; não representa patrimônio real"
        ativo["caminho"] = str(fundo)
        ativo["licenca"] = {"licenca": "CC0-1.0", "comercial": True}
    atomic_write_json(resolvidos_path, resolvidos)
    return projeto


def executar(raiz: Path) -> dict[str, Any]:
    os.chdir(raiz)
    from docforja.api import app

    cliente = TestClient(app)
    url = f"/api/projetos/{SLUG}/shorts/derivados"
    resposta = cliente.get(url)
    resposta.raise_for_status()
    candidatos = resposta.json()["candidatos"][:3]
    if len(candidatos) != 3:
        raise RuntimeError("O plano precisa oferecer três candidatos.")
    relatorio: dict[str, Any] = {
        "tipo": "ensaio_sintetico_sem_aprovacao_editorial",
        "origem": SLUG,
        "sem_publicacao": True,
        "candidatos": [],
    }
    for item in candidatos:
        ref = item["referencia"]
        candidato = item["candidato"]
        caminho = f"{url}/{ref}"
        registro: dict[str, Any] = {
            "referencia": ref,
            "segmentos": candidato["segmento_ids"],
            "inicio_s": candidato["inicio_s"],
            "fim_s": candidato["fim_s"],
            "pontuacao": candidato["pontuacao"],
            "ponte": candidato["frases_ponte"][0]["texto"],
            "ponte_status": "simulada_somente_para_ensaio",
        }
        relatorio["candidatos"].append(registro)
        aprovacao = cliente.post(f"{caminho}/aprovar", json={"indice_frase": 0})
        aprovacao.raise_for_status()
        plano = json.loads(
            (raiz / "projetos" / SLUG / "01_plano" / "plano.json").read_text(encoding="utf-8")
        )
        ids = set(candidato["segmento_ids"])
        dimensoes = {
            ativo_id: [1080, 1920]
            for bloco in plano["blocos"]
            for shot in bloco["shots"]
            if ids.intersection(shot["segmentos"])
            for ativo_id in shot["ativos"]
        }
        manifesto = cliente.post(
            f"{caminho}/manifesto-vertical",
            json={"dimensoes": dimensoes, "estrategia": "recorte"},
        )
        manifesto.raise_for_status()
        registro["shots_verticalizados"] = len(manifesto.json()["manifesto"]["shots"])
        producao = cliente.post(f"{caminho}/produzir")
        producao.raise_for_status()
        estado = cliente.get(url).json()["candidatos"]
        atual = next(c["producao"] for c in estado if c["referencia"] == ref)
        registro["producao"] = atual
        if atual.get("status") != "concluido":
            raise RuntimeError(f"Produção não concluída para {ref}: {atual}")
        video = Path(atual["resultado"]["caminho_video"])
        if not video.is_file():
            raise RuntimeError(f"Vídeo ausente: {video}")
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            raise RuntimeError("FFprobe não encontrado")
        sondagem = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "json",
                str(video),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if sondagem.returncode:
            raise RuntimeError(sondagem.stderr[-1000:])
        stream = json.loads(sondagem.stdout)["streams"][0]
        registro["dimensoes_video"] = [stream["width"], stream["height"]]
        if registro["dimensoes_video"] != [1080, 1920]:
            raise RuntimeError(f"Vídeo fora de 9:16: {video}")
        atomic_write_json(raiz / "relatorio.json", relatorio)
    return relatorio


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--origem",
        type=Path,
        default=Path("E:/05_PROJETOS/forja/projetos") / SLUG,
    )
    parser.add_argument("--raiz", type=Path)
    args = parser.parse_args()
    origem = args.origem.resolve()
    raiz = (
        args.raiz
        or Path("E:/05_PROJETOS/forja") / f"ensaio-m8-derivados-{datetime.now():%Y%m%d-%H%M%S}"
    ).resolve()
    if not origem.is_dir():
        raise SystemExit(f"Projeto de origem ausente: {origem}")
    preparar_copia(origem, raiz)
    print(f"Ensaio isolado em {raiz}", flush=True)
    relatorio = executar(raiz)
    print(json.dumps(relatorio, ensure_ascii=False, indent=2), flush=True)
    if any(not item["producao"]["resultado"]["qa_aprovado"] for item in relatorio["candidatos"]):
        raise SystemExit("Ensaio gerado, mas DS1-DS9 não passou; veja relatorio.json.")


if __name__ == "__main__":
    main()
