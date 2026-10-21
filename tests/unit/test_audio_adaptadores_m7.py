"""Testes unitários dos adaptadores de TTS do Marco M7 (openai_compat, voicestudio, pronta)."""

from __future__ import annotations

import io
import json
import wave
from pathlib import Path

import httpx
import pytest

from docforja.audio.adaptadores import (
    AdaptadorOpenAITTS,
    AdaptadorVoiceStudio,
    processar_narracao_pronta_completa,
)
from docforja.audio.narracao import OrquestradorNarracao
from docforja.nucleo.executor import ContextoEtapa, ExecutorPipeline
from docforja.nucleo.handlers import registrar_handlers_disponiveis
from docforja.nucleo.projeto import Projeto
from docforja.planejamento.entidades import SegmentoProcessado


def _criar_wav_mock(duracao_s: float = 0.5, sample_rate: int = 24000) -> bytes:
    """Gera bytes de um arquivo WAV válido e legível por FFmpeg."""
    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * int(sample_rate * duracao_s))
    return bio.getvalue()


def test_openai_compat_sintese(tmp_path: Path, httpx_mock):
    """Testa geração via endpoint compatível OpenAI /v1/audio/speech."""
    base_url = "http://mock-tts.local/v1"
    endpoint = f"{base_url}/audio/speech"

    wav_bytes = _criar_wav_mock(duracao_s=0.5)
    httpx_mock.add_response(url=endpoint, method="POST", content=wav_bytes, status_code=200)

    adaptador = AdaptadorOpenAITTS(base_url=base_url, modelo="tts-1", timeout_s=5.0)
    assert adaptador.disponivel() is True

    saida = tmp_path / "saida_openai.wav"
    res = adaptador.gerar(texto="Texto de teste", saida_wav=saida, voz="echo", velocidade=1.1)

    assert res == saida
    assert saida.is_file()

    # Confere payload da requisição HTTP
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    req_body = json.loads(requests[0].content)
    assert req_body["model"] == "tts-1"
    assert req_body["input"] == "Texto de teste"
    assert req_body["voice"] == "echo"
    assert req_body["speed"] == 1.1


def test_openai_compat_retry_apos_falha_temporaria(tmp_path: Path, httpx_mock):
    """Verifica que o adaptador retenta requisições com falha transitória."""
    base_url = "http://mock-tts.local/v1"
    endpoint = f"{base_url}/audio/speech"

    wav_bytes = _criar_wav_mock(duracao_s=0.5)
    httpx_mock.add_response(url=endpoint, method="POST", status_code=503)
    httpx_mock.add_response(url=endpoint, method="POST", content=wav_bytes, status_code=200)

    adaptador = AdaptadorOpenAITTS(base_url=base_url, max_retries=2)
    saida = tmp_path / "saida_retry.wav"
    res = adaptador.gerar(texto="Texto", saida_wav=saida)
    assert res.is_file()
    assert len(httpx_mock.get_requests()) == 2


def test_voicestudio_bloqueio_licenca_nao_comercial(tmp_path: Path):
    """Garante bloqueio de vozes/engines NC para projetos monetizados (AGENTS.md, Marco M7)."""
    adaptador_monetizado = AdaptadorVoiceStudio(
        comercial_exigido=True, engines_comerciais=["omnivoice"]
    )

    # 1. Bloqueia sufixos explícitos de licença NC
    with pytest.raises(PermissionError, match="não-comercial"):
        adaptador_monetizado.gerar("Texto", tmp_path / "saida.wav", voz="modelo_clonado-nc")

    # 2. Bloqueia engines não comerciais conhecidas
    with pytest.raises(PermissionError, match="não-comercial"):
        adaptador_monetizado.gerar("Texto", tmp_path / "saida.wav", voz="f5-tts-nc")

    # 3. Bloqueia a engine sem licença comercial registrada
    with pytest.raises(PermissionError, match="engines_comerciais"):
        AdaptadorVoiceStudio(comercial_exigido=True).verificar_licenca_comercial("perfil")

    # 4. Permite quando o projeto explicitamente não for monetizado
    adaptador_nao_monetizado = AdaptadorVoiceStudio(comercial_exigido=False)
    # Não levanta PermissionError na checagem
    adaptador_nao_monetizado.verificar_licenca_comercial("modelo_clonado-nc")


