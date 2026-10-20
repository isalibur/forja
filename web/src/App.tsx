import React, { useEffect, useState } from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { Sidebar } from "./components/layout/Sidebar";
import { Header } from "./components/layout/Header";
import { CommandPalette } from "./components/CommandPalette";
import { Inicio } from "./pages/Inicio";
import { Criar } from "./pages/Criar";
import { useEventosSSE } from "./hooks/useEventosSSE";

const Plano = React.lazy(() => import("./pages/Plano").then((modulo) => ({ default: modulo.Plano })));
const Ativos = React.lazy(() => import("./pages/Ativos").then((modulo) => ({ default: modulo.Ativos })));
const ListaBusca = React.lazy(() => import("./pages/ListaBusca").then((modulo) => ({ default: modulo.ListaBusca })));

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
  const [projetoAtivo, setProjetoAtivo] = useState<string>("");
  const [commandOpen, setCommandOpen] = useState<boolean>(false);
  const { data: projetos } = useQuery<{ slug: string }[]>({
    queryKey: ["projetos"],
    queryFn: async () => {
      const resposta = await fetch("/api/projetos");
      if (!resposta.ok) return [];
      return resposta.json();
    },
  });

  useEffect(() => {
    if (!projetoAtivo && projetos?.[0]?.slug) setProjetoAtivo(projetos[0].slug);
  }, [projetoAtivo, projetos]);

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
          <React.Suspense fallback={<div className="p-8 text-mut">Abrindo tela…</div>}>
          {telaAtiva === "inicio" && <Inicio onNavegar={setTelaAtiva} onSelecionarProjeto={setProjetoAtivo} />}
          {telaAtiva === "criar" && (
            <Criar
              onNavegar={setTelaAtiva}
              onProjetoCriado={(slug) => setProjetoAtivo(slug)}
            />
          )}
          {telaAtiva === "plano" && <Plano slug={projetoAtivo} onNavegar={setTelaAtiva} />}
          {telaAtiva === "ativos" && <Ativos slug={projetoAtivo} onNavegar={setTelaAtiva} />}
          {telaAtiva === "busca" && <ListaBusca slug={projetoAtivo} />}
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
          </React.Suspense>
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
