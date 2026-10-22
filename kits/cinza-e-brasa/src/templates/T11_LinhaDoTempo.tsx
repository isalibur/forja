import React from "react";
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT11LinhaDoTempo } from "../schemas/templates";
import { tokens } from "../tokens";
import { animarEntrada, easingMovimento } from "../utilitarios/animacoes";
import { TexturaFilme } from "../utilitarios/TexturaFilme";
import { useSafeArea, useFormatoVertical } from "../utilitarios/SafeArea";

export const T11_LinhaDoTempo: React.FC<PropsT11LinhaDoTempo> = ({
  titulo = "CRONOLOGIA DOS EVENTOS",
  eventos,
  indice_ativo = 0,
}) => {
  const area = useSafeArea();
  const vertical = useFormatoVertical();
  const frame = useCurrentFrame();
  const { durationInFrames, width } = useVideoConfig();

  const escala = width / 1920;
  const entrada = animarEntrada(frame, tokens.durationFrames.enter);

  // Travelling lateral suave acompanhando a evolucao dos eventos
  const translacaoX = interpolate(
    frame,
    [0, durationInFrames],
    [40 * escala, -((eventos.length - 1) * 320 * escala - 40 * escala)],
    {
      easing: easingMovimento,
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  if (vertical) {
    return (
      <AbsoluteFill
        style={{
          backgroundColor: tokens.color.ink,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          paddingTop: `${area.y * 100}%`,
          paddingBottom: `${area.title * 100}%`,
          paddingLeft: `${area.x * 100}%`,
          paddingRight: `${area.x * 100}%`,
        }}
      >
        <div
          style={{
            opacity: entrada,
            fontFamily: tokens.font.title.family,
            fontSize: `${34 * escala}px`,
            fontWeight: 600,
            color: tokens.color.bone,
            letterSpacing: tokens.font.title.tracking,
            textTransform: "uppercase",
            marginBottom: `${28 * escala}px`,
          }}
        >
          {titulo}
        </div>

        <div style={{ position: "relative", display: "flex", flexDirection: "column", gap: `${22 * escala}px` }}>
          <div
            style={{
              position: "absolute",
              left: `${8 * escala}px`,
              top: 0,
              bottom: 0,
              width: `${2 * escala}px`,
              backgroundColor: "rgba(110, 106, 102, 0.4)",
            }}
          />
          {eventos.map((ev, idx) => {
            const isAtivo = idx === indice_ativo;
            return (
              <div
                key={idx}
                style={{
                  display: "flex",
                  flexDirection: "row",
                  alignItems: "flex-start",
                  gap: `${20 * escala}px`,
                  opacity: isAtivo ? 1 : 0.55,
                }}
              >
                <div
                  style={{
                    width: `${18 * escala}px`,
                    height: `${18 * escala}px`,
                    borderRadius: "50%",
                    backgroundColor: isAtivo ? tokens.color.ember : tokens.color.ash,
                    border: `${3 * escala}px solid ${tokens.color.ink}`,
                    boxShadow: isAtivo ? `0 0 12px ${tokens.color.ember}` : undefined,
                    marginTop: `${4 * escala}px`,
                    flexShrink: 0,
                    zIndex: 2,
                  }}
                />
                <div style={{ display: "flex", flexDirection: "column", gap: `${6 * escala}px` }}>
                  {ev.src_ativo && (
                    <div
                      style={{
                        width: "100%",
                        maxWidth: `${520 * escala}px`,
                        aspectRatio: "16 / 9",
                        backgroundColor: tokens.color.basalt,
                        borderRadius: "4px",
                        overflow: "hidden",
                        border: `1px solid ${isAtivo ? tokens.color.ember : "rgba(110, 106, 102, 0.4)"}`,
                        boxShadow: "0 10px 24px rgba(0,0,0,0.7)",
                      }}
                    >
                      <Img
                        src={ev.src_ativo}
                        style={{ width: "100%", height: "100%", objectFit: "cover" }}
                      />
                    </div>
                  )}
                  <div
                    style={{
                      fontFamily: tokens.font.data.family,
                      fontSize: `${30 * escala}px`,
                      fontWeight: 700,
                      color: isAtivo ? tokens.color.ochre : tokens.color.bone,
                      letterSpacing: "0.04em",
                    }}
                  >
                    {ev.data}
                  </div>
                  <div
                    style={{
                      fontFamily: tokens.font.body.family,
                      fontSize: `${24 * escala}px`,
                      color: tokens.color.ashLight,
                      textAlign: "left",
                      lineHeight: 1.3,
                    }}
                  >
                    {ev.rotulo}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <TexturaFilme />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill
      style={{
        backgroundColor: tokens.color.ink,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
      }}
    >
      {/* Titulo fixo superior */}
      <div
        style={{
          position: "absolute",
          top: `${area.y * 100}%`,
          left: `${area.x * 100}%`,
          opacity: entrada,
          fontFamily: tokens.font.title.family,
          fontSize: `${22 * escala}px`,
          fontWeight: 600,
          color: tokens.color.bone,
          letterSpacing: tokens.font.title.tracking,
          textTransform: "uppercase",
        }}
      >
        {titulo}
      </div>

      {/* Trilho horizontal da Linha do Tempo */}
      <div
        style={{
          position: "relative",
          width: "100%",
          height: `${380 * escala}px`,
          display: "flex",
          alignItems: "center",
        }}
      >
        {/* Linha horizontal base */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: 0,
            right: 0,
            height: `${2 * escala}px`,
            backgroundColor: "rgba(110, 106, 102, 0.4)",
          }}
        />

        {/* Marcadores e Eventos em travelling */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: `${260 * escala}px`,
            transform: `translateX(${translacaoX}px)`,
            paddingLeft: "30%",
          }}
        >
          {eventos.map((ev, idx) => {
            const isAtivo = idx === indice_ativo;
            return (
              <div
                key={idx}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  position: "relative",
                  width: `${240 * escala}px`,
                }}
              >
                {/* Imagem / Card suspenso acima da linha */}
                {ev.src_ativo && (
                  <div
                    style={{
                      width: `${180 * escala}px`,
                      height: `${110 * escala}px`,
                      backgroundColor: tokens.color.basalt,
                      borderRadius: "4px",
                      overflow: "hidden",
                      border: `1px solid ${isAtivo ? tokens.color.ember : "rgba(110, 106, 102, 0.4)"}`,
                      marginBottom: `${24 * escala}px`,
                      boxShadow: "0 10px 24px rgba(0,0,0,0.7)",
                    }}
                  >
                    <Img
                      src={ev.src_ativo}
                      style={{ width: "100%", height: "100%", objectFit: "cover" }}
                    />
                  </div>
                )}

                {/* Marcador do Ponto na Linha */}
                <div
                  style={{
                    width: `${16 * escala}px`,
                    height: `${16 * escala}px`,
                    borderRadius: "50%",
                    backgroundColor: isAtivo ? tokens.color.ember : tokens.color.ash,
                    border: `3px solid ${tokens.color.ink}`,
                    boxShadow: isAtivo ? `0 0 12px ${tokens.color.ember}` : undefined,
                    zIndex: 2,
                  }}
                />

                {/* Data */}
                <div
                  style={{
                    marginTop: `${14 * escala}px`,
                    fontFamily: tokens.font.data.family,
                    fontSize: `${18 * escala}px`,
                    fontWeight: 700,
                    color: isAtivo ? tokens.color.ochre : tokens.color.bone,
                    letterSpacing: "0.04em",
                  }}
                >
                  {ev.data}
                </div>

                {/* Rotulo do evento */}
                <div
                  style={{
                    marginTop: `${6 * escala}px`,
                    fontFamily: tokens.font.body.family,
                    fontSize: `${14 * escala}px`,
                    color: tokens.color.ashLight,
                    textAlign: "center",
                    lineHeight: 1.3,
                  }}
                >
                  {ev.rotulo}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <TexturaFilme />
    </AbsoluteFill>
  );
};
