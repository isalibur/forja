import React, { useEffect } from "react";
import { Composition, Folder, staticFile } from "remotion";
import { carregarFontesKit } from "./tokens";
import * as Templates from "./templates";
import * as Overlays from "./sobreposicoes";
import * as Schemas from "./schemas/templates";
import * as SchemasSob from "./schemas/sobreposicoes";
import { BlocoTeste } from "./composicoes/BlocoTeste";
import { PreviaPlano } from "./composicoes/PreviaPlano";
import {
  defaultPropsShort,
  ShortSafeAreaGuide,
  ShortVertical,
  type TemplateShort,
} from "./composicoes/ShortVertical";
import { SchemaShortTimeline, SchemaShortVertical } from "./schemas/shorts";
import { TEMPLATES_LONGOS } from "./composicoes/TemplatesLongos";
import { ShortTimeline } from "./composicoes/ShortTimeline";

export const Root: React.FC = () => {
  useEffect(() => {
    carregarFontesKit();
  }, []);

  return (
    <>
      <Composition
        id="Previa-Plano-540p"
        component={PreviaPlano}
        durationInFrames={240}
        fps={24}
        width={960}
        height={540}
        defaultProps={{ titulo: "Plano de Vídeo", shots: [], cartoes: [], duracao_frames: 240, tem_trilha_provisoria: false }}
        calculateMetadata={({ props }) => ({ durationInFrames: props.duracao_frames })}
      />
      <Composition
        id="Previa-Plano-1080p"
        component={PreviaPlano}
        durationInFrames={240}
        fps={24}
        width={1920}
        height={1080}
        defaultProps={{ titulo: "Plano de Vídeo", shots: [], cartoes: [], duracao_frames: 240, tem_trilha_provisoria: false }}
        calculateMetadata={({ props }) => ({ durationInFrames: props.duracao_frames })}
      />
      {/* 1. COMPOSICAO INTEGRADA MESTRA DO M2: BLOCO TESTE */}
      <Folder name="00-Integracao-M2">
        <Composition
          id="Bloco-Teste-1080p"
          component={BlocoTeste}
          durationInFrames={312} // ~13 segundos a 24 fps
          fps={24}
          width={1920}
          height={1080}
        />
        <Composition
          id="Bloco-Teste-360p"
          component={BlocoTeste}
          durationInFrames={312}
          fps={24}
          width={640}
          height={360}
        />
      </Folder>

      {/* 2. TEMPLATES T00 A T14 ISOLADOS COM PROPS E SCHEMAS ZOD */}
      <Folder name="01-Templates">
        {TEMPLATES_LONGOS.map((modelo) => (
          <Composition
            key={modelo.id}
            id={modelo.id}
            component={modelo.componente}
            durationInFrames={modelo.duracaoFrames}
            fps={24}
            width={1920}
            height={1080}
            schema={modelo.schema}
            defaultProps={modelo.defaultProps}
          />
        ))}

        <Folder name="04-Templates-Verticais-9x16">
          {TEMPLATES_LONGOS.map((modelo) => (
            <Composition
              key={`${modelo.id}-V`}
              id={`${modelo.id}-V`}
              component={modelo.componente}
              durationInFrames={modelo.duracaoFrames}
              fps={24}
              width={1080}
              height={1920}
              schema={modelo.schema}
              defaultProps={modelo.defaultProps}
            />
          ))}
        </Folder>














      </Folder>

      {/* 3. SOBREPOSICOES O1 A O4 */}
      <Folder name="02-Sobreposicoes">
        <Composition
          id="O1-Identificacao"
          component={Overlays.O1_Identificacao}
          durationInFrames={72}
          fps={24}
          width={1920}
          height={1080}
          schema={SchemasSob.SchemaO1Identificacao}
          defaultProps={{
            nome: "PLÍNIO, O JOVEM",
            descricao: "Testemunha ocular · 17 anos em Miseno",
          }}
        />

        <Composition
          id="O2-Rotulo"
          component={Overlays.O2_Rotulo}
          durationInFrames={72}
          fps={24}
          width={1920}
          height={1080}
          schema={SchemasSob.SchemaO2Rotulo}
          defaultProps={{
            tipo: "reconstituicao",
          }}
        />

        <Composition
          id="O3-Contexto"
          component={Overlays.O3_Contexto}
          durationInFrames={72}
          fps={24}
          width={1920}
          height={1080}
          schema={SchemasSob.SchemaO3Contexto}
          defaultProps={{
            dia: 1,
            hora: "13:00",
            local: "POMPEIA",
            progresso: 0.15,
            aproximado: true,
          }}
        />

        <Composition
          id="O4-Destaque"
          component={Overlays.O4_Destaque}
          durationInFrames={72}
          fps={24}
          width={1920}
          height={1080}
          schema={SchemasSob.SchemaO4Destaque}
          defaultProps={{
            tipo: "circulo",
            posicao: { x: 50, y: 50 },
            tamanho: 140,
            rotulo: "ÁREA DE INTERESSE",
          }}
        />
      </Folder>

      <Folder name="03-Shorts-9x16">
        <Composition
          id="Short-Derivado"
          component={ShortTimeline}
          durationInFrames={1800}
          fps={30}
          width={1080}
          height={1920}
          schema={SchemaShortTimeline}
          defaultProps={{
            duracao_frames: 900,
            audio: "",
            cenas: [
              {
                id: "gancho",
                inicio_frame: 0,
                duracao_frames: 60,
                props: { ...defaultPropsShort, variante: "V01", titulo: "GANCHO" },
              },
            ],
          }}
          calculateMetadata={({ props }) => ({ durationInFrames: props.duracao_frames })}
        />
        <Composition
          id="Guia-Safe-Area-Short"
          component={ShortSafeAreaGuide}
          durationInFrames={48}
          fps={24}
          width={1080}
          height={1920}
        />
        {(
          [
            "V01",
            "V02",
            "V03",
            "V04",
            "V05",
            "V06",
            "V07",
            "V08",
            "V09",
            "V10",
            "V11",
          ] as TemplateShort[]
        ).map((variante) => (
          <Composition
            key={variante}
            id={variante}
            component={ShortVertical}
            durationInFrames={720}
            fps={30}
            width={1080}
            height={1920}
            schema={SchemaShortVertical}
            defaultProps={{ ...defaultPropsShort, variante }}
          />
        ))}
      </Folder>
    </>
  );
};
