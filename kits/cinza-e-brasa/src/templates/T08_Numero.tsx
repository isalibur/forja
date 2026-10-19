import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT08Numero } from "../schemas/templates";
import { tokens } from "../tokens";
import { animarEntrada, easingEntrada } from "../utilitarios/animacoes";
import { AutoAjusteTexto } from "../utilitarios/AutoAjusteTexto";
import { TexturaFilme } from "../utilitarios/TexturaFilme";

export const T08_Numero: React.FC<PropsT08Numero> = ({
  valor,
  prefixo = "",
  unidade = "",
  legenda,
  casas_decimais = 0,
}) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();

  const escala = width / 1920;
  const entrada = animarEntrada(frame, tokens.durationFrames.enter);

  // Contador animado de 0 ate o valor
  const duracaoContagem = 26;
  const valorAtual = interpolate(frame, [0, duracaoContagem], [0, valor], {
    easing: easingEntrada,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const textoValorFormatado = valorAtual.toLocaleString("pt-BR", {
    minimumFractionDigits: casas_decimais,
    maximumFractionDigits: casas_decimais,
  });

  const larguraMaxima = width * (1 - tokens.safeArea.x * 2);

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
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          opacity: entrada,
          transform: `scale(${0.95 + entrada * 0.05})`,
        }}
      >
        {/* Bloco numerico de destaque */}
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: `${12 * escala}px`,
            fontFamily: tokens.font.data.family,
          }}
        >
          {prefixo && (
            <span
              style={{
                fontSize: `${54 * escala}px`,
                color: tokens.color.ember,
                fontWeight: 600,
              }}
            >
              {prefixo}
            </span>
          )}

          <span
            style={{
              fontSize: `${110 * escala}px`,
              fontWeight: 700,
              color: tokens.color.bone,
              letterSpacing: "-0.02em",
              textShadow: "0 0 32px rgba(255, 106, 43, 0.4)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {textoValorFormatado}
          </span>

          {unidade && (
            <span
              style={{
                fontSize: `${46 * escala}px`,
                color: tokens.color.ochre,
                fontWeight: 500,
                marginLeft: `${4 * escala}px`,
              }}
            >
              {unidade}
            </span>
          )}
        </div>

        {/* Fina linha divisoria Ember */}
        <div
          style={{
            width: `${140 * escala}px`,
            height: `${3 * escala}px`,
            backgroundColor: tokens.color.ember,
            margin: `${20 * escala}px 0`,
            borderRadius: "2px",
            boxShadow: `0 0 10px ${tokens.color.ember}`,
          }}
        />

        {/* Legenda explicativa com auto-ajuste */}
        <AutoAjusteTexto
          texto={legenda}
          tamanhoPadrao={Math.round(26 * escala)}
          larguraMaximaPx={larguraMaxima}
          fontFamily={tokens.font.body.family}
          fontWeight={tokens.font.body.weight}
          cor={tokens.color.ashLight}
          textAlign="center"
        />
      </div>

      <TexturaFilme />
    </AbsoluteFill>
  );
};
