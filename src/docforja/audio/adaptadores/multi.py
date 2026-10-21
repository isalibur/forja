"""Despacho da narração por idioma, para usar uma voz diferente em cada língua."""

from __future__ import annotations

from pathlib import Path

from docforja.audio.adaptadores.base import AdaptadorTTS


class AdaptadorMultiIdioma(AdaptadorTTS):
    """Escolhe o motor pelo idioma e usa o motor padrão nos idiomas sem entrada."""

    def __init__(self, motores: dict[str, AdaptadorTTS], padrao: AdaptadorTTS) -> None:
        self.motores = {chave.lower(): motor for chave, motor in motores.items()}
        self.padrao = padrao

    def motor_do_idioma(self, idioma: str) -> AdaptadorTTS:
        return self.motores.get((idioma or "").lower(), self.padrao)

    def disponivel(self) -> bool:
        return self.padrao.disponivel() and all(
            motor.disponivel() for motor in self.motores.values()
        )

    def gerar(
        self,
        texto: str,
        saida_wav: Path,
        voz: str | None = None,
        idioma: str = "pt-BR",
        velocidade: float = 1.0,
    ) -> Path:
        return self.motor_do_idioma(idioma).gerar(
            texto, saida_wav, voz=voz, idioma=idioma, velocidade=velocidade
        )


__all__ = ["AdaptadorMultiIdioma"]
