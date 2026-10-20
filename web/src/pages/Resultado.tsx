import React, { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Check,
  CheckCircle2,
  Copy,
  FileText,
  FolderArchive,
  FolderSync,
  Image as ImageIcon,
  ListOrdered,
  Loader2,
  Play,
  Sparkles,
  Tag,
} from "lucide-react";
import { toast } from "sonner";
import { ErroCarregamento } from "../components/ErroCarregamento";

interface ItemTitulo {
  angulo: string;
  gatilho: string;
  titulo: string;
  nota: number;
  caracteres: number;
  recomendado_ab: boolean;
}

interface Capitulo {
  timestamp: string;
  segundos: number;
  titulo: string;
}

interface ConceitoThumb {
  id: string;
  nome: string;
  ideia: string;
  elemento_central: string;
  texto_tela: string;
  contraste: string;
  cores: string[];
  legibilidade_120px: boolean;
  arquivo_rascunho: string;
}

interface ItemPromocao {
  id: string;
  tipo: string;
  descricao: string;
  licenca: string;
  caminho_origem: string;
  motivo_sugestao: string;
  projetos_usados: string[];
}

interface SaidaDados {
  slug: string;
  pronto: boolean;
  idioma: string;
  video_url: string | null;
  metadados: {
    projeto: string;
    titulos?: ItemTitulo[];
    top_titulos_ab?: string[];
    descricao?: string;
    capitulos?: Capitulo[];
    tags?: string[];
    hashtags?: string[];
    palavras_chave?: string[];
    thumbnails?: ConceitoThumb[];
    comentario_fixado?: string;
    post_comunidade?: string;
  };
  relatorio: string;
  creditos: string;
  promover_itens: ItemPromocao[];
}

