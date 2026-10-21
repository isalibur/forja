import json
import subprocess
from pathlib import Path

from docforja.audio import mixagem


def _json_medicoes(saida: bool = False) -> str:
    dados = {
        "input_i": "-20.0",
        "input_tp": "-1.0",
        "input_lra": "5.0",
        "input_thresh": "-30.0",
        "target_offset": "0.0",
    }
    if saida:
        dados.update({"output_i": "-14.0", "output_tp": "-1.0", "output_lra": "7.0"})
    return json.dumps(dados)


def test_mixar_audio_executa_dois_passes_e_registra_medicoes_reais(tmp_path, monkeypatch):
    narracao = tmp_path / "voz.wav"
    trilha = tmp_path / "trilha.wav"
    destino = tmp_path / "mix_final.wav"
    narracao.write_bytes(b"voz de teste")
    trilha.write_bytes(b"trilha de teste")
    chamadas = []

    monkeypatch.setattr(mixagem.shutil, "which", lambda _programa: "ffmpeg.exe")

    def executar(comando, **_kwargs):
        chamadas.append(comando)
        if len(chamadas) == 2:
            Path(comando[-1]).write_bytes(b"mix renderizada")
        return subprocess.CompletedProcess(
            comando,
            0,
            "",
            _json_medicoes(saida=len(chamadas) == 2),
        )

    monkeypatch.setattr(mixagem.subprocess, "run", executar)

    relatorio = mixagem.mixar_audio(narracao, destino, "pt-BR", trilha)

    assert len(chamadas) == 2
    assert "sidechaincompress" in chamadas[0][chamadas[0].index("-filter_complex") + 1]
    assert "measured_I=-20.0" in chamadas[1][chamadas[1].index("-filter_complex") + 1]
    assert relatorio.medido_lufs == -14.0
    assert relatorio.true_peak_dbtp == -1.0
    assert relatorio.ganho_trilha_sob_fala == 0.12
    assert relatorio.hash_trilha is not None
    assert destino.read_bytes() == b"mix renderizada"
    dados = json.loads(destino.with_name("relatorio_mix.json").read_text(encoding="utf-8"))
    assert dados["medido_lufs"] == -14.0
    assert dados["hash_mix"] == relatorio.hash_mix
    relatorio_cache = mixagem.mixar_audio(narracao, destino, "pt-BR", trilha)
    assert len(chamadas) == 2
    assert relatorio_cache.hash_mix == relatorio.hash_mix


def test_mixar_audio_sem_trilha_normaliza_apenas_a_voz(tmp_path, monkeypatch):
    narracao = tmp_path / "voz.wav"
    destino = tmp_path / "mix_final.wav"
    narracao.write_bytes(b"voz de teste")
    chamadas = []

    monkeypatch.setattr(mixagem.shutil, "which", lambda _programa: "ffmpeg.exe")

    def executar(comando, **_kwargs):
        chamadas.append(comando)
        if len(chamadas) == 2:
            Path(comando[-1]).write_bytes(b"voz normalizada")
        return subprocess.CompletedProcess(
            comando,
            0,
            "",
            _json_medicoes(saida=len(chamadas) == 2),
        )

    monkeypatch.setattr(mixagem.subprocess, "run", executar)

    relatorio = mixagem.mixar_audio(narracao, destino, "pt-BR")

    assert "sidechaincompress" not in str(chamadas)
    assert relatorio.ganho_trilha_sob_fala is None
    assert relatorio.sidechain_ducking == "inativo (sem trilha)"
    assert relatorio.hash_trilha is None


def test_mixar_audio_recusa_medir_ffmpeg_com_loudness_nao_finito(tmp_path, monkeypatch):
    narracao = tmp_path / "voz.wav"
    narracao.write_bytes(b"voz de teste")
    monkeypatch.setattr(mixagem.shutil, "which", lambda _programa: "ffmpeg.exe")
    monkeypatch.setattr(
        mixagem,
        "_executar_ffmpeg",
        lambda _comando: _json_medicoes().replace('"-20.0"', '"-inf"'),
    )

    try:
        mixagem.mixar_audio(narracao, tmp_path / "mix.wav", "pt-BR")
    except ValueError as exc:
        assert "não é finita" in str(exc)
    else:
        raise AssertionError("Medições não finitas não devem produzir uma mix aprovada.")
