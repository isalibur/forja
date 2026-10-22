import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT13Abertura } from "../schemas/templates";
import { tokens } from "../tokens";
import { animarEntrada, easingEntrada } from "../utilitarios/animacoes";
import { AutoAjusteTexto } from "../utilitarios/AutoAjusteTexto";
import { TexturaFilme } from "../utilitarios/TexturaFilme";
import { useSafeArea } from "../utilitarios/SafeArea";

export const T13_Abertura: React.FC<PropsT13Abertura> = ({
  titulo,
  subtitulo,
}) => {
  const area = useSafeArea();
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();

  const escala = width / 1920;
  const entrada = animarEntrada(frame, tokens.durationFrames.enter + 10);

  // Brilho pulsante de brasa nas letras
  const brilhoBrasa = interpolate(frame, [0, 30], [20, 6], {
    easing: easingEntrada,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const larguraMaxima = width * (1 - area.x * 2);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: tokens.color.ink,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: `${area.y * 100}% ${area.x * 100}%`,
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          opacity: entrada,
          transform: `scale(${0.94 + entrada * 0.06})`,
        }}
      >
        {/* Titulo Monumental */}
        <div
          style={{
            filter: `drop-shadow(0 0 ${brilhoBrasa * escala}px rgba(255, 106, 43, 0.7))`,
          }}
        >
          <AutoAjusteTexto
            texto={titulo}
            tamanhoPadrao={Math.round(112 * escala)}
            larguraMaximaPx={larguraMaxima}
            fontFamily={tokens.font.title.family}
            fontWeight={tokens.font.title.weight}
            letterSpacing="0.14em"
            cor={tokens.color.bone}
            textTransform="uppercase"
            textAlign="center"
          />
        </div>

        {/* Linha Fina Ember */}
        <div
          style={{
            width: `${160 * escala}px`,
            height: `${3 * escala}px`,
            backgroundColor: tokens.color.ember,
            boxShadow: `0 0 16px ${tokens.color.ember}`,
            margin: `${28 * escala}px 0`,
            borderRadius: "2px",
          }}
        />

        {/* Subtitulo em font.data */}
        <AutoAjusteTexto
          texto={subtitulo}
          tamanhoPadrao={Math.round(22 * escala)}
          larguraMaximaPx={larguraMaxima}
          fontFamily={tokens.font.data.family}
          fontWeight={tokens.font.data.weight}
          letterSpacing="0.12em"
          cor={tokens.color.ashLight}
          textTransform="uppercase"
          textAlign="center"
        />
      </div>

      {/* Textura com particulas de cinza caindo */}
      <TexturaFilme mostrarPoeira={true} />
    </AbsoluteFill>
  );
};
