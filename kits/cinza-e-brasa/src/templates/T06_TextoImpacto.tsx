import React from "react";
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT06TextoImpacto } from "../schemas/templates";
import { tokens } from "../tokens";
import { animarEntrada, easingEntrada } from "../utilitarios/animacoes";
import { AutoAjusteTexto } from "../utilitarios/AutoAjusteTexto";
import { TexturaFilme } from "../utilitarios/TexturaFilme";

export const T06_TextoImpacto: React.FC<PropsT06TextoImpacto> = ({
  texto,
  estilo = "limpo",
  src_fundo,
  fundo_escuro = true,
}) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();

  const escala = width / 1920;
  const entrada = animarEntrada(frame, tokens.durationFrames.enter);

  // Animacao de tracking (espacamento de letras recolhe de 0.25em para 0.08em)
  const trackingAtual = interpolate(frame, [0, tokens.durationFrames.enter], [0.25, 0.08], {
    easing: easingEntrada,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Animacao do risco vermelho para estilo "riscado"
  const progressoRisco = interpolate(frame, [10, 24], [0, 100], {
    easing: easingEntrada,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const larguraMaximaTexto = width * (1 - tokens.safeArea.x * 2);

  return (
    <AbsoluteFill style={{ backgroundColor: tokens.color.ink, overflow: "hidden" }}>
      {/* Fundo opcional escurecido */}
      {src_fundo && (
        <AbsoluteFill style={{ filter: "brightness(0.25) contrast(1.2)" }}>
          <Img
            src={src_fundo}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </AbsoluteFill>
      )}

      {fundo_escuro && (
        <AbsoluteFill
          style={{
            background: `radial-gradient(circle at center, rgba(28, 28, 33, 0.6) 0%, rgba(14, 14, 16, 0.95) 100%)`,
          }}
        />
      )}

      {/* Conteudo central */}
      <AbsoluteFill
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          padding: `${tokens.safeArea.y * 100}% ${tokens.safeArea.x * 100}%`,
        }}
      >
        <div
          style={{
            position: "relative",
            opacity: entrada,
            transform: `scale(${0.96 + entrada * 0.04})`,
            display: "inline-block",
          }}
        >
          <AutoAjusteTexto
            texto={texto}
            tamanhoPadrao={Math.round(76 * escala)}
            larguraMaximaPx={larguraMaximaTexto}
            fontFamily={tokens.font.title.family}
            fontWeight={tokens.font.title.weight}
            letterSpacing={`${trackingAtual}em`}
            textTransform="uppercase"
            cor={estilo === "carvao" ? tokens.color.ashLight : tokens.color.bone}
            textAlign="center"
          />

          {/* Risco animado estilo "strike" em vermelho Pompeia */}
          {estilo === "riscado" && (
            <div
              style={{
                position: "absolute",
                top: "50%",
                left: "-5%",
                width: `${progressoRisco * 1.1}%`,
                height: `${8 * escala}px`,
                backgroundColor: tokens.color.pompeiiRed,
                transform: "translateY(-50%) rotate(-2deg)",
                boxShadow: `0 0 12px ${tokens.color.pompeiiRed}`,
                borderRadius: "2px",
              }}
            />
          )}

          {/* Efeito de traco de carvao */}
          {estilo === "carvao" && (
            <div
              style={{
                position: "absolute",
                bottom: `-${12 * escala}px`,
                left: "15%",
                width: "70%",
                height: `${4 * escala}px`,
                backgroundColor: tokens.color.ember,
                opacity: 0.8,
                borderRadius: "2px",
              }}
            />
          )}
        </div>
      </AbsoluteFill>

      <TexturaFilme />
    </AbsoluteFill>
  );
};