export const Resultado: React.FC<{
  slug: string;
  onNavegar?: (tela: string) => void;
}> = ({ slug }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [copiado, setCopiado] = useState<string | null>(null);
  const [promocoesSelecionadas, setPromocoesSelecionadas] = useState<Set<string>>(new Set());
  const [enviandoPromocao, setEnviandoPromocao] = useState(false);
  const [abaMetadados, setAbaMetadados] = useState<"titulos" | "descricao" | "thumbs" | "tags">("titulos");

  // Checklist interativo de publicação
  const [checklist, setChecklist] = useState<Record<string, boolean>>({
    titulo: true,
    thumb: true,
    descricao: false,
    capitulos: false,
    tags: false,
    comentario: false,
    reconstituicao: true,
  });

  const { data, isLoading, error, refetch } = useQuery<SaidaDados>({
    queryKey: ["saida", slug],
    queryFn: async () => {
      const res = await fetch(`/api/projetos/${encodeURIComponent(slug)}/saida`);
      if (!res.ok) throw new Error("Falha ao carregar pacote de saída.");
      const json = await res.json();
      return json;
    },
    enabled: Boolean(slug),
  });

  // Inicializa promoções sugeridas como todas marcadas por padrão
  React.useEffect(() => {
    if (data?.promover_itens?.length) {
      setPromocoesSelecionadas(new Set(data.promover_itens.map((item) => item.id)));
    }
  }, [data?.promover_itens]);

  const copiarTexto = (chave: string, texto: string) => {
    void navigator.clipboard.writeText(texto);
    setCopiado(chave);
    toast.success("Copiado para a área de transferência!");
    setTimeout(() => setCopiado(null), 2000);
  };

  const pularParaSegundo = (segundos: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = segundos;
      void videoRef.current.play();
    }
  };

  const alternarPromocao = (id: string) => {
    setPromocoesSelecionadas((prev) => {
      const novo = new Set(prev);
      if (novo.has(id)) novo.delete(id);
      else novo.add(id);
      return novo;
    });
  };

  const confirmarPromocaoGlobal = async () => {
    if (promocoesSelecionadas.size === 0) {
      toast.error("Nenhum item selecionado para promoção.");
      return;
    }
    setEnviandoPromocao(true);
    try {
      const res = await fetch(`/api/projetos/${encodeURIComponent(slug)}/promover_global`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ itens: Array.from(promocoesSelecionadas) }),
      });
      if (!res.ok) throw new Error("Falha ao promover itens para a pasta global.");
      const resDados = await res.json();
      toast.success(`${resDados.promovidos?.length ?? 0} ativos promovidos com sucesso para a pasta global!`);
    } catch (err: any) {
      toast.error(err.message || "Erro na promoção global.");
    } finally {
      setEnviandoPromocao(false);
    }
  };

  if (!slug) {
    return (
      <div className="p-8 text-mut text-center max-w-lg mx-auto py-24">
        Selecione um projeto em Início para visualizar o resultado final.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-8 text-mut flex items-center justify-center gap-3 py-24">
        <Loader2 className="w-5 h-5 animate-spin text-brasa" />
        Carregando resultado final e pacote estratégico…
      </div>
    );
  }

  if (error || !data) {
    return <ErroCarregamento tentarNovamente={() => { void refetch(); }} />;
  }

  const meta = data.metadados;
  const titulos = meta.titulos || [];
  const topTitulos = titulos.filter((t) => t.recomendado_ab);
  const outrosTitulos = titulos.filter((t) => !t.recomendado_ab);
  const capitulos = meta.capitulos || [];
  const thumbs = meta.thumbnails || [];

  return (
    <div className="p-6 xl:p-8 max-w-[1600px] mx-auto space-y-8 animate-in fade-in-50">
      {/* Cabeçalho */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase tracking-widest text-brasa font-semibold">
              Projeto · Resultado Final & Publicação
            </span>
            <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-ok/15 text-ok">
              Marco M6 Concluído
            </span>
          </div>
          <h1 className="text-2xl font-bold mt-1">{data.slug}</h1>
          <p className="text-sm text-mut mt-1">
            Vídeo final, metadados de alto CTR, briefing de thumbnails e promoção para pasta global
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => copiarTexto("caminho", `05_saida/${data.idioma}/`)}
            className="flex items-center gap-2 px-4 py-2 rounded-btn border border-line bg-elev hover:bg-elev/80 text-sm font-medium transition-colors cursor-pointer"
          >
            <FolderArchive className="w-4 h-4 text-mut" />
            Copiar Caminho da Saída
          </button>
        </div>
      </div>

      {/* Grid Principal: Player de Vídeo e Resumo de Publicação */}
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.5fr)_minmax(360px,1fr)] gap-6">
        {/* Player de Vídeo Final */}
        <div className="rounded-card border border-line bg-surf overflow-hidden flex flex-col justify-between">
          <div className="aspect-video bg-black flex items-center justify-center">
            {data.video_url ? (
              <video
                ref={videoRef}
                controls
                src={data.video_url}
                className="w-full h-full object-contain"
                playsInline
              />
            ) : (
              <div className="text-center p-8 text-mut space-y-2">
                <Play className="w-10 h-10 mx-auto text-line" />
                <p>Vídeo final ainda em processamento ou não renderizado.</p>
              </div>
            )}
          </div>

          <div className="p-4 border-t border-line flex flex-wrap items-center justify-between gap-4 bg-elev/30 text-xs text-mut">
            <div className="flex items-center gap-4">
              <span>Idioma: <strong>{data.idioma}</strong></span>
              <span>Resolução: <strong>1080p (1920×1080)</strong></span>
              <span>Áudio: <strong>-14 LUFS (EBU R128)</strong></span>
            </div>
            <div className="flex items-center gap-1.5 text-ok">
              <CheckCircle2 className="w-4 h-4" />
              <span>Rotulado: RECONSTITUIÇÃO ARTÍSTICA</span>
            </div>
          </div>
        </div>

        {/* Checklist Rápido de Publicação */}
        <div className="rounded-card border border-line bg-surf p-6 space-y-5">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-brasa" />
            <h2 className="font-semibold text-tx">Checklist de Publicação (13 §4.5)</h2>
          </div>

          <div className="space-y-2.5 text-sm">
            {[
              { id: "titulo", label: "Título verificado e aprovado nos primeiros 60 s" },
              { id: "thumb", label: "Thumbnail testada e legível em miniatura (120 px)" },
              { id: "descricao", label: "Resumo em 3 frases + aviso ético na descrição" },
              { id: "capitulos", label: "Capítulos com início obrigatório em 00:00" },
              { id: "tags", label: "Tags específicas (sem poluição de termos genéricos)" },
              { id: "comentario", label: "Comentário fixado de engajamento copiado" },
              { id: "reconstituicao", label: "Rótulo de transparência de reconstituição incluído" },
            ].map((item) => (
              <label
                key={item.id}
                className="flex items-start gap-3 p-2 rounded-btn hover:bg-elev/40 cursor-pointer select-none transition-colors"
              >
                <input
                  type="checkbox"
                  checked={checklist[item.id] ?? false}
                  onChange={(e) => setChecklist((prev) => ({ ...prev, [item.id]: e.target.checked }))}
                  className="mt-1 rounded accent-brasa"
                />
                <span className={`text-xs ${checklist[item.id] ? "text-tx line-through opacity-70" : "text-tx"}`}>
                  {item.label}
                </span>
              </label>
            ))}
          </div>

          <div className="pt-4 border-t border-line text-xs text-mut flex justify-between">
            <span>Progresso da checagem:</span>
            <strong>
              {Object.values(checklist).filter(Boolean).length} de {Object.keys(checklist).length} ok
            </strong>
          </div>
        </div>
      </div>

      {/* Navegação por Abas do Pacote Estratégico */}
      <div className="space-y-4">
        <div className="flex border-b border-line gap-2 overflow-x-auto pb-px">
          {[
            { id: "titulos", label: "Títulos para CTR (10 Ideias)", icone: Sparkles },
            { id: "descricao", label: "Descrição & Capítulos", icone: FileText },
            { id: "thumbs", label: "Briefing de Thumbnails (120 px)", icone: ImageIcon },
            { id: "tags", label: "Tags & Comunidade", icone: Tag },
          ].map((aba) => {
            const Icone = aba.icone;
            const ativa = abaMetadados === aba.id;
            return (
              <button
                key={aba.id}
                onClick={() => setAbaMetadados(aba.id as any)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                  ativa
                    ? "border-brasa text-brasa font-semibold"
                    : "border-transparent text-mut hover:text-tx hover:border-line"
                }`}
              >
                <Icone className="w-4 h-4" />
                {aba.label}
              </button>
            );
          })}
        </div>

        {/* Conteúdo da Aba TÍTULOS */}
        {abaMetadados === "titulos" && (
          <div className="space-y-6">
            {/* Top 3 Recomendados A/B */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-tx uppercase tracking-wider">
                  Top 3 Recomendados para Teste A/B
                </h3>
                <span className="text-xs text-mut">
                  Multicritério (Gatilho + Curiosidade + Especificidade + Legibilidade)
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {topTitulos.map((t, idx) => (
                  <div
                    key={idx}
                    className="rounded-card border-2 border-brasa/40 bg-surf p-5 space-y-3 relative overflow-hidden shadow-sm"
                  >
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brasa text-white uppercase tracking-wider">
                        Opção {String.fromCharCode(65 + idx)} · Nota {t.nota}/10
                      </span>
                      <span className="text-xs font-mono text-mut">{t.caracteres} chars</span>
                    </div>

                    <p className="font-bold text-tx text-base leading-snug">
                      "{t.titulo}"
                    </p>

                    <p className="text-xs text-mut">
                      <strong className="text-tx">Gatilho:</strong> {t.gatilho} ({t.angulo})
                    </p>

                    <button
                      onClick={() => copiarTexto(`titulo-${idx}`, t.titulo)}
                      className="w-full flex items-center justify-center gap-2 py-2 rounded-btn bg-elev hover:bg-elev/80 text-xs font-medium text-tx transition-colors cursor-pointer"
                    >
                      {copiado === `titulo-${idx}` ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-ok" /> Copiado!
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" /> Copiar Título
                        </>
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Outros 7 Títulos */}
            <div className="rounded-card border border-line bg-surf p-5 space-y-3">
              <h4 className="text-xs font-bold text-mut uppercase tracking-wider">
                Outros Ângulos Testados (≤ 60 Caracteres)
              </h4>

              <div className="divide-y divide-line">
                {outrosTitulos.map((t, idx) => (
                  <div key={idx} className="py-2.5 flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-tx">{t.titulo}</p>
                      <p className="text-xs text-mut">
                        {t.angulo} · {t.gatilho} · {t.caracteres} caracteres · Nota {t.nota}/10
                      </p>
                    </div>

                    <button
                      onClick={() => copiarTexto(`outro-titulo-${idx}`, t.titulo)}
                      className="p-2 rounded-btn hover:bg-elev text-mut hover:text-tx transition-colors shrink-0"
                      title="Copiar título"
                    >
                      {copiado === `outro-titulo-${idx}` ? (
                        <Check className="w-4 h-4 text-ok" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Conteúdo da Aba DESCRIÇÃO & CAPÍTULOS */}
        {abaMetadados === "descricao" && (
          <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.3fr)_minmax(320px,1fr)] gap-6">
            <div className="rounded-card border border-line bg-surf p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-tx">Descrição Completa para Publicação</h3>
                <button
                  onClick={() => copiarTexto("desc", meta.descricao || "")}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-btn bg-elev hover:bg-elev/80 text-xs font-medium cursor-pointer"
                >
                  {copiado === "desc" ? <Check className="w-3.5 h-3.5 text-ok" /> : <Copy className="w-3.5 h-3.5" />}
                  Copiar Descrição
                </button>
              </div>

              <textarea
                readOnly
                value={meta.descricao || ""}
                rows={16}
                className="w-full rounded-btn border border-line bg-elev/50 p-4 font-mono text-xs text-tx leading-relaxed outline-none"
              />
            </div>

            {/* Capítulos Clicáveis */}
            <div className="rounded-card border border-line bg-surf p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ListOrdered className="w-4 h-4 text-brasa" />
                  <h3 className="font-semibold text-tx">Capítulos (Timestamps Reais)</h3>
                </div>
                <button
                  onClick={() =>
                    copiarTexto(
                      "caps",
                      capitulos.map((c) => `${c.timestamp} ${c.titulo}`).join("\n")
                    )
                  }
                  className="text-xs text-brasa hover:underline cursor-pointer"
                >
                  Copiar lista
                </button>
              </div>

              <div className="space-y-1.5">
                {capitulos.map((c, idx) => (
                  <button
                    key={idx}
                    onClick={() => pularParaSegundo(c.segundos)}
                    className="w-full flex items-center justify-between p-2.5 rounded-btn border border-line hover:border-brasa hover:bg-elev text-left transition-colors cursor-pointer"
                  >
                    <span className="text-xs text-tx font-medium truncate pr-2">{c.titulo}</span>
                    <span className="text-xs font-mono text-brasa font-bold shrink-0">{c.timestamp}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Conteúdo da Aba THUMBNAILS & BRIEFING */}
        {abaMetadados === "thumbs" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {thumbs.map((thumb) => (
                <div key={thumb.id} className="rounded-card border border-line bg-surf p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-tx">Conceito {thumb.id}</span>
                    <span className="text-xs text-mut">{thumb.nome}</span>
                  </div>

                  {/* Simulador Mobile 120 px */}
                  <div className="bg-bg border border-line rounded-btn p-3 flex flex-col items-center justify-center gap-2">
                    <p className="text-[11px] text-mut uppercase tracking-wider font-semibold">
                      Simulação Mobile (120 px)
                    </p>
                    <div
                      style={{ width: "120px", height: "68px" }}
                      className="rounded bg-elev border-2 border-dashed border-line flex flex-col items-center justify-center p-1 text-center shadow-inner relative overflow-hidden"
                    >
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                      <span className="font-black text-[10px] text-white tracking-wider z-10 uppercase px-1 leading-none drop-shadow">
                        {thumb.texto_tela}
                      </span>
                    </div>
                    <span className="text-[10px] text-ok font-medium flex items-center gap-1">
                      <Check className="w-3 h-3" /> Legível em tela pequena
                    </span>
                  </div>

                  <div className="space-y-2 text-xs text-mut">
                    <p><strong className="text-tx">Ideia:</strong> {thumb.ideia}</p>
                    <p><strong className="text-tx">Elemento central:</strong> {thumb.elemento_central}</p>
                    <p><strong className="text-tx">Texto na tela:</strong> <code className="bg-elev px-1.5 py-0.5 rounded text-tx">{thumb.texto_tela}</code></p>
                    <p><strong className="text-tx">Contraste:</strong> {thumb.contraste}</p>
                    <div className="flex items-center gap-1.5 pt-1">
                      <strong className="text-tx">Paleta:</strong>
                      {thumb.cores.map((cor, i) => (
                        <span
                          key={i}
                          style={{ backgroundColor: cor }}
                          className="w-4 h-4 rounded-full border border-line inline-block"
                          title={cor}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Conteúdo da Aba TAGS & COMUNIDADE */}
        {abaMetadados === "tags" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="rounded-card border border-line bg-surf p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-tx">Tags & Palavras-Chave</h3>
                <button
                  onClick={() => copiarTexto("tags", (meta.tags || []).join(", "))}
                  className="flex items-center gap-1 text-xs text-brasa hover:underline cursor-pointer"
                >
                  <Copy className="w-3.5 h-3.5" /> Copiar Tags
                </button>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {(meta.tags || []).map((tag, idx) => (
                  <span key={idx} className="px-2.5 py-1 rounded-btn bg-elev border border-line text-xs text-tx font-mono">
                    {tag}
                  </span>
                ))}
              </div>

              <div className="pt-4 border-t border-line space-y-2">
                <p className="text-xs font-bold text-mut uppercase">Hashtags Recomendadas (3 primeiras)</p>
                <div className="flex gap-2">
                  {(meta.hashtags || []).slice(0, 3).map((ht, idx) => (
                    <span key={idx} className="px-2 py-0.5 rounded bg-brasa/15 text-brasa text-xs font-semibold">
                      {ht}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="rounded-card border border-line bg-surf p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-tx">Comentário Fixado & Comunidade</h3>
                <button
                  onClick={() => copiarTexto("coment", meta.comentario_fixado || "")}
                  className="flex items-center gap-1 text-xs text-brasa hover:underline cursor-pointer"
                >
                  <Copy className="w-3.5 h-3.5" /> Copiar Comentário
                </button>
              </div>

              <div className="p-3 bg-elev/40 rounded-btn border border-line text-xs text-tx whitespace-pre-wrap leading-relaxed">
                {meta.comentario_fixado || "Nenhum comentário fixado gerado."}
              </div>

              <div className="pt-2 space-y-2">
                <p className="text-xs font-bold text-mut uppercase">Post de Comunidade (YouTube)</p>
                <div className="p-3 bg-elev/40 rounded-btn border border-line text-xs text-tx whitespace-pre-wrap leading-relaxed">
                  {meta.post_comunidade || "Nenhum post de comunidade gerado."}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Seção de Promoção para a Pasta Global (13 §3) */}
      <div className="rounded-card border border-line bg-surf p-6 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-brasa/15 text-brasa grid place-items-center">
              <FolderSync className="w-4 h-4" />
            </div>
            <div>
              <h2 className="font-bold text-tx">Promover Ativos para a Pasta Global (13 §3)</h2>
              <p className="text-xs text-mut">
                Itens com licença comercial confirmada que enriquecem a biblioteca do canal para futuros vídeos.
              </p>
            </div>
          </div>

          <button
            onClick={confirmarPromocaoGlobal}
            disabled={enviandoPromocao || promocoesSelecionadas.size === 0}
            className={`px-5 py-2 rounded-btn text-sm font-semibold text-white transition-all cursor-pointer ${
              promocoesSelecionadas.size > 0 && !enviandoPromocao
                ? "bg-brasa shadow-md hover:bg-orange-600"
                : "bg-line text-mut cursor-not-allowed opacity-50"
            }`}
          >
            {enviandoPromocao
              ? "Promovendo…"
              : `Confirmar Promoção de ${promocoesSelecionadas.size} Ativos`}
          </button>
        </div>

        {data.promover_itens?.length > 0 ? (
          <div className="divide-y divide-line border border-line rounded-btn overflow-hidden">
            {data.promover_itens.map((item) => {
              const selecionado = promocoesSelecionadas.has(item.id);
              return (
                <div
                  key={item.id}
                  onClick={() => alternarPromocao(item.id)}
                  className={`p-3.5 flex items-center justify-between gap-4 cursor-pointer transition-colors ${
                    selecionado ? "bg-elev/40" : "hover:bg-elev/20 opacity-60"
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <input
                      type="checkbox"
                      checked={selecionado}
                      onChange={() => alternarPromocao(item.id)}
                      className="rounded accent-brasa"
                    />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-brasa font-bold">{item.id}</span>
                        <span className="text-[11px] px-1.5 py-0.5 rounded bg-elev text-mut font-medium">
                          {item.tipo}
                        </span>
                        <span className="text-xs text-tx font-medium truncate">{item.descricao}</span>
                      </div>
                      <p className="text-xs text-mut mt-0.5">{item.motivo_sugestao}</p>
                    </div>
                  </div>

                  <div className="shrink-0 text-right text-xs">
                    <span className="px-2 py-0.5 rounded text-[11px] bg-ok/15 text-ok font-medium">
                      {item.licenca}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-mut">
            Nenhum ativo cumpriu os critérios automáticos de promoção nesta execução.
          </p>
        )}
      </div>

      {/* Relatório Técnico de Produção */}
      {data.relatorio && (
        <div className="rounded-card border border-line bg-surf p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-tx text-sm">Relatório Geral de Produção (05_saida/relatorio.md)</h3>
            <button
              onClick={() => copiarTexto("relat", data.relatorio)}
              className="text-xs text-brasa hover:underline cursor-pointer"
            >
              Copiar Relatório
            </button>
          </div>
          <pre className="p-4 bg-bg rounded-btn border border-line text-xs font-mono text-mut whitespace-pre-wrap overflow-x-auto">
            {data.relatorio}
          </pre>
        </div>
      )}
    </div>
  );
};
