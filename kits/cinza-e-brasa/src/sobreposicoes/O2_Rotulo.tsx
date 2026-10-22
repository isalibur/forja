import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { PropsO2Rotulo } from "../schemas/sobreposicoes";
import { tokens } from "../tokens";
import { useSafeArea } from "../utilitarios/SafeArea";

export const O2_Rotulo: React.FC<PropsO2Rotulo> = ({
  tipo = "reconstituicao",
  texto,
}) => {
  const area = useSafeArea();
  const { width } = useVideoConfig();
  const escala = width / 1920;

  let conteudoTexto = tokens.label.aiReconstruction;
  let alinhamento: "left" | "right" = "left";

  if (tipo === "outro_vulcao") {
    conteudoTexto = tokens.label.realOtherVolcano;
  } else if (tipo === "credito") {
    conteudoTexto = texto || "FONTE HISTÓRICA / ACERVO";
    alinhamento = "right";
  }

  if (texto && tipo !== "credito") {
    conteudoTexto = texto;
  }

  const paddingX = area.x * 100;
  const paddingY = area.y * 100;

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        zIndex: 45,
        display: "flex",
        justifyContent: "flex-end",
        alignItems: alinhamento === "left" ? "flex-start" : "flex-end",
        paddingLeft: alinhamento === "left" ? `${paddingX}%` : undefined,
        paddingRight: alinhamento === "right" ? `${paddingX}%` : undefined,
        paddingBottom: `${paddingY}%`,
      }}
    >
      <div
        style={{
          fontFamily: tokens.font.data.family,
          fontWeight: tokens.font.data.weight,
          fontSize: `${13 * escala}px`,
          letterSpacing: "0.08em",
          color: tokens.color.bone,
          opacity: tokens.label.opacity,
          background: "rgba(14, 14, 16, 0.45)",
          backdropFilter: "blur(4px)",
          padding: `${4 * escala}px ${10 * escala}px`,
          borderRadius: "2px",
          border: `1px solid rgba(110, 106, 102, 0.3)`,
          textTransform: "uppercase",
        }}
      >
        {conteudoTexto}
      </div>
    </AbsoluteFill>
  );
};
