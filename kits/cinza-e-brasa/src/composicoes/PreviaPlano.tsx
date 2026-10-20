import React from "react";
import { Audio } from "@remotion/media";
import { AbsoluteFill, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

export type ItemPrevia = {
  id: string;
  template: string;
  inicio_frame: number;
  fim_frame: number;
  bloco: string;
  descricao: string;
  texto: string;
  situacao: string;
};

export type PropsPreviaPlano = {
  titulo: string;
  shots: ItemPrevia[];
  cartoes: ItemPrevia[];
  duracao_frames: number;
  tem_trilha_provisoria?: boolean;
  idioma?: string;
  i18n?: Record<string, string>;
};

export const PreviaPlano: React.FC<PropsPreviaPlano> = ({
  titulo,
  shots,
  cartoes,
  tem_trilha_provisoria,
  idioma,
  i18n,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const shot = shots.find((item) => frame >= item.inicio_frame && frame < item.fim_frame);
  const cartao = cartoes.find((item) => frame >= item.inicio_frame && frame < item.fim_frame);
  const atual = cartao ?? shot;
  const andamento = shot
    ? interpolate(frame, [shot.inicio_frame, shot.fim_frame], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 0;
  const escala = width / 960;

  // Ducking: volume da cama provisória atenuado sob narração (-18 dB, 0.12),
  // com respiro sutil em cartões e pausas (0.22).
  const volumeTrilha = (f: number) => {
    const s = shots.find((item) => f >= item.inicio_frame && f < item.fim_frame);
    if (!s || s.template === "T00" || s.template === "T14" || !s.texto) {
      return 0.22;
    }
    return 0.12;
  };

  return (
    <AbsoluteFill style={{ backgroundColor: "#0e0e10", color: "#f0e8d8", fontFamily: "Arial, sans-serif" }}>
      <Audio src={staticFile("narracao.wav")} />
      {tem_trilha_provisoria && (
        <Audio
          src={staticFile("trilha_provisoria.wav")}
          loop
          volume={volumeTrilha}
        />
      )}
      <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 65% 45%, #4c281f 0%, #1a1718 40%, #0e0e10 85%)" }} />
      <div style={{ position: "absolute", top: 30 * escala, left: 42 * escala, right: 42 * escala, display: "flex", justifyContent: "space-between", fontSize: 13 * escala, letterSpacing: 3 * escala, color: "#dd9c76" }}>
        <span>DOCFORJA · {width > 1280 ? "1080p" : "540p"}{idioma ? ` · ${idioma.toUpperCase()}` : ""}</span>
        <span>{atual?.bloco ?? "PLANO"}</span>
      </div>
      <div style={{ position: "absolute", left: 62 * escala, right: 62 * escala, top: 106 * escala }}>
        <div style={{ fontSize: 16 * escala, letterSpacing: 2 * escala, color: "#c98a66", marginBottom: 18 * escala }}>
          {cartao ? "CARTÃO DE PLANEJAMENTO" : `SHOT ${shot?.id ?? "—"} · ${shot?.template ?? "—"}`}
        </div>
        <div style={{ fontFamily: "Georgia, serif", fontSize: 41 * escala, lineHeight: 1.13, maxHeight: 220 * escala, overflow: "hidden" }}>
          {cartao ? cartao.texto || cartao.descricao : (i18n && shot?.id && i18n[shot.id]) || shot?.texto || shot?.descricao || titulo}
        </div>
        {!cartao && shot?.texto && shot.descricao && (
          <div style={{ marginTop: 24 * escala, fontSize: 21 * escala, color: "#b8aba4", maxHeight: 105 * escala, overflow: "hidden" }}>
            Imagem planejada: {shot.descricao}
          </div>
        )}
      </div>
      <div style={{ position: "absolute", left: 42 * escala, right: 42 * escala, bottom: 35 * escala }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 * escala, color: "#c1afa3", letterSpacing: 1 * escala }}>
          <span>{shot?.situacao ?? "PLACEHOLDER"} · RECONSTITUIÇÃO ARTÍSTICA{tem_trilha_provisoria ? " · TRILHA PROVISÓRIA ATIVA" : ""}</span>
          <span>{Math.floor(frame / fps / 60).toString().padStart(2, "0")}:{Math.floor((frame / fps) % 60).toString().padStart(2, "0")}</span>
        </div>
        <div style={{ height: 3 * escala, marginTop: 12 * escala, backgroundColor: "#51403a" }}>
          <div style={{ width: `${andamento * 100}%`, height: "100%", backgroundColor: "#d8784d" }} />
        </div>
      </div>
    </AbsoluteFill>
  );
};
