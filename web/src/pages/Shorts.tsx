import React, { useMemo, useState } from "react";
import { Check, CircleAlert, Clapperboard, Smartphone, WandSparkles } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ErroCarregamento } from "../components/ErroCarregamento";
import { usePlano } from "../hooks/usePlano";

type FrasePonte = { texto: string; aprovada: boolean };
type Candidato = {
  id: string;
  inicio_s: number;
  fim_s: number;
  segmento_ids: string[];
  texto: string;
  pontuacao: number;
  componentes: Record<string, number>;
  motivos: string[];
  frases_ponte: FrasePonte[];
};
type ShortDerivado = {
  referencia: string;
  candidato: Candidato;
  aprovacao: { versao: string; candidato: Candidato } | null;
  manifesto_atual: { versao: string; shots: number } | null;
  producao: {
    status: "aguardando" | "executando" | "concluido" | "falhou";
    erro?: string;
    resultado?: {
      idioma: string;
      revisao: string;
      duracao_s: number;
      qa_aprovado: boolean;
      falhas_qa: string[];
    };
  } | null;
};
type DadosShorts = {
  fonte_hash: string;
  candidatos: ShortDerivado[];
};

const nomesComponentes: Record<string, string> = {
  batida_forte: "Gancho ou revelação",
  autonomia: "Entendimento sozinho",
  curiosidade: "Curiosidade para o longo",
  forca_visual: "Potencial visual",
  duracao_ritmo: "Duração e ritmo",
};

const tempo = (segundos: number) => {
  const minutos = Math.floor(segundos / 60);
  const resto = Math.floor(segundos % 60);
  return `${String(minutos).padStart(2, "0")}:${String(resto).padStart(2, "0")}`;
};

async function medirImagem(url: string): Promise<[number, number]> {
  return new Promise((resolve, reject) => {
    const imagem = new Image();
    imagem.onload = () => resolve([imagem.naturalWidth, imagem.naturalHeight]);
    imagem.onerror = () => reject(new Error("Não foi possível medir uma imagem licenciada."));
    imagem.src = url;
  });
}

