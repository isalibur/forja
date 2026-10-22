"""Ensaio isolado dos cinco objetivos de avulsos do aceite M8.

Cria mídia sintética, aprova apenas dados fictícios dentro da raiz do ensaio,
renderiza cinco rascunhos locais e verifica os pacotes. Não publica nada.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ensaio_avulso_m8 import (
    _executar,
    _json_erro,
    _pedir,
    _porta_livre,
    esperar_api,
    gerar_imagens,
    iniciar_api,
    preparar_raiz,
    verificar_capa,
    verificar_legendas,
    verificar_video,
)

from docforja.nucleo.etapas import calcular_hash_dados

CASOS = [
    {
        "tema": "Um rio e seus nomes",
        "objetivo": "educativo",
        "formula": "lista_3",
        "cta": "Salve este vídeo para lembrar",
        "roteiro": (
            "Um rio pode mudar de nome. O mesmo curso de água nasce com um nome pequeno e "
            "recebe outros ao passar por cidades e vilarejos. Só quando chega ao mar ele "
            "ganha o nome que o mundo costuma conhecer. Por isso dois mapas podem chamar o "
            "mesmo rio de maneiras diferentes, e nenhum dos dois está errado. Cada trecho "
            "do percurso é tratado como um rio próprio, e é por isso que os nomes vão "
            "mudando. No fim, o rio pode ter cinco nomes e chegar ao mar com um só. E é "
            "assim que o nome mais famoso quase sempre chega depois. Salve este vídeo para "
            "lembrar."
        ),
    },
    {
        "tema": "Bastidores do canal",
        "objetivo": "bastidores",
        "formula": "bastidores",
        "cta": "Acompanhe o canal para mais",
        "roteiro": (
            "Como fazemos um vídeo? Este é um ensaio visual de bastidores, não a gravação "
            "de uma produção real. Primeiro, separamos uma ideia pequena e escrevemos o que "
            "o público precisa entender. Depois, organizamos três exemplos de imagem para "
            "testar ritmo, cortes e espaço das legendas. Por fim, ouvimos a narração e "
            "conferimos se cada frase cabe na tela sem correr. Os clipes que aparecem aqui "
            "são padrões gerados para teste; eles não mostram pessoas, locais ou métodos de "
            "trabalho verdadeiros. Acompanhe o canal para mais."
        ),
    },
    {
        "tema": "Escolha de cidades",
        "objetivo": "engajamento",
        "formula": "pergunta_comentarios",
        "opcao_a": "Pompeia",
        "opcao_b": "Herculano",
        "cta": "Comente A ou B",
        "roteiro": (
            "Qual cidade? Nesta simulação de enquete, você escolhe qual nome gostaria "
            "de ver em um próximo exemplo do canal. A opção A é Pompeia; a opção B é "
            "Herculano. A pergunta serve para testar se duas alternativas aparecem com "
            "clareza em um vídeo vertical curto. As letras e os nomes precisam ficar "
            "claros. O material "
            "visual é sintético e não retrata nenhuma das cidades. Esse teste não registra "
            "votos e não escolhe uma pauta definitiva. Se quiser indicar "
            "qual tema vem primeiro, Comente A ou B."
        ),
    },
    {
        "tema": "Mais histórias no canal",
        "objetivo": "promocao_canal",
        "formula": "curiosidade_1_fato",
        "cta": "Siga o canal para mais",
        "roteiro": (
            "Uma pergunta muda tudo. Às vezes um detalhe aparece em uma "
            "nota de rodapé, em um mapa ou em duas versões de um mesmo relato. Neste "
            "ensaio, mostramos como uma pergunta curta pode abrir espaço para explicar o "
            "contexto com calma. As imagens são abstratas e não representam fatos ou "
            "lugares reais. A ideia é testar o ritmo de um convite ao canal, com narração "
            "clara, legenda legível e uma chamada no final. Nenhum episódio novo está sendo "
            "prometido por este arquivo de demonstração. Siga o canal para mais."
        ),
    },
    {
        "tema": "Nova série em preparação",
        "objetivo": "anuncio",
        "formula": "anuncio",
        "cta": "Acompanhe as novidades do canal",
        "roteiro": (
            "Uma nova série está em teste. Este anúncio é apenas uma simulação técnica; "
            "não existe data de estreia confirmada. Estamos verificando como apresentar "
            "uma novidade de maneira clara, sem prometer algo que ainda não foi definido. "
            "As imagens e as cenas "
            "foram geradas exclusivamente para este ensaio e não retratam uma produção "
            "pronta. Antes de publicar um anúncio verdadeiro, o texto, a data e os "
            "materiais precisariam de revisão humana. Nada será divulgado automaticamente "
            "depois que o ensaio for concluído. Por enquanto, Acompanhe as novidades "
            "do canal."
        ),
    },
]


def gerar_clipes(raiz: Path) -> list[str]:
    """Três MP4s H.264/AAC distintos para testar V09 e o mute da fonte."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("FFmpeg não está no PATH.")
    pasta = raiz / "global" / "loops"
    pasta.mkdir(parents=True, exist_ok=True)
    ids: list[str] = []
    for indice, cor in enumerate(("red", "green", "blue"), start=1):
        identificador = f"bastidor-sintetico-{indice}"
        arquivo = pasta / f"{identificador}.mp4"
        _executar(
            [
                ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={cor}:s=640x360:r=30",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={300 + indice * 100}:sample_rate=48000",
                "-t",
                "4",
                "-shortest",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "96k",
                str(arquivo),
            ],
            cwd=raiz,
        )
        ficha = {
            "id": identificador,
            "arquivo": arquivo.name,
            "descricao": f"Padrão sintético {cor}; não mostra bastidor real",
            "licenca": "CC0-1.0",
            "comercial": True,
            "publicacao_permitida": True,
            "credito": "DocForja — síntese local de ensaio",
            "origem": "gerada pelo script de ensaio M8",
            "sha256": calcular_hash_dados(arquivo),
        }
        (pasta / f"{identificador}.json").write_text(
            json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        ids.append(f"global:loops:{identificador}")
    return ids


def _csv() -> str:
    linhas = ["tema,objetivo,duracao_s,formula,cta,opcao_a,opcao_b"]
    for caso in CASOS:
        linhas.append(
            ",".join(
                [
                    str(caso["tema"]),
                    str(caso["objetivo"]),
                    "30",
                    str(caso["formula"]),
                    str(caso["cta"]),
                    str(caso.get("opcao_a", "")),
                    str(caso.get("opcao_b", "")),
                ]
            )
        )
    return "\n".join(linhas) + "\n"


def _verificar_artefatos(pasta: Path) -> dict[str, Any]:
    video = verificar_video(pasta / "video.mp4")
    capa = verificar_capa(pasta / "capa.jpg")
    legenda = verificar_legendas(pasta / "legendas.srt", video["duracao_s"])
    meta = json.loads((pasta / "metadados.json").read_text(encoding="utf-8"))
    falhas_qa = [item["regra"] for item in meta["qa"]["violacoes"] if not item["aprovada"]]
    return {
        "video": video,
        "capa": capa,
        "legendas": legenda,
        "qa_aprovado": meta["qa"]["aprovado"],
        "falhas_qa": falhas_qa,
        "wer": meta["wer"],
        "publicacao_autorizada": meta["publicacao_autorizada"],
        "creditos_clipes": len(meta.get("creditos_clipes", [])),
    }


def executar_fluxo(base: str, raiz: Path, imagens: list[str], clipes: list[str]) -> dict[str, Any]:
    cliente = httpx.Client(base_url=base, timeout=3600.0)
    previa = cliente.post("/api/shorts/avulsos/planejar", json={"csv_texto": _csv()})
    if previa.status_code != 200 or previa.json().get("quantidade") != 5:
        raise RuntimeError(f"Prévia de cinco temas recusada: {_json_erro(previa)}")
    criacao = cliente.post(
        "/api/shorts/avulsos/campanhas",
        json={"nome": "Ensaio isolado M8 cinco objetivos", "csv_texto": _csv()},
    )
    if criacao.status_code != 201:
        raise RuntimeError(f"Campanha recusada: {_json_erro(criacao)}")
    campanha = criacao.json()
    registro: dict[str, Any] = {"campanha": campanha["id"], "pedidos": []}
    print(f"[M8] Campanha isolada {campanha['id']} com cinco pedidos.", flush=True)
    for caso, pedido in zip(CASOS, campanha["pedidos"], strict=True):
        pedido_id = pedido["id"]
        rota = f"/api/shorts/avulsos/campanhas/{campanha['id']}/pedidos/{pedido_id}"
        aprovacao = cliente.post(
            f"{rota}/roteiro/aprovar",
            json={"texto": caso["roteiro"], "hash_campanha": campanha["hash_conteudo"]},
        )
        if aprovacao.status_code != 200:
            raise RuntimeError(f"{pedido_id} roteiro: {_json_erro(aprovacao)}")
        midias = [*imagens, *clipes] if caso["objetivo"] == "bastidores" else imagens
        selecao = cliente.post(
            f"{rota}/midias/selecionar",
            json={
                "ids_globais": midias,
                "hash_campanha": campanha["hash_conteudo"],
                "revisao_roteiro": aprovacao.json()["revisao"],
            },
        )
        if selecao.status_code != 200:
            raise RuntimeError(f"{pedido_id} mídias: {_json_erro(selecao)}")
        dados: dict[str, Any] = {
            "revisado_pelo_usuario": True,
            "relacao_comercial": "nenhuma",
            "fontes": [
                {
                    "alegacao": "Cenário narrativo sintético do ensaio M8.",
                    "fonte": "Roteiro fictício interno, sem verificação factual externa.",
                }
            ],
        }
        ficha = cliente.post(
            f"{rota}/alegacoes/registrar",
            json={
                "hash_campanha": campanha["hash_conteudo"],
                "revisao_roteiro": aprovacao.json()["revisao"],
                "revisao_midias": selecao.json()["revisao"],
                "dados": dados,
            },
        )
        if ficha.status_code != 200:
            raise RuntimeError(f"{pedido_id} ficha: {_json_erro(ficha)}")
        registro["pedidos"].append({"id": pedido_id, "objetivo": caso["objetivo"], "rota": rota})
    for item in registro["pedidos"]:
        rota = item["rota"]
        print(f"[M8] Produzindo {item['id']} ({item['objetivo']})...", flush=True)
        sem_codigo = cliente.post(f"{rota}/produzir", json={"codigo": "sim"})
        if sem_codigo.status_code != 403:
            raise RuntimeError(f"{item['id']} portão sem código não bloqueou.")
        resposta = cliente.post(f"{rota}/produzir", json={"codigo": "PRODUZIR"})
        if resposta.status_code != 200:
            raise RuntimeError(f"{item['id']} produção: {_json_erro(resposta)}")
        limite = time.monotonic() + 3600
        estado = resposta.json()
        while estado.get("status") not in {"concluido", "falhou"} and time.monotonic() < limite:
            time.sleep(5)
            estado = _pedir(cliente, "GET", f"{rota}/producao").json()
        item["estado"] = estado
        if estado.get("status") != "concluido":
            break
        pasta = raiz / "artefatos" / item["id"]
        pasta.mkdir(parents=True, exist_ok=True)
        for nome in (
            "video.mp4",
            "capa.jpg",
            "legendas.srt",
            "metadados.json",
            "youtube.md",
            "instagram.md",
        ):
            resposta = _pedir(cliente, "GET", f"{rota}/artefatos/{nome}")
            if resposta.status_code != 200:
                raise RuntimeError(f"{item['id']} artefato {nome}: {_json_erro(resposta)}")
            (pasta / nome).write_bytes(resposta.content)
        item["verificacoes"] = _verificar_artefatos(pasta)
        print(
            f"[M8] {item['id']}: QA={item['verificacoes']['qa_aprovado']}, "
            f"falhas={item['verificacoes']['falhas_qa']}",
            flush=True,
        )
    cliente.close()
    return registro


def main() -> int:
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument("--raiz", type=Path)
    argumentos = analisador.parse_args()
    raiz = argumentos.raiz or Path("E:/05_PROJETOS/forja") / (
        f"ensaio-m8-cinco-avulsos-{time.strftime('%Y%m%d-%H%M%S')}"
    )
    if raiz.exists() and any(raiz.iterdir()):
        raise SystemExit(f"A raiz do ensaio já contém arquivos: {raiz}")
    raiz.mkdir(parents=True, exist_ok=True)
    preparar_raiz(raiz)
    imagens = gerar_imagens(raiz)
    clipes = gerar_clipes(raiz)
    porta = _porta_livre()
    processo = iniciar_api(raiz, porta)
    inicio = time.monotonic()
    registro: dict[str, Any] = {}
    erro: str | None = None
    try:
        esperar_api(f"http://127.0.0.1:{porta}", processo)
        registro = executar_fluxo(f"http://127.0.0.1:{porta}", raiz, imagens, clipes)
    except (RuntimeError, SystemExit) as exc:
        erro = str(exc)
    finally:
        processo.terminate()
        try:
            processo.wait(timeout=30)
        except subprocess.TimeoutExpired:
            processo.kill()
    pedidos = registro.get("pedidos", [])
    sucesso = bool(
        erro is None
        and len(pedidos) == 5
        and all(
            item.get("verificacoes", {}).get("qa_aprovado") is True
            and item["verificacoes"]["video"].get("ok") is True
            and item["verificacoes"]["video"].get("largura") == 1080
            and item["verificacoes"]["video"].get("altura") == 1920
            and item["verificacoes"]["video"].get("fps") == 30
            and item["verificacoes"]["video"].get("codec_video") == "h264"
            and item["verificacoes"]["video"].get("codec_audio") == "aac"
            and item["verificacoes"]["capa"].get("ok")
            and item["verificacoes"]["capa"].get("largura") == 1080
            and item["verificacoes"]["capa"].get("altura") == 1920
            and item["verificacoes"]["legendas"].get("ok")
            and item["verificacoes"].get("publicacao_autorizada") is False
            for item in pedidos
        )
    )
    relatorio = {
        "raiz": str(raiz),
        "sucesso": sucesso,
        "erro": erro,
        "tempo_s": round(time.monotonic() - inicio, 1),
        "avisos": [
            "Roteiros e fichas são simulações; a aprovação humana ocorre só dentro do ensaio.",
            "Imagens e clipes são sintéticos; nenhum pacote está autorizado para publicação.",
        ],
        **registro,
    }
    (raiz / "relatorio.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "raiz": str(raiz),
                "sucesso": sucesso,
                "erro": erro,
                "resultados": [
                    {
                        "id": item["id"],
                        "objetivo": item["objetivo"],
                        "duracao_s": item.get("verificacoes", {}).get("video", {}).get("duracao_s"),
                        "falhas_qa": item.get("verificacoes", {}).get("falhas_qa"),
                    }
                    for item in pedidos
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if sucesso else 1


if __name__ == "__main__":
    sys.exit(main())
