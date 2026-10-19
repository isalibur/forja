import { z } from "zod";

export const SchemaT00Respiro = z.object({
  cor: z.string().default("#0E0E10"),
  particulas: z.boolean().default(true),
});

export const SchemaT01Foto = z.object({
  src: z.string(),
  movimento: z.enum(["push_in", "pull_out", "pan_esq", "pan_dir", "estatico"]).default("push_in"),
  amplitude: z.number().min(0.01).max(0.4).default(0.12),
  foco: z.object({ x: z.number().min(0).max(1), y: z.number().min(0).max(1) }).default({ x: 0.5, y: 0.5 }),
});

export const SchemaT02FotoProfundidade = z.object({
  src: z.string(),
  movimento: z.enum(["dolly", "orbita", "zoom"]).default("dolly"),
  intensidade: z.number().min(0.1).max(1.0).default(0.4),
});

export const SchemaT03FotoRecorte = z.object({
  src_sujeito: z.string(),
  src_fundo: z.string().optional(),
  fundo_tipo: z.enum(["desfocado", "paleta", "outra_imagem"]).default("desfocado"),
  entrada: z.enum(["baixo", "suave", "zoom"]).default("baixo"),
});

export const SchemaT04FotoDetalhe = z.object({
  src: z.string(),
  regiao: z.object({
    x: z.number().min(0).max(100),
    y: z.number().min(0).max(100),
    w: z.number().min(5).max(100),
    h: z.number().min(5).max(100),
  }),
  rotulo: z.string().optional(),
});

export const SchemaT05Comparacao = z.object({
  src_a: z.string(),
  src_b: z.string(),
  rotulo_a: z.string().optional().default("ANTES"),
  rotulo_b: z.string().optional().default("DEPOIS"),
  modo: z.enum(["lado_a_lado", "divisor"]).default("divisor"),
});

export const SchemaT06TextoImpacto = z.object({
  texto: z.string().min(1),
  estilo: z.enum(["limpo", "riscado", "carvao"]).default("limpo"),
  src_fundo: z.string().optional(),
  fundo_escuro: z.boolean().default(true),
});

export const SchemaT07Citacao = z.object({
  texto: z.string().min(1),
  traducao: z.string().optional(),
  fonte: z.string().min(1),
  estilo: z.enum(["papel", "pedra", "escuro"]).default("papel"),
});

export const SchemaT08Numero = z.object({
  valor: z.number(),
  prefixo: z.string().optional(),
  unidade: z.string().optional(),
  legenda: z.string().min(1),
  casas_decimais: z.number().int().min(0).max(3).default(0),
});

export const SchemaT09GraficoItem = z.object({
  rotulo: z.string(),
  valor: z.number().optional(),
  faixa: z.tuple([z.number(), z.number()]).optional(),
  unidade: z.string().optional(),
  prefixo: z.string().optional(),
});

export const SchemaT09Grafico = z.object({
  tipo: z.enum(["barras", "linhas", "escala"]).default("escala"),
  titulo: z.string().optional(),
  dados: z.array(SchemaT09GraficoItem).min(1),
});

export const SchemaT10Ponto = z.object({
  rotulo: z.string(),
  x: z.number().min(0).max(100),
  y: z.number().min(0).max(100),
  tipo: z.enum(["cidade", "vulcao", "porto"]).default("cidade"),
});

export const SchemaT10Rota = z.object({
  de: z.string(),
  para: z.string(),
  pontos: z.array(z.object({ x: z.number(), y: z.number() })),
});

export const SchemaT10Area = z.object({
  rotulo: z.string(),
  centro: z.object({ x: z.number(), y: z.number() }),
  raio: z.number().default(15),
  cor: z.string().optional(),
});

export const SchemaT10Mapa = z.object({
  regiao: z.string().default("BAIA DE NAPOLES · CAMPANIA 79 d.C."),
  pontos: z.array(SchemaT10Ponto).default([]),
  rotas: z.array(SchemaT10Rota).default([]),
  areas: z.array(SchemaT10Area).default([]),
  rotulo_costa: z.string().default("LINHA DE COSTA APROXIMADA DE 79 d.C."),
});

export const SchemaT11Evento = z.object({
  data: z.string(),
  rotulo: z.string(),
  src_ativo: z.string().optional(),
  descricao: z.string().optional(),
});

export const SchemaT11LinhaDoTempo = z.object({
  titulo: z.string().optional().default("CRONOLOGIA"),
  eventos: z.array(SchemaT11Evento).min(1),
  indice_ativo: z.number().int().default(0),
});

export const SchemaT12Capitulo = z.object({
  numero: z.string(),
  titulo: z.string(),
  subtitulo: z.string().optional(),
});

export const SchemaT13Abertura = z.object({
  titulo: z.string(),
  subtitulo: z.string(),
});

export const SchemaT14Encerramento = z.object({
  titulo: z.string().optional().default("DOCFORJA"),
  creditos: z.array(z.string()).default([]),
  mostrar_espaco_youtube: z.boolean().default(true),
});

export type PropsT00Respiro = z.infer<typeof SchemaT00Respiro>;
export type PropsT01Foto = z.infer<typeof SchemaT01Foto>;
export type PropsT02FotoProfundidade = z.infer<typeof SchemaT02FotoProfundidade>;
export type PropsT03FotoRecorte = z.infer<typeof SchemaT03FotoRecorte>;
export type PropsT04FotoDetalhe = z.infer<typeof SchemaT04FotoDetalhe>;
export type PropsT05Comparacao = z.infer<typeof SchemaT05Comparacao>;
export type PropsT06TextoImpacto = z.infer<typeof SchemaT06TextoImpacto>;
export type PropsT07Citacao = z.infer<typeof SchemaT07Citacao>;
export type PropsT08Numero = z.infer<typeof SchemaT08Numero>;
export type PropsT09Grafico = z.infer<typeof SchemaT09Grafico>;
export type PropsT10Mapa = z.infer<typeof SchemaT10Mapa>;
export type PropsT11LinhaDoTempo = z.infer<typeof SchemaT11LinhaDoTempo>;
export type PropsT12Capitulo = z.infer<typeof SchemaT12Capitulo>;
export type PropsT13Abertura = z.infer<typeof SchemaT13Abertura>;
export type PropsT14Encerramento = z.infer<typeof SchemaT14Encerramento>;
