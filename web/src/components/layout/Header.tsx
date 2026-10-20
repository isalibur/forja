import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Bell, Menu } from "lucide-react";

interface HeaderProps {
  onOpenCommand: () => void;
  onOpenMenu: () => void;
  menuButtonRef: React.RefObject<HTMLButtonElement>;
}

export const Header: React.FC<HeaderProps> = ({ onOpenCommand, onOpenMenu, menuButtonRef }) => {
  const { data: saude } = useQuery({
    queryKey: ["saude"],
    queryFn: async () => {
      const res = await fetch("/api/saude");
      if (!res.ok) throw new Error("Erro ao carregar saúde");
      return res.json();
    },
    refetchInterval: 5000,
  });

  const gpuOcupada = saude?.gpu?.ocupada;
  const modeloGpu = saude?.gpu?.modelo_atual;
  const tarefaGpu = saude?.gpu?.tarefa_atual;

  return (
    <header className="h-14 shrink-0 border-b border-line bg-bg/80 backdrop-blur flex items-center gap-3 px-3 md:px-6 z-10">
      <button ref={menuButtonRef} onClick={onOpenMenu} aria-label="Abrir menu" className="md:hidden w-8 h-8 shrink-0 grid place-items-center rounded-btn text-mut hover:text-tx focus-visible:outline-2 focus-visible:outline-brasa">
        <Menu className="w-5 h-5" />
      </button>
      <button
        onClick={onOpenCommand}
        className="flex min-w-0 flex-1 max-w-80 items-center gap-2 bg-surf border border-line rounded-btn px-3 py-1.5 text-sm text-mut hover:border-zinc-600 transition-colors cursor-pointer text-left"
      >
        <Search className="w-4 h-4 shrink-0" />
        <span className="truncate">Buscar projetos, ativos, ações…</span>
        <span className="hidden lg:inline ml-auto font-mono text-[11px] border border-line rounded px-1 text-mut">
          Ctrl K
        </span>
      </button>

      <div className="ml-auto flex items-center gap-2 text-xs">
        {/* Pílula de GPU */}
        {gpuOcupada ? (
          <span className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-full bg-info/10 text-info border border-info/20 whitespace-nowrap">
            <span className="w-1.5 h-1.5 rounded-full bg-info live" />
            GPU · {tarefaGpu || "processando"} ({modeloGpu || "ativo"})
          </span>
        ) : (
          <span className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-full bg-surf border border-line text-mut whitespace-nowrap">
            <span className="w-1.5 h-1.5 rounded-full bg-ok" />
            GPU · ociosa
          </span>
        )}

        {/* O estado da LLM só aparece quando houver telemetria real. */}

        {/* Notificações */}
        <button
          className="w-8 h-8 grid place-items-center rounded-btn hover:bg-surf text-mut hover:text-tx transition-colors relative"
          title="Notificações"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-brasa" />
        </button>

        {/* Avatar */}
        <div className="hidden lg:grid w-8 h-8 rounded-full bg-gradient-to-br from-zinc-600 to-zinc-800 place-items-center text-[11px] font-semibold text-tx">
          DF
        </div>
      </div>
    </header>
  );
};
