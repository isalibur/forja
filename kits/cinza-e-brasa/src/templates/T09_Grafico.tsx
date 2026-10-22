import React, { useMemo } from "react";
import { scaleLinear } from "d3";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT09Grafico } from "../schemas/templates";
import { tokens } from "../tokens";
import { animarEntrada, easingEntrada } from "../utilitarios/animacoes";
import { TexturaFilme } from "../utilitarios/TexturaFilme";
import { useSafeArea } from "../utilitarios/SafeArea";

export const T09_Grafico: React.FC<PropsT09Grafico> = ({
  tipo = "escala",
  titulo,
  dados,
}) => {
  const area = useSafeArea();
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();

  const escala = width / 1920;
  const entradaGeral = animarEntrada(frame, tokens.durationFrames.enter);

  // Calcula o valor maximo para a escala D3
  const valorMaximo = useMemo(() => {
    let max = 0;
    for (const d of dados) {
      if (d.valor && d.valor > max) max = d.valor;
      if (d.faixa && d.faixa[1] > max) max = d.faixa[1];
    }
    return Math.max(max * 1.15, 10);
  }, [dados]);

  // Escala D3 para a largura util das barras (ex: 750px)
  const larguraGraficoPx = 800 * escala;
  const escalaD3 = useMemo(() => {
    return scaleLinear().domain([0, valorMaximo]).range([0, larguraGraficoPx]);
  }, [valorMaximo, larguraGraficoPx]);

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
          width: `${larguraGraficoPx + 360 * escala}px`,
          opacity: entradaGeral,
          transform: `scale(${0.96 + entradaGeral * 0.04})`,
          background: "rgba(28, 28, 33, 0.7)",
          backdropFilter: "blur(12px)",
          border: `1px solid rgba(110, 106, 102, 0.3)`,
          padding: `${32 * escala}px ${40 * escala}px`,
          borderRadius: "8px",
          boxShadow: "0 20px 50px rgba(0, 0, 0, 0.8)",
        }}
      >
        {/* Titulo do Grafico */}
        {titulo && (
          <div
            style={{
              fontFamily: tokens.font.title.family,
              fontSize: `${24 * escala}px`,
              fontWeight: 600,
              color: tokens.color.bone,
              letterSpacing: tokens.font.title.tracking,
              textTransform: "uppercase",
              borderBottom: `1px solid rgba(255, 106, 43, 0.3)`,
              paddingBottom: `${12 * escala}px`,
              marginBottom: `${28 * escala}px`,
            }}
          >
            {titulo}
          </div>
        )}

        {/* Linhas de dados / barras */}
        <div style={{ display: "flex", flexDirection: "column", gap: `${24 * escala}px` }}>
          {dados.map((item, index) => {
            const delay = index * tokens.durationFrames.stagger;
            const progressoBarra = interpolate(
              frame - delay,
              [0, tokens.durationFrames.enter + 6],
              [0, 1],
              {
                easing: easingEntrada,
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }
            );

            const isFaixa = Boolean(item.faixa);
            const valInicio = isFaixa ? item.faixa![0] : 0;
            const valFim = isFaixa ? item.faixa![1] : item.valor || 0;

            const posInicioPx = escalaD3(valInicio);
            const posFimPx = escalaD3(valFim);
            const larguraBarraPx = (posFimPx - posInicioPx) * progressoBarra;

            const isErupcao = item.rotulo.toLowerCase().includes("coluna") || item.rotulo.toLowerCase().includes("erup");

            return (
              <div key={index} style={{ display: "flex", flexDirection: "column", gap: `${6 * escala}px` }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontFamily: tokens.font.data.family,
                    fontSize: `${16 * escala}px`,
                    color: isErupcao ? tokens.color.ember : tokens.color.bone,
                    fontWeight: 600,
                  }}
                >
                  <span>{item.rotulo}</span>
                  <span style={{ color: isErupcao ? tokens.color.ember : tokens.color.ochre }}>
                    {item.prefixo ? `${item.prefixo} ` : ""}
                    {isFaixa ? `${item.faixa![0]}–${item.faixa![1]}` : item.valor} {item.unidade || ""}
                  </span>
                </div>

                {/* Trilha da Barra */}
                <div
                  style={{
                    width: `${larguraGraficoPx}px`,
                    height: `${14 * escala}px`,
                    backgroundColor: tokens.color.basalt,
                    borderRadius: "4px",
                    position: "relative",
                    overflow: "hidden",
                  }}
                >
                  {/* Barra Animada com gradiente */}
                  <div
                    style={{
                      position: "absolute",
                      left: isFaixa ? `${posInicioPx}px` : "0px",
                      width: `${larguraBarraPx}px`,
                      height: "100%",
                      borderRadius: "3px",
                      background: isErupcao
                        ? `linear-gradient(90deg, ${tokens.color.pompeiiRed}, ${tokens.color.ember})`
                        : `linear-gradient(90deg, ${tokens.color.ash}, ${tokens.color.ochre})`,
                      boxShadow: isErupcao ? `0 0 12px ${tokens.color.ember}` : undefined,
                    }}
                  />
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
