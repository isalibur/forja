import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { Sidebar } from "./components/layout/Sidebar";
import { Header } from "./components/layout/Header";
import { CommandPalette } from "./components/CommandPalette";
import { Inicio } from "./pages/Inicio";
import { Criar } from "./pages/Criar";
import { useEventosSSE } from "./hooks/useEventosSSE";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 1,
    },
  },
});

const AppContent: React.FC = () => {
  const [telaAtiva, setTelaAtiva] = useState<string>("inicio");
  const [projetoAtivo, setProjetoAtivo] = useState<string>("vesuvio");
  const [commandOpen, setCommandOpen] = useState<boolean>(false);

  // Conecta ao fluxo de eventos SSE do backend
  useEventosSSE();

  return (
    <div className="flex h-screen overflow-hidden bg-bg text-tx font-sans">
      {/* Barra Lateral */}
      <Sidebar
        telaAtiva={telaAtiva}
        onNavegar={setTelaAtiva}
        projetoAtivoSlug={projetoAtivo}
      />

      {/* Conteúdo Principal */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header onOpenCommand={() => setCommandOpen(true)} />

        <main className="flex-1 overflow-y-auto">
          {telaAtiva === "inicio" && <Inicio onNavegar={setTelaAtiva} />}
          {telaAtiva === "criar" && (
            <Criar
              onNavegar={setTelaAtiva}
              onProjetoCriado={(slug) => setProjetoAtivo(slug)}
            />
          )}
          {telaAtiva === "plano" && (
            <div className="p-8 max-w-[1200px] mx-auto text-center py-24 space-y-4">
              <h2 className="text-xl font-bold text-tx">Plano de Vídeo · {projetoAtivo}</h2>
              <p className="text-sm text-mut">
                A visualização detalhada do Plano com prévia ao vivo @remotion/player e tabela de shots está programada para o Marco 5 (M5).
              </p>
              <button
                onClick={() => setTelaAtiva("inicio")}
                className="px-4 py-2 rounded-btn bg-surf border border-line text-xs font-medium text-mut hover:text-tx"
              >
                Voltar para Início
              </button>
            </div>
          )}
          {telaAtiva === "busca" && (
            <div className="p-8 max-w-[1200px] mx-auto text-center py-24 space-y-4">
              <h2 className="text-xl font-bold text-tx">Lista de Busca · {projetoAtivo}</h2>
              <p className="text-sm text-mut">
                A interface com upload de imagens e sugestões da pasta manual integra-se no Marco 5 (M5).
              </p>
            </div>
          )}
          {telaAtiva === "producao" && (
            <div className="p-8 max-w-[1200px] mx-auto text-center py-24 space-y-4">
              <h2 className="text-xl font-bold text-tx">Acompanhamento de Produção · {projetoAtivo}</h2>
              <p className="text-sm text-mut">
                Renderização de vídeo final, tratamento e trilha sonora completos no Marco 6 (M6).
              </p>
            </div>
          )}
          {telaAtiva === "resultado" && (
            <div className="p-8 max-w-[1200px] mx-auto text-center py-24 space-y-4">
              <h2 className="text-xl font-bold text-tx">Resultado Final · {projetoAtivo}</h2>
              <p className="text-sm text-mut">
                Player final por idioma, legendas e pacote estratégico no Marco 6 (M6).
              </p>
            </div>
          )}
        </main>
      </div>

      {/* Paleta de Comandos (Ctrl+K) */}
      <CommandPalette
        open={commandOpen}
        onOpenChange={setCommandOpen}
        onNavegar={setTelaAtiva}
      />

      {/* Notificações discretas Sonner */}
      <Toaster position="bottom-right" theme="dark" richColors />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
};

export default App;
