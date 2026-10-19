import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Video,
  Smartphone,
  Music,
  ArrowRight,
  HardDrive,
  Cpu,
  Clock,
} from "lucide-react";

interface InicioProps {
  onNavegar: (tela: string) => void;
}

export const Inicio: React.FC<InicioProps> = ({ onNavegar }) => {
  const { data: projetos, isLoading } = useQuery({
    queryKey: ["projetos"],
    queryFn: async () => {
      const res = await fetch("/api/projetos");
      if (!res.ok) return [];
      return res.json();
    },
  });

  const { data: saude } = useQuery({
    queryKey: ["saude"],
    queryFn: async () => {
      const res = await fetch("/api/saude");
      if (!res.ok) return null;
      return res.json();
    },
  });

  return (
    <div className="p-8 max-w-[1400px] mx-auto space-y-8 animate-in fade-in duration-200">
      {/* Header Boas-vindas */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-tx">
          Boa tarde, Gabriel
        </h1>
        <p className="text-mut mt-1">
          Você tem{" "}
          <strong className="text-warn font-semibold">
            {projetos?.length || 1} projeto(s)
          </strong>{" "}
          no seu workspace local.
        </p>
      </div>

      {/* Cartão de Projeto em Destaque ("Continuar de onde parou") */}
      <div className="bg-surf border border-line rounded-card p-6 flex flex-col md:flex-row items-start md:items-center gap-6 shadow-xl relative overflow-hidden">
        <div className="w-40 h-24 rounded-lg bg-gradient-to-tr from-stone-900 to-amber-950/60 border border-line flex items-center justify-center shrink-0">
          <Video className="w-8 h-8 text-brasa" />
        </div>

        <div className="space-y-1.5 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs px-2 py-0.5 rounded bg-brasa/10 text-brasa font-medium">
              Vídeo Longo
            </span>
            <span className="text-xs text-mut font-mono">Kit Cinza e Brasa</span>
          </div>
          <h2 className="text-lg font-bold text-tx">
            Vesúvio: 24 Horas que Mudaram a História
          </h2>
          <p className="text-sm text-mut">
            Etapa atual: <strong className="text-tx">P8_estimativa_previa</strong> · 116 segmentos analisados
          </p>

          {/* Barra de Progresso */}
          <div className="w-full bg-line rounded-full h-2 mt-3 overflow-hidden">
            <div className="bg-brasa h-2 rounded-full w-[65%]" />
          </div>
        </div>

        <div className="shrink-0 flex items-center gap-3">
          <button
            onClick={() => onNavegar("plano")}
            className="px-4 py-2 rounded-btn bg-brasa hover:bg-orange-600 text-white font-medium text-sm flex items-center gap-2 transition-colors cursor-pointer shadow-lg shadow-brasa/20"
          >
            <span>Revisar plano</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Seção Criar Rápido */}
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-500 mb-3">
          Criar Rápido
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => onNavegar("criar")}
            className="p-5 rounded-card bg-surf border border-line hover:border-brasa/50 text-left transition-all hover:-translate-y-0.5 group cursor-pointer"
          >
            <div className="w-10 h-10 rounded-lg bg-brasa/10 text-brasa grid place-items-center mb-3 group-hover:scale-105 transition-transform">
              <Video className="w-5 h-5" />
            </div>
            <h4 className="font-semibold text-tx">Vídeo longo</h4>
            <p className="text-xs text-mut mt-1">
              Documentário com roteiro, narração multi-idioma e kits completos.
            </p>
          </button>

          <button
            onClick={() => onNavegar("criar")}
            className="p-5 rounded-card bg-surf border border-line hover:border-info/50 text-left transition-all hover:-translate-y-0.5 group cursor-pointer"
          >
            <div className="w-10 h-10 rounded-lg bg-info/10 text-info grid place-items-center mb-3 group-hover:scale-105 transition-transform">
              <Smartphone className="w-5 h-5" />
            </div>
            <h4 className="font-semibold text-tx">Short avulso ou em lote</h4>
            <p className="text-xs text-mut mt-1">
              Formato vertical 9:16 para YouTube Shorts, Reels e TikTok.
            </p>
          </button>

          <button
            onClick={() => onNavegar("criar")}
            className="p-5 rounded-card bg-surf border border-line hover:border-purple-500/50 text-left transition-all hover:-translate-y-0.5 group cursor-pointer"
          >
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 text-purple-400 grid place-items-center mb-3 group-hover:scale-105 transition-transform">
              <Music className="w-5 h-5" />
            </div>
            <h4 className="font-semibold text-tx">Canal de música</h4>
            <p className="text-xs text-mut mt-1">
              Vídeos de 1 h com loops visuais animados e ficha de direitos.
            </p>
          </button>
        </div>
      </div>

      {/* Grid: Saúde do Sistema & Projetos Recentes */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Saúde do Sistema */}
        <div className="bg-surf border border-line rounded-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-tx text-sm flex items-center gap-2">
              <Cpu className="w-4 h-4 text-zinc-400" />
              Saúde do Sistema
            </h3>
            <span className="text-[11px] px-2 py-0.5 rounded bg-ok/10 text-ok font-medium">
              100% Operacional
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-1.5 border-b border-line/50">
              <span className="text-mut">GPU / VRAM</span>
              <span className="font-mono text-tx font-medium">
                RTX 3060 · 12 GB
              </span>
            </div>
            <div className="flex items-center justify-between py-1.5 border-b border-line/50">
              <span className="text-mut">Serviços Ativos</span>
              <span className="text-tx flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-ok" />
                ComfyUI · Ollama · 9Router
              </span>
            </div>
            <div className="flex items-center justify-between py-1.5 border-b border-line/50">
              <span className="text-mut">Espaço em Disco</span>
              <span className="font-mono text-tx font-medium flex items-center gap-1">
                <HardDrive className="w-3.5 h-3.5 text-zinc-400" />
                &gt; 200 GB livres em E:
              </span>
            </div>
            <div className="flex items-center justify-between py-1.5">
              <span className="text-mut">Cota 9Router Hoje</span>
              <span className="font-mono text-tx">
                {saude?.cotas?.requisicoes?.openai_compat || 0} / 500 req
              </span>
            </div>
          </div>
        </div>

        {/* Projetos Existentes */}
        <div className="lg:col-span-2 bg-surf border border-line rounded-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-tx text-sm flex items-center gap-2">
              <Clock className="w-4 h-4 text-zinc-400" />
              Projetos no Workspace
            </h3>
            <span className="text-xs text-mut">
              {projetos?.length || 0} cadastrado(s)
            </span>
          </div>

          <div className="divide-y divide-line/40">
            {isLoading ? (
              <p className="text-xs text-mut py-4 text-center">Carregando projetos…</p>
            ) : projetos && projetos.length > 0 ? (
              projetos.map((proj: any) => (
                <div
                  key={proj.slug}
                  className="py-3 flex items-center justify-between hover:bg-elev/40 px-2 rounded transition-colors"
                >
                  <div>
                    <h4 className="text-sm font-medium text-tx">{proj.nome}</h4>
                    <p className="text-xs text-mut font-mono mt-0.5">
                      {proj.tipo} · {proj.etapa_atual}
                    </p>
                  </div>
                  <button
                    onClick={() => onNavegar("plano")}
                    className="p-1.5 rounded-btn hover:bg-elev text-mut hover:text-tx transition-colors cursor-pointer"
                    title="Ver projeto"
                  >
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              ))
            ) : (
              <div className="py-6 text-center text-xs text-mut">
                Nenhum projeto encontrado. Clique em "Criar" para começar!
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
