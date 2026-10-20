"""Serve uma amostra descartável para conferir imagem licenciada na UI M5.

Todos os arquivos são criados em TemporaryDirectory. Encerramento abrupto do
processo pode deixar a pasta temporária para limpeza manual posterior.
Não lê nem altera projetos ou mídias do usuário.
"""

from __future__ import annotations

import struct
import tempfile
import wave
import zlib
from pathlib import Path
from types import SimpleNamespace

import uvicorn

import docforja.api as api
from docforja.io import atomic_write_json
from docforja.midia.licenca import FichaLicenca, salvar_ficha_licenca
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.nucleo.projeto import Projeto


def _png_teste(caminho: Path, alternativa: bool = False) -> None:
    largura, altura = 640, 360
    linhas = bytearray()
    for y in range(altura):
        linhas.append(0)
        for x in range(largura):
            if alternativa:
                linhas.extend((180, 45 + x * 70 // largura, 30 + y * 110 // altura))
            else:
                linhas.extend((28 + x * 120 // largura, 65 + y * 100 // altura, 140))

    def bloco(tipo: bytes, conteudo: bytes) -> bytes:
        corpo = tipo + conteudo
        return struct.pack(">I", len(conteudo)) + corpo + struct.pack(">I", zlib.crc32(corpo))

    caminho.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0))
        + bloco(b"IDAT", zlib.compress(bytes(linhas)))
        + bloco(b"IEND", b"")
    )


def _criar_amostra(raiz: Path) -> Projeto:
    projeto = Projeto.criar("Amostra M5", raiz_projetos=raiz)
    imagem = projeto.pastas.midias / "pesquisadas" / "A-001" / "escolhida.png"
    imagem.parent.mkdir(parents=True, exist_ok=True)
    _png_teste(imagem)
    salvar_ficha_licenca(
        imagem,
        FichaLicenca(
            url_origem="gerada_localmente_para_teste",
            autor="DocForja — amostra de teste",
            licenca="CC0",
            credito_obrigatorio=False,
        ),
    )
    candidata = imagem.parent / "cand_amostra_1.png"
    _png_teste(candidata, alternativa=True)
    salvar_ficha_licenca(
        candidata,
        FichaLicenca(
            url_origem="https://example.org/amostra-sintetica",
            autor="DocForja — candidata sintética",
            licenca="CC0",
            texto_credito="DocForja / CC0 (amostra sintética)",
            detalhes={"nota_curador": 8.0, "motivo_curador": "Contraste visual para o teste"},
        ),
    )
    ativo = {
        "id": "A-001",
        "descricao": "Gradiente de teste criado localmente",
        "origem": "pesquisar",
        "caminho": str(imagem),
        "usado_em": ["B0-01"],
    }
    manual_sem_licenca = projeto.pastas.midias / "manual" / "A-002.png"
    _png_teste(manual_sem_licenca)
    ativo_pendente = {
        "id": "A-002",
        "descricao": "Imagem de teste recebida sem ficha de licença",
        "origem": "pedir_ao_usuario",
        "nome_arquivo": "A-002.png",
        "usado_em": ["B0-01"],
    }
    plano = {
        "projeto": projeto.slug,
        "orcamento_producao_min": 10,
        "estimativa_producao_min": 1,
        "blocos": [{"id": "B0", "titulo": "TESTE VISUAL", "shots": [{
            "id": "B0-01", "segmentos": ["S-001"], "inicio_s": 0,
            "fim_s": 5, "duracao_s": 5, "template": "T01", "textos": [],
            "ativos": ["A-001"],
        }]}],
    }
    atomic_write_json(projeto.pastas.plano / "plano.json", plano)
    resolvidos = projeto.pastas.plano / "ativos_resolvidos.json"
    atomic_write_json(resolvidos, {"ativos": {"A-001": ativo, "A-002": ativo_pendente}})
    verificacao = projeto.pastas.plano / "verificacao.json"
    atomic_write_json(verificacao, {"aprovado": True, "total_violacoes": 0})
    segmentos = projeto.pastas.audio / "pt-BR" / "segmentos.json"
    atomic_write_json(segmentos, {"segmentos": []})
    audio = projeto.pastas.audio / "pt-BR" / "narracao_completa.wav"
    with wave.open(str(audio), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b"\x00\x00" * 8000 * 5)
    props = projeto.pastas.sistema / "previa" / "props.json"
    props.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(props, {
        "titulo": projeto.slug,
        "shots": [{
            "id": "B0-01", "template": "T01", "inicio_frame": 0,
            "fim_frame": 120, "bloco": "TESTE VISUAL",
            "descricao": ativo["descricao"], "texto": "", "situacao": "RESOLVIDO",
        }],
        "cartoes": [],
        "duracao_frames": 120,
    })
    atomic_write_json(projeto.pastas.plano / "previa.json", {
        "hash_verificacao": calcular_hash_dados(verificacao),
        "hash_resolvidos": calcular_hash_dados(resolvidos),
        "hash_audio": calcular_hash_dados(audio),
        "hash_segmentos": calcular_hash_dados(segmentos),
    })
    return projeto


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="docforja-m5-") as pasta:
        raiz = Path(pasta)
        projeto_teste = _criar_amostra(raiz)
        api.load_settings = lambda: SimpleNamespace(paths=SimpleNamespace(projects=raiz))
        print(f"Amostra descartável: {projeto_teste.raiz}")
        uvicorn.run(api.app, host="127.0.0.1", port=7862, access_log=False)
