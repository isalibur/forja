import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT01Foto } from "../schemas/templates";
import { tokens } from "../tokens";
import { calcularKenBurns } from "../utilitarios/animacoes";
import { TexturaFilme } from "../utilitarios/TexturaFilme";

export const T01_Foto: React.FC<PropsT01Foto> = ({
  src,
  movimento = "push_in",
  amplitude = 0.12,
  foco = { x: 0.5, y: 0.5 },
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const estiloKenBurns = calcularKenBurns(frame, durationInFrames, {
    movimento,
    amplitude,
    foco,
  });

  const isVideo = src.endsWith(".mp4") || src.endsWith(".webm");

  return (
    <AbsoluteFill style={{ backgroundColor: tokens.color.ink, overflow: "hidden" }}>
      <div
        style={{
          width: "100%",
          height: "100%",
          ...estiloKenBurns,
        }}
      >
        {isVideo ? (
          <OffthreadVideo
            src={src}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
            muted
          />
        ) : (
          <Img
            src={src}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        )}
      </div>

      <TexturaFilme />
    </AbsoluteFill>
  );
};
