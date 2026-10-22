"""Ensaio real controlado de shorts de afiliado do Marco M8 (V11 e agenda.csv).

Executa a API local contra uma raiz isolada, com TTS configurado e WhisperX locais,
FFmpeg e Remotion do kit, e verifica vídeo, narração, legendas, capa, áudio,
as regras DS1-DS9 e a planilha de publicação. Nada é publicado, nenhuma
aprovação do usuário é concedida e nada fora da raiz do ensaio é escrito.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ensaio_avulso_m8 import (
    _executar,
    _pedir,
    _porta_livre,
    esperar_api,
    gerar_imagens,
    iniciar_api,
    preparar_raiz,
    verificar_audio,
    verificar_capa,
    verificar_legendas,
    verificar_video,
)

from docforja.nucleo.etapas import calcular_hash_dados
from docforja.shorts.afiliados import PADRAO_PRECO

PLANILHA = (
    "nome,descricao,beneficios,link_afiliado,imagens,nicho,"
    "plataforma,marca,duracao_s\n"
    "Furadeira Leve,Furadeira compacta para uso doméstico.,"
    "Peso leve|Motor silencioso,https://loja.exemplo.com/furadeira?ref=docforja,"
    "global:imagens:produto-furadeira,"
    "ferramentas,youtube_shorts,Loja Exemplo,30\n"
    "Luminaria Mesa,Luminaria de mesa com luz ajustavel.,"
    "Luz ajustavel|Bateria recarregavel,https://loja.exemplo.com/luminaria?ref=docforja,"
    "global:imagens:produto-luminaria,"
    "decoracao,instagram_reels,Loja Exemplo,30\n"
)

ROTEIRO_FURADEIRA = (
    "Furadeira compacta para uso doméstico. O peso baixo faz diferença em quem "
    "trabalha a tarde inteira, e o motor silencioso deixa o ambiente tranquilo. "
    "Ela ainda guarda a corda na caixa, o que evita ficar procurando tomada no "
    "meio da obra. O cabo tem dois metros de alcance em mesas grandes. Veja a oferta "
    "e as condições atuais diretamente pelo link indicado na publicação. O modelo é o "
    "mesmo da foto, sem diferenças de acabamento. Antes de escolher, confira "
    "medidas, acessórios e detalhes na página. Link na bio para ver o detalhe "
    "e a ficha completa."
)

ROTEIRO_LUMINARIA = (
    "Luminária de mesa com luz ajustável. A luz muda de intensidade, e isso ajuda "
    "quem trabalha de manhã cedo ou de noite sem acordar o vizinho. A bateria "
    "recarregável tira a preocupação de encontrar tomada perto da cama. Para quem "
    "passa a tarde na mesa, a diferença de conforto aparece na primeira semana "
    "de uso. Veja a oferta e as condições atuais no link da loja. "
    "O modelo é o mesmo da foto, sem diferenças de acabamento. Antes de escolher, "
    "confira medidas, acessórios e detalhes na página. Link na bio para "
    "ver o detalhe e a ficha completa."
)

NOMES_DEZ = ("Um", "Dois", "Tres", "Quatro", "Cinco", "Seis", "Sete", "Oito", "Nove", "Dez")
ROTEIRO_DEZ = (
    "Este é um item de demonstração. Não representa um produto à venda. "
    "A imagem e os benefícios da planilha existem para testar a montagem do cartão vertical. "
    "Formato e montagem são dados simulados, não promessas sobre produto real. "
    "A gravação confere se nome, benefícios e aviso de publicidade cabem na tela. "
    "Uma compra real exigiria fotos autorizadas, dados verificados e um link válido da loja. "
    "A oferta atual deve ser conferida na página indicada, no link da bio. Link na bio."
)


def _planilha_dez() -> str:
    saida = io.StringIO()
    escritor = csv.writer(saida, lineterminator="\n")
    escritor.writerow(
        (
            "nome", "descricao", "beneficios", "link_afiliado", "imagens",
            "nicho", "plataforma", "marca", "duracao_s",
        )
    )
    for nome in NOMES_DEZ:
        escritor.writerow(
            (
                f"Organizador de Ensaio {nome}",
                "Objeto fictício para testar a produção de Shorts de afiliado.",
                "Formato compacto|Montagem simples",
                f"https://example.invalid/ensaio/{nome.lower()}",
                "global:imagens:produto-demonstracao",
                "teste",
                "ambas",
                "Marca Fictícia",
                30,
            )
        )
    return saida.getvalue()


def _gerar_imagens_produto(raiz: Path) -> None:
    """Cria as imagens de produto com ficha CC0 na Pasta Global do ensaio."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("FFmpeg não está no PATH.")
    pasta = raiz / "global" / "imagens"
    for indice, (identificador, cor_a, cor_b) in enumerate(
        [
            ("produto-furadeira", "0x12161d", "0x8a5a2a"),
            ("produto-luminaria", "0x0f1b1f", "0x2f6f6a"),
            ("produto-demonstracao", "0x1b2028", "0x727982"),
        ]
    ):
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
                    f"x0={140 + indice * 120}:y0={260 + indice * 90}:"
                    f"x1={880 - indice * 60}:y1={1600 - indice * 80}:"
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
            "descricao": f"Imagem sintética de produto do ensaio M8 ({identificador})",
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


