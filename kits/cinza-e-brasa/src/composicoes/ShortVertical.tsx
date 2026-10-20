import React from "react";
import { Video } from "@remotion/media";
import type { Caption } from "@remotion/captions";
import {
  AbsoluteFill,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { tokens } from "../tokens";

export type TemplateShort =
  | "V01"
  | "V02"
  | "V03"
  | "V04"
  | "V05"
  | "V06"
  | "V07"
  | "V08"
  | "V09"
  | "V10";

export type PropsShortVertical = {
  variante: TemplateShort;
  titulo: string;
  subtitulo: string;
  texto: string;
  imagem: string;
  imagem_antes: string;
  imagem_depois: string;
  clipe: string;
  itens: string[];
  opcao_a: string;
  opcao_b: string;
  preco: string;
  condicao: string;
  aviso_publicidade: string;
  prova: string;
  fonte_prova: string;
  cta: string;
  marca: string;
  foco_x: number;
  foco_y: number;
  usar_fundo_desfocado: boolean;
  legendas: Caption[];
};

const resolverMidia = (src: string): string => {
  if (!src || /^(?:https?:|data:|blob:|\/)/i.test(src)) return src;
  return staticFile(src);
};

const Texto: React.FC<{
  children: React.ReactNode;
  grande?: boolean;
  cor?: string;
}> = ({ children, grande = false, cor = tokens.color.bone }) => (
  <div
    style={{
      width: "100%",
      color: cor,
      textAlign: "center",
      fontFamily: grande ? tokens.font.title.family : tokens.font.body.family,
      fontWeight: grande ? 700 : 600,
      fontSize: grande ? 94 : 52,
      lineHeight: 1.08,
      overflowWrap: "anywhere",
      textShadow: "0 4px 24px rgba(0,0,0,.8)",
    }}
  >
    {children}
  </div>
);

const LegendaPalavra: React.FC<{ captions: Caption[] }> = ({ captions }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tempoMs = (frame / fps) * 1000;
  const ativa = captions.find(
    (caption) => tempoMs >= caption.startMs && tempoMs < caption.endMs,
  );
  if (!ativa) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: "8%",
        right: "14%",
        bottom: "28%",
        minHeight: "5%",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "16px 20px",
        borderRadius: 14,
        backgroundColor: "rgba(14, 14, 16, .86)",
        color: tokens.color.bone,
        fontFamily: tokens.font.body.family,
        fontWeight: 700,
        fontSize: 54,
        lineHeight: 1.05,
        textAlign: "center",
        textShadow: `0 0 18px ${tokens.color.ember}`,
      }}
    >
      {ativa.text.trim()}
    </div>
  );
};

const Fundo: React.FC<{
  src: string;
  focoX: number;
  focoY: number;
  usarFundoDesfocado: boolean;
}> = ({ src, focoX, focoY, usarFundoDesfocado }) => {
  const fonte = resolverMidia(src);
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progresso = interpolate(frame, [0, fps * 2.5], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const escala = interpolate(progresso, [0, 1], [1, 1.08]);
  const deslocamento = (focoX < 0.5 ? 1 : -1) * progresso * 0.025;
  const posicaoX = Math.min(0.98, Math.max(0.02, focoX + deslocamento));

  return (
    <>
      {src ? (
        <AbsoluteFill>
          {usarFundoDesfocado ? (
            <>
              <Img
                src={fonte}
                style={{
                  position: "absolute",
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  filter: "blur(28px) brightness(.48)",
                  transform: `scale(${1.12 * escala})`,
                }}
              />
              <Img
                src={fonte}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "contain",
                  transform: `scale(${escala})`,
                }}
              />
            </>
          ) : (
            <Img
              src={fonte}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: `${posicaoX * 100}% ${focoY * 100}%`,
                transform: `scale(${escala})`,
              }}
            />
          )}
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(14,14,16,.28) 0%, rgba(14,14,16,.56) 46%, rgba(14,14,16,.94) 100%)",
        }}
      />
    </>
  );
};

