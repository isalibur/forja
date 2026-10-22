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
  roteiro_sugerido?: string | null;
  cta: string | null;
  opcao_a?: string | null;
  opcao_b?: string | null;
  produto?: ProdutoAfiliado | null;
  pendencias: string[];
};
type ProdutoAfiliado = {
  nome: string;
  descricao: string;
  beneficios: string[];
  preco: string | null;
  fonte_preco: string | null;
  condicao: string | null;
  link_afiliado: string;
  imagens: string[];
  nicho: string | null;
  plataforma: string;
  marca: string | null;
  cta: string;
};
type Formula = { nome: string; estrutura: string[]; templates: string[] };
type AprovacaoRoteiro = { texto: string; revisao: string; status: string };
type MidiaGlobal = { id_global: string; descricao: string; licenca: string; credito: string; hash_arquivo: string };
type SelecaoMidias = { revisao: string; midias: MidiaGlobal[]; status: string };
type FonteAlegacao = { alegacao: string; fonte: string };
type DadosAlegacoes = {
  fontes: FonteAlegacao[];
  sem_alegacoes_verificaveis: boolean;
  prova_real: FonteAlegacao | null;
  fonte_preco: string | null;
  condicao_urgencia: string | null;
  relacao_comercial: "nenhuma" | "produto_proprio" | "afiliado" | "parceria_paga";
  marca: string | null;
  aviso_publicidade: boolean;
  revisado_pelo_usuario: boolean;
};
type Documentacao = { revisao: string; dados: DadosAlegacoes; status: string };
type ProducaoAvulsa = { status: string; revisao?: string; erro?: string; cache?: boolean };
type RegraQa = { regra: string; aprovada: boolean; descricao: string; detalhes: string };
type MetadadosRascunho = {
  status: string;
  publicacao_autorizada: boolean;
  duracao_s: number;
  wer: number | null;
  qa: { aprovado: boolean; violacoes: RegraQa[] };
};
const FICHA_VAZIA: DadosAlegacoes = {
  fontes: [{ alegacao: "", fonte: "" }], sem_alegacoes_verificaveis: false,
  prova_real: null, fonte_preco: null, condicao_urgencia: null,
  relacao_comercial: "nenhuma", marca: null, aviso_publicidade: false,
  revisado_pelo_usuario: false,
};
type Resultado = {
  id?: string;
  nome?: string;
  hash_conteudo?: string;
  aprovacoes_roteiro?: Record<string, AprovacaoRoteiro>;
  selecoes_midias?: Record<string, SelecaoMidias>;
  midias_desatualizadas?: string[];
  documentacoes_alegacoes?: Record<string, Documentacao>;
  alegacoes_desatualizadas?: string[];
  quantidade: number;
  pedidos: PedidoAvulso[];
  formulas: Record<string, Formula>;
  status: string;
};

const t = textos.shortsAvulsos;

const relacaoPermitida = (pedido: PedidoAvulso, documentacao: Documentacao): boolean => {
  if (["educativo", "promocao_canal", "anuncio", "engajamento"].includes(pedido.objetivo)) {
    return documentacao.dados.relacao_comercial === "nenhuma";
  }
  return Boolean(pedido.produto) && !pedido.produto?.preco && documentacao.dados.relacao_comercial === "afiliado";
};

const fichaInicial = (pedido: PedidoAvulso): DadosAlegacoes => {
  if (!pedido.produto) return FICHA_VAZIA;
  const produto = pedido.produto;
  return {
    ...FICHA_VAZIA,
    fontes: produto.condicao && produto.fonte_preco
      ? [{ alegacao: `Condição da oferta de ${produto.nome}.`, fonte: produto.fonte_preco }]
      : FICHA_VAZIA.fontes,
    fonte_preco: produto.condicao ? produto.fonte_preco : null,
    relacao_comercial: "afiliado",
    marca: produto.marca,
    aviso_publicidade: true,
  };
};

