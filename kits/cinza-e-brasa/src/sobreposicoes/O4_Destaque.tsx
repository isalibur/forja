import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsO4Destaque } from "../schemas/sobreposicoes";
import { tokens } from "../tokens";
import { animarEntrada, animarSaida } from "../utilitarios/animacoes";

export const O4_Destaque: React.FC<PropsO4Destaque> = ({
  tipo = "circulo",
  posicao = { x: 50, y: 50 },
  tamanho = 120,
  rotulo,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width } = useVideoConfig();

  const escala = width / 1920;
  const entrada = animarEntrada(frame, tokens.durationFrames.enter);
  const saida = animarSaida(frame, durationInFrames, tokens.durationFrames.exit);
  const opacidade = entrada * saida;

  // Pulso continuo sutil
  const pulso = 1.0 + Math.sin(frame * 0.15) * 0.05;
  const raioAjustado = (tamanho / 2) * escala * pulso;

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        zIndex: 49,
      }}
    >
      <div
        style={{
          position: "absolute",
          left: `${posicao.x}%`,
          top: `${posicao.y}%`,
          transform: `translate(-50%, -50%) scale(${entrada})`,
          opacity: opacidade,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <svg
          width={raioAjustado * 2 + 40}
          height={raioAjustado * 2 + 40}
          viewBox={`0 0 ${raioAjustado * 2 + 40} ${raioAjustado * 2 + 40}`}
          style={{ overflow: "visible" }}
        >
          {tipo === "circulo" && (
            <>
              {/* Anel de brilho externo */}
              <circle
                cx={raioAjustado + 20}
                cy={raioAjustado + 20}
                r={raioAjustado + 8}
                fill="none"
                stroke={tokens.color.ember}
                strokeWidth={1.5}
                strokeDasharray="4 4"
                opacity={0.4}
              />
              {/* Anel principal */}
              <circle
                cx={raioAjustado + 20}
                cy={raioAjustado + 20}
                r={raioAjustado}
                fill="rgba(255, 106, 43, 0.08)"
                stroke={tokens.color.ember}
                strokeWidth={3 * escala}
                filter="drop-shadow(0 0 8px rgba(255, 106, 43, 0.8))"
              />
              {/* Ponto central */}
              <circle
                cx={raioAjustado + 20}
                cy={raioAjustado + 20}
                r={4 * escala}
                fill={tokens.color.bone}
              />
            </>
          )}

          {tipo === "caixa" && (
            <rect
              x={20}
              y={20}
              width={raioAjustado * 2}
              height={raioAjustado * 2}
              fill="rgba(255, 106, 43, 0.08)"
              stroke={tokens.color.ember}
              strokeWidth={2.5 * escala}
              rx={6}
              filter="drop-shadow(0 0 8px rgba(255, 106, 43, 0.8))"
            />
          )}

          {tipo === "seta" && (
            <path
              d={`M ${raioAjustado + 20} 5 L ${raioAjustado + 10} 25 L ${raioAjustado + 16} 25 L ${raioAjustado + 16} 50 L ${raioAjustado + 24} 50 L ${raioAjustado + 24} 25 L ${raioAjustado + 30} 25 Z`}
              fill={tokens.color.ember}
              filter="drop-shadow(0 0 6px rgba(255, 106, 43, 0.9))"
            />
          )}
        </svg>

        {rotulo && (
          <div
            style={{
              marginTop: `${8 * escala}px`,
              background: "rgba(14, 14, 16, 0.9)",
              border: `1px solid ${tokens.color.ember}`,
              padding: `${4 * escala}px ${12 * escala}px`,
              borderRadius: "4px",
              fontFamily: tokens.font.data.family,
              fontSize: `${13 * escala}px`,
              fontWeight: 600,
              color: tokens.color.bone,
              letterSpacing: "0.06em",
              textTransform: "uppercase",
              whiteSpace: "nowrap",
              boxShadow: "0 4px 16px rgba(0,0,0,0.6)",
            }}
          >
            {rotulo}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
