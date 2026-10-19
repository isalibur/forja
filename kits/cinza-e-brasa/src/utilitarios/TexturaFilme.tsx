import React, { useMemo } from "react";
import { AbsoluteFill, random, useCurrentFrame } from "remotion";
import { tokens } from "../tokens";

interface TexturaFilmeProps {
  opacidadeGrao?: number;
  mostrarVinheta?: boolean;
  mostrarPoeira?: boolean;
}

export const TexturaFilme: React.FC<TexturaFilmeProps> = ({
  opacidadeGrao = tokens.texture.grain.opacity,
  mostrarVinheta = true,
  mostrarPoeira = false,
}) => {
  const frame = useCurrentFrame();

  // Seed aleatorio variavel por frame para simular emulsao de filme 35mm
  const seed = useMemo(() => {
    return Math.floor(random(frame) * 1000);
  }, [frame]);

  // Particulas de poeira e cinza caindo (se ativo)
  const particulas = useMemo(() => {
    if (!mostrarPoeira) return [];
    const lista = [];
    for (let i = 0; i < 20; i++) {
      const baseX = random(`x-${i}`) * 100;
      const velocidadeY = 0.5 + random(`vy-${i}`) * 1.5;
      const posY = (random(`y-${i}`) * 100 + frame * velocidadeY) % 105;
      const raio = 1.5 + random(`r-${i}`) * 2.5;
      const opacidade = 0.15 + random(`op-${i}`) * 0.35;
      lista.push({ x: baseX, y: posY, r: raio, opacidade });
    }
    return lista;
  }, [mostrarPoeira, frame]);

  return (
    <AbsoluteFill style={{ pointerEvents: "none", zIndex: 90 }}>
      {/* Camada de grao animado via filtro SVG fractal noise */}
      <svg
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          opacity: opacidadeGrao,
          mixBlendMode: "overlay",
        }}
      >
        <filter id="noiseFilter">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.8"
            numOctaves="3"
            stitchTiles="stitch"
            seed={seed}
          />
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 0
                    0 0 0 0 0
                    0 0 0 0 0
                    0 0 0 1 0"
          />
        </filter>
        <rect width="100%" height="100%" filter="url(#noiseFilter)" />
      </svg>

      {/* Vinheta cinematografica */}
      {mostrarVinheta && (
        <AbsoluteFill
          style={{
            background: `radial-gradient(circle at center, transparent 40%, rgba(14, 14, 16, ${tokens.texture.vignette.amount * 2.5}) 100%)`,
            mixBlendMode: "multiply",
          }}
        />
      )}

      {/* Particulas de poeira e cinza */}
      {mostrarPoeira && (
        <svg
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            mixBlendMode: "screen",
          }}
        >
          {particulas.map((p, idx) => (
            <circle
              key={idx}
              cx={`${p.x}%`}
              cy={`${p.y}%`}
              r={p.r}
              fill="#F4F0E8"
              opacity={p.opacidade}
            />
          ))}
        </svg>
      )}
    </AbsoluteFill>
  );
};
