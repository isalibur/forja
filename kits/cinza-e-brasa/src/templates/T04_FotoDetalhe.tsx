import React from "react";
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT04FotoDetalhe } from "../schemas/templates";
import { tokens } from "../tokens";
import { animarEntrada, easingMovimento } from "../utilitarios/animacoes";
import { TexturaFilme } from "../utilitarios/TexturaFilme";

export const T04_FotoDetalhe: React.FC<PropsT04FotoDetalhe> = ({
  src,
  regiao = { x: 50, y: 50, w: 25, h: 25 },
  rotulo,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width } = useVideoConfig();

  const escalaResponsiva = width / 1920;

  // Zoom suave em direcao a regiao do detalhe
  const progressoZoom = interpolate(frame, [0, Math.min(48, durationInFrames)], [0, 1], {
    easing: easingMovimento,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const zoomFinal = 1.6;
  const escalaAtual = 1.0 + progressoZoom * (zoomFinal - 1.0);
  const centroX = regiao.x;
  const centroY = regiao.y;

  const animEntradaRotulo = animarEntrada(frame, tokens.durationFrames.enter, 16);

  return (
    <AbsoluteFill style={{ backgroundColor: tokens.color.ink, overflow: "hidden" }}>
      {/* Imagem com transform origin no ponto de interesse */}
      <div
        style={{
          width: "100%",
          height: "100%",
          transform: `scale(${escalaAtual})`,
          transformOrigin: `${centroX}% ${centroY}%`,
        }}
      >
        <Img
          src={src}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </div>

      {/* Caixa de destaque e chamada sobre a regiao */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            left: `${regiao.x}%`,
            top: `${regiao.y}%`,
            width: `${regiao.w}%`,
            height: `${regiao.h}%`,
            transform: "translate(-50%, -50%)",
            border: `2px solid ${tokens.color.ember}`,
            boxShadow: `0 0 16px rgba(255, 106, 43, 0.6)`,
            borderRadius: "4px",
            opacity: animEntradaRotulo,
          }}
        >
          {/* Cantoneiras refinadas estilo HUD */}
          <div style={{ position: "absolute", top: -4, left: -4, width: 8, height: 8, borderTop: `3px solid ${tokens.color.bone}`, borderLeft: `3px solid ${tokens.color.bone}` }} />
          <div style={{ position: "absolute", top: -4, right: -4, width: 8, height: 8, borderTop: `3px solid ${tokens.color.bone}`, borderRight: `3px solid ${tokens.color.bone}` }} />
          <div style={{ position: "absolute", bottom: -4, left: -4, width: 8, height: 8, borderBottom: `3px solid ${tokens.color.bone}`, borderLeft: `3px solid ${tokens.color.bone}` }} />
          <div style={{ position: "absolute", bottom: -4, right: -4, width: 8, height: 8, borderBottom: `3px solid ${tokens.color.bone}`, borderRight: `3px solid ${tokens.color.bone}` }} />

          {/* Rotulo explicativo */}
          {rotulo && (
            <div
              style={{
                position: "absolute",
                top: "100%",
                left: "50%",
                transform: "translateX(-50%)",
                marginTop: `${12 * escalaResponsiva}px`,
                background: "rgba(14, 14, 16, 0.9)",
                border: `1px solid ${tokens.color.ember}`,
                padding: `${6 * escalaResponsiva}px ${16 * escalaResponsiva}px`,
                borderRadius: "4px",
                fontFamily: tokens.font.data.family,
                fontSize: `${14 * escalaResponsiva}px`,
                fontWeight: 600,
                color: tokens.color.bone,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                whiteSpace: "nowrap",
                boxShadow: "0 4px 20px rgba(0,0,0,0.8)",
              }}
            >
              {rotulo}
            </div>
          )}
        </div>
      </AbsoluteFill>

      <TexturaFilme />
    </AbsoluteFill>
  );
};
