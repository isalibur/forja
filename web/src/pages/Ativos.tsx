import React, { useState } from "react";
import { ImageOff } from "lucide-react";
import { ErroCarregamento } from "../components/ErroCarregamento";
import { CreditoImagem, usePlano } from "../hooks/usePlano";

const origemTexto: Record<string, string> = { pesquisar: "Pesquisada", gerar: "Gerada", biblioteca: "Global", pedir_ao_usuario: "Precisa de você", dados: "Dados" };

const MiniaturaAtivo: React.FC<{ url?: string | null; descricao: string }> = ({ url, descricao }) => {
  const [falhou, setFalhou] = useState(false);
  if (url && !falhou) {
    return <img src={url} alt={descricao} loading="lazy" onError={() => setFalhou(true)} className="h-32 w-full object-cover bg-elev" />;
  }
  return <div className="h-32 bg-elev flex items-center justify-center text-mut"><ImageOff className="w-7 h-7" /><span className="text-xs ml-2">Prévia indisponível ou sem licença confirmada</span></div>;
};

const FichaCredito: React.FC<{ ficha: CreditoImagem }> = ({ ficha }) => <div className="text-xs text-mut space-y-1">
  <p>Autor: {ficha.autor || "não informado"} · Licença: {ficha.licenca}</p>
  {ficha.credito && <p>Crédito: {ficha.credito}</p>}
  {ficha.fonte && <a href={ficha.fonte} target="_blank" rel="noopener noreferrer" className="text-brasa underline break-all">Abrir página de origem</a>}
  {typeof ficha.nota === "number" && <p>Curadoria: {ficha.nota.toFixed(1)}/10{ficha.motivo ? ` · ${ficha.motivo}` : ""}</p>}
</div>;

export const Ativos: React.FC<{ slug: string; onNavegar: (tela: string) => void }> = ({ slug, onNavegar }) => {
  const { data, isLoading, error, refetch } = usePlano(slug);
  const [filtro, setFiltro] = useState("todos");
  const [limite, setLimite] = useState(60);
  const [alternativasAbertas, setAlternativasAbertas] = useState<string[]>([]);
  const ativos = Object.values(data?.ativos ?? {});
  const visiveis = ativos.filter((ativo) => filtro === "todos" || ativo.origem === filtro);

  if (!slug) return <div className="p-8 text-mut">Selecione um projeto em Início para ver os ativos.</div>;
  if (isLoading) return <div className="p-8 text-mut">Carregando ativos…</div>;
  if (error) return <ErroCarregamento tentarNovamente={() => { void refetch(); }} />;
  return <div className="p-6 xl:p-8 max-w-[1600px] mx-auto space-y-6">
    <div className="flex items-start justify-between gap-4"><div><p className="text-xs uppercase tracking-widest text-brasa">Projeto · Ativos</p><h1 className="text-2xl font-bold mt-1">Imagens do plano</h1><p className="text-sm text-mut mt-1">{ativos.length} ativos · origem, uso e licença em um lugar</p></div><button onClick={() => onNavegar("busca")} className="rounded-btn bg-warn/15 text-warn px-4 py-2 text-sm">Ver lista de busca</button></div>
    {!data?.pronto ? <p className="text-mut">Os ativos aparecerão após o planejamento.</p> : <>
      <div className="flex flex-wrap gap-2" role="group" aria-label="Filtrar ativos">{[["todos", "Todos"], ["pesquisar", "Pesquisadas"], ["gerar", "Geradas"], ["pedir_ao_usuario", "Precisam de você"], ["biblioteca", "Global"]].map(([valor, rotulo]) => <button key={valor} onClick={() => { setFiltro(valor); setLimite(60); }} aria-pressed={filtro === valor} className={`px-3 py-1.5 rounded-btn border text-sm ${filtro === valor ? "border-brasa text-brasa bg-brasa/10" : "border-line text-mut"}`}>{rotulo}</button>)}</div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">{visiveis.slice(0, limite).map((ativo) => {
        const abertas = alternativasAbertas.includes(ativo.id);
        return <article key={ativo.id} className="rounded-card border border-line bg-surf overflow-hidden"><MiniaturaAtivo key={ativo.imagem_url ?? "sem-imagem"} url={ativo.imagem_url} descricao={ativo.descricao} /><div className="p-4 space-y-3"><div className="flex items-start justify-between gap-3"><strong className="font-mono text-brasa text-sm">{ativo.id}</strong><span className={`text-xs rounded px-2 py-0.5 ${ativo.origem === "pedir_ao_usuario" ? "bg-warn/15 text-warn" : "bg-elev text-mut"}`}>{origemTexto[ativo.origem] ?? ativo.origem}</span></div><p className="text-sm">{ativo.descricao}</p><p className="text-xs text-mut">Usado em {ativo.usado_em.join(", ") || "nenhum shot"}</p><p className={`text-xs ${ativo.imagem_url ? "text-ok" : "text-warn"}`}>{ativo.imagem_url ? "Imagem liberada para prévia" : "Imagem não liberada para prévia"}</p>{ativo.credito_imagem && <FichaCredito ficha={ativo.credito_imagem} />}{Boolean(ativo.candidatas?.length) && <div><button aria-expanded={abertas} onClick={() => setAlternativasAbertas((ids) => abertas ? ids.filter((id) => id !== ativo.id) : [...ids, ativo.id])} className="text-sm text-brasa underline">{abertas ? "Ocultar" : "Ver"} alternativas ({ativo.candidatas?.length})</button>{abertas && <div className="mt-3 space-y-3">{ativo.candidatas?.map((candidata) => <div key={candidata.nome} className="rounded-btn border border-line overflow-hidden"><MiniaturaAtivo url={candidata.imagem_url} descricao={`Candidata ${candidata.nome} para ${ativo.descricao}`} /><div className="p-2 space-y-1"><p className="font-mono text-xs text-tx">{candidata.nome}</p><FichaCredito ficha={candidata} /></div></div>)}</div>}</div>}</div></article>;
      })}</div>
      {limite < visiveis.length && <button onClick={() => setLimite((n) => n + 60)} className="text-sm text-brasa hover:underline">Mostrar mais ativos</button>}
    </>}
  </div>;
};