def test_voicestudio_sintese_usa_endpoint_compativel_com_openai(
    tmp_path: Path, httpx_mock
):
    """A síntese usa POST {raiz}/v1/audio/speech com model, voice e input."""
    base_url = "http://127.0.0.1:3900"
    wav_bytes = _criar_wav_mock(duracao_s=0.5)
    httpx_mock.add_response(
        url=f"{base_url}/v1/models", method="GET", json={"data": []}, status_code=200
    )
    httpx_mock.add_response(
        url=f"{base_url}/v1/audio/speech",
        method="POST",
        content=wav_bytes,
        status_code=200,
    )

    adaptador = AdaptadorVoiceStudio(
        base_url=base_url,
        engine="omnivoice",
        engines_comerciais=["omnivoice"],
        comercial_exigido=True,
    )
    saida = tmp_path / "saida_voicestudio.wav"
    res = adaptador.gerar("Texto narrado", saida_wav=saida, voz="locutor_comercial")

    assert res.is_file()
    requisicao = httpx_mock.get_requests()[-1]
    corpo = json.loads(requisicao.content.decode("utf-8"))
    assert requisicao.method == "POST"
    assert requisicao.url.path == "/v1/audio/speech"
    assert corpo["model"] == "omnivoice"
    assert corpo["voice"] == "locutor_comercial"
    assert corpo["input"] == "Texto narrado"
    assert corpo["response_format"] == "wav"


def test_voicestudio_relata_erro_do_servico_e_servico_fora_do_ar(
    tmp_path: Path, httpx_mock
):
    """Erros do app local viram mensagem legível e serviço ausente é recusado."""
    base_url = "http://127.0.0.1:3900"
    httpx_mock.add_response(
        url=f"{base_url}/v1/models", method="GET", json={"data": []}, status_code=200
    )
    httpx_mock.add_response(
        url=f"{base_url}/v1/audio/speech",
        method="POST",
        json={"error": {"message": "engine não instalada", "type": "invalid_request_error"}},
        status_code=400,
    )
    adaptador = AdaptadorVoiceStudio(
        base_url=base_url, engines_comerciais=["omnivoice"], comercial_exigido=True
    )
    with pytest.raises(RuntimeError, match="engine não instalada"):
        adaptador.gerar("Texto", tmp_path / "saida.wav", voz="perfil")

    httpx_mock.add_exception(
        httpx.ConnectError("conexão recusada"),
        url="http://127.0.0.1:59999/v1/models",
    )
    fora = AdaptadorVoiceStudio(base_url="http://127.0.0.1:59999")
    assert fora.disponivel() is False

def test_voicestudio_lista_perfis_de_voz(tmp_path: Path, httpx_mock):
    """A lista de vozes do app é lida no endpoint próprio."""
    base_url = "http://127.0.0.1:3900"
    httpx_mock.add_response(
        url=f"{base_url}/v1/audio/voices",
        method="GET",
        json={"data": [{"voice_id": "v1", "name": "Locutor", "addressable_by_name": True}]},
        status_code=200,
    )
    adaptador = AdaptadorVoiceStudio(base_url=base_url)
    vozes = adaptador.listar_vozes()
    assert vozes[0]["voice_id"] == "v1"


