import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import * as Templates from "../templates";
import * as Overlays from "../sobreposicoes";

export interface ShotTimeline {
  id: string;
  template: string;
  params: Record<string, unknown>;
  duracao_frames: number;
  sobreposicoes?: Array<{
    tipo: "O1" | "O2" | "O3" | "O4";
    params: Record<string, unknown>;
    de_frame?: number;
    duracao_frames?: number;
  }>;
  transicao?: "corte" | "dissolve" | "fade_preto";
}

export interface PropsBloco {
  id: string;
  titulo?: string;
  shots: ShotTimeline[];
}

// Mapa de componentes de template
const MAPA_TEMPLATES: Record<string, React.FC<any>> = {
  T00: Templates.T00_Respiro,
  T01: Templates.T01_Foto,
  T02: Templates.T02_FotoProfundidade,
  T03: Templates.T03_FotoRecorte,
  T04: Templates.T04_FotoDetalhe,
  T05: Templates.T05_Comparacao,
  T06: Templates.T06_TextoImpacto,
  T07: Templates.T07_Citacao,
  T08: Templates.T08_Numero,
  T09: Templates.T09_Grafico,
  T10: Templates.T10_Mapa,
  T11: Templates.T11_LinhaDoTempo,
  T12: Templates.T12_Capitulo,
  T13: Templates.T13_Abertura,
  T14: Templates.T14_Encerramento,
};

// Mapa de sobreposicoes
const MAPA_SOBREPOSICOES: Record<string, React.FC<any>> = {
  O1: Overlays.O1_Identificacao,
  O2: Overlays.O2_Rotulo,
  O3: Overlays.O3_Contexto,
  O4: Overlays.O4_Destaque,
};

export const Bloco: React.FC<PropsBloco> = ({ shots }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#0E0E10" }}>
      <TransitionSeries>
        {shots.map((shot, index) => {
          const ComponenteTemplate = MAPA_TEMPLATES[shot.template] || Templates.T00_Respiro;
          const temTransicaoDissolve = shot.transicao === "dissolve" && index < shots.length - 1;

          return (
            <React.Fragment key={shot.id}>
              <TransitionSeries.Sequence durationInFrames={shot.duracao_frames}>
                {/* Componente visual do shot */}
                <ComponenteTemplate {...shot.params} />

                {/* Sobreposicoes O1-O4 ativas durante o shot */}
                {shot.sobreposicoes?.map((sob, sobIdx) => {
                  const ComponenteSob = MAPA_SOBREPOSICOES[sob.tipo];
                  if (!ComponenteSob) return null;

                  const deFrame = sob.de_frame || 0;
                  const duracao = sob.duracao_frames || shot.duracao_frames - deFrame;

                  return (
                    <Sequence
                      key={sobIdx}
                      from={deFrame}
                      durationInFrames={duracao}
                    >
                      <ComponenteSob {...sob.params} />
                    </Sequence>
                  );
                })}
              </TransitionSeries.Sequence>

              {/* Transicao dissolve opcional se solicitada */}
              {temTransicaoDissolve && (
                <TransitionSeries.Transition
                  presentation={fade()}
                  timing={linearTiming({ durationInFrames: 10 })}
                />
              )}
            </React.Fragment>
          );
        })}
      </TransitionSeries>
    </AbsoluteFill>
  );
};
