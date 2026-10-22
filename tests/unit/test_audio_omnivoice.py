"""Motor OmniVoice com voz clonada: adaptador, catálogo e ligação no handler."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from docforja.audio.adaptadores.kokoro import AdaptadorKokoro
from docforja.audio.adaptadores.multi import AdaptadorMultiIdioma
from docforja.audio.adaptadores.omnivoice import AdaptadorOmniVoice
from docforja.audio.catalogo import listar_vozes, resolver_voz
from docforja.nucleo.handlers import _criar_orquestrador
from docforja.nucleo.projeto import Projeto
from docforja.settings import AppSettings, OmniVoiceSettings

ROTEIRO_VALIDO = """## B1 — Abertura\n\n**B1-S01** {calmo}\nA história começa aqui.\n"""


def _ambiente(tmp_path: Path) -> tuple[Path, Path]:
    python = tmp_path / "envs" / "tts" / "python.exe"
    python.parent.mkdir(parents=True)
    python.touch()
    prompt = tmp_path / "voz" / "perfil.pt"
    prompt.parent.mkdir(parents=True)
    prompt.touch()
    return python, prompt


def test_adaptador_exige_ambiente_e_prompt(tmp_path: Path) -> None:
    python, prompt = _ambiente(tmp_path)
    completo = AdaptadorOmniVoice(python_path=python, prompt=prompt)
    sem_prompt = AdaptadorOmniVoice(python_path=python, prompt=tmp_path / "ausente.pt")
    sem_python = AdaptadorOmniVoice(python_path=tmp_path / "ausente.exe", prompt=prompt)

    assert completo.disponivel() is True
    assert sem_prompt.disponivel() is False
    assert sem_python.disponivel() is False


def test_gerar_chama_o_worker_com_o_prompt_da_voz(tmp_path: Path, monkeypatch) -> None:
    python, prompt = _ambiente(tmp_path)
    chamadas: list[list[str]] = []

    def executar(comando, **_kwargs):
        chamadas.append(list(comando))
        Path(comando[comando.index("--saida") + 1]).write_bytes(b"wav")
        return subprocess.CompletedProcess(comando, 0, "", "")

    monkeypatch.setattr(
        "docforja.audio.adaptadores.omnivoice.subprocess.run", executar
    )
    adaptador = AdaptadorOmniVoice(
        python_path=python, prompt=prompt, cache=tmp_path / "cache"
    )

    saida = adaptador.gerar("Texto", tmp_path / "saida.wav", voz="perfil")

    assert saida.is_file()
    comando = chamadas[0]
    assert comando[0] == str(python)
    assert comando[comando.index("--voz") + 1] == str(prompt)
    assert comando[comando.index("--texto") + 1] == "Texto"
    assert comando[comando.index("--cache") + 1] == str(tmp_path / "cache")


def test_gerar_relata_a_falha_do_worker(tmp_path: Path, monkeypatch) -> None:
    python, prompt = _ambiente(tmp_path)
    monkeypatch.setattr(
        "docforja.audio.adaptadores.omnivoice.subprocess.run",
        lambda comando, **_kwargs: subprocess.CompletedProcess(comando, 1, "", "sem VRAM"),
    )
    adaptador = AdaptadorOmniVoice(python_path=python, prompt=prompt)

    with pytest.raises(RuntimeError, match="sem VRAM"):
        adaptador.gerar("Texto", tmp_path / "saida.wav", voz="perfil")


def test_termos_de_uso_registram_a_origem_da_voz(tmp_path: Path) -> None:
    python, prompt = _ambiente(tmp_path)
    adaptador = AdaptadorOmniVoice(python_path=python, prompt=prompt)

    termos = adaptador.termos_de_uso()

    assert termos["motor"] == "omnivoice"
    assert termos["prompt_de_clonagem"] == str(prompt)
    assert "consentimento" in termos["origem"]


def test_catalogo_encontra_a_voz_clonada_e_recusa_a_desconhecida() -> None:
    vozes = listar_vozes("omnivoice")

    assert vozes
    assert resolver_voz("omnivoice", "voz-inexistente") is None
    assert resolver_voz("kokoro", "pm_alex") is not None


