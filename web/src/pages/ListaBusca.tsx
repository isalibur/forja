import React from "react";
import { Copy, FolderOpen } from "lucide-react";
import { toast } from "sonner";
import { ErroCarregamento } from "../components/ErroCarregamento";
import { usePlano } from "../hooks/usePlano";

export const ListaBusca: React.FC<{ slug: string }> = ({ slug }) => {
  const { data, isLoading, error, refetch } = usePlano(slug);
  const pedidos = data?.pedidos ?? [];
  const recebidos = pedidos.filter((pedido) => pedido.recebido || pedido.resolvido).length;
  const licenciados = pedidos.filter((pedido) => Boolean(data?.ativos?.[pedido.id]?.imagem_url)).length;
  const copiar = async (texto: string) => {
    try {
      await navigator.clipboard.writeText(texto);
      toast.success("Copiado para a área de transferência");
    } catch {
      toast.error("Não foi possível copiar. Selecione e copie o texto manualmente.");
    }
  };
  if (!slug) return <div className="p-8 text-mut">Selecione um projeto em Início para ver a lista de busca.</div>;
  if (isLoading) return <div className="p-8 text-mut">Carregando lista de busca…</div>;
  if (error) return <ErroCarregamento tentarNovamente={() => { void refetch(); }} />;
  return <div className="p-6 xl:p-8 max-w-[1200px] mx-auto space-y-6">
    <div><p className="text-xs uppercase tracking-widest text-brasa">Projeto · Lista de busca</p><h1 className="text-2xl font-bold mt-1">O que precisa de você</h1><p className="text-sm text-mut mt-1">{recebidos} de {pedidos.length} arquivos recebidos ou resolvidos · {licenciados} com licença confirmada</p></div>
    {!data?.pronto ? <p className="text-mut">A lista aparecerá após a resolução dos ativos.</p> : pedidos.length === 0 ? <p className="p-8 rounded-card border border-line bg-surf text-mut">Nenhuma imagem precisa de entrega manual neste momento.</p> : <>
      <div className="h-2 rounded-full bg-elev" role="progressbar" aria-label="Arquivos recebidos ou resolvidos; licença verificada separadamente" aria-valuemin={0} aria-valuemax={pedidos.length} aria-valuenow={recebidos}><div className="h-2 rounded-full bg-brasa" style={{ width: `${100 * recebidos / pedidos.length}%` }} /></div>
      <div className="rounded-card border border-warn/30 bg-warn/5 p-4 text-sm"><div className="flex items-center gap-2 font-semibold text-warn"><FolderOpen className="w-4 h-4" />Pasta manual</div><p className="mt-2 text-mut">Salve a imagem com o nome indicado na pasta abaixo. A lista confere novos arquivos automaticamente; a ficha de licença será revisada antes do uso no vídeo.</p><div className="mt-3 flex gap-2 items-center"><code className="text-xs break-all flex-1">{data.pasta_manual}</code><button onClick={() => copiar(data.pasta_manual ?? "")} className="text-brasa text-xs flex gap-1 items-center"><Copy className="w-4 h-4" />Copiar caminho</button></div></div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">{pedidos.map((pedido) => <article key={pedido.id} className="rounded-card border border-line bg-surf p-5 space-y-3"><div className="flex justify-between gap-3"><h2 className="font-semibold">{pedido.id} · {pedido.descricao}</h2><span className={`shrink-0 text-xs px-2 py-1 rounded ${data.ativos?.[pedido.id]?.imagem_url ? "bg-ok/10 text-ok" : "bg-warn/10 text-warn"}`}>{data.ativos?.[pedido.id]?.imagem_url ? "Licença confirmada" : pedido.recebido || pedido.resolvido ? "Recebida · licença pendente" : "Pendente"}</span></div><p className="text-sm text-mut">{pedido.motivo || "Ativo documental que precisa da sua seleção."}</p><div className="text-xs"><span className="text-mut">Procure por:</span> {(pedido.busca.termos ?? [pedido.descricao]).join(" · ")} <button onClick={() => { void copiar((pedido.busca.termos ?? [pedido.descricao]).join(" ")); }} aria-label={`Copiar termos de ${pedido.id}`} className="text-brasa ml-1"><Copy className="w-3.5 h-3.5 inline" /></button></div><p className="text-xs text-mut">Sugestões: {(pedido.busca.sites ?? []).join(" · ") || "Acervos com licença verificável"}</p><div className="border-t border-line pt-3 text-xs"><strong>Salvar como:</strong> <code className="text-brasa">{pedido.nome_arquivo}</code><span className="text-mut"> · mínimo 1600 px</span></div><p className="text-xs text-mut">Plano B: {pedido.plano_b || "revisão manual"}</p><p className="text-xs text-mut">Usado em: {pedido.usado_em.join(", ") || "plano geral"}</p></article>)}</div>
    </>}
  </div>;
};
