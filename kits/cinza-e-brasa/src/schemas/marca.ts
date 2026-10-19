import { z } from "zod";

export const SchemaMarca = z.object({
  nome: z.string().optional(),
  logo_url: z.string().optional(),
  cor_primaria: z.string().optional(),
  cor_secundaria: z.string().optional(),
  contato: z
    .object({
      telefone: z.string().optional(),
      arroba: z.string().optional(),
      site: z.string().optional(),
    })
    .optional(),
  cartao_final: z
    .object({
      titulo: z.string().optional(),
      chamada: z.string().optional(),
      mostrar_logo: z.boolean().default(true),
    })
    .optional(),
});

export type MarcaProjeto = z.infer<typeof SchemaMarca>;
