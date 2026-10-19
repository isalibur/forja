import React from "react";
import { AbsoluteFill } from "remotion";
import { PropsT00Respiro } from "../schemas/templates";
import { tokens } from "../tokens";
import { TexturaFilme } from "../utilitarios/TexturaFilme";

export const T00_Respiro: React.FC<PropsT00Respiro> = ({
  cor = tokens.color.ink,
  particulas = true,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: cor }}>
      <TexturaFilme
        opacidadeGrao={tokens.texture.grain.opacity}
        mostrarVinheta={true}
        mostrarPoeira={particulas}
      />
    </AbsoluteFill>
  );
};
