import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export interface EventoPayload {
  projeto: string;
  tipo: string;
  etapa_id?: string;
  subetapa_id?: string;
  dados?: Record<string, unknown>;
  timestamp: string;
}

export function useEventosSSE(onEvento?: (evento: EventoPayload) => void) {
  const queryClient = useQueryClient();

  useEffect(() => {
    const sse = new EventSource("/api/eventos");

    sse.onmessage = (event) => {
      try {
        const payload: EventoPayload = JSON.parse(event.data);
        if (onEvento) {
          onEvento(payload);
        }

        // Invalida queries pertinentes quando houver mudança de estado
        if (payload.tipo === "gpu_status") {
          queryClient.invalidateQueries({ queryKey: ["saude"] });
        } else if (payload.tipo.startsWith("etapa_")) {
          queryClient.invalidateQueries({ queryKey: ["projetos"] });
          queryClient.invalidateQueries({ queryKey: ["projeto", payload.projeto] });

          if (payload.tipo === "etapa_concluida") {
            toast.success(`Etapa ${payload.etapa_id} concluída`);
          } else if (payload.tipo === "etapa_falhou") {
            toast.error(`Falha na etapa ${payload.etapa_id}`);
          }
        }
      } catch (err) {
        console.error("Erro ao decodificar evento SSE:", err);
      }
    };

    sse.onerror = () => {
      // Reconexão automática pelo navegador
    };

    return () => {
      sse.close();
    };
  }, [queryClient, onEvento]);
}
