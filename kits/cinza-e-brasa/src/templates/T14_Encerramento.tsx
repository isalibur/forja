import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { PropsT14Encerramento } from "../schemas/templates";
import { tokens } from "../tokens";
import { animarEntrada } from "../utilitarios/animacoes";
import { useMarca } from "../utilitarios/marca";
import { TexturaFilme } from "../utilitarios/TexturaFilme";
import { useSafeArea } from "../utilitarios/SafeArea";

export const T14_Encerramento: React.FC<PropsT14Encerramento> = ({
  titulo = "DOCFORJA",
  creditos = [],
  mostrar_espaco_youtube = true,
}) => {
  const area = useSafeArea();
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const marca = useMarca();

  const escala = width / 1920;
  const entrada = animarEntrada(frame, tokens.durationFrames.enter);

  const tituloExibido = marca?.nome || titulo;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: tokens.color.ink,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: `${area.y * 100}% ${area.x * 100}%`,
        boxSizing: "border-box",
      }}
    >
      {/* Topo: Titulo / Marca e Chamada Final */}
      <div
        style={{
          opacity: entrada,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
        }}
      >
        <div>
          <div
            style={{
              fontFamily: tokens.font.title.family,
              fontSize: `${36 * escala}px`,
              fontWeight: 700,
              color: tokens.color.bone,
              letterSpacing: tokens.font.title.tracking,
              textTransform: "uppercase",
            }}
          >
            {tituloExibido}
          </div>
          {marca?.cartao_final?.chamada && (
            <div
              style={{
                fontFamily: tokens.font.body.family,
                fontSize: `${18 * escala}px`,
                color: tokens.color.ashLight,
                marginTop: `${6 * escala}px`,
              }}
            >
              {marca.cartao_final.chamada}
            </div>
          )}
        </div>

        {/* Informacoes de contato da marca se existirem */}
        {marca?.contato && (
          <div
            style={{
              fontFamily: tokens.font.data.family,
              fontSize: `${14 * escala}px`,
              color: tokens.color.ochre,
              textAlign: "right",
              lineHeight: 1.5,
            }}
          >
            {marca.contato.arroba && <div>{marca.contato.arroba}</div>}
            {marca.contato.site && <div>{marca.contato.site}</div>}
          </div>
        )}
      </div>

      {/* Centro: Espacos seguros para elementos de tela final do YouTube */}
      {mostrar_espaco_youtube && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-around",
            alignItems: "center",
            width: "100%",
            margin: `${24 * escala}px 0`,
          }}
        >
          {/* Card de video recomendado */}
          <div
            style={{
              width: `${460 * escala}px`,
              height: `${260 * escala}px`,
              borderRadius: "8px",
              border: `2px dashed rgba(110, 106, 102, 0.4)`,
              backgroundColor: "rgba(28, 28, 33, 0.5)",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              fontFamily: tokens.font.data.family,
              fontSize: `${14 * escala}px`,
              color: tokens.color.ash,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            [ VÍDEO RECOMENDADO ]
          </div>

          {/* Botao de inscricao */}
          <div
            style={{
              width: `${140 * escala}px`,
              height: `${140 * escala}px`,
              borderRadius: "50%",
              border: `2px dashed rgba(255, 106, 43, 0.4)`,
              backgroundColor: "rgba(28, 28, 33, 0.5)",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              fontFamily: tokens.font.data.family,
              fontSize: `${13 * escala}px`,
              color: tokens.color.ember,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              textAlign: "center",
            }}
          >
            [ INSCREVA-SE ]
          </div>
        </div>
      )}

      {/* Rodape: Creditos e Licenciamento */}
      <div
        style={{
          opacity: entrada,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          borderTop: `1px solid rgba(110, 106, 102, 0.3)`,
          paddingTop: `${16 * escala}px`,
        }}
      >
        <div
          style={{
            fontFamily: tokens.font.data.family,
            fontSize: `${12 * escala}px`,
            color: tokens.color.ash,
            letterSpacing: "0.04em",
          }}
        >
          {creditos.length > 0 ? creditos.join(" · ") : "PRODUZIDO COM DOCFORJA · LICENÇAS LIVRES CC/OFL"}
        </div>

        <div
          style={{
            fontFamily: tokens.font.data.family,
            fontSize: `${12 * escala}px`,
            color: tokens.color.ember,
            fontWeight: 600,
          }}
        >
          CINZA E BRASA
        </div>
      </div>

      <TexturaFilme />
    </AbsoluteFill>
  );
};