def _ficha_alegacoes(produto: dict[str, Any]) -> dict[str, Any]:
    return {
        "fontes": [
            {
                "alegacao": f"Benefícios descritos para {produto['nome']} no ensaio sintético.",
                "fonte": produto["link_afiliado"],
            }
        ],
        "relacao_comercial": "afiliado",
        "marca": produto["marca"],
        "aviso_publicidade": True,
        "revisado_pelo_usuario": True,
    }


def executar_fluxo(
    base: str,
    raiz_saida: Path,
    planilha: str = PLANILHA,
    roteiros: dict[str, str] | None = None,
    apenas: str | None = None,
) -> dict[str, Any]:
    """Percorre o portão humano real da API para cada produto da planilha."""
    cliente = httpx.Client(base_url=base, timeout=3600.0)
    registro: dict[str, Any] = {}
    previa = cliente.post("/api/shorts/afiliados/planilhas/planejar", json={"csv_texto": planilha})
    if previa.status_code != 200:
        raise SystemExit(f"A prévia da planilha falhou: {previa.text[:400]}")
    registro["previa"] = previa.json()["quantidade"]
    criacao = cliente.post(
        "/api/shorts/afiliados/campanhas",
        json={"nome": "Ensaio M8 afiliados", "csv_texto": planilha},
    )
    if criacao.status_code != 201:
        raise SystemExit(f"A criação da campanha falhou: {criacao.text[:400]}")
    campanha = criacao.json()
    registro["campanha"] = campanha["id"]
    roteiros = roteiros or {"A001": ROTEIRO_FURADEIRA, "A002": ROTEIRO_LUMINARIA}
    producoes: dict[str, Any] = {}
    for pedido in campanha["pedidos"]:
        base_pedido = f"/api/shorts/avulsos/campanhas/{campanha['id']}/pedidos/{pedido['id']}"
        produto = pedido["produto"]
        registro.setdefault("produtos", []).append(
            {
                "id": pedido["id"],
                "nome": produto["nome"],
                "link_afiliado": produto["link_afiliado"],
                "plataforma": produto["plataforma"],
            }
        )
        aprovacao = cliente.post(f"{base_pedido}/roteiro/aprovar", json={
            "texto": roteiros[pedido["id"]],
            "hash_campanha": campanha["hash_conteudo"],
        })
        if aprovacao.status_code != 200:
            raise SystemExit(f"Aprovação do roteiro falhou: {aprovacao.text[:400]}")
        revisao_roteiro = aprovacao.json()["revisao"]
        selecao = cliente.post(f"{base_pedido}/midias/selecionar", json={
            "ids_globais": produto["imagens"],
            "hash_campanha": campanha["hash_conteudo"],
            "revisao_roteiro": revisao_roteiro,
        })
        if selecao.status_code != 200:
            raise SystemExit(f"Seleção de mídias falhou: {selecao.text[:400]}")
        revisao_midias = selecao.json()["revisao"]
        ficha = cliente.post(f"{base_pedido}/alegacoes/registrar", json={
            "hash_campanha": campanha["hash_conteudo"],
            "revisao_roteiro": revisao_roteiro,
            "revisao_midias": revisao_midias,
            "dados": _ficha_alegacoes(produto),
        })
        if ficha.status_code != 200:
            raise SystemExit(f"Registro da ficha falhou: {ficha.text[:400]}")
        if apenas and pedido["id"] != apenas:
            continue
        print(f"[M8] Produzindo afiliado {pedido['id']}...", flush=True)
        sem_codigo = cliente.post(f"{base_pedido}/produzir", json={"codigo": "sim"})
        producao = cliente.post(f"{base_pedido}/produzir", json={"codigo": "PRODUZIR"})
        if producao.status_code != 200:
            raise SystemExit(f"A produção foi recusada: {producao.text[:400]}")
        limite = time.monotonic() + 3600
        estado = producao.json()
        while estado.get("status") not in {"concluido", "falhou"} and time.monotonic() < limite:
            time.sleep(5.0)
            estado = _pedir(cliente, "GET", f"{base_pedido}/producao").json()
        producoes[pedido["id"]] = {
            "portao_sem_codigo": sem_codigo.status_code,
            "estado": estado.get("status"),
            "erro": estado.get("erro"),
            "revisao": estado.get("revisao"),
            "base_pedido": base_pedido,
        }
        print(
            f"[M8] {pedido['id']}: {estado.get('status')}, erro={estado.get('erro')}",
            flush=True,
        )
    registro["producoes"] = producoes
    agenda = _pedir(cliente, "GET", f"/api/shorts/avulsos/campanhas/{campanha['id']}/agenda")
    registro["agenda"] = agenda.json() if agenda.status_code == 200 else {"erro": agenda.text[:300]}
    artefatos: dict[str, str] = {}
    for pedido_id, dados in producoes.items():
        if dados["estado"] != "concluido":
            continue
        for nome in (
            "video.mp4",
            "capa.jpg",
            "legendas.srt",
            "metadados.json",
            "youtube.md",
            "instagram.md",
            "agenda.csv",
        ):
            resposta = _pedir(
                cliente, "GET", f"{dados['base_pedido']}/artefatos/{nome}"
            )
            registro[f"artefato_{pedido_id}_{nome}"] = resposta.status_code
            if resposta.status_code == 200:
                destino = raiz_saida / pedido_id / nome
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_bytes(resposta.content)
                artefatos[f"{pedido_id}/{nome}"] = str(destino)
    registro["artefatos"] = artefatos
    return registro


