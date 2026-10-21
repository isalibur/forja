import React, { useEffect, useState } from "react";
import textos from "../i18n/pt-BR.json";

type PedidoAvulso = {
  id: string;
  tema: string;
  objetivo: keyof typeof textos.shortsAvulsos.objetivos;
  duracao_s: number;
  formula_id: string;
  origem_roteiro: string;
  roteiro: string | null;
  pendencias: string[];
};
type Formula = { nome: string; estrutura: string[]; templates: string[] };
type AprovacaoRoteiro = { texto: string; revisao: string; status: string };
type MidiaGlobal = { id_global: string; descricao: string; licenca: string; credito: string; hash_arquivo: string };
type SelecaoMidias = { revisao: string; midias: MidiaGlobal[]; status: string };
type Resultado = {
  id?: string;
  nome?: string;
  hash_conteudo?: string;
  aprovacoes_roteiro?: Record<string, AprovacaoRoteiro>;
  selecoes_midias?: Record<string, SelecaoMidias>;
  midias_desatualizadas?: string[];
  quantidade: number;
  pedidos: PedidoAvulso[];
  formulas: Record<string, Formula>;
  status: string;
};

const t = textos.shortsAvulsos;

export const ShortsAvulsos: React.FC = () => {
  const [csvTexto, setCsvTexto] = useState("");
  const [nome, setNome] = useState("");
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [campanhas, setCampanhas] = useState<Resultado[]>([]);
  const [roteiros, setRoteiros] = useState<Record<string, string>>({});
  const [midiasDisponiveis, setMidiasDisponiveis] = useState<MidiaGlobal[]>([]);
  const [midiasEscolhidas, setMidiasEscolhidas] = useState<Record<string, string[]>>({});
  const [erro, setErro] = useState("");
  const [ocupado, setOcupado] = useState(false);

  useEffect(() => {
    void fetch("/api/shorts/avulsos/campanhas")
      .then((resposta) => resposta.ok ? resposta.json() as Promise<Resultado[]> : [])
      .then(setCampanhas)
      .catch(() => { /* A prévia continua disponível sem histórico. */ });
    void fetch("/api/shorts/avulsos/midias-disponiveis")
      .then((resposta) => resposta.ok ? resposta.json() as Promise<{ midias: MidiaGlobal[] }> : { midias: [] })
      .then((corpo) => setMidiasDisponiveis(corpo.midias))
      .catch(() => { /* A seleção informa que não há imagens elegíveis. */ });
  }, []);

  const planejar = async (evento: React.FormEvent<HTMLFormElement>) => {
    evento.preventDefault();
    setOcupado(true);
    setErro("");
    setResultado(null);
    try {
      const resposta = await fetch("/api/shorts/avulsos/planejar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv_texto: csvTexto }),
      });
      const corpo = await resposta.json();
      if (!resposta.ok) throw new Error(corpo.detail || t.erroPadrao);
      setResultado(corpo as Resultado);
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : t.erroPadrao);
    } finally {
      setOcupado(false);
    }
  };

  const salvar = async () => {
    setOcupado(true);
    setErro("");
    try {
      const resposta = await fetch("/api/shorts/avulsos/campanhas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome, csv_texto: csvTexto }),
      });
      const corpo = await resposta.json();
      if (!resposta.ok) throw new Error(corpo.detail || t.erroPadrao);
      const campanha = corpo as Resultado;
      setResultado(campanha);
      setCampanhas((anteriores) => [campanha, ...anteriores.filter((item) => item.id !== campanha.id)]);
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : t.erroPadrao);
    } finally {
      setOcupado(false);
    }
  };

  const aprovarRoteiro = async (pedido: PedidoAvulso) => {
    if (!resultado?.id || !resultado.hash_conteudo) return;
    const campanhaId = resultado.id;
    const chave = `${campanhaId}:${pedido.id}`;
    const texto = roteiros[chave] ?? resultado.aprovacoes_roteiro?.[pedido.id]?.texto ?? pedido.roteiro ?? "";
    setOcupado(true);
    setErro("");
    try {
      const resposta = await fetch(`/api/shorts/avulsos/campanhas/${campanhaId}/pedidos/${pedido.id}/roteiro/aprovar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto, hash_campanha: resultado.hash_conteudo }),
      });
      const corpo = await resposta.json();
      if (!resposta.ok) throw new Error(corpo.detail || t.erroPadrao);
      const aprovacao = corpo as AprovacaoRoteiro;
      const atualizado = {
        ...resultado,
        aprovacoes_roteiro: { ...resultado.aprovacoes_roteiro, [pedido.id]: aprovacao },
        selecoes_midias: resultado.aprovacoes_roteiro?.[pedido.id]?.revisao === aprovacao.revisao
          ? resultado.selecoes_midias
          : Object.fromEntries(Object.entries(resultado.selecoes_midias ?? {}).filter(([id]) => id !== pedido.id)),
        midias_desatualizadas: resultado.selecoes_midias?.[pedido.id]
          && resultado.aprovacoes_roteiro?.[pedido.id]?.revisao !== aprovacao.revisao
          ? [...new Set([...(resultado.midias_desatualizadas ?? []), pedido.id])]
          : resultado.midias_desatualizadas,
      };
      setResultado(atualizado);
      setCampanhas((anteriores) => anteriores.map((item) => item.id === campanhaId ? atualizado : item));
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : t.erroPadrao);
    } finally {
      setOcupado(false);
    }
  };

  const selecionarMidias = async (pedido: PedidoAvulso) => {
    if (!resultado?.id || !resultado.hash_conteudo) return;
    const aprovacao = resultado.aprovacoes_roteiro?.[pedido.id];
    if (!aprovacao) return;
    const campanhaId = resultado.id;
    const chave = `${campanhaId}:${pedido.id}`;
    const ids = midiasEscolhidas[chave] ?? resultado.selecoes_midias?.[pedido.id]?.midias.map((item) => item.id_global) ?? [];
    setOcupado(true);
    setErro("");
    try {
      const resposta = await fetch(`/api/shorts/avulsos/campanhas/${campanhaId}/pedidos/${pedido.id}/midias/selecionar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids_globais: ids, hash_campanha: resultado.hash_conteudo, revisao_roteiro: aprovacao.revisao }),
      });
      const corpo = await resposta.json();
      if (!resposta.ok) throw new Error(corpo.detail || t.erroPadrao);
      const selecao = corpo as SelecaoMidias;
      const atualizado = {
        ...resultado,
        selecoes_midias: { ...resultado.selecoes_midias, [pedido.id]: selecao },
        midias_desatualizadas: resultado.midias_desatualizadas?.filter((id) => id !== pedido.id),
      };
      setResultado(atualizado);
      setCampanhas((anteriores) => anteriores.map((item) => item.id === campanhaId ? atualizado : item));
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : t.erroPadrao);
    } finally {
      setOcupado(false);
    }
  };

  return (
    <section className="p-6 xl:p-8 max-w-5xl mx-auto space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold text-tx">{t.titulo}</h1>
        <p className="text-sm text-mut">{t.descricao}</p>
      </header>
      <form className="rounded-card border border-line bg-surf p-5 space-y-4" onSubmit={(evento) => { void planejar(evento); }}>
        <div className="space-y-1">
          <label htmlFor="csv-avulsos" className="font-medium text-tx">{t.rotuloCsv}</label>
          <p id="ajuda-csv-avulsos" className="text-xs text-mut">{t.ajudaCsv}</p>
        </div>
        <textarea
          id="csv-avulsos"
          aria-describedby="ajuda-csv-avulsos"
          className="min-h-40 w-full rounded-btn border border-line bg-bg p-3 font-mono text-sm text-tx focus:outline-none focus:ring-2 focus:ring-brasa"
          placeholder={t.exemploCsv}
          maxLength={262144}
          required
          value={csvTexto}
          onChange={(evento) => { setCsvTexto(evento.target.value); setResultado(null); setErro(""); }}
        />
        <button type="submit" disabled={ocupado || !csvTexto.trim()} className="rounded-btn bg-brasa px-4 py-2 font-semibold text-bg disabled:opacity-50">
          {ocupado ? t.planejando : t.planejar}
        </button>
      </form>
      {erro && <p role="alert" className="rounded-btn border border-red-500 p-3 text-sm text-red-500">{erro}</p>}
      {resultado && (
        <div className="space-y-4" aria-live="polite">
          <h2 className="text-lg font-semibold text-tx">{resultado.pedidos.length} {t.resultado}</h2>
          {resultado.id ? <p className="text-sm text-mut">{t.salvo}: {resultado.nome} · {resultado.id}</p> : (
            <div className="flex flex-wrap items-end gap-3 rounded-card border border-line bg-surf p-4">
              <label className="text-sm text-tx">{t.nomeCampanha}
                <input className="ml-2 rounded-btn border border-line bg-bg p-2 text-tx" maxLength={120}
                  value={nome} onChange={(evento) => setNome(evento.target.value)} />
              </label>
              <button type="button" disabled={ocupado || !nome.trim()}
                onClick={() => { void salvar(); }}
                className="rounded-btn bg-brasa px-4 py-2 font-semibold text-bg disabled:opacity-50">
                {t.salvar}
              </button>
            </div>
          )}
          <p className="text-sm text-mut">{t.semProducao}</p>
          <div className="grid gap-4 md:grid-cols-2">
            {resultado.pedidos.map((pedido) => {
              const formula = resultado.formulas[pedido.formula_id];
              const aprovacao = resultado.aprovacoes_roteiro?.[pedido.id];
              const chave = `${resultado.id}:${pedido.id}`;
              const selecao = resultado.selecoes_midias?.[pedido.id];
              const escolhidas = midiasEscolhidas[chave] ?? selecao?.midias.map((item) => item.id_global) ?? [];
              return (
                <article key={pedido.id} className="rounded-card border border-line bg-surf p-5 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs text-mut">{pedido.id} · {t.objetivos[pedido.objetivo]} · {pedido.duracao_s} s</p>
                      <h3 className="font-semibold text-tx">{pedido.tema}</h3>
                    </div>
                  </div>
                  <p className="text-sm text-mut">{t.formula}: {formula?.nome ?? pedido.formula_id}</p>
                  <div>
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-mut">{t.estrutura}</p>
                    <div className="flex flex-wrap items-center gap-1 text-xs text-tx">
                      {formula?.estrutura.map((parte, indice) => (
                        <React.Fragment key={`${parte}-${indice}`}>
                          {indice > 0 && <span aria-hidden="true">→</span>}
                          <span className="rounded-btn border border-line px-2 py-1">{parte.replace(/_/g, " ")}</span>
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                  <p className="text-xs text-mut">{pedido.roteiro ? t.roteiroProprio : t.roteiroPendente}</p>
                  {resultado.id && (
                    <div className="space-y-2">
                      <label htmlFor={`roteiro-${pedido.id}`} className="block text-sm font-medium text-tx">
                        {t.revisarRoteiro}
                      </label>
                      <textarea id={`roteiro-${pedido.id}`} maxLength={20000}
                        className="min-h-28 w-full rounded-btn border border-line bg-bg p-3 text-sm text-tx"
                        value={roteiros[chave] ?? aprovacao?.texto ?? pedido.roteiro ?? ""}
                        onChange={(evento) => setRoteiros((anteriores) => ({ ...anteriores, [chave]: evento.target.value }))}
                      />
                      <button type="button" disabled={ocupado || !(roteiros[chave] ?? aprovacao?.texto ?? pedido.roteiro ?? "").trim()}
                        onClick={() => { void aprovarRoteiro(pedido); }}
                        className="rounded-btn border border-brasa px-3 py-2 text-sm font-semibold text-brasa disabled:opacity-50">
                        {aprovacao ? t.aprovarNovaRevisao : t.aprovarRoteiro}
                      </button>
                      {aprovacao && <p className="text-xs text-mut">{t.roteiroAprovado} · {aprovacao.revisao.slice(0, 8)}</p>}
                    </div>
                  )}
                  {resultado.id && aprovacao && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-tx">{t.selecionarMidias}</p>
                      {resultado.midias_desatualizadas?.includes(pedido.id) && (
                        <p className="text-xs text-red-500">{t.midiasDesatualizadas}</p>
                      )}
                      {midiasDisponiveis.length === 0 ? (
                        <p className="text-xs text-mut">{t.semMidiasElegiveis}</p>
                      ) : (
                        <div className="max-h-64 space-y-2 overflow-y-auto">
                          {midiasDisponiveis.map((midia) => {
                            const [, categoria, itemId] = midia.id_global.split(":");
                            return (
                              <label key={midia.id_global} className="flex gap-2 rounded-btn border border-line p-2 text-xs text-tx">
                                <input type="checkbox" checked={escolhidas.includes(midia.id_global)}
                                  onChange={(evento) => setMidiasEscolhidas((anteriores) => ({
                                    ...anteriores,
                                    [chave]: evento.target.checked
                                      ? [...escolhidas, midia.id_global]
                                      : escolhidas.filter((id) => id !== midia.id_global),
                                  }))} />
                                <img src={`/api/shorts/avulsos/midias/${categoria}/${itemId}/imagem`}
                                  alt={midia.descricao || itemId} className="h-14 w-14 rounded object-cover" loading="lazy" />
                                <span>{midia.descricao || itemId}<br />{midia.licenca} · {midia.credito || t.semCredito}</span>
                              </label>
                            );
                          })}
                        </div>
                      )}
                      <button type="button" disabled={ocupado || escolhidas.length === 0 || escolhidas.length > 20}
                        onClick={() => { void selecionarMidias(pedido); }}
                        className="rounded-btn border border-brasa px-3 py-2 text-sm font-semibold text-brasa disabled:opacity-50">
                        {t.confirmarMidias}
                      </button>
                      {selecao && <p className="text-xs text-mut">{t.midiasSelecionadas} · {selecao.midias.length} · {selecao.revisao.slice(0, 8)}</p>}
                    </div>
                  )}
                  <div>
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-mut">{t.pendencias}</p>
                    <ul className="list-disc pl-5 text-sm text-mut">
                      {pedido.pendencias.filter((item) => !(
                        (aprovacao && item === "aprovar roteiro")
                        || (selecao && item === "aprovar mídias e licenças")
                      ))
                        .map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      )}
      {campanhas.length > 0 && (
        <section className="space-y-2">
          <h2 className="text-lg font-semibold text-tx">{t.historico}</h2>
          <ul className="space-y-2">
            {campanhas.map((campanha) => (
              <li key={campanha.id}>
                <button type="button" onClick={() => setResultado(campanha)}
                  className="w-full rounded-btn border border-line bg-surf p-3 text-left text-sm text-tx">
                  {campanha.nome} · {campanha.pedidos.length} {t.resultado} · {campanha.id}
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </section>
  );
};
