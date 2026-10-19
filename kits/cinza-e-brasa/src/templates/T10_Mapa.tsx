import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT10Mapa } from "../schemas/templates";
import { tokens } from "../tokens";
import { animarEntrada, easingEntrada, easingMovimento } from "../utilitarios/animacoes";
import { TexturaFilme } from "../utilitarios/TexturaFilme";

export const T10_Mapa: React.FC<PropsT10Mapa> = ({
  regiao = "BAÍA DE NÁPOLES · CAMPÂNIA 79 d.C.",
  pontos = [
    { rotulo: "VESÚVIO", x: 55, y: 38, tipo: "vulcao" },
    { rotulo: "POMPEIA", x: 62, y: 55, tipo: "cidade" },
    { rotulo: "HERCULANO", x: 44, y: 46, tipo: "cidade" },
    { rotulo: "MISENO (Frota)", x: 20, y: 58, tipo: "porto" },
  ],
  rotas = [
    {
      de: "Miseno",
      para: "Estábia",
      pontos: [
        { x: 20, y: 58 },
        { x: 38, y: 68 },
        { x: 56, y: 72 },
        { x: 68, y: 68 },
      ],
    },
  ],
  areas = [
    {
      rotulo: "ZONA DE IMPACTO PIROCLÁSTICO",
      centro: { x: 55, y: 44 },
      raio: 16,
      cor: tokens.color.pompeiiRed,
    },
  ],
  rotulo_costa = "LINHA DE COSTA APROXIMADA DE 79 d.C.",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width } = useVideoConfig();

  const escala = width / 1920;
  const entrada = animarEntrada(frame, tokens.durationFrames.enter);

  // Voo de camera suave (zoom de 1.05 para 1.15)
  const cameraZoom = interpolate(frame, [0, durationInFrames], [1.02, 1.12], {
    easing: easingMovimento,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Animacao das rotas navais / trajetos
  const progressoRota = interpolate(frame, [15, 45], [0, 1], {
    easing: easingEntrada,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: tokens.color.ink,
        overflow: "hidden",
      }}
    >
      {/* Camada do Mapa Cartografico estilizado */}
      <div
        style={{
          width: "100%",
          height: "100%",
          transform: `scale(${cameraZoom})`,
          transformOrigin: "55% 45%",
          position: "relative",
        }}
      >
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 1000 600"
          style={{ width: "100%", height: "100%" }}
        >
          {/* Fundo do Mar (Tirreno / Baia de Napoles) */}
          <rect width="1000" height="600" fill="#0A0B0E" />

          {/* Massa de Terra (Campania) */}
          <path
            d="M 0 0 L 1000 0 L 1000 600 L 780 600 C 700 520, 650 480, 580 430 C 500 370, 380 430, 280 450 C 180 470, 100 390, 0 340 Z"
            fill={tokens.color.basalt}
            stroke="rgba(110, 106, 102, 0.4)"
            strokeWidth="1.5"
          />

          {/* Linha da costa estilizada com brilho suave */}
          <path
            d="M 0 340 C 100 390, 180 470, 280 450 C 380 430, 500 370, 580 430 C 650 480, 700 520, 780 600"
            fill="none"
            stroke={tokens.color.scienceCyan}
            strokeWidth="2"
            opacity="0.45"
            strokeDasharray="6 3"
          />

          {/* Areas de risco ou cobertura piroclastica */}
          {areas.map((area, idx) => {
            const cx = (area.centro.x / 100) * 1000;
            const cy = (area.centro.y / 100) * 600;
            const r = (area.raio / 100) * 1000;
            return (
              <g key={idx} opacity={entrada * 0.45}>
                <circle
                  cx={cx}
                  cy={cy}
                  r={r}
                  fill={area.cor || tokens.color.pompeiiRed}
                  stroke={area.cor || tokens.color.ember}
                  strokeWidth="2"
                  strokeDasharray="4 4"
                />
              </g>
            );
          })}

          {/* Rotas de navio / resgate */}
          {rotas.map((rota, idx) => {
            if (rota.pontos.length < 2) return null;
            const d = rota.pontos.reduce((acc, p, i) => {
              const px = (p.x / 100) * 1000;
              const py = (p.y / 100) * 600;
              return i === 0 ? `M ${px} ${py}` : `${acc} L ${px} ${py}`;
            }, "");

            return (
              <path
                key={idx}
                d={d}
                fill="none"
                stroke={tokens.color.ember}
                strokeWidth="3"
                strokeDasharray="12 6"
                strokeDashoffset={(1 - progressoRota) * 200}
                filter="drop-shadow(0 0 6px rgba(255, 106, 43, 0.8))"
              />
            );
          })}

          {/* Pontos / Cidades */}
          {pontos.map((p, idx) => {
            const px = (p.x / 100) * 1000;
            const py = (p.y / 100) * 600;
            const isVulcao = p.tipo === "vulcao";
            return (
              <g key={idx} opacity={entrada}>
                {isVulcao ? (
                  <>
                    <polygon
                      points={`${px},${py - 14} ${px - 12},${py + 8} ${px + 12},${py + 8}`}
                      fill={tokens.color.ember}
                      stroke={tokens.color.bone}
                      strokeWidth="1.5"
                    />
                    <circle cx={px} cy={py - 14} r="3" fill={tokens.color.pompeiiRed} />
                  </>
                ) : (
                  <>
                    <circle cx={px} cy={py} r="5" fill={tokens.color.bone} stroke={tokens.color.ember} strokeWidth="2" />
                    <circle cx={px} cy={py} r="12" fill="none" stroke={tokens.color.ember} strokeWidth="1" opacity="0.5" />
                  </>
                )}
                <text
                  x={px + 14}
                  y={py + 4}
                  fill={isVulcao ? tokens.color.ember : tokens.color.bone}
                  fontFamily={tokens.font.data.family}
                  fontSize="13"
                  fontWeight="600"
                  letterSpacing="0.08em"
                  filter="drop-shadow(0 2px 4px rgba(0,0,0,0.9))"
                >
                  {p.rotulo}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Cabecalho de Regiao */}
      <div
        style={{
          position: "absolute",
          top: `${tokens.safeArea.y * 100}%`,
          left: `${tokens.safeArea.x * 100}%`,
          opacity: entrada,
          fontFamily: tokens.font.data.family,
          fontSize: `${16 * escala}px`,
          fontWeight: 700,
          color: tokens.color.bone,
          background: "rgba(14, 14, 16, 0.85)",
          backdropFilter: "blur(6px)",
          padding: `${8 * escala}px ${16 * escala}px`,
          borderRadius: "4px",
          border: `1px solid rgba(255, 106, 43, 0.25)`,
          letterSpacing: "0.06em",
          textTransform: "uppercase",
        }}
      >
        {regiao}
      </div>

      {/* Selo obrigatorio da costa antiga */}
      <div
        style={{
          position: "absolute",
          bottom: `${tokens.safeArea.y * 100}%`,
          right: `${tokens.safeArea.x * 100}%`,
          fontFamily: tokens.font.data.family,
          fontSize: `${12 * escala}px`,
          color: tokens.color.ashLight,
          opacity: 0.7,
          background: "rgba(14, 14, 16, 0.7)",
          padding: `${4 * escala}px ${10 * escala}px`,
          borderRadius: "3px",
          letterSpacing: "0.05em",
        }}
      >
        {rotulo_costa}
      </div>

      <TexturaFilme />
    </AbsoluteFill>
  );
};
