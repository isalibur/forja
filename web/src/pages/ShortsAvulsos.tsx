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
type Resultado = {
  id?: string;
  nome?: string;
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
  const [erro, setErro] = useState("");
  const [ocupado, setOcupado] = useState(false);

  useEffect(() => {
    void fetch("/api/shorts/avulsos/campanhas")
      .then((resposta) => resposta.ok ? resposta.json() as Promise<Resultado[]> : [])
      .then(setCampanhas)
      .catch(() => { /* A prévia continua disponível sem histórico. */ });
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
                  <div>
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-mut">{t.pendencias}</p>
                    <ul className="list-disc pl-5 text-sm text-mut">
                      {pedido.pendencias.map((item) => <li key={item}>{item}</li>)}
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
