import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsO1Identificacao } from "../schemas/sobreposicoes";
import { tokens } from "../tokens";
import { animarEntrada, animarSaida } from "../utilitarios/animacoes";

export const O1_Identificacao: React.FC<PropsO1Identificacao> = ({
  nome,
  descricao,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width } = useVideoConfig();

  // Animacao de entrada e saida (fade + slide horizontal/vertical de 40px)
  const entrada = animarEntrada(frame, tokens.durationFrames.enter);
  const saida = animarSaida(frame, durationInFrames, tokens.durationFrames.exit);
  const opacidade = entrada * saida;
  const translacaoY = (1 - entrada) * 30 + (1 - saida) * 20;

  const escala = width / 1920;

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        zIndex: 50,
        paddingLeft: `${tokens.safeArea.x * 100}%`,
        paddingBottom: `${tokens.safeArea.y * 100}%`,
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-end",
        alignItems: "flex-start",
      }}
    >
      <div
        style={{
          opacity: opacidade,
          transform: `translateY(${translacaoY}px)`,
          display: "flex",
          alignItems: "stretch",
          gap: `${16 * escala}px`,
          background: "rgba(14, 14, 16, 0.85)",
          backdropFilter: "blur(8px)",
          border: `1px solid rgba(255, 106, 43, 0.2)`,
          padding: `${12 * escala}px ${20 * escala}px`,
          borderRadius: "4px",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.6)",
        }}
      >
        {/* Barra fina Ember */}
        <div
          style={{
            width: `${4 * escala}px`,
            backgroundColor: tokens.color.ember,
            borderRadius: "2px",
          }}
        />

        <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
          {/* Nome */}
          <div
            style={{
              fontFamily: tokens.font.title.family,
              fontWeight: tokens.font.title.weight,
              fontSize: `${28 * escala}px`,
              letterSpacing: tokens.font.title.tracking,
              color: tokens.color.bone,
              textTransform: "uppercase",
              lineHeight: 1.1,
            }}
          >
            {nome}
          </div>

          {/* Descricao opcional */}
          {descricao && (
            <div
              style={{
                fontFamily: tokens.font.data.family,
                fontWeight: tokens.font.data.weight,
                fontSize: `${16 * escala}px`,
                letterSpacing: tokens.font.data.tracking,
                color: tokens.color.ashLight,
                marginTop: `${4 * escala}px`,
                lineHeight: 1.2,
              }}
            >
              {descricao}
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
