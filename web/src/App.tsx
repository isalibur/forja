import React, { useEffect, useRef, useState } from "react";
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
const Producao = React.lazy(() => import("./pages/Producao").then((modulo) => ({ default: modulo.Producao })));
const Resultado = React.lazy(() => import("./pages/Resultado").then((modulo) => ({ default: modulo.Resultado })));
const PastaGlobal = React.lazy(() => import("./pages/PastaGlobal").then((modulo) => ({ default: modulo.PastaGlobal })));
const Kits = React.lazy(() => import("./pages/Kits").then((modulo) => ({ default: modulo.Kits })));
const Sistema = React.lazy(() => import("./pages/Sistema").then((modulo) => ({ default: modulo.Sistema })));

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
  const [menuMobileAberto, setMenuMobileAberto] = useState(false);
  const [tema, setTema] = useState<"dark" | "light">(() => {
    try { return localStorage.getItem("docforja-tema") === "light" ? "light" : "dark"; }
    catch { return "dark"; }
  });
  const botaoMenu = useRef<HTMLButtonElement>(null);
  const botaoFecharMenu = useRef<HTMLButtonElement>(null);
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

  useEffect(() => {
    document.documentElement.dataset.theme = tema;
    try { localStorage.setItem("docforja-tema", tema); } catch { /* modo privado */ }
  }, [tema]);

  useEffect(() => {
    if (!menuMobileAberto) return;
    botaoFecharMenu.current?.focus();
    const fecharComEscape = (evento: KeyboardEvent) => {
      if (evento.key === "Escape") setMenuMobileAberto(false);
    };
    document.addEventListener("keydown", fecharComEscape);
    return () => {
      document.removeEventListener("keydown", fecharComEscape);
      botaoMenu.current?.focus();
    };
  }, [menuMobileAberto]);

  const conterFocoMenu = (evento: React.KeyboardEvent<HTMLDivElement>) => {
    if (evento.key !== "Tab") return;
    const botoes = Array.from(evento.currentTarget.querySelectorAll<HTMLButtonElement>("button:not([tabindex='-1'])"));
    if (botoes.length === 0) return;
    if (evento.shiftKey && document.activeElement === botoes[0]) {
      evento.preventDefault();
      botoes[botoes.length - 1].focus();
    } else if (!evento.shiftKey && document.activeElement === botoes[botoes.length - 1]) {
      evento.preventDefault();
      botoes[0].focus();
    }
  };

  // Conecta ao fluxo de eventos SSE do backend
  useEventosSSE();

  return (
    <div className="flex h-screen overflow-hidden bg-bg text-tx font-sans">
      {/* Barra Lateral */}
      <div className="hidden md:block"><Sidebar telaAtiva={telaAtiva} onNavegar={setTelaAtiva} projetoAtivoSlug={projetoAtivo} /></div>
      {menuMobileAberto && (
        <div role="dialog" aria-modal="true" aria-label="Menu de navegação" className="fixed inset-0 z-50 md:hidden">
          <button tabIndex={-1} aria-label="Fechar menu" onClick={() => setMenuMobileAberto(false)} className="absolute inset-0 w-full bg-black/70" />
          <div className="relative w-60 h-full" onKeyDown={conterFocoMenu}>
            <button ref={botaoFecharMenu} onClick={() => setMenuMobileAberto(false)} aria-label="Fechar menu" className="absolute top-3 right-3 z-10 w-8 h-8 rounded-btn bg-elev text-tx focus-visible:outline-2 focus-visible:outline-brasa">×</button>
            <Sidebar telaAtiva={telaAtiva} onNavegar={(tela) => { setTelaAtiva(tela); setMenuMobileAberto(false); }} projetoAtivoSlug={projetoAtivo} />
          </div>
        </div>
      )}

      {/* Conteúdo Principal */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header onOpenCommand={() => setCommandOpen(true)} onOpenMenu={() => setMenuMobileAberto(true)} menuButtonRef={botaoMenu} tema={tema} onAlternarTema={() => setTema((atual) => atual === "dark" ? "light" : "dark")} />

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
          {telaAtiva === "producao" && <Producao slug={projetoAtivo} onNavegar={setTelaAtiva} />}
          {telaAtiva === "resultado" && <Resultado slug={projetoAtivo} onNavegar={setTelaAtiva} />}
          {telaAtiva === "global" && <PastaGlobal />}
          {telaAtiva === "kits" && <Kits />}
          {telaAtiva === "sistema" && <Sistema />}
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
      <Toaster position="bottom-right" theme={tema} richColors />
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
