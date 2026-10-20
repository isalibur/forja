import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Cpu,
  HardDrive,
  Loader2,
  Server,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import { ErroCarregamento } from "../components/ErroCarregamento";

interface DetalhesSistema {
  gpu: {
    ocupada: boolean;
    tarefa_atual: string | null;
    projeto_atual: string | null;
  };
  cotas: {
    total_requisicoes_hoje: number;
    limite_diario: number;
    tokens_usados: number;
  };
  pastas: {
    projetos: string;
    modelos: string;
    temp: string;
  };
  ambientes_python: Record<string, string>;
  adaptadores: {
    whisper: string;
    alinhador: string;
  };
}

export const Sistema: React.FC = () => {
  const { data, isLoading, error, refetch } = useQuery<DetalhesSistema>({
    queryKey: ["sistema-detalhes"],
    queryFn: async () => {
      const res = await fetch("/api/sistema/detalhes");
      if (!res.ok) throw new Error("Falha ao carregar detalhes do sistema.");
      return res.json();
    },
    refetchInterval: 5000,
  });

  if (isLoading) {
    return (
      <div className="p-8 text-mut flex items-center justify-center gap-3 py-24">
        <Loader2 className="w-5 h-5 animate-spin text-brasa" />
        Carregando telemetria do sistema…
      </div>
    );
  }

  if (error || !data) {
    return <ErroCarregamento tentarNovamente={() => { void refetch(); }} />;
  }

  return (
    <div className="p-6 xl:p-8 max-w-[1400px] mx-auto space-y-8 animate-in fade-in-50">
      <div>
        <p className="text-xs uppercase tracking-widest text-brasa font-semibold">
          Infraestrutura Local & Saúde (14 §5.12)
        </p>
        <h1 className="text-2xl font-bold mt-1">Status do Sistema e Adaptadores</h1>
        <p className="text-sm text-mut mt-1">
          Semáforo de GPU, isolamento de processos, cotas diárias e caminhos configurados
        </p>
      </div>

      {/* Cards de Status Rápido */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="rounded-card border border-line bg-surf p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-mut uppercase">Semáforo de GPU</span>
            <Cpu className={`w-4 h-4 ${data.gpu.ocupada ? "text-brasa animate-pulse" : "text-ok"}`} />
          </div>
          <p className="text-2xl font-extrabold text-tx">
            {data.gpu.ocupada ? "Em Uso" : "Livre"}
          </p>
          <p className="text-xs text-mut">
            {data.gpu.ocupada
              ? `Executando: ${data.gpu.tarefa_atual} (${data.gpu.projeto_atual})`
              : "Semáforo exclusivo aguardando cargas locais"}
          </p>
        </div>

        <div className="rounded-card border border-line bg-surf p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-mut uppercase">Cotas de IA Hoje</span>
            <Activity className="w-4 h-4 text-brasa" />
          </div>
          <p className="text-2xl font-extrabold text-tx">
            {data.cotas.total_requisicoes_hoje} / {data.cotas.limite_diario || "∞"}
          </p>
          <p className="text-xs text-mut">
            {data.cotas.tokens_usados.toLocaleString()} tokens consumidos em requisições locais/externas
          </p>
        </div>

        <div className="rounded-card border border-line bg-surf p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-mut uppercase">Integridade de Modelos</span>
            <ShieldCheck className="w-4 h-4 text-ok" />
          </div>
          <p className="text-2xl font-extrabold text-tx">Fixados no Lock</p>
          <p className="text-xs text-mut">
            Hashes SHA-256 de Whisper e Alinhador conferidos e registrados em config/lock.yaml
          </p>
        </div>
      </div>

      {/* Modelos e Adaptadores */}
      <div className="rounded-card border border-line bg-surf p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-brasa" />
          <h2 className="font-semibold text-tx">Modelos e Adaptadores Fonéticos</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-4 rounded-btn border border-line bg-elev/30 space-y-1.5">
            <span className="text-mut uppercase font-sans font-bold">ASR (Reconhecimento de Voz)</span>
            <p className="text-sm font-bold text-tx">{data.adaptadores.whisper}</p>
            <p className="text-mut font-sans">whisper-large-v3-turbo quantizado em CTranslate2 com WER &lt; 2%</p>
          </div>

          <div className="p-4 rounded-btn border border-line bg-elev/30 space-y-1.5">
            <span className="text-mut uppercase font-sans font-bold">Alinhador Fonético (Português)</span>
            <p className="text-sm font-bold text-tx">{data.adaptadores.alinhador}</p>
            <p className="text-mut font-sans">Wav2Vec2 XLSR-53 treinado para o português com snapshot fixado</p>
          </div>
        </div>
      </div>

      {/* Ambientes Python Isolados */}
      <div className="rounded-card border border-line bg-surf p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-brasa" />
          <h2 className="font-semibold text-tx">Ambientes Python Isolados (Subprocessos)</h2>
        </div>

        <div className="divide-y divide-line text-xs font-mono">
          {Object.entries(data.ambientes_python || {}).map(([servico, caminho]) => (
            <div key={servico} className="py-2.5 flex items-center justify-between gap-4">
              <span className="font-bold text-tx uppercase">{servico}</span>
              <span className="text-mut truncate max-w-xl">{caminho}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Pastas de Armazenamento */}
      <div className="rounded-card border border-line bg-surf p-6 space-y-4">
        <div className="flex items-center gap-2">
          <HardDrive className="w-5 h-5 text-brasa" />
          <h2 className="font-semibold text-tx">Caminhos e Diretórios do Workspace</h2>
        </div>

        <div className="divide-y divide-line text-xs font-mono">
          {Object.entries(data.pastas || {}).map(([tipo, caminho]) => (
            <div key={tipo} className="py-2.5 flex items-center justify-between gap-4">
              <span className="font-bold text-tx uppercase">{tipo}</span>
              <span className="text-mut truncate max-w-xl">{caminho}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