def test_narracao_pronta_com_divergencia_textual_acima_de_8_pct(tmp_path: Path):
    """Garante que divergência > 8% (WER) adota a transcrição como verdade e gera aviso (05 §1)."""
    arquivo_audio = tmp_path / "narracao_locutor.wav"
    # Gera áudio WAV válido de 6 segundos
    with wave.open(str(arquivo_audio), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(b"\x00\x00" * (24000 * 6))

    segs_roteiro = [
        SegmentoProcessado(
            id="B0-S01",
            texto_original="O imperador decidiu marchar contra a cidade rebelde.",
            texto_limpo="O imperador decidiu marchar contra a cidade rebelde.",
        ),
        SegmentoProcessado(
            id="B0-S02",
            texto_original="Nenhum soldado hesitou durante o ataque decisivo.",
            texto_limpo="Nenhum soldado hesitou durante o ataque decisivo.",
        ),
    ]

    pasta_audio = tmp_path / "audio_out"

    # Simula locutor que improvisou e mudou mais de 8% das palavras do texto
    transcricao_improvisada = (
        "O imperador ordenou avançar rapidamente em direção à cidade ocupada. "
        "Nenhum homem recuou durante o combate decisivo."
    )

    relatorio = processar_narracao_pronta_completa(
        arquivo_narracao=arquivo_audio,
        pasta_audio=pasta_audio,
        idioma="pt-BR",
        segmentos_roteiro=segs_roteiro,
        limite_divergencia_wer=0.08,
        transcricao_mock=transcricao_improvisada,
    )

    # 1. Divergência > 8% detectada
    assert relatorio["divergencia_detectada"] is True
    assert relatorio["wer"] > 0.08
    assert "Divergência textual" in relatorio["aviso"]

    # 2. Transcrição adotada como verdade nos tempos e legendas
    segmentos_finais = relatorio["segmentos"]
    assert len(segmentos_finais) == 2
    # Texto reflete a fala real transcrita (não o texto original pré-improviso)
    assert "imperador ordenou" in segmentos_finais[0]["texto"]

    # 3. Artefato de qualidade gravado com o aviso
    qualidade = json.loads((pasta_audio / "qualidade.json").read_text(encoding="utf-8"))
    assert qualidade["divergencia_detectada"] is True
    assert qualidade["aviso"] == relatorio["aviso"]


def test_narracao_pronta_sem_divergencia(tmp_path: Path):
    """Verifica que narração fiel (WER <= 8%) preserva o texto original do roteiro."""
    arquivo_audio = tmp_path / "narracao_fiel.wav"
    with wave.open(str(arquivo_audio), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(b"\x00\x00" * (24000 * 4))

    segs_roteiro = [
        SegmentoProcessado(
            id="B0-S01",
            texto_original="O Vesúvio permaneceu adormecido.",
            texto_limpo="O Vesúvio permaneceu adormecido.",
        )
    ]

    pasta_audio = tmp_path / "audio_out_fiel"
    relatorio = processar_narracao_pronta_completa(
        arquivo_narracao=arquivo_audio,
        pasta_audio=pasta_audio,
        idioma="pt-BR",
        segmentos_roteiro=segs_roteiro,
        transcricao_mock="O Vesúvio permaneceu adormecido.",
    )

    assert relatorio["divergencia_detectada"] is False
    assert relatorio["wer"] == 0.0
    assert relatorio["aviso"] is None
    assert relatorio["segmentos"][0]["texto"] == "O Vesúvio permaneceu adormecido."


@pytest.mark.anyio
async def test_pipeline_p2_executa_com_narracao_pronta_e_gera_aviso(tmp_path: Path):
    """Verifica que o handler P2_narracao executa narração pronta e registra artefatos."""
    raiz = tmp_path / "projetos"
    proj = Projeto.criar(
        nome="proj_p2_pronta",
        roteiro="## B0\n\n**B0-S01**\nO imperador marchou para a batalha.",
        raiz_projetos=raiz,
    )

    # Fornece áudio do usuário em 00_entrada/narracao_pt-BR.wav
    audio_usuario = proj.pastas.entrada / "narracao_pt-BR.wav"
    with wave.open(str(audio_usuario), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(b"\x00\x00" * 48000)

    class AlinhadorMock:
        def disponivel(self) -> bool:
            return True

        def alinhar(
            self,
            audio_wav: Path,
            saida_palavras: Path,
            saida_segmentos: Path,
            segmentos_info: list[dict] | None = None,
            idioma: str = "pt",
            device: str | None = None,
            timeout: float = 300,
        ) -> tuple[Path, Path]:
            saida_palavras.write_text("[]", encoding="utf-8")
            # Texto com divergência para testar emissão do aviso
            segs = [
                {
                    "id": "B0-S01",
                    "texto": "O imperador marchou com grande fúria para a guerra distante.",
                    "inicio_s": 0.0,
                    "fim_s": 2.0,
                }
            ]
            saida_segmentos.write_text(json.dumps(segs), encoding="utf-8")
            return saida_palavras, saida_segmentos

    class TTSMock(AdaptadorVoiceStudio):
        def disponivel(self) -> bool:
            return True

    executor = ExecutorPipeline(proj)
    registrar_handlers_disponiveis(
        executor,
        orquestrador=OrquestradorNarracao(
            adaptador_tts=TTSMock(),
            alinhador=AlinhadorMock(),
        ),
    )
    ctx = ContextoEtapa(
        projeto=proj,
        etapa=executor.grafo.etapas["P2_narracao"],
        banco=executor.banco,
    )

    # Executa P2_narracao diretamente
    handler = executor._handlers["P2_narracao"]
    await handler(ctx)

    # Verifica que narracao_completa.wav e segmentos.json foram gerados
    pasta_pt = proj.pastas.audio / "pt-BR"
    assert (pasta_pt / "narracao_completa.wav").is_file()
    assert (pasta_pt / "segmentos.json").is_file()
    assert (pasta_pt / "qualidade.json").is_file()
    # Verifica que o aviso estruturado foi gravado em 01_plano
    aviso_plano = proj.pastas.plano / "aviso_narracao_pronta.json"
    assert aviso_plano.is_file()
    dados_aviso = json.loads(aviso_plano.read_text(encoding="utf-8"))
    assert dados_aviso["idioma"] == "pt-BR"
    assert "Divergência textual" in dados_aviso["aviso"]
    assert dados_aviso["wer"] > 0.08
