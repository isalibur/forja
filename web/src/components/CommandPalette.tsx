import React, { useEffect } from "react";
import { Command } from "cmdk";
import { Search, PlusCircle, LayoutTemplate, PlaySquare, Home, Sparkles } from "lucide-react";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onNavegar: (tela: string) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  open,
  onOpenChange,
  onNavegar,
}) => {
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        onOpenChange(!open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-start justify-center pt-24 p-4 animate-in fade-in duration-150">
      <div
        className="w-full max-w-lg bg-surf border border-line rounded-card shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <Command label="Comandos globais" className="w-full">
          <div className="flex items-center px-4 border-b border-line">
            <Search className="w-4 h-4 text-mut mr-3" />
            <Command.Input
              placeholder="Digite um comando ou busque projetos…"
              className="w-full bg-transparent py-3 text-sm text-tx outline-none placeholder:text-mut"
              autoFocus
            />
          </div>

          <Command.List className="max-h-72 overflow-y-auto p-2 space-y-1">
            <Command.Empty className="p-4 text-center text-xs text-mut">
              Nenhum resultado encontrado.
            </Command.Empty>

            <Command.Group heading="Navegação" className="text-[11px] font-semibold text-zinc-500 uppercase px-2 py-1">
              <Command.Item
                onSelect={() => {
                  onNavegar("inicio");
                  onOpenChange(false);
                }}
                className="flex items-center gap-3 px-3 py-2 text-sm text-mut rounded-btn hover:bg-elev hover:text-tx cursor-pointer aria-selected:bg-elev aria-selected:text-tx"
              >
                <Home className="w-4 h-4 text-zinc-400" />
                <span>Ir para Início</span>
              </Command.Item>

              <Command.Item
                onSelect={() => {
                  onNavegar("criar");
                  onOpenChange(false);
                }}
                className="flex items-center gap-3 px-3 py-2 text-sm text-mut rounded-btn hover:bg-elev hover:text-tx cursor-pointer aria-selected:bg-elev aria-selected:text-tx"
              >
                <PlusCircle className="w-4 h-4 text-brasa" />
                <span>Criar Novo Projeto</span>
              </Command.Item>
            </Command.Group>

            <Command.Group heading="Projeto Vesúvio" className="text-[11px] font-semibold text-zinc-500 uppercase px-2 py-1">
              <Command.Item
                onSelect={() => {
                  onNavegar("plano");
                  onOpenChange(false);
                }}
                className="flex items-center gap-3 px-3 py-2 text-sm text-mut rounded-btn hover:bg-elev hover:text-tx cursor-pointer aria-selected:bg-elev aria-selected:text-tx"
              >
                <LayoutTemplate className="w-4 h-4 text-zinc-400" />
                <span>Abrir Plano do Vídeo</span>
              </Command.Item>

              <Command.Item
                onSelect={() => {
                  onNavegar("producao");
                  onOpenChange(false);
                }}
                className="flex items-center gap-3 px-3 py-2 text-sm text-mut rounded-btn hover:bg-elev hover:text-tx cursor-pointer aria-selected:bg-elev aria-selected:text-tx"
              >
                <PlaySquare className="w-4 h-4 text-zinc-400" />
                <span>Acompanhar Produção</span>
              </Command.Item>
            </Command.Group>

            <Command.Group heading="Ações Rápidas" className="text-[11px] font-semibold text-zinc-500 uppercase px-2 py-1">
              <Command.Item
                onSelect={() => {
                  window.location.reload();
                }}
                className="flex items-center gap-3 px-3 py-2 text-sm text-mut rounded-btn hover:bg-elev hover:text-tx cursor-pointer aria-selected:bg-elev aria-selected:text-tx"
              >
                <Sparkles className="w-4 h-4 text-info" />
                <span>Atualizar Dados e Conexão SSE</span>
              </Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </div>

      <div className="fixed inset-0 -z-10" onClick={() => onOpenChange(false)} />
    </div>
  );
};