export const ShortVertical: React.FC<PropsShortVertical> = (props) => {
  const frame = useCurrentFrame();
  const entrada = interpolate(frame, [0, 14], [0.92, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const safeStack: React.CSSProperties = {
    position: "absolute",
    top: "18%",
    left: "8%",
    right: "14%",
    bottom: "34%",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    gap: 30,
    transform: `scale(${entrada})`,
  };

  return (
    <AbsoluteFill style={{ backgroundColor: tokens.color.ink, overflow: "hidden" }}>
      <Fundo
        src={props.imagem}
        focoX={props.foco_x}
        focoY={props.foco_y}
        usarFundoDesfocado={props.usar_fundo_desfocado}
      />
      {props.variante === "V05" && props.imagem_antes ? (
        <div style={{ position: "absolute", inset: "18% 14% 38% 8%", display: "flex", gap: 8 }}>
          {[props.imagem_antes, props.imagem_depois].map((src, index) => (
            <div key={`${index}-${src}`} style={{ position: "relative", flex: 1, overflow: "hidden" }}>
              <Img
                src={resolverMidia(src)}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  objectPosition: `${props.foco_x * 100}% ${props.foco_y * 100}%`,
                }}
              />
              <span style={{ position: "absolute", left: 12, top: 12, color: "white", fontSize: 34 }}>
                {index === 0 ? "ANTES" : "DEPOIS"}
              </span>
            </div>
          ))}
        </div>
      ) : null}
      {props.variante === "V09" && props.clipe ? (
        <AbsoluteFill style={{ inset: "15% 12% 36% 6%", overflow: "hidden", borderRadius: 20 }}>
          <Video
            src={resolverMidia(props.clipe)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: `${props.foco_x * 100}% ${props.foco_y * 100}%`,
            }}
          />
        </AbsoluteFill>
      ) : null}

      <div style={safeStack}>
        {props.variante === "V01" ? (
          <Texto grande>{props.titulo || props.texto}</Texto>
        ) : null}
        {props.variante === "V02" ? <Texto>{props.subtitulo || props.texto}</Texto> : null}
        {props.variante === "V03" ? (
          <>
            {props.itens.slice(0, 3).map((item, index) => (
              <div key={`${index}-${item}`} style={{ display: "flex", alignItems: "center", gap: 20 }}>
                <span style={{ color: tokens.color.ember, fontSize: 92, fontWeight: 800 }}>{index + 1}</span>
                <Texto>{item}</Texto>
              </div>
            ))}
          </>
        ) : null}
        {props.variante === "V04" ? (
          <>
            <Texto grande>{props.titulo}</Texto>
            <Texto>{props.subtitulo}</Texto>
            {props.preco ? <Texto cor={tokens.color.ochre}>{props.preco}</Texto> : null}
            {props.condicao ? <Texto>{props.condicao}</Texto> : null}
            {props.aviso_publicidade ? <Texto>{props.aviso_publicidade}</Texto> : null}
          </>
        ) : null}
        {props.variante === "V05" ? <Texto grande>{props.titulo || "ANTES → DEPOIS"}</Texto> : null}
        {props.variante === "V06" ? (
          <>
            <Texto grande>{props.titulo || props.texto}</Texto>
            <Texto>A · {props.opcao_a}</Texto>
            <Texto>B · {props.opcao_b}</Texto>
          </>
        ) : null}
        {props.variante === "V07" ? (
          <>
            <Texto grande>{props.titulo || "CONTINUE A HISTÓRIA"}</Texto>
            <Texto cor={tokens.color.ember}>{props.cta}</Texto>
          </>
        ) : null}
        {props.variante === "V08" ? <Texto grande>{props.marca || props.titulo}</Texto> : null}
        {props.variante === "V09" ? <Texto>{props.subtitulo || props.texto}</Texto> : null}
        {props.variante === "V10" ? (
          props.prova && props.fonte_prova ? (
            <>
              <Texto grande>{props.prova}</Texto>
              <Texto>Fonte: {props.fonte_prova}</Texto>
            </>
          ) : (
            <Texto>V10 aguarda prova real fornecida pelo usuário.</Texto>
          )
        ) : null}
      </div>
      <LegendaPalavra captions={props.legendas} />
      <div
        style={{
          position: "absolute",
          top: "4%",
          left: "8%",
          right: "14%",
          height: 4,
          backgroundColor: tokens.color.ember,
          opacity: 0.8,
        }}
      />
    </AbsoluteFill>
  );
};

export const defaultPropsShort: PropsShortVertical = {
  variante: "V01",
  titulo: "O CÉREBRO QUE VIROU VIDRO",
  subtitulo: "Uma descoberta inesperada",
  texto: "",
  imagem: "",
  imagem_antes: "",
  imagem_depois: "",
  clipe: "",
  itens: ["Primeiro ponto", "Segundo ponto", "Terceiro ponto"],
  opcao_a: "Opção A",
  opcao_b: "Opção B",
  preco: "",
  condicao: "",
  aviso_publicidade: "",
  prova: "",
  fonte_prova: "",
  cta: "Veja o vídeo completo",
  marca: "DOCFORJA",
  foco_x: 0.5,
  foco_y: 0.5,
  usar_fundo_desfocado: false,
  legendas: [],
};

export const ShortSafeAreaGuide: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#333", color: "white", fontFamily: "Arial" }}>
    <AbsoluteFill
      style={{
        inset: "0 0 85% 0",
        backgroundColor: "rgba(210,40,40,.55)",
        justifyContent: "center",
        alignItems: "center",
        fontSize: 38,
      }}
    >
      ÁREA SUPERIOR · 15%
    </AbsoluteFill>
    <AbsoluteFill
      style={{
        inset: "75% 0 0 0",
        backgroundColor: "rgba(210,40,40,.55)",
        justifyContent: "center",
        alignItems: "center",
        fontSize: 38,
      }}
    >
      ÁREA INFERIOR · 25%
    </AbsoluteFill>
    <AbsoluteFill
      style={{
        inset: "15% 0 25% 88%",
        backgroundColor: "rgba(210,40,40,.65)",
        justifyContent: "center",
        alignItems: "center",
        fontSize: 30,
        writingMode: "vertical-rl",
      }}
    >
      ÁREA DIREITA · 12%
    </AbsoluteFill>
    <div
      style={{
        position: "absolute",
        left: "5%",
        top: "15%",
        width: "83%",
        height: "60%",
        border: "4px dashed #87e5ac",
        boxSizing: "border-box",
      }}
    />
    <div style={{ position: "absolute", left: "10%", top: "35%", fontSize: 42 }}>
      ZONA SEGURA PARA CONTEÚDO
    </div>
  </AbsoluteFill>
);