export const ShortsAvulsos: React.FC = () => {
  const [csvTexto, setCsvTexto] = useState("");
  const [planilhaAfiliados, setPlanilhaAfiliados] = useState("");
  const [previaAfiliados, setPreviaAfiliados] = useState<Resultado | null>(null);
  const [agenda, setAgenda] = useState("");
  const [nome, setNome] = useState("");
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [campanhas, setCampanhas] = useState<Resultado[]>([]);
  const [roteiros, setRoteiros] = useState<Record<string, string>>({});
  const [midiasDisponiveis, setMidiasDisponiveis] = useState<MidiaGlobal[]>([]);
  const [midiasEscolhidas, setMidiasEscolhidas] = useState<Record<string, string[]>>({});
  const [fichas, setFichas] = useState<Record<string, DadosAlegacoes>>({});
  const [codigos, setCodigos] = useState<Record<string, string>>({});
  const [producoes, setProducoes] = useState<Record<string, ProducaoAvulsa>>({});
  const [metadados, setMetadados] = useState<Record<string, MetadadosRascunho>>({});
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

  useEffect(() => {
    if (!resultado?.id) return;
    const campanhaId = resultado.id;
    const atualizar = () => {
      resultado.pedidos.forEach((pedido) => {
        void fetch(`/api/shorts/avulsos/campanhas/${campanhaId}/pedidos/${pedido.id}/producao`)
          .then((resposta) => resposta.ok ? resposta.json() as Promise<ProducaoAvulsa> : null)
          .then((estado) => {
            if (!estado) return;
            setProducoes((anteriores) => ({ ...anteriores, [`${campanhaId}:${pedido.id}`]: estado }));
            if (estado.status !== "concluido") return;
            void fetch(`/api/shorts/avulsos/campanhas/${campanhaId}/pedidos/${pedido.id}/artefatos/metadados.json`)
              .then((resposta) => resposta.ok ? resposta.json() as Promise<MetadadosRascunho> : null)
              .then((dados) => {
                if (dados) setMetadados((anteriores) => ({ ...anteriores, [`${campanhaId}:${pedido.id}`]: dados }));
              })
              .catch(() => { /* Os metadados podem ser recarregados abrindo a campanha. */ });
          })
          .catch(() => { /* A produção pode ser consultada novamente ao reabrir. */ });
      });
    };
    atualizar();
    const timer = window.setInterval(atualizar, 5000);
    return () => window.clearInterval(timer);
  }, [resultado?.id, resultado?.pedidos]);

  const produzirAvulso = async (pedido: PedidoAvulso) => {
    if (!resultado?.id) return;
    const chave = `${resultado.id}:${pedido.id}`;
    setOcupado(true);
    setErro("");
    try {
      const resposta = await fetch(`/api/shorts/avulsos/campanhas/${resultado.id}/pedidos/${pedido.id}/produzir`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ codigo: codigos[chave] ?? "" }),
      });
      const corpo = await resposta.json() as ProducaoAvulsa & { detail?: string };
      if (!resposta.ok) throw new Error(corpo.detail || t.erroPadrao);
      setProducoes((anteriores) => ({ ...anteriores, [chave]: corpo }));
      setCodigos((anteriores) => ({ ...anteriores, [chave]: "" }));
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : t.erroPadrao);
    } finally {
      setOcupado(false);
    }
  };

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

  const planejarAfiliados = async (evento: React.FormEvent<HTMLFormElement>) => {
    evento.preventDefault();
    setOcupado(true);
    setErro("");
    setPreviaAfiliados(null);
    try {
      const resposta = await fetch("/api/shorts/afiliados/planilhas/planejar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv_texto: planilhaAfiliados }),
      });
      const corpo = await resposta.json();
      if (!resposta.ok) throw new Error(corpo.detail || t.erroPadrao);
      setPreviaAfiliados(corpo as Resultado);
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : t.erroPadrao);
    } finally {
      setOcupado(false);
    }
  };

  const salvarAfiliados = async () => {
    setOcupado(true);
    setErro("");
    try {
      const resposta = await fetch("/api/shorts/afiliados/campanhas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome, csv_texto: planilhaAfiliados }),
      });
      const corpo = await resposta.json();
      if (!resposta.ok) throw new Error(corpo.detail || t.erroPadrao);
      const campanha = corpo as Resultado;
      setResultado(campanha);
      setPreviaAfiliados(null);
      setCampanhas((anteriores) => [campanha, ...anteriores.filter((item) => item.id !== campanha.id)]);
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : t.erroPadrao);
    } finally {
      setOcupado(false);
    }
  };

  const carregarAgenda = async () => {
    if (!resultado?.id) return;
    setOcupado(true);
    setErro("");
    try {
      const resposta = await fetch(`/api/shorts/avulsos/campanhas/${resultado.id}/agenda`);
      const corpo = await resposta.json();
      if (!resposta.ok) throw new Error(corpo.detail || t.erroPadrao);
      setAgenda(String(corpo.agenda_csv ?? ""));
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
    const texto = roteiros[chave]
      ?? resultado.aprovacoes_roteiro?.[pedido.id]?.texto
      ?? pedido.roteiro
      ?? pedido.roteiro_sugerido
      ?? "";
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
        documentacoes_alegacoes: resultado.aprovacoes_roteiro?.[pedido.id]?.revisao === aprovacao.revisao
          ? resultado.documentacoes_alegacoes
          : Object.fromEntries(Object.entries(resultado.documentacoes_alegacoes ?? {}).filter(([id]) => id !== pedido.id)),
        alegacoes_desatualizadas: resultado.documentacoes_alegacoes?.[pedido.id]
          && resultado.aprovacoes_roteiro?.[pedido.id]?.revisao !== aprovacao.revisao
          ? [...new Set([...(resultado.alegacoes_desatualizadas ?? []), pedido.id])]
          : resultado.alegacoes_desatualizadas,
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
        documentacoes_alegacoes: resultado.selecoes_midias?.[pedido.id]?.revisao === selecao.revisao
          ? resultado.documentacoes_alegacoes
          : Object.fromEntries(Object.entries(resultado.documentacoes_alegacoes ?? {}).filter(([id]) => id !== pedido.id)),
        alegacoes_desatualizadas: resultado.documentacoes_alegacoes?.[pedido.id]
          && resultado.selecoes_midias?.[pedido.id]?.revisao !== selecao.revisao
          ? [...new Set([...(resultado.alegacoes_desatualizadas ?? []), pedido.id])]
          : resultado.alegacoes_desatualizadas,
      };
      setResultado(atualizado);
      setCampanhas((anteriores) => anteriores.map((item) => item.id === campanhaId ? atualizado : item));
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : t.erroPadrao);
    } finally {
      setOcupado(false);
    }
  };

  const atualizarFicha = (chave: string, atual: DadosAlegacoes, mudancas: Partial<DadosAlegacoes>) => {
    setFichas((anteriores) => ({ ...anteriores, [chave]: { ...atual, ...mudancas } }));
  };

  const registrarAlegacoes = async (pedido: PedidoAvulso, dados: DadosAlegacoes) => {
    if (!resultado?.id || !resultado.hash_conteudo) return;
    const aprovacao = resultado.aprovacoes_roteiro?.[pedido.id];
    const selecao = resultado.selecoes_midias?.[pedido.id];
    if (!aprovacao || !selecao) return;
    const campanhaId = resultado.id;
    setOcupado(true);
    setErro("");
    try {
      const resposta = await fetch(`/api/shorts/avulsos/campanhas/${campanhaId}/pedidos/${pedido.id}/alegacoes/registrar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          hash_campanha: resultado.hash_conteudo,
          revisao_roteiro: aprovacao.revisao,
          revisao_midias: selecao.revisao,
          dados: {
            ...dados,
            fontes: dados.sem_alegacoes_verificaveis ? []
              : dados.fontes.filter((item) => item.alegacao.trim() || item.fonte.trim()),
            prova_real: dados.prova_real?.alegacao || dados.prova_real?.fonte ? dados.prova_real : null,
          },
        }),
      });
      const corpo = await resposta.json();
      if (!resposta.ok) {
        const detalhe = typeof corpo.detail === "string" ? corpo.detail
          : Array.isArray(corpo.detail) ? corpo.detail[0]?.msg : t.erroPadrao;
        throw new Error(detalhe || t.erroPadrao);
      }
      const documentacao = corpo as Documentacao;
      const atualizado = {
        ...resultado,
        documentacoes_alegacoes: { ...resultado.documentacoes_alegacoes, [pedido.id]: documentacao },
        alegacoes_desatualizadas: resultado.alegacoes_desatualizadas?.filter((id) => id !== pedido.id),
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
      <form className="rounded-card border border-line bg-surf p-5 space-y-4"
        onSubmit={(evento) => { void planejarAfiliados(evento); }}>
        <div className="space-y-1">
          <h2 className="font-semibold text-tx">{t.tituloAfiliados}</h2>
          <p id="ajuda-planilha" className="text-xs text-mut">{t.ajudaPlanilha}</p>
        </div>
        <textarea
          id="planilha-afiliados"
          aria-describedby="ajuda-planilha"
          className="min-h-32 w-full rounded-btn border border-line bg-bg p-3 font-mono text-sm text-tx focus:outline-none focus:ring-2 focus:ring-brasa"
          placeholder={t.exemploPlanilha}
          maxLength={262144}
          required
          value={planilhaAfiliados}
          onChange={(evento) => { setPlanilhaAfiliados(evento.target.value); setPreviaAfiliados(null); setErro(""); }}
        />
        <button type="submit" disabled={ocupado || !planilhaAfiliados.trim()} className="rounded-btn border border-brasa px-4 py-2 font-semibold text-brasa disabled:opacity-50">
          {ocupado ? t.planejando : t.revisarPlanilha}
        </button>
        {previaAfiliados && (
          <div className="space-y-3">
            <p className="text-sm text-mut">{previaAfiliados.pedidos.length} {t.produtosRevistos}</p>
            <ul className="space-y-2">
              {previaAfiliados.pedidos.map((pedido) => (
                <li key={pedido.id} className="rounded-btn border border-line p-3 text-xs text-mut">
                  <p className="font-semibold text-tx">{pedido.id} · {pedido.tema}</p>
                  {pedido.produto && (
                    <>
                      <p>{pedido.produto.beneficios.join(" · ")}</p>
                      <p>{pedido.produto.preco ? t.campanhaAntigaPreco : t.ofertaSemPreco}</p>
                      <p className="break-all">{pedido.produto.link_afiliado}</p>
                    </>
                  )}
                </li>
              ))}
            </ul>
            <div className="flex flex-wrap items-end gap-3">
              <label className="text-sm text-tx">{t.nomeCampanha}
                <input className="ml-2 rounded-btn border border-line bg-bg p-2 text-tx" maxLength={120}
                  value={nome} onChange={(evento) => setNome(evento.target.value)} />
              </label>
              <button type="button" disabled={ocupado || !nome.trim()}
                onClick={() => { void salvarAfiliados(); }}
                className="rounded-btn bg-brasa px-4 py-2 font-semibold text-bg disabled:opacity-50">
                {t.salvar}
              </button>
            </div>
          </div>
        )}
      </form>
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
          <p className="text-sm text-mut">Produção avulsa: rascunhos sujeitos a revisão final; afiliados mostram a oferta sem preço.</p>
          {resultado.id && resultado.pedidos.some((pedido) => pedido.produto) && (
            <div className="space-y-2 rounded-btn border border-line p-3">
              <p className="text-sm font-medium text-tx">{t.tituloAgenda}</p>
              <p className="text-xs text-mut">{t.ajudaAgenda}</p>
              <button type="button" onClick={() => { void carregarAgenda(); }} disabled={ocupado}
                className="rounded-btn border border-brasa px-3 py-2 text-sm font-semibold text-brasa disabled:opacity-50">
                {t.gerarAgenda}
              </button>
              {agenda && (
                <pre className="max-h-64 overflow-auto rounded-btn border border-line bg-bg p-2 text-xs text-tx">{agenda}</pre>
              )}
            </div>
          )}
          <div className="grid gap-4 md:grid-cols-2">
            {resultado.pedidos.map((pedido) => {
              const formula = resultado.formulas[pedido.formula_id];
              const aprovacao = resultado.aprovacoes_roteiro?.[pedido.id];
              const chave = `${resultado.id}:${pedido.id}`;
              const selecao = resultado.selecoes_midias?.[pedido.id];
              const documentacao = resultado.documentacoes_alegacoes?.[pedido.id];
              const producao = producoes[chave];
              const metadadosRascunho = metadados[chave];
              const ficha = fichas[chave] ?? documentacao?.dados ?? fichaInicial(pedido);
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
                  {pedido.formula_id === "pergunta_comentarios" && pedido.opcao_a && pedido.opcao_b && (
                    <p className="text-sm text-tx">{t.opcoesEngajamento}: A · {pedido.opcao_a} / B · {pedido.opcao_b}</p>
                  )}
                  {pedido.produto && (
                    <div className="space-y-1 rounded-btn border border-line p-3 text-xs text-mut">
                      <p className="font-semibold uppercase tracking-wide text-mut">{t.tituloProduto}</p>
                      <p>{pedido.produto.descricao}</p>
                      <ul className="list-disc pl-4">
                        {pedido.produto.beneficios.map((beneficio) => (
                          <li key={beneficio}>{beneficio}</li>
                        ))}
                      </ul>
                      <p>{pedido.produto.preco ? t.campanhaAntigaPreco : t.ofertaSemPreco}</p>
                      <p>{t.plataforma}: {pedido.produto.plataforma}{pedido.produto.marca ? ` · ${pedido.produto.marca}` : ""}</p>
                      <p className="break-all">{t.linkAfiliado}: {pedido.produto.link_afiliado}</p>
                      <p>{t.linkNaoQueimado}</p>
                    </div>
                  )}
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
                        value={roteiros[chave] ?? aprovacao?.texto ?? pedido.roteiro ?? pedido.roteiro_sugerido ?? ""}
                        onChange={(evento) => setRoteiros((anteriores) => ({ ...anteriores, [chave]: evento.target.value }))}
                      />
                      <button type="button" disabled={ocupado || !(roteiros[chave] ?? aprovacao?.texto ?? pedido.roteiro ?? pedido.roteiro_sugerido ?? "").trim()}
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
                  {resultado.id && aprovacao && selecao && (
                    <div className="space-y-3 rounded-btn border border-line p-3">
                      <p className="text-sm font-medium text-tx">{t.tituloAlegacoes}</p>
                      <p className="text-xs text-mut">{t.avisoAlegacoes}</p>
                      {resultado.alegacoes_desatualizadas?.includes(pedido.id) && (
                        <p className="text-xs text-red-500">{t.alegacoesDesatualizadas}</p>
                      )}
                      <label className="flex gap-2 text-xs text-tx">
                        <input type="checkbox" checked={ficha.sem_alegacoes_verificaveis}
                          onChange={(evento) => atualizarFicha(chave, ficha, {
                            sem_alegacoes_verificaveis: evento.target.checked,
                            fontes: evento.target.checked ? [] : ficha.fontes.length ? ficha.fontes : [{ alegacao: "", fonte: "" }],
                          })} />
                        {t.semAlegacoes}
                      </label>
                      {!ficha.sem_alegacoes_verificaveis && ficha.fontes.map((fonte, indice) => (
                        <div key={indice} className="space-y-1 border-t border-line pt-2">
                          <input aria-label={`${t.alegacao} ${indice + 1}`} placeholder={t.alegacao}
                            className="w-full rounded-btn border border-line bg-bg p-2 text-xs text-tx"
                            value={fonte.alegacao} onChange={(evento) => atualizarFicha(chave, ficha, {
                              fontes: ficha.fontes.map((item, i) => i === indice ? { ...item, alegacao: evento.target.value } : item),
                            })} />
                          <input aria-label={`${t.fonte} ${indice + 1}`} placeholder={t.fonte}
                            className="w-full rounded-btn border border-line bg-bg p-2 text-xs text-tx"
                            value={fonte.fonte} onChange={(evento) => atualizarFicha(chave, ficha, {
                              fontes: ficha.fontes.map((item, i) => i === indice ? { ...item, fonte: evento.target.value } : item),
                            })} />
                        </div>
                      ))}
                      {!ficha.sem_alegacoes_verificaveis && (
                        <button type="button" onClick={() => atualizarFicha(chave, ficha, { fontes: [...ficha.fontes, { alegacao: "", fonte: "" }] })}
                          className="text-xs text-brasa">{t.adicionarFonte}</button>
                      )}
                      <input placeholder={t.provaReal} aria-label={t.provaReal}
                        className="w-full rounded-btn border border-line bg-bg p-2 text-xs text-tx"
                        value={ficha.prova_real?.alegacao ?? ""} onChange={(evento) => atualizarFicha(chave, ficha, {
                          prova_real: { alegacao: evento.target.value, fonte: ficha.prova_real?.fonte ?? "" },
                        })} />
                      <input placeholder={t.fonteProva} aria-label={t.fonteProva}
                        className="w-full rounded-btn border border-line bg-bg p-2 text-xs text-tx"
                        value={ficha.prova_real?.fonte ?? ""} onChange={(evento) => atualizarFicha(chave, ficha, {
                          prova_real: { alegacao: ficha.prova_real?.alegacao ?? "", fonte: evento.target.value },
                        })} />
                      <input placeholder={t.fontePreco} aria-label={t.fontePreco}
                        className="w-full rounded-btn border border-line bg-bg p-2 text-xs text-tx"
                        value={ficha.fonte_preco ?? ""} onChange={(evento) => atualizarFicha(chave, ficha, { fonte_preco: evento.target.value || null })} />
                      <input placeholder={t.condicaoUrgencia} aria-label={t.condicaoUrgencia}
                        className="w-full rounded-btn border border-line bg-bg p-2 text-xs text-tx"
                        value={ficha.condicao_urgencia ?? ""} onChange={(evento) => atualizarFicha(chave, ficha, { condicao_urgencia: evento.target.value || null })} />
                      <label className="block text-xs text-tx">{t.relacaoComercial}
                        <select value={ficha.relacao_comercial}
                          onChange={(evento) => atualizarFicha(chave, ficha, { relacao_comercial: evento.target.value as DadosAlegacoes["relacao_comercial"] })}
                          className="mt-1 w-full rounded-btn border border-line bg-bg p-2 text-tx">
                          <option value="nenhuma">{t.semRelacao}</option>
                          <option value="produto_proprio">{t.produtoProprio}</option>
                          <option value="afiliado">{t.afiliado}</option>
                          <option value="parceria_paga">{t.parceriaPaga}</option>
                        </select>
                      </label>
                      {(ficha.relacao_comercial === "parceria_paga" || pedido.produto) && (
                        <input placeholder={t.marca} aria-label={t.marca}
                          className="w-full rounded-btn border border-line bg-bg p-2 text-xs text-tx"
                          value={ficha.marca ?? ""} onChange={(evento) => atualizarFicha(chave, ficha, { marca: evento.target.value || null })} />
                      )}
                      <label className="flex gap-2 text-xs text-tx"><input type="checkbox" checked={ficha.aviso_publicidade}
                        onChange={(evento) => atualizarFicha(chave, ficha, { aviso_publicidade: evento.target.checked })} />
                        {t.avisoPublicidade}</label>
                      <label className="flex gap-2 text-xs text-tx"><input type="checkbox" checked={ficha.revisado_pelo_usuario}
                        onChange={(evento) => atualizarFicha(chave, ficha, { revisado_pelo_usuario: evento.target.checked })} />
                        {t.confirmacaoHumana}</label>
                      <button type="button" disabled={ocupado || !ficha.revisado_pelo_usuario}
                        onClick={() => { void registrarAlegacoes(pedido, ficha); }}
                        className="rounded-btn border border-brasa px-3 py-2 text-sm font-semibold text-brasa disabled:opacity-50">
                        {t.registrarAlegacoes}
                      </button>
                      {documentacao && <p className="text-xs text-mut">{t.alegacoesRegistradas} · {documentacao.revisao.slice(0, 8)}</p>}
                    </div>
                  )}
                  {resultado.id && (
                    <div className="space-y-2 rounded-btn border border-line p-3">
                      <p className="text-sm font-medium text-tx">Produzir rascunho vertical</p>
                      <p className="text-xs text-mut">
                        {pedido.produto
                          ? "Short de afiliado: exige aviso de publicidade, marca da loja e fontes das alegações. Não fala nem mostra preço; o link vai nos textos, metadados e agenda."
                          : "Somente educativo, sem relação comercial, com CTA no roteiro aprovado exatamente uma vez. Sem música nem publicação automática."}
                      </p>
                      <p className="text-xs text-mut">CTA informado no CSV: {pedido.cta || "não informado"}</p>
                      <label className="block text-xs text-tx">Confirmação: digite PRODUZIR
                        <input value={codigos[chave] ?? ""} autoComplete="off"
                          onChange={(evento) => setCodigos((anteriores) => ({ ...anteriores, [chave]: evento.target.value }))}
                          className="mt-1 block w-full rounded-btn border border-line bg-bg p-2 text-tx" />
                      </label>
                      <button type="button" onClick={() => { void produzirAvulso(pedido); }}
                        disabled={ocupado || codigos[chave] !== "PRODUZIR" || !aprovacao || !selecao || !documentacao || !relacaoPermitida(pedido, documentacao) || producao?.status === "aguardando" || producao?.status === "executando"}
                        className="rounded-btn border border-brasa px-3 py-2 text-sm font-semibold text-brasa disabled:opacity-50">
                        Produzir rascunho
                      </button>
                      {producao && <p className="text-xs text-mut">Estado: {producao.status}{producao.erro ? ` — ${producao.erro}` : ""}</p>}
                      {producao?.status === "concluido" && (
                        <div className="space-y-2">
                          <video controls preload="none" className="mx-auto max-h-[560px] w-auto max-w-full" src={`/api/shorts/avulsos/campanhas/${resultado.id}/pedidos/${pedido.id}/artefatos/video.mp4`} />
                          <a className="text-sm text-brasa underline" href={`/api/shorts/avulsos/campanhas/${resultado.id}/pedidos/${pedido.id}/artefatos/legendas.srt`}>Baixar legendas</a>
                          <p className="text-xs text-mut">Rascunho não autorizado para publicação; confira alegações, imagem, áudio e QA.</p>
                          {metadadosRascunho && (
                            <div className="space-y-1 rounded-btn border border-line p-2">
                              <p className="text-xs font-semibold uppercase tracking-wide text-mut">{t.qaTitulo}</p>
                              <p className="text-xs text-mut">
                                {t.qaDuracao}: {metadadosRascunho.duracao_s.toFixed(1)} s · {t.qaWer}:{" "}
                                {metadadosRascunho.wer === null ? "—" : `${(metadadosRascunho.wer * 100).toFixed(2)}%`}
                              </p>
                              <ul className="space-y-1 text-xs">
                                {metadadosRascunho.qa.violacoes.map((regra) => (
                                  <li key={regra.regra} className={regra.aprovada ? "text-mut" : "text-brasa"}>
                                    <span className="font-semibold">{regra.regra}</span>{" "}
                                    {regra.aprovada ? t.qaAprovada : t.qaReprovada} — {regra.descricao}
                                    {regra.detalhes ? ` (${regra.detalhes})` : ""}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  <div>
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-mut">{t.pendencias}</p>
                    <ul className="list-disc pl-5 text-sm text-mut">
                      {pedido.pendencias.filter((item) => !(
                        (aprovacao && item === "aprovar roteiro")
                        || (selecao && item === "aprovar mídias e licenças")
                        || (documentacao && item === "comprovar alegações exigidas pela fórmula")
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
