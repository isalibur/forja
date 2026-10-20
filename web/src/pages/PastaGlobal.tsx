import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  FileText,
  FolderSync,
  Image as ImageIcon,
  Loader2,
  Map as MapIcon,
  Music,
  Repeat,
  Search,
  Users,
  Volume2,
} from "lucide-react";
import { ErroCarregamento } from "../components/ErroCarregamento";

interface ItemGlobal {
  id: string;
  tipo: string;
  descricao: string;
  licenca: string;
  autor?: string;
  projetos_usados?: string[];
  caminho_arquivo?: string;
}

interface RespostaGlobal {
  categorias: Record<string, ItemGlobal[]>;
  total: number;
}

const CATEGORIAS = [
  { id: "imagens", label: "Imagens", icone: ImageIcon },
  { id: "personagens", label: "Personagens", icone: Users },
  { id: "mapas", label: "Mapas", icone: MapIcon },
  { id: "loops", label: "Loops de Vídeo", icone: Repeat },
  { id: "trilhas", label: "Trilhas Sonoras", icone: Music },
  { id: "sfx", label: "Efeitos Sonoros", icone: Volume2 },
];

export const PastaGlobal: React.FC = () => {
  const [categoriaAtiva, setCategoriaAtiva] = useState<string>("imagens");
  const [busca, setBusca] = useState<string>("");

  const { data, isLoading, error, refetch } = useQuery<RespostaGlobal>({
    queryKey: ["global-itens"],
    queryFn: async () => {
      const res = await fetch("/api/global/itens");
      if (!res.ok) throw new Error("Falha ao carregar itens da pasta global.");
      return res.json();
    },
  });

  if (isLoading) {
    return (
      <div className="p-8 text-mut flex items-center justify-center gap-3 py-24">
        <Loader2 className="w-5 h-5 animate-spin text-brasa" />
        Carregando acervo global…
      </div>
    );
  }

  if (error || !data) {
    return <ErroCarregamento tentarNovamente={() => { void refetch(); }} />;
  }

  const itensCategoria = data.categorias[categoriaAtiva] || [];
  const itensFiltrados = itensCategoria.filter((item) =>
    `${item.id} ${item.descricao} ${item.licenca}`.toLowerCase().includes(busca.toLowerCase())
  );

  return (
    <div className="p-6 xl:p-8 max-w-[1500px] mx-auto space-y-6 animate-in fade-in-50">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-brasa font-semibold">
            Biblioteca · Pasta Global (13 §3)
          </p>
          <h1 className="text-2xl font-bold mt-1">Acervo Reutilizável Multi-Projeto</h1>
          <p className="text-sm text-mut mt-1">
            Ativos licenciados promovidos automaticamente ou manualmente para uso em múltiplos vídeos
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-mut bg-elev px-3 py-1.5 rounded-full border border-line">
          <FolderSync className="w-4 h-4 text-brasa" />
          <span>{data.total} ativos catalogados</span>
        </div>
      </div>

      {/* Abas de Categorias */}
      <div className="flex border-b border-line gap-2 overflow-x-auto pb-px">
        {CATEGORIAS.map((cat) => {
          const Icone = cat.icone;
          const ativa = categoriaAtiva === cat.id;
          const contagem = data.categorias[cat.id]?.length ?? 0;
          return (
            <button
              key={cat.id}
              onClick={() => setCategoriaAtiva(cat.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                ativa
                  ? "border-brasa text-brasa font-semibold"
                  : "border-transparent text-mut hover:text-tx hover:border-line"
              }`}
            >
              <Icone className="w-4 h-4" />
              <span>{cat.label}</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-elev text-mut font-mono">
                {contagem}
              </span>
            </button>
          );
        })}
      </div>

      {/* Barra de Busca */}
      <div className="flex items-center gap-2 rounded-btn border border-line bg-surf px-3 py-2 max-w-md">
        <Search className="w-4 h-4 text-mut" />
        <input
          type="text"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder={`Buscar em ${categoriaAtiva}…`}
          className="bg-transparent text-sm text-tx outline-none w-full"
        />
      </div>

      {/* Grade de Itens */}
      {itensFiltrados.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {itensFiltrados.map((item) => (
            <div
              key={item.id}
              className="rounded-card border border-line bg-surf p-4 space-y-3 flex flex-col justify-between hover:border-brasa/60 transition-colors"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-brasa font-bold">{item.id}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-ok/15 text-ok">
                    {item.licenca}
                  </span>
                </div>
                <p className="text-sm font-medium text-tx line-clamp-2">{item.descricao}</p>
                {item.autor && (
                  <p className="text-xs text-mut">Autor: {item.autor}</p>
                )}
              </div>

              <div className="pt-3 border-t border-line text-xs text-mut flex justify-between items-center">
                <span>Usado em {item.projetos_usados?.length ?? 1} projeto(s)</span>
                <span className="font-mono text-[10px] bg-elev px-1.5 py-0.5 rounded">{item.tipo}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-card border border-line bg-surf p-12 text-center text-mut space-y-2">
          <FileText className="w-8 h-8 mx-auto text-line" />
          <p className="text-sm font-medium">Nenhum ativo encontrado nesta categoria.</p>
          <p className="text-xs">
            Ativos confirmados na aba <strong>Resultado</strong> dos seus projetos aparecerão aqui automaticamente.
          </p>
        </div>
      )}
    </div>
  );
};
