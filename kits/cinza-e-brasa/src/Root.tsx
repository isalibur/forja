import React, { useEffect } from "react";
import { Composition, Folder, staticFile } from "remotion";
import { carregarFontesKit } from "./tokens";
import * as Templates from "./templates";
import * as Overlays from "./sobreposicoes";
import * as Schemas from "./schemas/templates";
import * as SchemasSob from "./schemas/sobreposicoes";
import { BlocoTeste } from "./composicoes/BlocoTeste";
import { PreviaPlano } from "./composicoes/PreviaPlano";

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
        <Composition
          id="T00-Respiro"
          component={Templates.T00_Respiro}
          durationInFrames={48}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT00Respiro}
          defaultProps={{
            cor: "#0E0E10",
            particulas: true,
          }}
        />

        <Composition
          id="T01-Foto"
          component={Templates.T01_Foto}
          durationInFrames={72}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT01Foto}
          defaultProps={{
            src: staticFile("volcano.png"),
            movimento: "push_in",
            amplitude: 0.14,
            foco: { x: 0.5, y: 0.4 },
          }}
        />

        <Composition
          id="T02-FotoProfundidade"
          component={Templates.T02_FotoProfundidade}
          durationInFrames={72}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT02FotoProfundidade}
          defaultProps={{
            src: staticFile("volcano.png"),
            movimento: "dolly",
            intensidade: 0.45,
          }}
        />

        <Composition
          id="T03-FotoRecorte"
          component={Templates.T03_FotoRecorte}
          durationInFrames={72}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT03FotoRecorte}
          defaultProps={{
            src_sujeito: staticFile("volcano.png"),
            fundo_tipo: "desfocado",
            entrada: "baixo",
          }}
        />

        <Composition
          id="T04-FotoDetalhe"
          component={Templates.T04_FotoDetalhe}
          durationInFrames={72}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT04FotoDetalhe}
          defaultProps={{
            src: staticFile("volcano.png"),
            regiao: { x: 50, y: 40, w: 22, h: 22 },
            rotulo: "CRATERA SOMMA-VESÚVIO",
          }}
        />

        <Composition
          id="T05-Comparacao"
          component={Templates.T05_Comparacao}
          durationInFrames={72}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT05Comparacao}
          defaultProps={{
            src_a: staticFile("volcano.png"),
            src_b: staticFile("volcano.png"),
            rotulo_a: "79 d.C. (CUME ÚNICO)",
            rotulo_b: "HOJE (DUPLO CONE)",
            modo: "divisor",
          }}
        />

        <Composition
          id="T06-TextoImpacto"
          component={Templates.T06_TextoImpacto}
          durationInFrames={72}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT06TextoImpacto}
          defaultProps={{
            texto: "NÃO FOI LAVA.\nESSE É O PRIMEIRO MITO.",
            estilo: "riscado",
            fundo_escuro: true,
          }}
        />

        <Composition
          id="T07-Citacao"
          component={Templates.T07_Citacao}
          durationInFrames={96}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT07Citacao}
          defaultProps={{
            texto: "Nubes oriebatur, cuius similitudinem et formam non alia magis arbor quam pinus expresserit.",
            traducao: "Uma nuvem subia, cuja aparência e formato nenhuma outra árvore expressaria melhor que um pinheiro.",
            fonte: "Plínio, o Jovem · Cartas 6.16",
            estilo: "papel",
          }}
        />

        <Composition
          id="T08-Numero"
          component={Templates.T08_Numero}
          durationInFrames={72}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT08Numero}
          defaultProps={{
            valor: 33,
            prefixo: "até ≈",
            unidade: "km",
            legenda: "Altura máxima da coluna eruptiva sobre o Vesúvio",
            casas_decimais: 0,
          }}
        />

        <Composition
          id="T09-Grafico"
          component={Templates.T09_Grafico}
          durationInFrames={96}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT09Grafico}
          defaultProps={{
            tipo: "escala",
            titulo: "COMPARAÇÃO DE ALTITUDE DA PLUMA ERUPTIVA",
            dados: [
              { rotulo: "Monte Everest", valor: 8.8, unidade: "km" },
              { rotulo: "Voo comercial", valor: 11, unidade: "km", prefixo: "≈" },
              { rotulo: "Coluna do Vesúvio", faixa: [26, 33], unidade: "km" },
            ],
          }}
        />

        <Composition
          id="T10-Mapa"
          component={Templates.T10_Mapa}
          durationInFrames={96}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT10Mapa}
          defaultProps={{
            regiao: "BAÍA DE NÁPOLES · CAMPÂNIA 79 d.C.",
            pontos: [
              { rotulo: "VESÚVIO", x: 55, y: 38, tipo: "vulcao" },
              { rotulo: "POMPEIA", x: 62, y: 55, tipo: "cidade" },
              { rotulo: "HERCULANO", x: 44, y: 46, tipo: "cidade" },
              { rotulo: "MISENO (Frota)", x: 20, y: 58, tipo: "porto" },
            ],
            rotas: [
              {
                de: "Miseno",
                para: "Estábia",
                pontos: [
                  { x: 20, y: 58 },
                  { x: 38, y: 68 },
                  { x: 56, y: 72 },
                  { x: 68, y: 68 },
                ],
              },
            ],
            areas: [
              {
                rotulo: "ÁREA PIROCLÁSTICA",
                centro: { x: 55, y: 44 },
                raio: 16,
              },
            ],
            rotulo_costa: "LINHA DE COSTA APROXIMADA DE 79 d.C.",
          }}
        />

        <Composition
          id="T11-LinhaDoTempo"
          component={Templates.T11_LinhaDoTempo}
          durationInFrames={96}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT11LinhaDoTempo}
          defaultProps={{
            titulo: "AS 24 HORAS DA ERUPÇÃO",
            indice_ativo: 0,
            eventos: [
              { data: "13:00", rotulo: "Abertura da chaminé e coluna inicial" },
              { data: "17:00", rotulo: "Chuva intensa de pedra-pomes sobre Pompeia" },
              { data: "01:00", rotulo: "Colapso térmico e primeira corrente piroclástica" },
              { data: "06:30", rotulo: "Soterramento total e alvorada de cinza" },
            ],
          }}
        />

        <Composition
          id="T12-Capitulo"
          component={Templates.T12_Capitulo}
          durationInFrames={48}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT12Capitulo}
          defaultProps={{
            numero: "BLOCO III",
            titulo: "A COLUNA DE FUMAÇA",
            subtitulo: "Pompeia · 13:00 às 17:00",
          }}
        />

        <Composition
          id="T13-Abertura"
          component={Templates.T13_Abertura}
          durationInFrames={72}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT13Abertura}
          defaultProps={{
            titulo: "VESÚVIO",
            subtitulo: "24 HORAS QUE MUDARAM A HISTÓRIA",
          }}
        />

        <Composition
          id="T14-Encerramento"
          component={Templates.T14_Encerramento}
          durationInFrames={96}
          fps={24}
          width={1920}
          height={1080}
          schema={Schemas.SchemaT14Encerramento}
          defaultProps={{
            titulo: "DOCFORJA",
            creditos: ["Pesquisa e Roteiro: Equipe Histórica", "Voz e Locução: Chatterbox pt-BR", "Imagens: MANN / USGS / Acervo Público"],
            mostrar_espaco_youtube: true,
          }}
        />
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
    </>
  );
};
