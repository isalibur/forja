import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  Layers,
  Loader2,
  PlaySquare,
  ShieldAlert,
} from "lucide-react";
import { ErroCarregamento } from "../components/ErroCarregamento";

interface EtapaInfo {
  id: string;
  status: "pendente" | "executando" | "concluida" | "falhou" | "pausada_revisao";
  duracao_s?: number;
  erro?: string;
}

interface ProducaoDados {
  slug: string;
  em_producao: boolean;
  concluida: boolean;
  progresso_percent: number;
  etapa_ativa: string | null;
  tempo_restante_min: number;
  etapas: EtapaInfo[];
  gpu_status: {
    ocupada: boolean;
    tarefa_atual: string | null;
    projeto_atual: string | null;
  };
}

const ETAPAS_LABELS: Record<string, { nome: string; descricao: string }> = {
  REVISAO: { nome: "Portão de Revisão", descricao: "Aprovação humana e confirmação de licenças" },
  R1_imagens: { nome: "Geração de Imagens", descricao: "Geração visual ComfyUI e consolidação de ativos" },
  R2_tratamento: { nome: "Tratamento Visual", descricao: "Recorte BiRefNet e mapa de profundidade DepthFlow" },
  R3_mapas: { nome: "Mapas Cartográficos", descricao: "Renderização de itinerários e camadas OpenStreetMap" },
  R4_trilha_sfx: { nome: "Trilha & SFX", descricao: "Sound design documental, biblioteca CLAP e mix SFX" },
  R5_montagem: { nome: "Montagem da Timeline", descricao: "Sincronização dos shots e exportação OTIO para DaVinci" },
  R6_mix: { nome: "Mixagem de Áudio", descricao: "Sidechain ducking sob narração a -14 LUFS integrados" },
  R7_render: { nome: "Renderização de Vídeo", descricao: "Composição Remotion por bloco e mux H.264/AAC" },
  R8_qa: { nome: "Garantia de Qualidade", descricao: "Checagem de safe area, blackdetect e ebur128" },
  R9_pacote: { nome: "Empacotamento de Saída", descricao: "Organização completa da árvore 05_saida e metadados" },
  R10_biblioteca: { nome: "Biblioteca Global", descricao: "Avaliação de ativos elegíveis para promoção global" },
};