export const Shorts: React.FC<{ slug: string }> = ({ slug }) => {
  const queryClient = useQueryClient();
  const plano = usePlano(slug);
  const [escolhas, setEscolhas] = useState<Record<string, string>>({});
  const [frasesEditadas, setFrasesEditadas] = useState<Record<string, string>>({});
  const [estrategias, setEstrategias] = useState<Record<string, "recorte" | "fundo_desfocado">>({});
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [manifestos, setManifestos] = useState<Record<string, { versao: string; shots: number }>>({});

  const query = useQuery<DadosShorts>({
    queryKey: ["shorts-derivados", slug],
    enabled: Boolean(slug),
    refetchInterval: 10000,
    queryFn: async () => {
      const resposta = await fetch(`/api/projetos/${encodeURIComponent(slug)}/shorts/derivados`);
      const corpo = await resposta.json().catch(() => ({}));
      if (!resposta.ok) throw new Error(corpo.detail || "Não foi possível carregar os candidatos.");
      return corpo;
    },
  });

  const shotsPorSegmento = useMemo(() => {
    const mapa = new Map<string, string[]>();
    for (const bloco of plano.data?.plano?.blocos ?? []) {
      for (const shot of bloco.shots) {
        for (const segmento of shot.segmentos) {
          mapa.set(segmento, [...(mapa.get(segmento) ?? []), ...shot.ativos]);
        }
      }
    }
    return mapa;
  }, [plano.data?.plano?.blocos]);

  const aprovar = async (item: ShortDerivado) => {
    const escolha = escolhas[item.referencia] ?? "0";
    const ponteAnterior = item.aprovacao?.candidato.frases_ponte.find((frase) => frase.aprovada)?.texto;
    const ponteAnteriorEraPersonalizada = !item.candidato.frases_ponte.some(
      (frase) => frase.texto === ponteAnterior,
    );
    const frase = escolha === "personalizada"
      ? (frasesEditadas[item.referencia] ?? (ponteAnteriorEraPersonalizada ? ponteAnterior : ""))?.trim()
      : undefined;
    if (escolha === "personalizada" && !frase) {
      toast.error("Escreva a frase-ponte personalizada antes de aprovar.");
      return;
    }
    setOcupado(item.referencia);
    try {
      const resposta = await fetch(
        `/api/projetos/${encodeURIComponent(slug)}/shorts/derivados/${item.referencia}/aprovar`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(frase ? { frase_personalizada: frase } : { indice_frase: Number(escolha) }),
        },
      );
      const corpo = await resposta.json().catch(() => ({}));
      if (!resposta.ok) throw new Error(corpo.detail || "Não foi possível salvar a aprovação.");
      await queryClient.invalidateQueries({ queryKey: ["shorts-derivados", slug] });
      toast.success("Frase-ponte aprovada e salva em uma nova revisão.");
    } catch (erro) {
      toast.error(erro instanceof Error ? erro.message : "Falha ao salvar a aprovação.");
    } finally {
      setOcupado(null);
    }
  };

  const gerarManifesto = async (item: ShortDerivado) => {
    const ativosIds = [...new Set(item.candidato.segmento_ids.flatMap((id) => shotsPorSegmento.get(id) ?? []))];
    const ativos = ativosIds.map((id) => ({ id, ativo: plano.data?.ativos?.[id] }));
    const semImagem = ativos.find(({ ativo }) => !ativo?.imagem_url);
    if (semImagem) {
      toast.error(`O ativo ${semImagem.id} não tem imagem com licença liberada para prévia/verticalização.`);
      return;
    }
    setOcupado(item.referencia);
    try {
      const dimensoes = Object.fromEntries(await Promise.all(
        ativos.map(async ({ id, ativo }) => [id, await medirImagem(ativo!.imagem_url!)] as const),
      ));
      const resposta = await fetch(
        `/api/projetos/${encodeURIComponent(slug)}/shorts/derivados/${item.referencia}/manifesto-vertical`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            dimensoes,
            estrategia: estrategias[item.referencia] ?? "recorte",
          }),
        },
      );
      const corpo = await resposta.json().catch(() => ({}));
      if (!resposta.ok) throw new Error(corpo.detail || "Não foi possível criar o manifesto vertical.");
      setManifestos((atuais) => ({
        ...atuais,
        [item.referencia]: {
          versao: corpo.versao,
          shots: corpo.manifesto.shots.length,
        },
      }));
      await queryClient.invalidateQueries({ queryKey: ["shorts-derivados", slug] });
      toast.success("Manifesto vertical salvo. O plano mestre não foi alterado.");
    } catch (erro) {
      toast.error(erro instanceof Error ? erro.message : "Falha ao gerar o manifesto vertical.");
    } finally {
      setOcupado(null);
    }
  };

  const produzir = async (item: ShortDerivado) => {
    setOcupado(item.referencia);
    try {
      const resposta = await fetch(
        `/api/projetos/${encodeURIComponent(slug)}/shorts/derivados/${item.referencia}/produzir`,
        { method: "POST" },
      );
      const corpo = await resposta.json().catch(() => ({}));
      if (!resposta.ok) throw new Error(corpo.detail || "Não foi possível iniciar a produção.");
      await queryClient.invalidateQueries({ queryKey: ["shorts-derivados", slug] });
      toast.success("Produção iniciada. A tela atualizará o andamento automaticamente.");
    } catch (erro) {
      toast.error(erro instanceof Error ? erro.message : "Falha ao iniciar a produção.");
    } finally {
      setOcupado(null);
    }
  };

  if (!slug) return <div className="p-8 text-mut">Selecione um projeto longo em Início para revisar shorts.</div>;
  if (plano.isLoading || query.isLoading) return <div className="p-8 text-mut">Carregando candidatos…</div>;
  if (plano.error) return <ErroCarregamento tentarNovamente={() => { void plano.refetch(); }} />;
  if (query.error) {
    const mensagem = query.error instanceof Error ? query.error.message : "Falha ao carregar shorts.";
    if (mensagem.includes("Plano e narração segmentada")) {
      return <div className="p-6 xl:p-8 max-w-3xl mx-auto space-y-3"><p className="text-xs uppercase tracking-widest text-brasa">Projeto · Shorts</p><h1 className="text-2xl font-bold">Candidatos ainda não disponíveis</h1><p className="text-sm text-mut">Finalize o plano longo e a narração segmentada para receber sugestões de trechos.</p></div>;
    }
    return <ErroCarregamento tentarNovamente={() => { void query.refetch(); }} />;
  }

  const candidatos = query.data?.candidatos ?? [];
  return (
    <div className="p-6 xl:p-8 max-w-[1500px] mx-auto space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-brasa">Projeto · Shorts derivados</p>
          <h1 className="text-2xl font-bold mt-1">Momentos para levar ao vídeo completo</h1>
          <p className="text-sm text-mut mt-2 max-w-3xl">Revise os trechos sugeridos, aprove uma frase-ponte e prepare o manifesto 9:16. O roteiro e o plano mestre continuam intactos.</p>
        </div>
        <div className="flex items-center gap-2 rounded-btn border border-line bg-surf px-3 py-2 text-xs text-mut"><Smartphone className="w-4 h-4 text-brasa" />Produção vertical · idioma principal</div>
      </header>

      {candidatos.length === 0 ? (
        <div className="rounded-card border border-line bg-surf p-8 text-center space-y-2">
          <Clapperboard className="w-8 h-8 text-mut mx-auto" />
          <h2 className="font-semibold">Nenhum trecho contínuo entre 20 e 55 segundos foi encontrado</h2>
          <p className="text-sm text-mut">Confira se a narração está segmentada e alinhada ao plano longo.</p>
        </div>
      ) : (
        <div className="space-y-5">
          {candidatos.map((item, indice) => {
            const candidato = item.candidato;
            const aprovado = item.aprovacao?.candidato;
            const frases = candidato.frases_ponte;
            const indicePonteAprovada = aprovado?.frases_ponte.findIndex((frase) => frase.aprovada) ?? -1;
            const textoPonteAprovada = aprovado?.frases_ponte.find((frase) => frase.aprovada)?.texto;
            const escolhaPadrao = indicePonteAprovada >= 0
              ? String(indicePonteAprovada)
              : textoPonteAprovada
                ? "personalizada"
                : "0";
            const escolha = escolhas[item.referencia] ?? escolhaPadrao;
            const fraseEscolhida = escolha === "personalizada"
              ? frasesEditadas[item.referencia] ?? textoPonteAprovada ?? ""
              : frases[Number(escolha)]?.texto ?? "";
            const faixaTexto = candidato.texto.length > 150
              ? `${candidato.texto.slice(0, 147).trimEnd()}…`
              : candidato.texto;
            const ativo = ocupado === item.referencia;
            return (
              <article key={item.referencia} className="rounded-card border border-line bg-surf overflow-hidden">
                <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_300px]">
                  <div className="p-5 md:p-6 space-y-5">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div><p className="text-xs text-mut">Sugestão {indice + 1} · {tempo(candidato.inicio_s)}–{tempo(candidato.fim_s)}</p><h2 className="text-lg font-semibold mt-1">Trecho de {Math.round(candidato.fim_s - candidato.inicio_s)} segundos</h2></div>
                      <div className="rounded-btn border border-brasa/40 bg-brasa/10 px-3 py-2 text-center"><strong className="text-xl text-brasa">{candidato.pontuacao.toFixed(1)}</strong><span className="block text-[11px] text-mut">pontuação / 100</span></div>
                    </div>
                    <blockquote className="border-l-2 border-brasa pl-4 text-sm leading-relaxed">{candidato.texto}</blockquote>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-5 gap-y-2" aria-label="Critérios da pontuação">
                      {Object.entries(candidato.componentes).map(([chave, nota]) => <div key={chave} className="flex justify-between gap-3 text-xs"><span className="text-mut">{nomesComponentes[chave] ?? chave}</span><span>{nota.toFixed(1)}/10</span></div>)}
                    </div>
                    <details className="text-xs text-mut"><summary className="cursor-pointer hover:text-tx">Como essa nota foi calculada</summary><ul className="list-disc pl-5 mt-2 space-y-1">{candidato.motivos.map((motivo) => <li key={motivo}>{motivo}</li>)}</ul></details>

                    <fieldset className="space-y-2">
                      <legend className="text-sm font-semibold">Frase-ponte para o vídeo completo</legend>
                      {frases.map((frase, posicao) => <label key={`${posicao}-${frase.texto}`} className={`flex gap-3 rounded-btn border p-3 text-sm cursor-pointer ${escolha === String(posicao) ? "border-brasa bg-brasa/5" : "border-line hover:border-brasa/50"}`}><input type="radio" name={`ponte-${item.referencia}`} value={posicao} checked={escolha === String(posicao)} onChange={() => setEscolhas((atuais) => ({ ...atuais, [item.referencia]: String(posicao) }))} className="accent-[rgb(var(--color-brasa))] mt-0.5" /><span>{frase.texto}</span></label>)}
                      <label className={`flex gap-3 rounded-btn border p-3 text-sm cursor-pointer ${escolha === "personalizada" ? "border-brasa bg-brasa/5" : "border-line hover:border-brasa/50"}`}><input type="radio" name={`ponte-${item.referencia}`} value="personalizada" checked={escolha === "personalizada"} onChange={() => setEscolhas((atuais) => ({ ...atuais, [item.referencia]: "personalizada" }))} className="accent-[rgb(var(--color-brasa))] mt-0.5" /><span className="font-medium">Escrever outra frase</span></label>
                      {escolha === "personalizada" && <textarea aria-label="Frase-ponte personalizada" maxLength={240} value={frasesEditadas[item.referencia] ?? (indicePonteAprovada < 0 ? textoPonteAprovada ?? "" : "")} onChange={(evento) => setFrasesEditadas((atuais) => ({ ...atuais, [item.referencia]: evento.target.value }))} placeholder="Digite uma frase curta para convidar ao vídeo completo" className="w-full min-h-20 rounded-btn border border-line bg-elev px-3 py-2 text-sm outline-none focus:border-brasa" />}
                    </fieldset>

                    <div className="flex flex-wrap items-center gap-3">
                      <button disabled={ativo} onClick={() => { void aprovar(item); }} className="inline-flex items-center gap-2 rounded-btn bg-brasa px-4 py-2 text-sm font-semibold text-bg disabled:opacity-50"><Check className="w-4 h-4" />{ativo ? "Salvando…" : aprovado ? "Salvar nova aprovação" : "Aprovar frase-ponte"}</button>
                      {aprovado && <span className="text-xs text-ok">Ponte aprovada · revisão {item.aprovacao?.versao.slice(0, 8)}</span>}
                    </div>

                    {aprovado && <div className="border-t border-line pt-4 space-y-3">
                      <div><h3 className="text-sm font-semibold">Preparar versão vertical 9:16</h3><p className="text-xs text-mut mt-1">Usa apenas imagens liberadas para prévia. O foco começa centralizado; confira o enquadramento antes de renderizar.</p></div>
                      <div className="flex flex-wrap items-end gap-3">
                        <label className="text-xs text-mut">Enquadramento<select value={estrategias[item.referencia] ?? "recorte"} onChange={(evento) => setEstrategias((atuais) => ({ ...atuais, [item.referencia]: evento.target.value as "recorte" | "fundo_desfocado" }))} className="block mt-1 rounded-btn border border-line bg-elev px-3 py-2 text-sm text-tx"><option value="recorte">Recorte central</option><option value="fundo_desfocado">Imagem inteira com fundo desfocado</option></select></label>
                        <button disabled={ativo} onClick={() => { void gerarManifesto(item); }} className="inline-flex items-center gap-2 rounded-btn border border-line px-4 py-2 text-sm hover:border-brasa disabled:opacity-50"><WandSparkles className="w-4 h-4 text-brasa" />{ativo ? "Preparando…" : "Gerar manifesto vertical"}</button>
                      </div>
                      {manifestos[item.referencia] && <p role="status" className="text-xs text-ok">Manifesto salvo · {manifestos[item.referencia].shots} shots · revisão {manifestos[item.referencia].versao.slice(0, 8)}</p>}
                      {item.manifesto_atual && <p className="text-xs text-ok">Manifesto vigente · {item.manifesto_atual.shots} shots · revisão {item.manifesto_atual.versao.slice(0, 8)}</p>}
                      {(item.manifesto_atual || manifestos[item.referencia]) && <div className="space-y-2">
                        <button disabled={ativo || item.producao?.status === "aguardando" || item.producao?.status === "executando"} onClick={() => { void produzir(item); }} className="inline-flex items-center gap-2 rounded-btn bg-brasa px-4 py-2 text-sm font-semibold text-bg disabled:opacity-50">
                          <Clapperboard className="w-4 h-4" />
                          {item.producao?.status === "aguardando" || item.producao?.status === "executando" ? "Produzindo…" : item.producao?.status === "concluido" ? "Produzir nova revisão" : "Produzir short"}
                        </button>
                        <p className="text-xs text-mut">A primeira versão usa o idioma principal e a voz TTS configurada. Projetos com narração gravada ficam bloqueados até a ponte gravada estar disponível.</p>
                      </div>}
                      {item.producao?.status === "falhou" && <p role="alert" className="text-xs text-err">A produção não foi concluída: {item.producao.erro || "verifique os arquivos e tente novamente"}</p>}
                      {item.producao?.status === "concluido" && item.producao.resultado && <div className="space-y-2 rounded-btn border border-line bg-bg p-3">
                        <p role="status" className={`text-xs ${item.producao.resultado.qa_aprovado ? "text-ok" : "text-brasa"}`}>
                          Rascunho renderizado · {item.producao.resultado.idioma} · {Math.round(item.producao.resultado.duracao_s)} s · QA {item.producao.resultado.qa_aprovado ? "aprovado" : `com pendências (${item.producao.resultado.falhas_qa.join(", ") || "ver relatório"})`}
                        </p>
                        <video controls preload="metadata" className="w-full max-h-[320px] rounded-btn bg-black" src={`/api/projetos/${encodeURIComponent(slug)}/shorts/derivados/${item.referencia}/saida/video.mp4`} />
                        <div className="flex gap-3 text-xs"><a className="text-brasa underline" href={`/api/projetos/${encodeURIComponent(slug)}/shorts/derivados/${item.referencia}/saida/capa.jpg`} target="_blank" rel="noreferrer">Ver capa</a><a className="text-brasa underline" href={`/api/projetos/${encodeURIComponent(slug)}/shorts/derivados/${item.referencia}/saida/legendas.srt`} target="_blank" rel="noreferrer">Baixar legendas</a></div>
                      </div>}
                    </div>}
                  </div>

                  <aside className="bg-bg/70 border-t xl:border-t-0 xl:border-l border-line p-5 flex flex-col items-center justify-center gap-3">
                    <p className="text-[11px] uppercase tracking-widest text-mut">Moldura de celular · rascunho</p>
                    <div className="w-[220px] aspect-[9/16] rounded-[2rem] border-[5px] border-elev bg-black p-3 shadow-xl flex flex-col justify-between overflow-hidden">
                      <div className="flex items-center justify-between text-[9px] text-white/55"><span>● ● ●</span><span>SHORT · 9:16</span></div>
                      <div className="space-y-4 text-center">
                        <span className="inline-block rounded-full bg-brasa px-2 py-1 text-[9px] font-bold text-bg">{candidato.segmento_ids[0]}</span>
                        <p className="text-base font-bold leading-snug text-white">{faixaTexto}</p>
                      </div>
                      <div className="space-y-2"><p className="rounded bg-white/90 px-2 py-1 text-center text-[10px] font-semibold leading-snug text-black">{fraseEscolhida || "Sua frase-ponte aparecerá aqui"}</p><div className="h-1 rounded bg-white/20"><div className="h-1 w-1/3 rounded bg-brasa" /></div><p className="text-center text-[9px] text-white/45">Prévia textual · sem vídeo renderizado</p></div>
                    </div>
                    <p className="max-w-[250px] text-center text-[11px] text-mut flex gap-1.5"><CircleAlert className="w-3.5 h-3.5 shrink-0" />A moldura mostra trecho e ponte; ainda não reproduz áudio, imagens ou legendas.</p>
                  </aside>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
};
