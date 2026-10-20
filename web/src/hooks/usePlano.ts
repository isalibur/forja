import { useQuery } from "@tanstack/react-query";

export type Shot = {
  id: string;
  segmentos: string[];
  inicio_s: number | null;
  fim_s: number | null;
  duracao_s: number;
  template: string;
  textos: string[];
  ativos: string[];
  motivo?: string | null;
};

export type Ativo = {
  id: string;
  descricao: string;
  origem: string;
  caminho?: string | null;
  licenca?: Record<string, unknown> | null;
  imagem_url?: string | null;
  licenca_previa?: string | null;
  credito_imagem?: CreditoImagem | null;
  candidatas?: (CreditoImagem & { nome: string; imagem_url: string })[];
  candidata_selecionada?: string | null;
  usado_em: string[];
  nome_arquivo?: string | null;
};

export type CreditoImagem = {
  autor?: string | null;
  licenca: string;
  credito?: string | null;
  fonte?: string | null;
  nota?: number | null;
  motivo?: string | null;
};

export type Pedido = {
  id: string;
  descricao: string;
  motivo?: string | null;
  busca: { termos?: string[]; sites?: string[] };
  nome_arquivo: string;
  plano_b?: string | null;
  usado_em: string[];
  recebido: boolean;
  resolvido: boolean;
};

export type ItemPrevia = {
  id: string;
  template: string;
  inicio_frame: number;
  fim_frame: number;
  bloco: string;
  descricao: string;
  texto: string;
  situacao: string;
};

export type DadosPlano = {
  pronto: boolean;
  slug: string;
  plano?: {
    projeto: string;
    orcamento_producao_min: number;
    estimativa_producao_min: number;
    blocos: { id: string; titulo: string; shots: Shot[] }[];
  };
  ativos?: Record<string, Ativo>;
  pedidos?: Pedido[];
  verificacao?: { aprovado: boolean; total_violacoes: number; violacoes_corrigidas: number };
  manifesto?: {
    titulo: string;
    shots: ItemPrevia[];
    cartoes: ItemPrevia[];
    duracao_frames: number;
  } | null;
  pasta_manual?: string;
  imagens_por_shot?: Record<string, string>;
  hash_resolvidos?: string | null;
  previa_mp4_desatualizada?: boolean;
};

export function usePlano(slug: string) {
  return useQuery<DadosPlano>({
    queryKey: ["plano", slug],
    enabled: Boolean(slug),
    refetchInterval: 5000,
    queryFn: async () => {
      const resposta = await fetch(`/api/projetos/${encodeURIComponent(slug)}/plano`);
      if (!resposta.ok) throw new Error("Não foi possível carregar o plano deste projeto.");
      return resposta.json();
    },
  });
}
