import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT07Citacao } from "../schemas/templates";
import { tokens } from "../tokens";
import { animarEntrada, easingEntrada } from "../utilitarios/animacoes";
import { AutoAjusteTexto } from "../utilitarios/AutoAjusteTexto";
import { TexturaFilme } from "../utilitarios/TexturaFilme";

export const T07_Citacao: React.FC<PropsT07Citacao> = ({
  texto,
  traducao,
  fonte,
  estilo = "papel",
}) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();

  const escala = width / 1920;
  const entrada = animarEntrada(frame, tokens.durationFrames.enter);

  // Animacao da faixa marca-texto em tom ocre (passando da esquerda para a direita)
  const progressoMarcaTexto = interpolate(frame, [12, 32], [0, 100], {
    easing: easingEntrada,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Animacao de entrada da traducao
  const entradaTraducao = interpolate(frame, [24, 38], [0, 1], {
    easing: easingEntrada,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const larguraMaximaDoc = width * 0.78;

  let corFundo = tokens.color.parchment;
  let corTextoPrincipal = tokens.color.ink;
  let borda = "none";

  if (estilo === "escuro") {
    corFundo = tokens.color.basalt;
    corTextoPrincipal = tokens.color.bone;
    borda = `1px solid rgba(110, 106, 102, 0.4)`;
  } else if (estilo === "pedra") {
    corFundo = "#2A2A30";
    corTextoPrincipal = tokens.color.bone;
    borda = `1px solid rgba(192, 138, 62, 0.3)`;
  }

  return (
    <AbsoluteFill
      style={{
        backgroundColor: tokens.color.ink,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: `${tokens.safeArea.y * 100}% ${tokens.safeArea.x * 100}%`,
      }}
    >
      {/* Documento / Papiro central */}
      <div
        style={{
          width: `${larguraMaximaDoc}px`,
          backgroundColor: corFundo,
          border: borda,
          borderRadius: "6px",
          padding: `${36 * escala}px ${48 * escala}px`,
          boxShadow: "0 24px 60px rgba(0, 0, 0, 0.75)",
          transform: `scale(${0.96 + entrada * 0.04}) rotate(-0.5deg)`,
          opacity: entrada,
          position: "relative",
          display: "flex",
          flexDirection: "column",
          gap: `${20 * escala}px`,
        }}
      >
        {/* Texto original em font.quote com marca-texto */}
        <div style={{ position: "relative", display: "inline-block" }}>
          {/* Faixa animada de realce em ocre */}
          <div
            style={{
              position: "absolute",
              top: "10%",
              left: "-1%",
              width: `${progressoMarcaTexto}%`,
              height: "85%",
              backgroundColor: tokens.color.ochre,
              opacity: 0.35,
              borderRadius: "3px",
              zIndex: 1,
            }}
          />

          <div style={{ position: "relative", zIndex: 2 }}>
            <AutoAjusteTexto
              texto={`"${texto}"`}
              tamanhoPadrao={Math.round(40 * escala)}
              larguraMaximaPx={larguraMaximaDoc - 96 * escala}
              fontFamily={tokens.font.quote.family}
              fontWeight={tokens.font.quote.weight}
              fontStyle="italic"
              cor={corTextoPrincipal}
              textAlign="left"
            />
          </div>
        </div>

        {/* Traducao opcional em font.body */}
        {traducao && (
          <div
            style={{
              opacity: entradaTraducao,
              transform: `translateY(${(1 - entradaTraducao) * 10}px)`,
              borderTop: `1px solid rgba(110, 106, 102, 0.25)`,
              paddingTop: `${14 * escala}px`,
            }}
          >
            <AutoAjusteTexto
              texto={traducao}
              tamanhoPadrao={Math.round(22 * escala)}
              larguraMaximaPx={larguraMaximaDoc - 96 * escala}
              fontFamily={tokens.font.body.family}
              fontWeight={tokens.font.body.weight}
              cor={estilo === "papel" ? "#333333" : tokens.color.ashLight}
              textAlign="left"
            />
          </div>
        )}

        {/* Rodape de referencia / fonte */}
        <div
          style={{
            fontFamily: tokens.font.data.family,
            fontSize: `${14 * escala}px`,
            color: estilo === "papel" ? tokens.color.ash : tokens.color.ochre,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            fontWeight: 600,
            alignSelf: "flex-end",
            marginTop: `${8 * escala}px`,
          }}
        >
          — {fonte}
        </div>
      </div>

      <TexturaFilme />
    </AbsoluteFill>
  );
};
