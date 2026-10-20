import React, { useMemo, useRef, useState } from "react";
import { Player, type PlayerRef } from "@remotion/player";
import { AlertTriangle, Film, List, Play, Search } from "lucide-react";
import { PreviaInterativa } from "../components/PreviaInterativa";
import { usePlano, type Shot } from "../hooks/usePlano";

const tempo = (segundos: number) => `${String(Math.floor(segundos / 60)).padStart(2, "0")}:${String(Math.floor(segundos % 60)).padStart(2, "0")}`;

export const Plano: React.FC<{ slug: string; onNavegar: (tela: string) => void }> = ({ slug, onNavegar }) => {
  const { data, isLoading, error } = usePlano(slug);
  const player = useRef<PlayerRef>(null);
  const [selecionado, setSelecionado] = useState<Shot | null>(null);
  const [filtro, setFiltro] = useState("");
  const [limite, setLimite] = useState(50);
  const [visao, setVisao] = useState<"storyboard" | "tabela">("storyboard");
  const shots = useMemo(() => data?.plano?.blocos.flatMap((bloco) => bloco.shots.map((shot) => ({ ...shot, bloco: bloco.titulo }))) ?? [], [data]);
  const filtrados = shots.filter((shot) => `${shot.id} ${shot.template} ${shot.bloco} ${shot.textos.join(" ")}`.toLowerCase().includes(filtro.toLowerCase()));

  if (!slug) return <div className="p-8 text-mut">Selecione um projeto em Início para abrir o plano.</div>;
  if (isLoading) return <div className="p-8 text-mut">Carregando plano…</div>;
  if (error) return <div role="alert" className="p-8 text-err">{(error as Error).message}</div>;
  if (!data?.pronto || !data.plano) return <div className="p-8 max-w-3xl mx-auto"><h1 className="text-2xl font-bold">Plano em preparação</h1><p className="text-mut mt-2">Assim que as etapas de planejamento terminarem, a prévia e os shots aparecerão aqui.</p></div>;

  const manifesto = data.manifesto;
  const estimativa = data.plano.estimativa_producao_min;
  const orcamento = data.plano.orcamento_producao_min;
  return (
    <div className="p-6 xl:p-8 max-w-[1700px] mx-auto space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div><p className="text-xs uppercase tracking-widest text-brasa">Projeto · Plano</p><h1 className="text-2xl font-bold mt-1">{data.plano.projeto}</h1><p className="text-sm text-mut mt-1">{data.plano.blocos.length} blocos · {shots.length} shots · prévia de planejamento</p></div>
        <button onClick={() => onNavegar("busca")} className="rounded-btn bg-warn/15 text-warn px-4 py-2 text-sm font-medium hover:bg-warn/25">{data.pedidos?.filter((item) => !item.recebido).length ?? 0} imagens precisam de você</button>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.65fr)_minmax(290px,1fr)] gap-5">
        <div className="rounded-card border border-line bg-surf overflow-hidden">
          {manifesto ? (
            <Player ref={player} component={PreviaInterativa} inputProps={{ manifesto, imagensPorShot: data.imagens_por_shot ?? {}, audioUrl: `/api/projetos/${encodeURIComponent(slug)}/narracao.wav` }} durationInFrames={manifesto.duracao_frames} compositionWidth={960} compositionHeight={540} fps={24} controls style={{ width: "100%", aspectRatio: "16 / 9" }} />
          ) : <div className="aspect-video flex flex-col items-center justify-center gap-3 text-mut"><Film className="w-9 h-9" /><span>A prévia ficará disponível após P8.</span></div>}
          <div className="p-3 text-xs text-mut border-t border-line">Imagens com licença confirmada aparecem nesta prévia interativa; o MP4 de P8 continua sendo um animatic de planejamento.</div>
        </div>
        <div className="rounded-card border border-line bg-surf p-5 space-y-5">
          <h2 className="font-semibold">Saúde do plano</h2>
          <div className="flex items-center gap-2 text-sm"><span className={`w-2 h-2 rounded-full ${data.verificacao?.aprovado ? "bg-ok" : "bg-warn"}`} />{data.verificacao?.aprovado ? "Dosagem aprovada" : "Verificação pendente"}</div>
          <div><div className="flex justify-between text-sm mb-2"><span className="text-mut">Estimativa de produção</span><strong>{estimativa} / {orcamento} min</strong></div><div className="h-2 rounded-full bg-elev"><div className="h-2 rounded-full bg-brasa" style={{ width: `${Math.min(100, 100 * estimativa / Math.max(1, orcamento))}%` }} /></div></div>
          <div className="text-sm text-mut">{Object.keys(data.ativos ?? {}).length} ativos catalogados · {data.verificacao?.total_violacoes ?? 0} ajustes ou alertas registrados</div>
          <button onClick={() => onNavegar("ativos")} className="text-sm text-brasa hover:underline">Ver ativos e licenças →</button>
        </div>
      </div>
      <div className="rounded-card border border-line bg-surf p-5 space-y-4">
        <div className="flex flex-wrap gap-3 items-center justify-between"><h2 className="font-semibold">Linha do tempo</h2><div className="flex gap-2"><button onClick={() => setVisao("storyboard")} aria-pressed={visao === "storyboard"} className={`px-3 py-1.5 rounded-btn text-sm ${visao === "storyboard" ? "bg-elev text-tx" : "text-mut"}`}><Film className="inline w-4 h-4 mr-1" />Storyboard</button><button onClick={() => setVisao("tabela")} aria-pressed={visao === "tabela"} className={`px-3 py-1.5 rounded-btn text-sm ${visao === "tabela" ? "bg-elev text-tx" : "text-mut"}`}><List className="inline w-4 h-4 mr-1" />Tabela</button></div></div>
        <div className="relative h-4 rounded bg-elev overflow-hidden" aria-label="Distribuição dos shots"><div className="absolute inset-0 flex">{shots.filter((s) => s.segmentos.length).map((shot) => <button key={shot.id} title={`${shot.id} · ${shot.template}`} onClick={() => { setSelecionado(shot); if (shot.inicio_s != null) player.current?.seekTo(Math.round(shot.inicio_s * 24)); }} className="h-full border-r border-bg/60 bg-brasa/60 hover:bg-brasa" style={{ flexGrow: Math.max(0.1, shot.duracao_s), flexBasis: 0 }} />)}</div></div>
        <div className="flex items-center gap-2 rounded-btn border border-line bg-elev px-3 max-w-sm"><Search className="w-4 h-4 text-mut" /><input value={filtro} onChange={(e) => { setFiltro(e.target.value); setLimite(50); }} placeholder="Filtrar por shot, template ou bloco" className="bg-transparent py-2 text-sm outline-none w-full" /></div>
        <div className={visao === "storyboard" ? "grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3" : "space-y-1"}>{filtrados.slice(0, limite).map((shot) => <button key={shot.id} onClick={() => { setSelecionado(shot); if (shot.inicio_s != null) player.current?.seekTo(Math.round(shot.inicio_s * 24)); }} className={`text-left border rounded-btn hover:border-brasa focus-visible:outline-2 focus-visible:outline-brasa ${visao === "storyboard" ? "p-3 bg-elev border-line min-h-24" : "px-3 py-2 border-line flex gap-4 items-center w-full"}`}><span className="text-brasa text-xs font-mono">{shot.id} · {shot.template}</span><span className="block text-xs text-mut mt-1">{shot.bloco}</span><span className="block text-xs mt-1">{shot.inicio_s != null ? tempo(shot.inicio_s) : "—"} · {shot.duracao_s.toFixed(1)} s</span></button>)}</div>
        {limite < filtrados.length && <button onClick={() => setLimite((n) => n + 50)} className="text-sm text-brasa hover:underline">Mostrar mais {Math.min(50, filtrados.length - limite)} shots</button>}
      </div>
      {selecionado && <div role="dialog" aria-label={`Shot ${selecionado.id}`} className="fixed inset-0 z-40 bg-black/60 flex justify-end" onClick={() => setSelecionado(null)}><div className="w-full max-w-md bg-surf border-l border-line p-6 overflow-y-auto" onClick={(e) => e.stopPropagation()}><button onClick={() => setSelecionado(null)} className="text-sm text-mut hover:text-tx float-right">Fechar ×</button><h2 className="text-xl font-bold">Shot {selecionado.id}</h2><p className="text-sm text-mut mt-2">{selecionado.template} · {selecionado.duracao_s.toFixed(1)} s</p><div className="mt-6 space-y-4 text-sm"><div><span className="text-mut">Narração</span><p>{selecionado.segmentos.join(", ") || "Cartão visual"}</p></div><div><span className="text-mut">Texto na tela</span><p>{selecionado.textos.join(" · ") || "Sem texto"}</p></div><div><span className="text-mut">Ativos</span><p>{selecionado.ativos.join(", ") || "Nenhum"}</p></div><div><span className="text-mut">Motivo</span><p>{selecionado.motivo || "—"}</p></div></div>{manifesto && <button onClick={() => { if (selecionado.inicio_s != null) player.current?.seekTo(Math.round(selecionado.inicio_s * 24)); player.current?.play(); }} className="mt-6 flex gap-2 items-center text-brasa"><Play className="w-4 h-4" />Tocar trecho</button>}<p className="mt-8 text-xs text-warn flex gap-2"><AlertTriangle className="w-4 h-4 shrink-0" />Edição de shots com versionamento e verificação automática ainda não está disponível.</p></div></div>}
    </div>
  );
};