def main() -> int:
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument("--dez-sinteticos", action="store_true")
    analisador.add_argument("--apenas", choices=[f"A{n:03d}" for n in range(1, 11)])
    analisador.add_argument("--raiz", type=Path)
    argumentos = analisador.parse_args()
    if (
        argumentos.apenas
        and not argumentos.dez_sinteticos
        and argumentos.apenas not in {"A001", "A002"}
    ):
        analisador.error("A planilha padrão contém apenas A001 e A002.")
    raiz = argumentos.raiz or Path("E:/05_PROJETOS/forja") / (
        f"ensaio-m8-afiliados-{'dez-' if argumentos.dez_sinteticos else ''}"
        f"{time.strftime('%Y%m%d-%H%M%S')}"
    )
    if raiz.exists() and any(raiz.iterdir()):
        raise SystemExit(f"A raiz do ensaio já contém arquivos: {raiz}")
    raiz.mkdir(parents=True, exist_ok=True)
    raiz_saida = raiz / "artefatos"
    raiz_saida.mkdir(parents=True, exist_ok=True)
    preparar_raiz(raiz)
    gerar_imagens(raiz)
    _gerar_imagens_produto(raiz)
    porta = _porta_livre()
    base = f"http://127.0.0.1:{porta}"
    processo = iniciar_api(raiz, porta)
    inicio = time.monotonic()
    planilha = _planilha_dez() if argumentos.dez_sinteticos else PLANILHA
    roteiros = (
        {f"A{indice:03d}": ROTEIRO_DEZ for indice in range(1, 11)}
        if argumentos.dez_sinteticos
        else {"A001": ROTEIRO_FURADEIRA, "A002": ROTEIRO_LUMINARIA}
    )
    registro: dict[str, Any] = {}
    erro: str | None = None
    try:
        esperar_api(base, processo)
        registro = executar_fluxo(base, raiz_saida, planilha, roteiros, argumentos.apenas)
    except (RuntimeError, SystemExit, httpx.HTTPError) as exc:
        erro = str(exc)
    finally:
        processo.terminate()
        try:
            processo.wait(timeout=30)
        except Exception:
            processo.kill()
    duracao_total = round(time.monotonic() - inicio, 1)

    artefatos = registro.get("artefatos", {})
    verificacoes: dict[str, Any] = {}
    for pedido_id in sorted({chave.split("/")[0] for chave in artefatos}):
        pasta = raiz_saida / pedido_id
        if (pasta / "video.mp4").is_file():
            verificacoes[pedido_id] = {
                "video": verificar_video(pasta / "video.mp4"),
                "audio": verificar_audio(pasta / "video.mp4"),
                "capa": verificar_capa(pasta / "capa.jpg"),
            }
            duracao = verificacoes[pedido_id]["video"].get("duracao_s", 0.0)
            verificacoes[pedido_id]["legendas"] = verificar_legendas(
                pasta / "legendas.srt", duracao
            )
            metadados = json.loads((pasta / "metadados.json").read_text(encoding="utf-8"))
            srt = (pasta / "legendas.srt").read_text(encoding="utf-8")
            youtube = (pasta / "youtube.md").read_text(encoding="utf-8")
            instagram = (pasta / "instagram.md").read_text(encoding="utf-8")
            agenda = (pasta / "agenda.csv").read_text(encoding="utf-8")
            produto = metadados.get("produto", {})
            verificacoes[pedido_id]["metadados"] = {
                "status": metadados.get("status"),
                "publicacao_autorizada": metadados.get("publicacao_autorizada"),
                "relacao_comercial": metadados.get("relacao_comercial"),
                "wer": metadados.get("wer"),
                "duracao_s": metadados.get("duracao_s"),
                "qa_aprovado": metadados.get("qa", {}).get("aprovado"),
                "regras": [
                    {
                        "regra": item["regra"],
                        "aprovada": item["aprovada"],
                        "detalhes": item["detalhes"],
                    }
                    for item in metadados.get("qa", {}).get("violacoes", [])
                ],
                "link_queimado_no_video": produto.get("link_queimado_no_video"),
                "link_no_texto_publicacao": produto.get("link_afiliado", "") in youtube,
                "link_no_instagram": produto.get("link_afiliado", "") in instagram,
                "link_na_legenda": produto.get("link_afiliado", "") in srt,
                "aviso_publicidade": "Publicidade" in youtube and "Publicidade" in instagram,
                "preco_ausente": not PADRAO_PRECO.search(srt + youtube + instagram + agenda),
                "narracao": metadados.get("narracao"),
            }

    esperados = (
        {argumentos.apenas}
        if argumentos.apenas
        else {f"A{indice:03d}" for indice in range(1, 11)}
        if argumentos.dez_sinteticos
        else {"A001", "A002"}
    )
    sucesso = bool(
        erro is None
        and set(verificacoes) == esperados
        and all(
            verificacao["video"].get("ok")
            and verificacao["video"].get("largura") == 1080
            and verificacao["video"].get("altura") == 1920
            and verificacao["video"].get("fps") == 30
            and verificacao["video"].get("codec_video") == "h264"
            and verificacao["video"].get("codec_audio") == "aac"
            and verificacao["capa"].get("ok")
            and verificacao["legendas"].get("ok")
            and verificacao["metadados"]["qa_aprovado"]
            and verificacao["metadados"]["preco_ausente"]
            and verificacao["metadados"]["aviso_publicidade"]
            and verificacao["metadados"]["link_no_texto_publicacao"]
            and verificacao["metadados"]["link_no_instagram"]
            and verificacao["metadados"]["link_na_legenda"] is False
            and verificacao["metadados"]["link_queimado_no_video"] is False
            for verificacao in verificacoes.values()
        )
        and all(
            item["portao_sem_codigo"] == 403 and item["estado"] == "concluido"
            for item in registro.get("producoes", {}).values()
        )
        and registro.get("agenda", {}).get("quantidade") == len(esperados)
    )
    relatorio = {
        "sucesso": sucesso,
        "erro": erro,
        "raiz": str(raiz),
        "duracao_total_s": duracao_total,
        "planilha": planilha,
        "roteiros": roteiros,
        "apenas": argumentos.apenas,
        "fluxo": registro,
        "verificacoes": verificacoes,
    }
    (raiz / "relatorio-ensaio.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "raiz": str(raiz),
                "sucesso": sucesso,
                "erro": erro,
                "agenda_quantidade": registro.get("agenda", {}).get("quantidade"),
                "pacotes": {
                    chave: {
                        "duracao_s": valor["video"]["duracao_s"],
                        "qa_aprovado": valor["metadados"]["qa_aprovado"],
                        "narracao": valor["metadados"]["narracao"],
                    }
                    for chave, valor in verificacoes.items()
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if sucesso else 1


if __name__ == "__main__":
    sys.exit(main())
