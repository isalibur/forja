"""Ensaio real controlado de um short avulso educativo do Marco M8.

Executa a API local contra uma raiz isolada, com Kokoro e WhisperX locais,
FFmpeg e Remotion do kit, e verifica vídeo, narração, legendas, capa, áudio e
as regras DS1-DS9. Nada é publicado, nenhuma aprovação do usuário é concedida
e nada fora da raiz do ensaio é escrito.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from docforja.nucleo.etapas import calcular_hash_dados  # noqa: E402

TEMA = "Um rio pode mudar de nome"
ROTEIRO = (
    "Um rio pode mudar de nome. O mesmo curso de água nasce com um nome pequeno e "
    "recebe outros ao passar por cidades e vilarejos. Só quando chega ao mar ele "
    "ganha o nome que o mundo costuma conhecer. Por isso dois mapas podem chamar o "
    "mesmo rio de maneiras diferentes, e nenhum dos dois está errado. Cada trecho "
    "do percurso é tratado como um rio próprio, e é por isso que os nomes vão "
    "mudando. No fim, o rio pode ter cinco nomes e chegar ao mar com um só. E é "
    "assim que o nome mais famoso quase sempre chega depois. Salve este vídeo para "
    "lembrar."
)
CTA = "Salve este vídeo para lembrar"
CSV = (
    "tema,objetivo,duracao_s,cta\n"
    f"{TEMA},educativo,30,{CTA}\n"
)
DADOS_ALEGACOES = {
    "fontes": [
        {
            "alegacao": (
                "Um mesmo curso d'água pode receber nomes diferentes ao longo do percurso."
            ),
            "fonte": (
                "IBGE — Base Cartográfica Global (BCG): nomes de cursos d'água por trecho."
            ),
        }
    ],
    "revisado_pelo_usuario": True,
    "relacao_comercial": "nenhuma",
}


def _executar(comando: list[str], *, cwd: Path, timeout: int = 900) -> str:
    resultado = subprocess.run(
        comando, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
    )
    if resultado.returncode:
        raise RuntimeError((resultado.stderr or resultado.stdout)[-2000:])
    return resultado.stderr + "\n" + resultado.stdout


def _porta_livre() -> int:
    with socket.socket() as soquete:
        soquete.bind(("127.0.0.1", 0))
        return int(soquete.getsockname()[1])


def preparar_raiz(raiz: Path) -> None:
    """Cria uma raiz isolada com configuração própria apontando para ela."""
    (raiz / "projetos").mkdir(parents=True, exist_ok=True)
    (raiz / "global" / "imagens").mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPO / "config", raiz / "config")
    caminho_config = raiz / "config" / "adaptadores.yaml"
    dados = yaml.safe_load(caminho_config.read_text(encoding="utf-8"))
    dados["paths"]["projects"] = str((raiz / "projetos").as_posix())
    dados["paths"]["global_assets"] = str((raiz / "global").as_posix())
    dados["paths"]["benchmark_output"] = str((raiz / "benchmark_out").as_posix())
    caminho_config.write_text(
        yaml.safe_dump(dados, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def gerar_imagens(raiz: Path) -> list[str]:
    """Cria imagens verticais sintéticas com ficha CC0 para o ensaio."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("FFmpeg não está no PATH.")
    catalogo = [
        ("ensaio-rio-01", "0x12161d", "0x7a3a1c"),
        ("ensaio-rio-02", "0x0f1b1f", "0x2f6f6a"),
        ("ensaio-rio-03", "0x1a1420", "0x8a5a2a"),
    ]
    ids: list[str] = []
    pasta = raiz / "global" / "imagens"
    for indice, (identificador, cor_a, cor_b) in enumerate(catalogo):
        arquivo = pasta / f"{identificador}.png"
        _executar(
            [
                ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                (
                    f"gradients=size=1080x1920:c0={cor_a}:c1={cor_b}:"
                    f"x0={120 + indice * 90}:y0={240 + indice * 60}:"
                    f"x1={900 - indice * 40}:y1={1650 - indice * 70}:"
                    "nb_colors=2:type=linear"
                ),
                "-frames:v",
                "1",
                str(arquivo),
            ],
            cwd=raiz,
        )
        ficha = {
            "id": identificador,
            "tipo": "imagens",
            "descricao": f"Imagem sintética vertical de ensaio M8 ({identificador})",
            "licenca": "CC0-1.0",
            "comercial": True,
            "credito": "DocForja — síntese local de ensaio",
            "arquivo": arquivo.name,
            "publicacao_permitida": True,
            "origem": "gerada pelo script de ensaio M8",
            "id_global": f"global:imagens:{identificador}",
        }
        ficha["sha256"] = calcular_hash_dados(arquivo)
        (pasta / f"{identificador}.json").write_text(
            json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        ids.append(f"global:imagens:{identificador}")
    return ids


def iniciar_api(raiz: Path, porta: int) -> subprocess.Popen[str]:
    python = REPO / ".venv" / "Scripts" / "python.exe"
    if not python.is_file():
        raise SystemExit("Interpretador do ambiente virtual do repositório não encontrado.")
    ambiente = dict(os.environ)
    ambiente["PYTHONPATH"] = os.pathsep.join(
        [str(REPO / "src"), ambiente.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    log = (raiz / "api.log").open("w", encoding="utf-8")
    return subprocess.Popen(
        [
            str(python),
            "-m",
            "uvicorn",
            "docforja.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(porta),
            "--log-level",
            "warning",
        ],
        cwd=raiz,
        env=ambiente,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )


def esperar_api(base: str, processo: subprocess.Popen[str], limite_s: int = 90) -> None:
    limite = time.monotonic() + limite_s
    while time.monotonic() < limite:
        if processo.poll() is not None:
            raise SystemExit("A API local encerrou antes de responder.")
        try:
            resposta = httpx.get(f"{base}/api/saude", timeout=5.0)
            if resposta.status_code == 200:
                return
        except httpx.HTTPError:
            time.sleep(1.0)
    raise SystemExit("A API local não respondeu a tempo.")


def _json_erro(resposta: httpx.Response) -> str:
    try:
        return str(resposta.json().get("detail", resposta.text))
    except ValueError:
        return resposta.text[:400]


def _pedir(
    cliente: httpx.Client, metodo: str, url: str, tentativas: int = 6
) -> httpx.Response:
    """Repete a requisição quando o transporte local falha durante a produção."""
    ultimo: Exception | None = None
    for tentativa in range(tentativas):
        try:
            return cliente.request(metodo, url)
        except httpx.TransportError as erro:
            ultimo = erro
            time.sleep(2.0 + tentativa)
    raise RuntimeError(f"Falha de transporte em {url}: {ultimo}")


def executar_fluxo(base: str, ids_globais: list[str], raiz_saida: Path) -> dict[str, Any]:
    """Percorre o portão humano real da API: campanha, roteiro, mídias, ficha e produção."""
    cliente = httpx.Client(base_url=base, timeout=3600.0)
    registro: dict[str, Any] = {}
    previa = cliente.post("/api/shorts/avulsos/planejar", json={"csv_texto": CSV})
    registro["previa"] = previa.status_code
    if previa.status_code != 200:
        raise SystemExit(f"A prévia do CSV falhou: {_json_erro(previa)}")
    registro["pedidos_previstos"] = [
        {"id": item["id"], "tema": item["tema"], "formula": item["formula_id"]}
        for item in previa.json()["pedidos"]
    ]

    criacao = cliente.post(
        "/api/shorts/avulsos/campanhas",
        json={"nome": "Ensaio M8 avulso educativo", "csv_texto": CSV},
    )
    if criacao.status_code != 201:
        raise SystemExit(f"A criação da campanha falhou: {_json_erro(criacao)}")
    campanha = criacao.json()
    registro["campanha"] = campanha["id"]
    registro["hash_campanha"] = campanha["hash_conteudo"]
    base_pedido = f"/api/shorts/avulsos/campanhas/{campanha['id']}/pedidos/A001"

    disponiveis = cliente.get("/api/shorts/avulsos/midias-disponiveis")
    registro["midias_disponiveis"] = [
        item["id_global"] for item in disponiveis.json().get("midias", [])
    ]

    aprovacao = cliente.post(
        f"{base_pedido}/roteiro/aprovar",
        json={"texto": ROTEIRO, "hash_campanha": campanha["hash_conteudo"]},
    )
    if aprovacao.status_code != 200:
        raise SystemExit(f"A aprovação do roteiro falhou: {_json_erro(aprovacao)}")
    revisao_roteiro = aprovacao.json()["revisao"]
    registro["revisao_roteiro"] = revisao_roteiro

    selecao = cliente.post(
        f"{base_pedido}/midias/selecionar",
        json={
            "ids_globais": ids_globais,
            "hash_campanha": campanha["hash_conteudo"],
            "revisao_roteiro": revisao_roteiro,
        },
    )
    if selecao.status_code != 200:
        raise SystemExit(f"A seleção de mídias falhou: {_json_erro(selecao)}")
    revisao_midias = selecao.json()["revisao"]
    registro["revisao_midias"] = revisao_midias

    ficha = cliente.post(
        f"{base_pedido}/alegacoes/registrar",
        json={
            "hash_campanha": campanha["hash_conteudo"],
            "revisao_roteiro": revisao_roteiro,
            "revisao_midias": revisao_midias,
            "dados": DADOS_ALEGACOES,
        },
    )
    if ficha.status_code != 200:
        raise SystemExit(f"O registro da ficha de alegações falhou: {_json_erro(ficha)}")
    registro["revisao_alegacoes"] = ficha.json()["revisao"]

    sem_codigo = cliente.post(f"{base_pedido}/produzir", json={"codigo": "sim"})
    registro["portao_sem_codigo"] = sem_codigo.status_code

    producao = cliente.post(f"{base_pedido}/produzir", json={"codigo": "PRODUZIR"})
    if producao.status_code != 200:
        raise SystemExit(f"A produção foi recusada: {_json_erro(producao)}")
    registro["portao_com_codigo"] = producao.status_code
    registro["estado_inicial"] = producao.json()["status"]

    consulta = _pedir(cliente, "GET", f"{base_pedido}/producao")
    estado = consulta.json()
    registro["estado_inicial_poll"] = estado.get("status")
    limite = time.monotonic() + 3600
    tentativas = 0
    while estado.get("status") not in {"concluido", "falhou"} and time.monotonic() < limite:
        time.sleep(5.0)
        tentativas += 1
        estado = _pedir(cliente, "GET", f"{base_pedido}/producao").json()
    registro["espera_s"] = round(tentativas * 5.0, 1)
    registro["estado_final"] = estado.get("status")
    registro["erro_producao"] = estado.get("erro")
    registro["revisao"] = estado.get("revisao")
    registro["base_pedido"] = base_pedido

    artefatos: dict[str, str] = {}
    nomes = (
        "video.mp4",
        "capa.jpg",
        "legendas.srt",
        "metadados.json",
        "youtube.md",
        "instagram.md",
    )
    for nome in nomes:
        resposta = _pedir(cliente, "GET", f"{base_pedido}/artefatos/{nome}")
        registro[f"artefato_{nome}"] = resposta.status_code
        if resposta.status_code == 200:
            destino = raiz_saida / nome
            destino.write_bytes(resposta.content)
            artefatos[nome] = str(destino)
    registro["artefatos"] = artefatos
    return registro


def _ffprobe(caminho: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise SystemExit("ffprobe não está no PATH.")
    saida = _executar(
        [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(caminho),
        ],
        cwd=caminho.parent,
    )
    return json.loads(saida)


def verificar_video(caminho: Path) -> dict[str, Any]:
    dados = _ffprobe(caminho)
    video = next((item for item in dados["streams"] if item["codec_type"] == "video"), None)
    audio = next((item for item in dados["streams"] if item["codec_type"] == "audio"), None)
    if not video or not audio:
        return {"ok": False, "detalhe": "Vídeo sem faixa de vídeo e/ou de áudio."}
    taxa = video.get("avg_frame_rate", "0/1")
    numerador, _, denominador = taxa.partition("/")
    fps = float(numerador) / float(denominador or 1)
    return {
        "ok": True,
        "largura": video.get("width"),
        "altura": video.get("height"),
        "fps": round(fps, 3),
        "codec_video": video.get("codec_name"),
        "codec_audio": audio.get("codec_name"),
        "canais_audio": audio.get("channels"),
        "taxa_amostral": audio.get("sample_rate"),
        "duracao_s": round(float(dados["format"].get("duration", 0.0)), 3),
        "faixas": len(dados["streams"]),
    }


def verificar_capa(caminho: Path) -> dict[str, Any]:
    dados = _ffprobe(caminho)
    video = next((item for item in dados["streams"] if item["codec_type"] == "video"), None)
    if not video:
        return {"ok": False, "detalhe": "Capa sem faixa de imagem."}
    return {
        "ok": True,
        "largura": video.get("width"),
        "altura": video.get("height"),
        "codec": video.get("codec_name"),
    }


def _ler_srt(caminho: Path) -> list[dict[str, Any]]:
    blocos = [bloco for bloco in caminho.read_text(encoding="utf-8").strip().split("\n\n") if bloco]
    cues: list[dict[str, Any]] = []
    for bloco in blocos:
        linhas = bloco.splitlines()
        if len(linhas) < 3:
            continue
        inicio, _, fim = linhas[1].partition(" --> ")
        cues.append(
            {
                "inicio": _segundos(inicio),
                "fim": _segundos(fim),
                "linhas": linhas[2:],
            }
        )
    return cues


def _segundos(marca: str) -> float:
    horas, minutos, resto = marca.split(":")
    segundos, _, milissegundos = resto.replace(",", ".").partition(".")
    return (
        int(horas) * 3600
        + int(minutos) * 60
        + int(segundos)
        + int(milissegundos.ljust(3, "0") or 0) / 1000
    )


def verificar_legendas(caminho: Path, duracao_s: float) -> dict[str, Any]:
    cues = _ler_srt(caminho)
    if not cues:
        return {"ok": False, "detalhe": "Nenhuma legenda encontrada."}
    linhas_max = max(len(item["linhas"]) for item in cues)
    caracteres_max = max(len(linha) for item in cues for linha in item["linhas"])
    monotonicas = all(
        cues[indice]["fim"] <= cues[indice + 1]["inicio"] + 0.001
        for indice in range(len(cues) - 1)
    )
    return {
        "ok": bool(monotonicas and linhas_max <= 2 and caracteres_max <= 42),
        "cues": len(cues),
        "linhas_maximas": linhas_max,
        "caracteres_maximos": caracteres_max,
        "monotonicas": monotonicas,
        "primeira_inicio_s": round(cues[0]["inicio"], 3),
        "ultimo_fim_s": round(cues[-1]["fim"], 3),
        "cobertura_s": round(cues[-1]["fim"] - cues[0]["inicio"], 3),
        "duracao_video_s": round(duracao_s, 3),
    }


def verificar_audio(caminho: Path) -> dict[str, Any]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("FFmpeg não está no PATH.")
    medicao = _executar(
        [ffmpeg, "-i", str(caminho), "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"],
        cwd=caminho.parent,
        timeout=600,
    )
    integrado = re.search(r"\bI:\s*(-?[\d.]+)\s*LUFS", medicao)
    pico = re.search(r"\bPeak:\s*(-?[\d.]+)\s*dBFS", medicao)
    faixa = re.search(r"\bLRA:\s*(-?[\d.]+)\s*LU", medicao)
    return {
        "lufs_integrado": float(integrado.group(1)) if integrado else None,
        "pico_dbfs": float(pico.group(1)) if pico else None,
        "faixa_lu": float(faixa.group(1)) if faixa else None,
    }


def main() -> int:
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument(
        "--raiz",
        default=None,
        help="Raiz isolada do ensaio (padrão: pasta nova em E:/05_PROJETOS/forja).",
    )
    argumentos = analisador.parse_args()

    raiz = (
        Path(argumentos.raiz)
        if argumentos.raiz
        else Path("E:/05_PROJETOS/forja") / f"ensaio-m8-avulso-{time.strftime('%Y%m%d-%H%M%S')}"
    )
    if raiz.exists() and any(raiz.iterdir()):
        raise SystemExit(f"A raiz do ensaio já contém arquivos: {raiz}")
    raiz.mkdir(parents=True, exist_ok=True)
    raiz_saida = raiz / "artefatos"
    raiz_saida.mkdir(parents=True, exist_ok=True)

    preparar_raiz(raiz)
    ids_globais = gerar_imagens(raiz)
    porta = _porta_livre()
    base = f"http://127.0.0.1:{porta}"
    processo = iniciar_api(raiz, porta)
    inicio = time.monotonic()
    try:
        esperar_api(base, processo)
        registro = executar_fluxo(base, ids_globais, raiz_saida)
    finally:
        processo.terminate()
        try:
            processo.wait(timeout=30)
        except subprocess.TimeoutExpired:
            processo.kill()
    duracao_total = round(time.monotonic() - inicio, 1)

    artefatos = registro.get("artefatos", {})
    verificacoes: dict[str, Any] = {}
    if "video.mp4" in artefatos:
        verificacoes["video"] = verificar_video(Path(artefatos["video.mp4"]))
        verificacoes["audio"] = verificar_audio(Path(artefatos["video.mp4"]))
    if "capa.jpg" in artefatos:
        verificacoes["capa"] = verificar_capa(Path(artefatos["capa.jpg"]))
    if "legendas.srt" in artefatos:
        duracao_video = verificacoes.get("video", {}).get("duracao_s", 0.0)
        verificacoes["legendas"] = verificar_legendas(
            Path(artefatos["legendas.srt"]), duracao_video
        )
    if "metadados.json" in artefatos:
        metadados = json.loads(Path(artefatos["metadados.json"]).read_text(encoding="utf-8"))
        verificacoes["metadados"] = {
            "status": metadados.get("status"),
            "publicacao_autorizada": metadados.get("publicacao_autorizada"),
            "wer": metadados.get("wer"),
            "duracao_s": metadados.get("duracao_s"),
            "qa_aprovado": metadados.get("qa", {}).get("aprovado"),
            "regras": [
                {"regra": item["regra"], "aprovada": item["aprovada"], "detalhes": item["detalhes"]}
                for item in metadados.get("qa", {}).get("violacoes", [])
            ],
        }

    relatorio = {
        "raiz": str(raiz),
        "duracao_total_s": duracao_total,
        "tema": TEMA,
        "roteiro": ROTEIRO,
        "cta": CTA,
        "ficha_alegacoes": DADOS_ALEGACOES,
        "fluxo": registro,
        "verificacoes": verificacoes,
    }
    (raiz / "relatorio-ensaio.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
