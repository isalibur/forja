import React from "react";
import { AbsoluteFill, Img, interpolate, OffthreadVideo, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT02FotoProfundidade } from "../schemas/templates";
import { tokens } from "../tokens";
import { TexturaFilme } from "../utilitarios/TexturaFilme";

export const T02_FotoProfundidade: React.FC<PropsT02FotoProfundidade> = ({
  src,
  movimento = "dolly",
  intensidade = 0.4,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const isVideo = src.endsWith(".mp4") || src.endsWith(".webm");
  const progresso = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Em modo video (render oficial DepthFlow), toca o video diretamente
  if (isVideo) {
    return (
      <AbsoluteFill style={{ backgroundColor: tokens.color.ink }}>
        <OffthreadVideo
          src={src}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
          muted
        />
        <TexturaFilme />
      </AbsoluteFill>
    );
  }

  // Em modo imagem (fallback ou previa), simula camera 2.5D com perspectiva
  let transform = "";
  const amp = intensidade * 0.15;

  if (movimento === "dolly") {
    const scale = 1.05 + progresso * amp;
    const transY = (progresso - 0.5) * amp * 120;
    transform = `scale(${scale}) translateY(${transY}px)`;
  } else if (movimento === "orbita") {
    const scale = 1.08;
    const transX = Math.sin(progresso * Math.PI) * amp * 150;
    const rot = Math.sin(progresso * Math.PI) * (amp * 4);
    transform = `scale(${scale}) translateX(${transX}px) rotate(${rot}deg)`;
  } else {
    // zoom
    const scale = 1.0 + progresso * amp * 1.5;
    transform = `scale(${scale})`;
  }

  return (
    <AbsoluteFill
      style={{
        backgroundColor: tokens.color.ink,
        overflow: "hidden",
        perspective: 1000,
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          transform,
          transformOrigin: "center center",
          transition: "transform 0.1s linear",
        }}
      >
        <Img
          src={src}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </div>

      <TexturaFilme />
    </AbsoluteFill>
  );
};
