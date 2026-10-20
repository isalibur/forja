import React from "react";
import { Audio } from "@remotion/media";
import { AbsoluteFill, CanvasImage, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { DadosPlano } from "../hooks/usePlano";

type Manifesto = NonNullable<DadosPlano["manifesto"]>;

export const PreviaInterativa: React.FC<{ manifesto: Manifesto; audioUrl: string; imagensPorShot: Record<string, string> }> = ({
  manifesto,
  audioUrl,
  imagensPorShot,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const shot = manifesto.shots.find(
    (item) => frame >= item.inicio_frame && frame < item.fim_frame,
  );
  const cartao = manifesto.cartoes.find(
    (item) => frame >= item.inicio_frame && frame < item.fim_frame,
  );
  const atual = cartao ?? shot;
  const imagemUrl = !cartao && shot ? imagensPorShot[shot.id] : undefined;

  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 65% 45%, #4c281f, #0e0e10 75%)", color: "#f0e8d8", fontFamily: "Arial, sans-serif" }}>
      <Audio src={audioUrl} />
      {imagemUrl && <CanvasImage src={imagemUrl} style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.38 }} />}
      <div style={{ position: "absolute", top: 30, left: 42, right: 42, display: "flex", justifyContent: "space-between", fontSize: 13, letterSpacing: 3, color: "#dd9c76" }}>
        <span>DOCFORJA · PRÉVIA</span><span>{atual?.bloco ?? "PLANO"}</span>
      </div>
      <div style={{ position: "absolute", left: 62, right: 62, top: 106 }}>
        <div style={{ fontSize: 16, letterSpacing: 2, color: "#c98a66", marginBottom: 18 }}>
          {cartao ? "CARTÃO DE PLANEJAMENTO" : `SHOT ${shot?.id ?? "—"} · ${shot?.template ?? "—"}`}
        </div>
        <div style={{ fontFamily: "Georgia, serif", fontSize: 41, lineHeight: 1.13, maxHeight: 220, overflow: "hidden" }}>
          {cartao ? cartao.texto || cartao.descricao : shot?.texto || shot?.descricao || manifesto.titulo}
        </div>
        {!cartao && shot?.texto && shot.descricao && (
          <div style={{ marginTop: 24, fontSize: 21, color: "#b8aba4", maxHeight: 105, overflow: "hidden" }}>
            Imagem planejada: {shot.descricao}
          </div>
        )}
      </div>
      <div style={{ position: "absolute", left: 42, right: 42, bottom: 35 }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "#c1afa3", letterSpacing: 1 }}>
          <span>{imagemUrl ? "IMAGEM LICENCIADA · PRÉVIA" : `${shot?.situacao ?? "PLACEHOLDER"} · NÃO É IMAGEM FINAL`}</span>
          <span>{String(Math.floor(frame / fps / 60)).padStart(2, "0")}:{String(Math.floor((frame / fps) % 60)).padStart(2, "0")}</span>
        </div>
        <div style={{ height: 3, marginTop: 12, background: "#51403a" }}>
          <div style={{ width: `${interpolate(frame, [shot?.inicio_frame ?? 0, shot?.fim_frame ?? 1], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}%`, height: "100%", background: "#d8784d" }} />
        </div>
      </div>
    </AbsoluteFill>
  );
};
