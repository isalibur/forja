import { z } from "zod";

const CaptionSchema = z.object({
  text: z.string(),
  startMs: z.number().min(0),
  endMs: z.number().positive(),
  timestampMs: z.number().nullable(),
  confidence: z.number().nullable(),
  palavras: z.array(z.object({
    text: z.string(),
    startMs: z.number().min(0),
    endMs: z.number().positive(),
    destacar: z.boolean().optional(),
  })).optional(),
  pageBreakAfter: z.boolean().optional(),
});

export const SchemaShortVertical = z.object({
  variante: z.enum(["V01", "V02", "V03", "V04", "V05", "V06", "V07", "V08", "V09", "V10"]),
  titulo: z.string().default(""),
  subtitulo: z.string().default(""),
  texto: z.string().default(""),
  imagem: z.string().default(""),
  imagem_antes: z.string().default(""),
  imagem_depois: z.string().default(""),
  clipe: z.string().default(""),
  itens: z.array(z.string()).default([]),
  opcao_a: z.string().default(""),
  opcao_b: z.string().default(""),
  preco: z.string().default(""),
  condicao: z.string().default(""),
  aviso_publicidade: z.string().default(""),
  prova: z.string().default(""),
  fonte_prova: z.string().default(""),
  cta: z.string().default(""),
  marca: z.string().default(""),
  foco_x: z.number().min(0).max(1).default(0.5),
  foco_y: z.number().min(0).max(1).default(0.5),
  usar_fundo_desfocado: z.boolean().default(false),
  legendas: z.array(CaptionSchema).default([]),
});

export const SchemaShortTimeline = z.object({
  duracao_frames: z.number().int().positive(),
  audio: z.string().default(""),
  cenas: z.array(
    z.object({
      id: z.string().min(1),
      inicio_frame: z.number().int().min(0),
      duracao_frames: z.number().int().positive(),
      props: SchemaShortVertical,
    }),
  ).min(1),
});

export type PropsShortVerticalSchema = z.infer<typeof SchemaShortVertical>;
export type PropsShortTimelineSchema = z.infer<typeof SchemaShortTimeline>;
