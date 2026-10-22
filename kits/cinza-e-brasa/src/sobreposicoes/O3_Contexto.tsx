import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsO3Contexto } from "../schemas/sobreposicoes";
import { tokens } from "../tokens";
import { animarEntrada, animarSaida } from "../utilitarios/animacoes";
import { useSafeArea } from "../utilitarios/SafeArea";

export const O3_Contexto: React.FC<PropsO3Contexto> = ({
  dia = 1,
  hora = "13:00",
  local = "POMPEIA",
  progresso = 0.15,
  aproximado = true,
}) => {
  const area = useSafeArea();
  const frame = useCurrentFrame();
  const { durationInFrames, width } = useVideoConfig();

  const escala = width / 1920;
  const entrada = animarEntrada(frame, tokens.durationFrames.enter);
  const saida = animarSaida(frame, durationInFrames, tokens.durationFrames.exit);
  const opacidade = entrada * saida;
  const translacaoY = (1 - entrada) * -20;

  const progressoClamped = Math.min(1, Math.max(0, progresso));

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        zIndex: 48,
        paddingLeft: `${area.x * 100}%`,
        paddingTop: `${area.y * 100}%`,
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "flex-start",
      }}
    >
      <div
        style={{
          opacity: opacidade,
          transform: `translateY(${translacaoY}px)`,
          fontFamily: tokens.font.data.family,
          background: "rgba(14, 14, 16, 0.75)",
          backdropFilter: "blur(6px)",
          padding: `${10 * escala}px ${16 * escala}px`,
          borderRadius: "4px",
          border: `1px solid rgba(255, 106, 43, 0.15)`,
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.5)",
          minWidth: `${200 * escala}px`,
        }}
      >
        {/* Linha 1: DIA */}
        <div
          style={{
            fontSize: `${13 * escala}px`,
            letterSpacing: tokens.font.data.tracking,
            color: tokens.color.ash,
            textTransform: "uppercase",
            fontWeight: 600,
          }}
        >
          DIA {dia}
        </div>

        {/* Linha 2: HORA */}
        <div
          style={{
            fontSize: `${26 * escala}px`,
            letterSpacing: "0.02em",
            color: tokens.color.bone,
            fontWeight: 700,
            lineHeight: 1.15,
            margin: `${2 * escala}px 0`,
          }}
        >
          {aproximado ? `≈ ${hora}` : hora}
        </div>

        {/* Linha 3: LOCAL */}
        <div
          style={{
            fontSize: `${13 * escala}px`,
            letterSpacing: "0.08em",
            color: tokens.color.ember,
            textTransform: "uppercase",
            fontWeight: 600,
          }}
        >
          {local}
        </div>

        {/* Linha 4: Barra horizontal fina de progresso da erupção */}
        <div
          style={{
            width: "100%",
            height: `${3 * escala}px`,
            backgroundColor: tokens.color.basalt,
            marginTop: `${8 * escala}px`,
            borderRadius: "1px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${progressoClamped * 100}%`,
              height: "100%",
              backgroundColor: tokens.color.ember,
              boxShadow: `0 0 8px ${tokens.color.ember}`,
              transition: "width 0.3s ease",
            }}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};