export const Producao: React.FC<{
  slug: string;
  onNavegar: (tela: string) => void;
}> = ({ slug, onNavegar }) => {
  const [detalhesAbertos, setDetalhesAbertos] = useState(false);

  const { data, isLoading, error, refetch } = useQuery<ProducaoDados>({
    queryKey: ["producao", slug],
    queryFn: async () => {
      const res = await fetch(`/api/projetos/${encodeURIComponent(slug)}/producao`);
      if (!res.ok) throw new Error("Falha ao carregar estado da produção.");
      return res.json();
    },
    enabled: Boolean(slug),
    refetchInterval: 3000,
  });

  if (!slug) {
    return (
      <div className="p-8 text-mut text-center max-w-lg mx-auto py-24">
        Selecione um projeto em Início para acompanhar a produção.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-8 text-mut flex items-center justify-center gap-3 py-24">
        <Loader2 className="w-5 h-5 animate-spin text-brasa" />
        Carregando acompanhamento de produção…
      </div>
    );
  }

  if (error || !data) {
    return <ErroCarregamento tentarNovamente={() => { void refetch(); }} />;
  }

  const etapasChave = Object.keys(ETAPAS_LABELS);
  const mapaStatus = new Map(data.etapas.map((e) => [e.id, e]));
  const etapaFalhou = data.etapas.find((e) => e.status === "falhou");

  return (
    <div className="p-6 xl:p-8 max-w-[1200px] mx-auto space-y-8 animate-in fade-in-50">
      {/* Cabeçalho */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-brasa">Projeto · Produção Local</p>
          <h1 className="text-2xl font-bold mt-1">{slug}</h1>
          <p className="text-sm text-mut mt-1">
            Renderização em 1080p, áudio a -14 LUFS e empacotamento completo (Marco M6)
          </p>
        </div>

        {/* Pílula de GPU */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-line bg-elev text-xs text-mut">
          <Cpu className={`w-4 h-4 ${data.gpu_status?.ocupada ? "text-brasa animate-pulse" : "text-ok"}`} />
          <span>
            {data.gpu_status?.ocupada
              ? `GPU ativa: ${data.gpu_status.tarefa_atual || "processamento"}`
              : "GPU disponível"}
          </span>
        </div>
      </div>

      {/* Cartão Principal: Progresso e Tempo Restante */}
      <div className="rounded-card border border-line bg-surf p-8 shadow-sm">
        <div className="flex flex-col md:flex-row items-center gap-8 justify-between">
          <div className="space-y-3 max-w-md text-center md:text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-brasa/15 text-brasa">
              <PlaySquare className="w-3.5 h-3.5" />
              {data.concluida ? "Produção Concluída" : data.em_producao ? "Processando localmente" : "Aguardando"}
            </div>
            <h2 className="text-3xl font-extrabold text-tx tracking-tight">
              {data.progresso_percent}% concluído
            </h2>
            <p className="text-sm text-mut">
              {data.concluida ? (
                "Todos os módulos e o pacote de entrega foram finalizados com sucesso."
              ) : (
                <>
                  Tempo restante estimado: <strong>~{data.tempo_restante_min} min</strong>.
                  <span className="block mt-1 text-xs">
                    Pode fechar esta janela a qualquer momento; o processamento continuará em segundo plano.
                  </span>
                </>
              )}
            </p>
          </div>

          {/* Anel Visual de Progresso */}
          <div className="flex flex-col items-center gap-3">
            <div className="relative w-32 h-32 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  className="stroke-elev"
                  strokeWidth="8"
                  fill="transparent"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  className="stroke-brasa transition-all duration-700 ease-out"
                  strokeWidth="8"
                  strokeDasharray={264}
                  strokeDashoffset={264 - (264 * data.progresso_percent) / 100}
                  strokeLinecap="round"
                  fill="transparent"
                />
              </svg>
              <span className="absolute font-mono font-bold text-xl text-tx">
                {data.progresso_percent}%
              </span>
            </div>

            {data.concluida && (
              <button
                onClick={() => onNavegar("resultado")}
                className="flex items-center gap-2 rounded-btn bg-ok px-5 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-emerald-600 transition-colors cursor-pointer"
              >
                Ver Resultado Final
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Barra de Progresso Horizontal Contínua */}
        <div className="mt-8 pt-6 border-t border-line">
          <div className="h-2 rounded-full bg-elev overflow-hidden">
            <div
              className="h-full bg-brasa transition-all duration-500 ease-out"
              style={{ width: `${Math.max(2, data.progresso_percent)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Alerta de Falha se Houver */}
      {etapaFalhou && (
        <div className="rounded-card border border-rose-500/40 bg-rose-500/10 p-4 flex items-start gap-3 text-sm">
          <ShieldAlert className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h3 className="font-semibold text-rose-400">
              Falha na etapa {etapaFalhou.id}
            </h3>
            <p className="text-xs text-mut font-mono">
              {etapaFalhou.erro || "Verifique os logs detalhados abaixo."}
            </p>
          </div>
        </div>
      )}

      {/* Linha das Etapas de Produção */}
      <div className="rounded-card border border-line bg-surf p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-brasa" />
            <h2 className="font-semibold text-tx">Pipeline de Produção (Marco M6)</h2>
          </div>
          <span className="text-xs text-mut">
            {data.etapas.filter((e) => e.status === "concluida").length} de {etapasChave.length} etapas
          </span>
        </div>

        <div className="divide-y divide-line">
          {etapasChave.map((etapaId) => {
            const etapa = mapaStatus.get(etapaId);
            const status = etapa?.status || "pendente";
            const info = ETAPAS_LABELS[etapaId];

            return (
              <div
                key={etapaId}
                className="py-3.5 flex items-center justify-between gap-4 transition-colors hover:bg-elev/30 px-2 rounded-btn"
              >
                <div className="flex items-center gap-3 min-w-0">
                  {status === "concluida" && (
                    <CheckCircle2 className="w-5 h-5 text-ok shrink-0" />
                  )}
                  {status === "executando" && (
                    <Loader2 className="w-5 h-5 text-brasa animate-spin shrink-0" />
                  )}
                  {status === "falhou" && (
                    <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
                  )}
                  {status === "pendente" && (
                    <div className="w-5 h-5 rounded-full border-2 border-line shrink-0" />
                  )}
                  {status === "pausada_revisao" && (
                    <div className="w-5 h-5 rounded-full bg-warn/30 border border-warn shrink-0" />
                  )}

                  <div className="min-w-0">
                    <p className={`text-sm font-medium ${status === "executando" ? "text-brasa font-semibold" : "text-tx"}`}>
                      {etapaId} · {info.nome}
                    </p>
                    <p className="text-xs text-mut truncate">{info.descricao}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 text-xs font-mono">
                  {etapa?.duracao_s != null && (
                    <span className="text-mut">{etapa.duracao_s.toFixed(1)} s</span>
                  )}
                  <span
                    className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                      status === "concluida"
                        ? "bg-ok/15 text-ok"
                        : status === "executando"
                        ? "bg-brasa/15 text-brasa font-bold animate-pulse"
                        : status === "falhou"
                        ? "bg-rose-500/15 text-rose-400"
                        : "bg-elev text-mut"
                    }`}
                  >
                    {status}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detalhes Técnicos Recolhidos */}
      <div className="rounded-card border border-line bg-surf overflow-hidden">
        <button
          onClick={() => setDetalhesAbertos((aberto) => !aberto)}
          className="w-full p-4 flex items-center justify-between text-sm text-mut hover:text-tx transition-colors cursor-pointer"
        >
          <span className="font-medium">Detalhes Técnicos e Telemetria</span>
          {detalhesAbertos ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {detalhesAbertos && (
          <div className="p-4 border-t border-line bg-elev/30 space-y-3 font-mono text-xs text-mut">
            <div>
              <span className="text-tx font-bold block mb-1">Registros de Banco de Dados:</span>
              <pre className="p-3 bg-bg rounded-btn border border-line overflow-x-auto text-[11px]">
                {JSON.stringify(data.etapas, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
