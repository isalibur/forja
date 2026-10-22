import React from "react";
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT05Comparacao } from "../schemas/templates";
import { tokens } from "../tokens";
import { easingMovimento } from "../utilitarios/animacoes";
import { TexturaFilme } from "../utilitarios/TexturaFilme";
import { MARGEM_DIREITA_VERTICAL, useFormatoVertical, useSafeArea } from "../utilitarios/SafeArea";

export const T05_Comparacao: React.FC<PropsT05Comparacao> = ({
  src_a,
  src_b,
  rotulo_a = "ANTES",
  rotulo_b = "DEPOIS",
  modo = "divisor",
}) => {
  const area = useSafeArea();
  const vertical = useFormatoVertical();
  const frame = useCurrentFrame();
  const { durationInFrames, width } = useVideoConfig();

  const escala = width / 1920;

  // Divisor desliza da esquerda (30%) para a direita (70%)
  const progressoDivisor = interpolate(
    frame,
    [0, Math.min(60, durationInFrames)],
    [30, 65],
    {
      easing: easingMovimento,
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: tokens.color.ink, overflow: "hidden" }}>
      {modo === "divisor" ? (
        <>
          {/* Imagem A (fundo completo) */}
          <AbsoluteFill>
            <Img
              src={src_a}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>

          {/* Imagem B (revelada pelo clip-path do divisor) */}
          <AbsoluteFill
            style={{
              clipPath: `polygon(${progressoDivisor}% 0, 100% 0, 100% 100%, ${progressoDivisor}% 100%)`,
            }}
          >
            <Img
              src={src_b}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>

          {/* Linha vertical divisoria com brilho Ember */}
          <div
            style={{
              position: "absolute",
              top: 0,
              bottom: 0,
              left: `${progressoDivisor}%`,
              width: `${3 * escala}px`,
              backgroundColor: tokens.color.ember,
              boxShadow: `0 0 12px ${tokens.color.ember}`,
              transform: "translateX(-50%)",
            }}
          />
        </>
      ) : (
        /* Modo lado a lado */
        <div style={{ display: "flex", width: "100%", height: "100%" }}>
          <div style={{ flex: 1, position: "relative", borderRight: `2px solid ${tokens.color.basalt}` }}>
            <Img src={src_a} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          </div>
          <div style={{ flex: 1, position: "relative" }}>
            <Img src={src_b} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          </div>
        </div>
      )}

      {/* Rotulos superiores */}
      <div
        style={{
          position: "absolute",
          top: `${area.y * 100}%`,
          left: `${area.x * 100}%`,
          fontFamily: tokens.font.data.family,
          fontSize: `${14 * escala}px`,
          fontWeight: 700,
          color: tokens.color.bone,
          background: "rgba(14, 14, 16, 0.8)",
          padding: `${6 * escala}px ${14 * escala}px`,
          borderRadius: "4px",
          border: `1px solid rgba(255, 106, 43, 0.3)`,
          textTransform: "uppercase",
        }}
      >
        {rotulo_a}
      </div>

      <div
        style={{
          position: "absolute",
          top: `${area.y * 100}%`,
          right: `${(vertical ? MARGEM_DIREITA_VERTICAL : area.x) * 100}%`,
          fontFamily: tokens.font.data.family,
          fontSize: `${14 * escala}px`,
          fontWeight: 700,
          color: tokens.color.bone,
          background: "rgba(14, 14, 16, 0.8)",
          padding: `${6 * escala}px ${14 * escala}px`,
          borderRadius: "4px",
          border: `1px solid rgba(255, 106, 43, 0.3)`,
          textTransform: "uppercase",
        }}
      >
        {rotulo_b}
      </div>

      <TexturaFilme />
    </AbsoluteFill>
  );
};
