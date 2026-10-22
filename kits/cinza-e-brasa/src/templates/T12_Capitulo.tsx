import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT12Capitulo } from "../schemas/templates";
import { tokens } from "../tokens";
import { animarEntrada } from "../utilitarios/animacoes";
import { AutoAjusteTexto } from "../utilitarios/AutoAjusteTexto";
import { TexturaFilme } from "../utilitarios/TexturaFilme";
import { useSafeArea } from "../utilitarios/SafeArea";

export const T12_Capitulo: React.FC<PropsT12Capitulo> = ({
  numero,
  titulo,
  subtitulo,
}) => {
  const area = useSafeArea();
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();

  const escala = width / 1920;
  const entrada = animarEntrada(frame, tokens.durationFrames.enter);
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
          transform: `translateY(${(1 - entrada) * 20}px)`,
        }}
      >
        {/* Numero ou Identificador do Capitulo */}
        <div
          style={{
            fontFamily: tokens.font.data.family,
            fontSize: `${18 * escala}px`,
            fontWeight: 700,
            letterSpacing: "0.2em",
            color: tokens.color.ember,
            textTransform: "uppercase",
            marginBottom: `${16 * escala}px`,
          }}
        >
          {numero}
        </div>

        {/* Titulo do Capitulo */}
        <AutoAjusteTexto
          texto={titulo}
          tamanhoPadrao={Math.round(58 * escala)}
          larguraMaximaPx={larguraMaxima}
          fontFamily={tokens.font.title.family}
          fontWeight={tokens.font.title.weight}
          letterSpacing={tokens.font.title.tracking}
          cor={tokens.color.bone}
          textTransform="uppercase"
          textAlign="center"
        />

        {/* Traco divisor fino */}
        <div
          style={{
            width: `${80 * escala}px`,
            height: `${2 * escala}px`,
            backgroundColor: tokens.color.ochre,
            margin: `${24 * escala}px 0`,
            opacity: 0.8,
          }}
        />

        {/* Subtitulo opcional */}
        {subtitulo && (
          <AutoAjusteTexto
            texto={subtitulo}
            tamanhoPadrao={Math.round(20 * escala)}
            larguraMaximaPx={larguraMaxima}
            fontFamily={tokens.font.body.family}
            fontWeight={tokens.font.body.weight}
            cor={tokens.color.ashLight}
            textAlign="center"
          />
        )}
      </div>

      <TexturaFilme />
    </AbsoluteFill>
  );
};
