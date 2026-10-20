import wave
from pathlib import Path

from docforja.audio.trilha import (
    garantir_trilha_provisoria_kit,
    gerar_trilha_provisoria_drone,
    resolver_trilha_provisoria,
)
from docforja.esquemas import Bloco, Plano, Shot
from docforja.nucleo.projeto import Projeto
from docforja.planejamento.previa import montar_manifesto_previa


def test_gerar_trilha_provisoria_drone(tmp_path: Path):
    destino = tmp_path / "trilha_drone.wav"
    gerar_trilha_provisoria_drone(destino, duracao_s=2.0, sample_rate=48000)

    assert destino.is_file()
    with wave.open(str(destino), "rb") as f:
        assert f.getnchannels() == 2
        assert f.getsampwidth() == 2
        assert f.getframerate() == 48000
        assert f.getnframes() == 96000


def test_resolver_trilha_provisoria_prioriza_projeto(tmp_path: Path):
    proj = Projeto.criar(
        nome="proj_trilha",
        roteiro="## B0\n\n**B0-S01**\nTeste.",
        raiz_projetos=tmp_path / "projetos",
    )
    trilha_projeto = proj.pastas.audio / "trilha" / "provisoria.wav"
    trilha_projeto.write_bytes(b"RIFF....WAVE")

    resolvida = resolver_trilha_provisoria(proj, kit_dir=tmp_path / "kit")
    assert resolvida == trilha_projeto


def test_resolver_trilha_provisoria_usa_kit_se_projeto_nao_tiver(tmp_path: Path):
    proj = Projeto.criar(
        nome="proj_sem_trilha",
        roteiro="## B0\n\n**B0-S01**\nTeste.",
        raiz_projetos=tmp_path / "projetos",
    )
    kit_dir = tmp_path / "kit_custom"
    trilhas_kit = kit_dir / "trilhas"
    trilhas_kit.mkdir(parents=True, exist_ok=True)
    trilha_kit = trilhas_kit / "provisoria.wav"
    trilha_kit.write_bytes(b"RIFF....WAVE")

    resolvida = resolver_trilha_provisoria(proj, kit_dir=kit_dir)
    assert resolvida == trilha_kit


def test_garantir_trilha_provisoria_kit_cria_wav_e_licenca(tmp_path: Path):
    kit_dir = tmp_path / "kit_novo"
    wav = garantir_trilha_provisoria_kit(kit_dir=kit_dir)

    assert wav.is_file()
    assert (kit_dir / "trilhas" / "provisoria.licenca.json").is_file()


def test_manifesto_previa_inclui_flag_trilha_provisoria():
    plano = Plano(
        projeto="teste",
        blocos=[
            Bloco(
                id="B0",
                titulo="Abertura",
                shots=[Shot(id="B0-01", segmentos=["B0-S01"], duracao_s=4, template="T01")],
            )
        ],
    )
    segmentos = [{"id": "B0-S01", "inicio_s": 0, "fim_s": 4}]

    manifesto_com = montar_manifesto_previa(
        plano, segmentos, {}, tem_trilha_provisoria=True
    )
    assert manifesto_com["tem_trilha_provisoria"] is True

    manifesto_sem = montar_manifesto_previa(
        plano, segmentos, {}, tem_trilha_provisoria=False
    )
    assert manifesto_sem["tem_trilha_provisoria"] is False
