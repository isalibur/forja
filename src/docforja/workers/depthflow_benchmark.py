"""Animação de parallax 2.5D no ambiente isolado do DepthFlow."""

from __future__ import annotations

import math
import sys

from attrs import define
from depthflow.scene import DepthScene


@define
class OrbitalParallax(DepthScene):
    """Cena com movimento orbital/circular sutil para efeito 2.5D de parallax."""

    def update(self) -> None:
        intensity = 0.40
        self.state.steady = 0.30
        self.state.focus = 0.35
        self.state.zoom = 0.96
        self.state.isometric = 0.35 * math.cos(self.cycle) + 0.65
        self.state.offset = (
            intensity * math.sin(self.cycle),
            intensity * 0.3 * math.sin(2 * self.cycle),
        )


def main(args: list[str]) -> None:
    scene = OrbitalParallax(backend="headless")
    scene.cli.meta(args)


if __name__ == "__main__":
    main(sys.argv[1:])
