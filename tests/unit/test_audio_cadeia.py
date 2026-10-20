from __future__ import annotations

from pathlib import Path

from docforja.audio.cadeia import aplicar_cadeia_voz


def test_cadeia_voz_aplica_reducao_de_ruido_leve(monkeypatch, tmp_path: Path) -> None:
    comandos: list[list[str]] = []

    def executar(comando: list[str], **_kwargs: object) -> None:
        comandos.append(comando)

    monkeypatch.setattr("docforja.audio.cadeia.subprocess.run", executar)
    destino = tmp_path / "voz.wav"

    aplicar_cadeia_voz(tmp_path / "origem.wav", destino)

    filtro = comandos[0][comandos[0].index("-af") + 1]
    assert filtro.startswith("afftdn=nr=6:nf=-50:tn=1,")
    assert "highpass=f=80" in filtro
    assert "acompressor=threshold=-18dB:ratio=3" in filtro
    assert comandos[0][-1] == str(destino)