def test_handler_monta_o_motor_omnivoice_com_a_voz_do_projeto(
    tmp_path: Path, monkeypatch
) -> None:
    projeto = Projeto.criar(
        nome="teste_omnivoice",
        roteiro=ROTEIRO_VALIDO,
        raiz_projetos=tmp_path,
        opcoes_adicionais={"motor_tts": "omnivoice", "voz": "nova_ref_7s"},
    )
    monkeypatch.setattr(
        "docforja.nucleo.handlers.load_settings",
        lambda: AppSettings(omnivoice=OmniVoiceSettings(cache=str(tmp_path / "cache"))),
    )

    orquestrador = _criar_orquestrador("omnivoice", projeto)

    assert isinstance(orquestrador.tts, AdaptadorOmniVoice)
    assert orquestrador.tts.modelo_repo == "k2-fsa/OmniVoice"
    assert orquestrador.tts.prompt is not None
    assert orquestrador.tts.prompt.name == "nova_ref_7s.pt"


def test_handler_aceita_voz_explicita_de_campanha_sem_projeto(monkeypatch) -> None:
    monkeypatch.setattr("docforja.nucleo.handlers.load_settings", lambda: AppSettings())

    orquestrador = _criar_orquestrador("omnivoice", voz="nova_ref_7s")

    assert isinstance(orquestrador.tts, AdaptadorOmniVoice)
    assert orquestrador.tts.prompt is not None
    assert orquestrador.tts.prompt.name == "nova_ref_7s.pt"


def test_motores_por_idioma_despacham_a_voz_clonada_para_o_pt(
    tmp_path: Path, monkeypatch
) -> None:
    """O projeto pode usar a voz clonada no pt-BR e outro motor nos demais idiomas."""
    projeto = Projeto.criar(
        nome="teste_omnivoice_multilingue",
        roteiro=ROTEIRO_VALIDO,
        raiz_projetos=tmp_path,
        opcoes_adicionais={
            "motor_tts": "kokoro",
            "motores": {"pt-BR": "omnivoice"},
            "vozes": {"pt-BR": "nova_ref_7s", "en": "af_sarah"},
        },
    )
    monkeypatch.setattr(
        "docforja.nucleo.handlers.load_settings",
        lambda: AppSettings(omnivoice=OmniVoiceSettings(cache=str(tmp_path / "cache"))),
    )

    orquestrador = _criar_orquestrador(None, projeto)
    adaptador = orquestrador.tts

    assert isinstance(adaptador, AdaptadorMultiIdioma)
    assert isinstance(adaptador.motor_do_idioma("pt-BR"), AdaptadorOmniVoice)
    assert isinstance(adaptador.motor_do_idioma("en"), AdaptadorKokoro)


def test_handler_recusa_voz_que_nao_esta_no_catalogo(tmp_path: Path, monkeypatch) -> None:
    projeto = Projeto.criar(
        nome="teste_omnivoice_sem_voz",
        roteiro=ROTEIRO_VALIDO,
        raiz_projetos=tmp_path,
        opcoes_adicionais={"motor_tts": "omnivoice", "voz": "perfil-inexistente"},
    )
    monkeypatch.setattr(
        "docforja.nucleo.handlers.load_settings", lambda: AppSettings()
    )

    with pytest.raises(ValueError, match="catálogo"):
        _criar_orquestrador("omnivoice", projeto)


def test_configuracao_traz_o_motor_e_o_ambiente() -> None:
    import yaml

    configuracao = yaml.safe_load(
        (Path(__file__).resolve().parents[2] / "config" / "modelos.yaml").read_text(
            encoding="utf-8"
        )
    )
    candidatos = configuracao["tts"]["candidatos"]
    motores = {item["id"]: item for item in candidatos}

    assert motores["omnivoice-613m"]["adaptador"] == "omnivoice"
    vozes = motores["omnivoice-613m"]["benchmark"]["voices"]
    assert vozes[0]["id"] == "nova_ref_7s"
    assert vozes[0]["path"].endswith(".pt")
