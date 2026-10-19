import React from "react";
import { staticFile } from "remotion";
import { Bloco, ShotTimeline } from "./Bloco";

export const SHOTS_TESTE_M2: ShotTimeline[] = [
  // Shot 1: Foto (T01) com Ken Burns, HudClock (O3) e Rotulo (O2)
  {
    id: "B3-01",
    template: "T01",
    duracao_frames: 72, // 3 segundos a 24 fps
    transicao: "dissolve",
    params: {
      src: staticFile("volcano.png"),
      movimento: "push_in",
      amplitude: 0.14,
      foco: { x: 0.5, y: 0.4 },
    },
    sobreposicoes: [
      {
        tipo: "O3",
        params: {
          dia: 1,
          hora: "13:00",
          local: "POMPEIA",
          progresso: 0.15,
        },
      },
      {
        tipo: "O2",
        params: {
          tipo: "reconstituicao",
        },
      },
    ],
  },
  // Shot 2: Numero (T08) com contador de altitude da coluna eruptiva
  {
    id: "B3-02",
    template: "T08",
    duracao_frames: 72, // 3 segundos
    transicao: "corte",
    params: {
      valor: 33,
      prefixo: "até ≈",
      unidade: "km",
      legenda: "Altura máxima da coluna eruptiva sobre o Vesúvio",
      casas_decimais: 0,
    },
    sobreposicoes: [
      {
        tipo: "O1",
        params: {
          nome: "COLUNA PLINIANA",
          descricao: "Gases, cinza e pedra-pomes a 1.400 km/h",
        },
      },
    ],
  },
  // Shot 3: Mapa (T10) com rotas e areas de impacto na Campania
  {
    id: "B3-03",
    template: "T10",
    duracao_frames: 96, // 4 segundos
    transicao: "dissolve",
    params: {
      regiao: "CAMPÂNIA · BAÍA DE NÁPOLES 79 d.C.",
      pontos: [
        { rotulo: "VESÚVIO", x: 55, y: 38, tipo: "vulcao" },
        { rotulo: "POMPEIA", x: 62, y: 55, tipo: "cidade" },
        { rotulo: "HERCULANO", x: 44, y: 46, tipo: "cidade" },
        { rotulo: "MISENO (Esquadra)", x: 20, y: 58, tipo: "porto" },
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
          rotulo: "ZONA DE QUEDA DE POMES",
          centro: { x: 55, y: 44 },
          raio: 16,
        },
      ],
      rotulo_costa: "LINHA DE COSTA APROXIMADA DE 79 d.C.",
    },
  },
  // Shot 4: TextoImpacto (T06) com estilo riscado
  {
    id: "B3-04",
    template: "T06",
    duracao_frames: 72, // 3 segundos
    transicao: "corte",
    params: {
      texto: "NÃO FOI LAVA.\nESSE É O PRIMEIRO MITO.",
      estilo: "riscado",
      fundo_escuro: true,
    },
    sobreposicoes: [
      {
        tipo: "O4",
        params: {
          tipo: "circulo",
          posicao: { x: 50, y: 50 },
          tamanho: 240,
          rotulo: "FATO HISTÓRICO",
        },
      },
    ],
  },
];

export const BlocoTeste: React.FC = () => {
  return (
    <Bloco
      id="B3-TESTE"
      titulo="Dia 1 — A Coluna Eruptiva"
      shots={SHOTS_TESTE_M2}
    />
  );
};
