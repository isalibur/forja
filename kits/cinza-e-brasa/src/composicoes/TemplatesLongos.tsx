import { staticFile } from "remotion";
import * as Schemas from "../schemas/templates";
import * as Templates from "../templates";

export type TemplateLongo = {
  id: string;
  // biome-ignore lint/suspicious/noExplicitAny: o schema valida cada template
  componente: React.FC<any>;
  duracaoFrames: number;
  // biome-ignore lint/suspicious/noExplicitAny: o schema valida cada template
  schema: any;
  // biome-ignore lint/suspicious/noExplicitAny: o schema valida cada template
  defaultProps: any;
};

export const TEMPLATES_LONGOS: TemplateLongo[] = [
  {
    id: "T00-Respiro",
    componente: Templates.T00_Respiro,
    duracaoFrames: 48,
    schema: Schemas.SchemaT00Respiro,
    defaultProps: {
      
      cor: "#0E0E10",
      particulas: true,
    },
  },
  {
    id: "T01-Foto",
    componente: Templates.T01_Foto,
    duracaoFrames: 72,
    schema: Schemas.SchemaT01Foto,
    defaultProps: {
      
      src: staticFile("volcano.png"),
      movimento: "push_in",
      amplitude: 0.14,
      foco: { x: 0.5, y: 0.4 },
    },
  },
  {
    id: "T02-FotoProfundidade",
    componente: Templates.T02_FotoProfundidade,
    duracaoFrames: 72,
    schema: Schemas.SchemaT02FotoProfundidade,
    defaultProps: {
      
      src: staticFile("volcano.png"),
      movimento: "dolly",
      intensidade: 0.45,
    },
  },
  {
    id: "T03-FotoRecorte",
    componente: Templates.T03_FotoRecorte,
    duracaoFrames: 72,
    schema: Schemas.SchemaT03FotoRecorte,
    defaultProps: {
      
      src_sujeito: staticFile("volcano.png"),
      fundo_tipo: "desfocado",
      entrada: "baixo",
    },
  },
  {
    id: "T04-FotoDetalhe",
    componente: Templates.T04_FotoDetalhe,
    duracaoFrames: 72,
    schema: Schemas.SchemaT04FotoDetalhe,
    defaultProps: {
      
      src: staticFile("volcano.png"),
      regiao: { x: 50, y: 40, w: 22, h: 22 },
      rotulo: "CRATERA SOMMA-VESÚVIO",
    },
  },
  {
    id: "T05-Comparacao",
    componente: Templates.T05_Comparacao,
    duracaoFrames: 72,
    schema: Schemas.SchemaT05Comparacao,
    defaultProps: {
      
      src_a: staticFile("volcano.png"),
      src_b: staticFile("volcano.png"),
      rotulo_a: "79 d.C. (CUME ÚNICO)",
      rotulo_b: "HOJE (DUPLO CONE)",
      modo: "divisor",
    },
  },
  {
    id: "T06-TextoImpacto",
    componente: Templates.T06_TextoImpacto,
    duracaoFrames: 72,
    schema: Schemas.SchemaT06TextoImpacto,
    defaultProps: {
      
      texto: "NÃO FOI LAVA.\nESSE É O PRIMEIRO MITO.",
      estilo: "riscado",
      fundo_escuro: true,
    },
  },
  {
    id: "T07-Citacao",
    componente: Templates.T07_Citacao,
    duracaoFrames: 96,
    schema: Schemas.SchemaT07Citacao,
    defaultProps: {
      
      texto: "Nubes oriebatur, cuius similitudinem et formam non alia magis arbor quam pinus expresserit.",
      traducao: "Uma nuvem subia, cuja aparência e formato nenhuma outra árvore expressaria melhor que um pinheiro.",
      fonte: "Plínio, o Jovem · Cartas 6.16",
      estilo: "papel",
    },
  },
  {
    id: "T08-Numero",
    componente: Templates.T08_Numero,
    duracaoFrames: 72,
    schema: Schemas.SchemaT08Numero,
    defaultProps: {
      
      valor: 33,
      prefixo: "até ≈",
      unidade: "km",
      legenda: "Altura máxima da coluna eruptiva sobre o Vesúvio",
      casas_decimais: 0,
    },
  },
  {
    id: "T09-Grafico",
    componente: Templates.T09_Grafico,
    duracaoFrames: 96,
    schema: Schemas.SchemaT09Grafico,
    defaultProps: {
      
      tipo: "escala",
      titulo: "COMPARAÇÃO DE ALTITUDE DA PLUMA ERUPTIVA",
      dados: [
      { rotulo: "Monte Everest", valor: 8.8, unidade: "km" },
      { rotulo: "Voo comercial", valor: 11, unidade: "km", prefixo: "≈" },
      { rotulo: "Coluna do Vesúvio", faixa: [26, 33], unidade: "km" },
      ],
    },
  },
  {
    id: "T10-Mapa",
    componente: Templates.T10_Mapa,
    duracaoFrames: 96,
    schema: Schemas.SchemaT10Mapa,
    defaultProps: {
      
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
    },
  },
  {
    id: "T11-LinhaDoTempo",
    componente: Templates.T11_LinhaDoTempo,
    duracaoFrames: 96,
    schema: Schemas.SchemaT11LinhaDoTempo,
    defaultProps: {
      
      titulo: "AS 24 HORAS DA ERUPÇÃO",
      indice_ativo: 0,
      eventos: [
      { data: "13:00", rotulo: "Abertura da chaminé e coluna inicial" },
      { data: "17:00", rotulo: "Chuva intensa de pedra-pomes sobre Pompeia" },
      { data: "01:00", rotulo: "Colapso térmico e primeira corrente piroclástica" },
      { data: "06:30", rotulo: "Soterramento total e alvorada de cinza" },
      ],
    },
  },
  {
    id: "T12-Capitulo",
    componente: Templates.T12_Capitulo,
    duracaoFrames: 48,
    schema: Schemas.SchemaT12Capitulo,
    defaultProps: {
      
      numero: "BLOCO III",
      titulo: "A COLUNA DE FUMAÇA",
      subtitulo: "Pompeia · 13:00 às 17:00",
    },
  },
  {
    id: "T13-Abertura",
    componente: Templates.T13_Abertura,
    duracaoFrames: 72,
    schema: Schemas.SchemaT13Abertura,
    defaultProps: {
      
      titulo: "VESÚVIO",
      subtitulo: "24 HORAS QUE MUDARAM A HISTÓRIA",
    },
  },
  {
    id: "T14-Encerramento",
    componente: Templates.T14_Encerramento,
    duracaoFrames: 96,
    schema: Schemas.SchemaT14Encerramento,
    defaultProps: {
      
      titulo: "DOCFORJA",
      creditos: ["Pesquisa e Roteiro: Equipe Histórica", "Voz e Locução: Chatterbox pt-BR", "Imagens: MANN / USGS / Acervo Público"],
      mostrar_espaco_youtube: true,
    },
  },
];
