import React from "react";
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT03FotoRecorte } from "../schemas/templates";
import { tokens } from "../tokens";
import { animarEntrada } from "../utilitarios/animacoes";
import { TexturaFilme } from "../utilitarios/TexturaFilme";

export const T03_FotoRecorte: React.FC<PropsT03FotoRecorte> = ({
  src_sujeito,
  src_fundo,
  fundo_tipo = "desfocado",
  entrada = "baixo",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const progresso = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const animEntrada = animarEntrada(frame, tokens.durationFrames.enter + 6);

  // Deslocamento sutil independente entre as duas camadas para criar profundidade
  const escalaFundo = 1.05 + progresso * 0.04;
  const escalaSujeito = 1.0 + progresso * 0.08;

  let translacaoYSujeito = 0;
  if (entrada === "baixo") {
    translacaoYSujeito = (1 - animEntrada) * 80;
  } else if (entrada === "zoom") {
    translacaoYSujeito = (1 - animEntrada) * 20;
  }

  const imagemFundo = src_fundo || src_sujeito;

  return (
    <AbsoluteFill style={{ backgroundColor: tokens.color.ink, overflow: "hidden" }}>
      {/* Camada 1: Fundo */}
      <AbsoluteFill
        style={{
          transform: `scale(${escalaFundo})`,
          filter: fundo_tipo === "desfocado" ? "blur(18px) brightness(0.4) saturate(0.6)" : undefined,
          background: fundo_tipo === "paleta" ? tokens.color.basalt : undefined,
        }}
      >
        {fundo_tipo !== "paleta" && (
          <Img
            src={imagemFundo}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        )}
      </AbsoluteFill>

      {/* Gradiente de escurecimento cinematografico */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 60%, transparent 20%, rgba(14, 14, 16, 0.7) 100%)`,
        }}
      />

      {/* Camada 2: Sujeito Recortado (BiRefNet) */}
      <AbsoluteFill
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "flex-end",
          transform: `translateY(${translacaoYSujeito}px) scale(${escalaSujeito})`,
          opacity: animEntrada,
          filter: "drop-shadow(0 20px 40px rgba(0, 0, 0, 0.8))",
        }}
      >
        <Img
          src={src_sujeito}
          style={{
            maxHeight: "92%",
            maxWidth: "85%",
            objectFit: "contain",
          }}
        />
      </AbsoluteFill>

      <TexturaFilme />
    </AbsoluteFill>
  );
};
