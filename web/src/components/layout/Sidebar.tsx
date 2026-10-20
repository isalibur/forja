import React from "react";
import {
  Home,
  PlusCircle,
  LayoutTemplate,
  Images,
  Search,
  PlaySquare,
  CheckCircle2,
  Smartphone,
  Music,
  FolderSync,
  Palette,
  Flame,
  Settings,
} from "lucide-react";

interface SidebarProps {
  telaAtiva: string;
  onNavegar: (tela: string) => void;
  projetoAtivoSlug?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  telaAtiva,
  onNavegar,
  projetoAtivoSlug = "",
}) => {
  const linkClass = (tela: string) =>
    `flex items-center gap-3 px-3 py-2 rounded-btn cursor-pointer transition-colors ${
      telaAtiva === tela
        ? "bg-elev text-tx font-medium"
        : "text-mut hover:bg-elev hover:text-tx"
    }`;

  return (
    <aside className="w-60 shrink-0 border-r border-line bg-surf flex flex-col h-screen select-none">
      {/* Brand */}
      <div className="h-14 flex items-center gap-2 px-5 border-b border-line">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brasa to-orange-700 grid place-items-center shadow-md">
          <Flame className="w-4 h-4 text-white fill-white" />
        </div>
        <span className="font-semibold tracking-tight text-tx">DocForja</span>
        <span className="ml-auto text-[10px] px-1.5 py-0.5 rounded bg-elev text-mut font-mono">
          v2
        </span>
      </div>

      {/* Nav */}
      <nav className="p-3 space-y-0.5 text-sm overflow-y-auto flex-1">
        <button
          onClick={() => onNavegar("inicio")}
          className={`w-full ${linkClass("inicio")}`}
        >
          <Home className={`w-4 h-4 ${telaAtiva === "inicio" ? "text-brasa" : ""}`} />
          Início
        </button>

        <button
          onClick={() => onNavegar("criar")}
          className={`w-full ${linkClass("criar")}`}
        >
          <PlusCircle className={`w-4 h-4 ${telaAtiva === "criar" ? "text-brasa" : ""}`} />
          Criar
        </button>

        {/* Seção do Projeto Ativo */}
        <div className="pt-4 pb-1 px-3 text-[11px] uppercase tracking-wider text-mut font-semibold">
          Projeto · {projetoAtivoSlug || "selecione um"}
        </div>

        <button
          onClick={() => onNavegar("plano")}
          className={`w-full ${linkClass("plano")}`}
        >
          <LayoutTemplate className={`w-4 h-4 ${telaAtiva === "plano" ? "text-brasa" : ""}`} />
          Plano
        </button>

        <button onClick={() => onNavegar("ativos")} className={`w-full ${linkClass("ativos")}`}>
          <Images className={`w-4 h-4 ${telaAtiva === "ativos" ? "text-brasa" : ""}`} />
          Ativos
        </button>

        <button
          onClick={() => onNavegar("busca")}
          className={`w-full ${linkClass("busca")}`}
        >
          <Search className={`w-4 h-4 ${telaAtiva === "busca" ? "text-brasa" : ""}`} />
          Lista de busca
        </button>

        <button
          onClick={() => onNavegar("producao")}
          className={`w-full ${linkClass("producao")}`}
        >
          <PlaySquare className={`w-4 h-4 ${telaAtiva === "producao" ? "text-brasa" : ""}`} />
          Produção
        </button>

        <button
          onClick={() => onNavegar("resultado")}
          className={`w-full ${linkClass("resultado")}`}
        >
          <CheckCircle2 className={`w-4 h-4 ${telaAtiva === "resultado" ? "text-brasa" : ""}`} />
          Resultado
        </button>

        {/* Seção Biblioteca */}
        <div className="pt-4 pb-1 px-3 text-[11px] uppercase tracking-wider text-mut font-semibold">
          Biblioteca
        </div>

        <button
          onClick={() => onNavegar("shorts")}
          className={`w-full ${linkClass("shorts")}`}
        >
          <Smartphone className={`w-4 h-4 ${telaAtiva === "shorts" ? "text-brasa" : ""}`} />
          Shorts
        </button>

        <button
          onClick={() => onNavegar("musica")}
          className={`w-full ${linkClass("musica")}`}
        >
          <Music className={`w-4 h-4 ${telaAtiva === "musica" ? "text-brasa" : ""}`} />
          Música
        </button>

        <button
          onClick={() => onNavegar("global")}
          className={`w-full ${linkClass("global")}`}
        >
          <FolderSync className={`w-4 h-4 ${telaAtiva === "global" ? "text-brasa" : ""}`} />
          Pasta global
        </button>

        <button
          onClick={() => onNavegar("kits")}
          className={`w-full ${linkClass("kits")}`}
        >
          <Palette className={`w-4 h-4 ${telaAtiva === "kits" ? "text-brasa" : ""}`} />
          Kits
        </button>

        <button
          onClick={() => onNavegar("sistema")}
          className={`w-full ${linkClass("sistema")}`}
        >
          <Settings className={`w-4 h-4 ${telaAtiva === "sistema" ? "text-brasa" : ""}`} />
          Sistema
        </button>
      </nav>

      {/* Footer / Saúde */}
      <div className="p-3 border-t border-line text-xs text-mut bg-surf/80">
        <div className="flex items-center gap-2 px-2">
          <span className="w-2 h-2 rounded-full bg-ok" />
          <span className="font-medium text-tx">DocForja local</span>
        </div>
        <div className="px-2 mt-1 font-mono text-[11px] text-mut">
          Dados locais
        </div>
      </div>
    </aside>
  );
};
