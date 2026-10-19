import { z } from "zod";

export const SchemaO1Identificacao = z.object({
  nome: z.string().min(1),
  descricao: z.string().optional(),
});

export const SchemaO2Rotulo = z.object({
  tipo: z.enum(["reconstituicao", "credito", "outro_vulcao"]).default("reconstituicao"),
  texto: z.string().optional(),
});

export const SchemaO3Contexto = z.object({
  dia: z.number().int().min(1).max(2).default(1),
  hora: z.string().default("13:00"),
  local: z.string().default("POMPEIA"),
  progresso: z.number().min(0).max(1).default(0.1),
  aproximado: z.boolean().default(true),
});

export const SchemaO4Destaque = z.object({
  tipo: z.enum(["seta", "circulo", "caixa"]).default("circulo"),
  posicao: z.object({
    x: z.number().min(0).max(100),
    y: z.number().min(0).max(100),
  }),
  tamanho: z.number().optional().default(120),
  rotulo: z.string().optional(),
});

export type PropsO1Identificacao = z.infer<typeof SchemaO1Identificacao>;
export type PropsO2Rotulo = z.infer<typeof SchemaO2Rotulo>;
export type PropsO3Contexto = z.infer<typeof SchemaO3Contexto>;
export type PropsO4Destaque = z.infer<typeof SchemaO4Destaque>;
