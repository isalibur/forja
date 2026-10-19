import React, { useState } from "react";
import { toast } from "sonner";
import {
  Video,
  Smartphone,
  Music,
  Check,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  Volume2,
  Layers,
} from "lucide-react";

interface CriarProps {
  onNavegar: (tela: string) => void;
  onProjetoCriado?: (slug: string) => void;
}

export const Criar: React.FC<CriarProps> = ({ onNavegar, onProjetoCriado }) => {
  const [passo, setPasso] = useState<number>(1);
  const [carregando, setCarregando] = useState<boolean>(false);

  // Form State
  const [tipo, setTipo] = useState<string>("longo");
  const [nome, setNome] = useState<string>("Vesúvio: 24 Horas que Mudaram a História");
  const [roteiro, setRoteiro] = useState<string>("");
  const idiomaPrincipal = "pt-BR";
  const [idiomasExtras, setIdiomasExtras] = useState<string[]>(["en", "es"]);
  const [preset, setPreset] = useState<string>("padrao");
  const kit = "cinza-e-brasa@1.0";
  const [densidadeMotion, setDensidadeMotion] = useState<string>("media");

  // Estatísticas do Roteiro ao vivo (~145 palavras/min conforme 14 §5.2)
  const palavras = roteiro.trim() ? roteiro.trim().split(/\s+/).length : 0;
  const minutosEstimados = Math.ceil(palavras / 145);

  const toggleIdiomaExtra = (lang: string) => {
    if (idiomasExtras.includes(lang)) {
      setIdiomasExtras(idiomasExtras.filter((l) => l !== lang));
    } else {
      setIdiomasExtras([...idiomasExtras, lang]);
    }
  };

  const handleCriarProjeto = async () => {
    if (!nome.trim()) {
      toast.error("Por favor, informe o tema ou nome do projeto.");
      return;
    }

    setCarregando(true);
    try {
      const res = await fetch("/api/projetos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nome,
          tipo,
          roteiro,
          idioma_principal: idiomaPrincipal,
          idiomas_extras: idiomasExtras,
          preset,
          kit,
          opcoes_adicionais: { densidade_motion: densidadeMotion },
        }),
      });

      if (!res.ok) {
        throw new Error("Erro ao criar projeto");
      }

      const data = await res.json();
      toast.success(`Projeto '${data.slug}' criado com sucesso!`);
      if (onProjetoCriado) {
        onProjetoCriado(data.slug);
      }
      onNavegar("plano");
    } catch (err: any) {
      toast.error(`Falha ao criar: ${err.message}`);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div className="p-8 max-w-[1000px] mx-auto space-y-8 animate-in fade-in duration-200">
      {/* Header & Progresso do Wizard */}
      <div className="border-b border-line pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-tx">
          Criar Novo Projeto
        </h1>
        <p className="text-mut text-sm mt-1">
          Assistente de produção em 4 etapas (documento 14 §5.2).
        </p>

        {/* Steps Pills */}
        <div className="flex items-center gap-3 mt-6">
          {[
            { n: 1, label: "Tipo" },
            { n: 2, label: "Conteúdo & Roteiro" },
            { n: 3, label: "Estilo & Voz" },
            { n: 4, label: "Revisão" },
          ].map((s) => (
            <div
              key={s.n}
              className={`flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full transition-colors ${
                passo === s.n
                  ? "bg-brasa text-white"
                  : passo > s.n
                  ? "bg-elev text-ok border border-ok/20"
                  : "bg-surf text-mut border border-line"
              }`}
            >
              <span>{passo > s.n ? "✓" : s.n}.</span>
              <span>{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ================= PASSO 1: TIPO ================= */}
      {passo === 1 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-tx">
            1. Escolha o tipo de produção
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {[
              {
                id: "longo",
                titulo: "Vídeo longo",
                desc: "Documentário padrão 16:9 completo com blocos, shots, mapa e narração multi-idioma.",
                icon: Video,
              },
              {
                id: "short_derivado",
                titulo: "Short derivado",
                desc: "Corta os melhores momentos de um vídeo longo com frases-ponte e layout vertical 9:16.",
                icon: Smartphone,
              },
              {
                id: "short_avulso",
                titulo: "Short avulso ou em lote",
                desc: "Cria vídeos verticais a partir de temas ou planilha CSV com templates dinâmicos.",
                icon: Layers,
              },
              {
                id: "musica",
                titulo: "Canal de música",
                desc: "Vídeos longos de 1 h com loops visuais e normalização de áudio em compasso.",
                icon: Music,
              },
            ].map((item) => {
              const Icon = item.icon;
              const sel = tipo === item.id;
              return (
                <div
                  key={item.id}
                  onClick={() => setTipo(item.id)}
                  className={`p-5 rounded-card border text-left cursor-pointer transition-all ${
                    sel
                      ? "bg-surf border-brasa shadow-lg shadow-brasa/10"
                      : "bg-surf/60 border-line hover:border-zinc-600"
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className={`w-9 h-9 rounded-lg grid place-items-center ${sel ? "bg-brasa text-white" : "bg-elev text-mut"}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    {sel && <Check className="w-5 h-5 text-brasa" />}
                  </div>
                  <h3 className="font-semibold text-tx text-sm">{item.titulo}</h3>
                  <p className="text-xs text-mut mt-1">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ================= PASSO 2: CONTEÚDO ================= */}
      {passo === 2 && (
        <div className="space-y-6">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
              Tema ou Título do Vídeo
            </label>
            <input
              type="text"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              placeholder="Ex.: Vesúvio: 24 Horas que Mudaram a História"
              className="w-full bg-surf border border-line rounded-btn px-4 py-2.5 text-sm text-tx outline-none focus:border-brasa transition-colors"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                Roteiro (Cole ou digite em Markdown)
              </label>
              <div className="text-xs text-mut font-mono flex items-center gap-3">
                <span>{palavras} palavras</span>
                <span>≈ {minutosEstimados} min de narração</span>
              </div>
            </div>
            <textarea
              rows={10}
              value={roteiro}
              onChange={(e) => setRoteiro(e.target.value)}
              placeholder="# Título do Bloco 1&#10;Durante séculos, a montanha parecia tranquila..."
              className="w-full bg-surf border border-line rounded-card p-4 text-sm font-mono text-tx outline-none focus:border-brasa transition-colors resize-y"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
              Idiomas da Produção
            </label>
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1.5 rounded-btn bg-brasa/10 text-brasa border border-brasa/30 text-xs font-medium flex items-center gap-1.5">
                🇧🇷 pt-BR (Principal)
              </span>

              {[
                { code: "en", label: "🇺🇸 en (Inglês)" },
                { code: "es", label: "🇪🇸 es (Espanhol)" },
              ].map((lang) => {
                const ativo = idiomasExtras.includes(lang.code);
                return (
                  <button
                    key={lang.code}
                    type="button"
                    onClick={() => toggleIdiomaExtra(lang.code)}
                    className={`px-3 py-1.5 rounded-btn text-xs font-medium border transition-colors cursor-pointer ${
                      ativo
                        ? "bg-elev border-info text-info"
                        : "bg-surf border-line text-mut hover:border-zinc-500"
                    }`}
                  >
                    {lang.label} {ativo && "✓"}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ================= PASSO 3: ESTILO & VOZ ================= */}
      {passo === 3 && (
        <div className="space-y-6">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
              Kit Visual
            </label>
            <div className="p-4 rounded-card bg-surf border border-brasa flex items-center justify-between">
              <div>
                <h4 className="font-semibold text-tx text-sm">Cinza e Brasa (v1.0)</h4>
                <p className="text-xs text-mut mt-0.5">
                  Estilo sóbrio documental, texturas minerais, tipografia Inter/JetBrains e paleta escura.
                </p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded bg-ok/10 text-ok font-medium">
                Padrão do Canal
              </span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
              Preset de Produção
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {[
                { id: "rapido", titulo: "Rápido", tempo: "~45 min", desc: "Prioriza velocidade e 1 variação de imagem." },
                { id: "padrao", titulo: "Padrão", tempo: "~120 min", desc: "Equilíbrio ideal: 2 variações e parallax nos destaques." },
                { id: "caprichado", titulo: "Caprichado", tempo: "~240 min", desc: "Máxima qualidade visual e todas as checagens." },
              ].map((p) => {
                const sel = preset === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => setPreset(p.id)}
                    className={`p-4 rounded-card border cursor-pointer transition-all ${
                      sel ? "bg-surf border-brasa" : "bg-surf/60 border-line hover:border-zinc-600"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-tx text-sm">{p.titulo}</span>
                      <span className="text-[11px] font-mono text-zinc-400">{p.tempo}</span>
                    </div>
                    <p className="text-xs text-mut">{p.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
              Voz Padrão da Narração
            </label>
            <div className="p-3 bg-surf border border-line rounded-btn flex items-center justify-between">
              <div className="flex items-center gap-3 text-sm text-tx">
                <Volume2 className="w-4 h-4 text-brasa" />
                <span>Alex (pt-BR · Kokoro-82M / Chatterbox)</span>
              </div>
              <span className="text-xs text-ok font-mono">Disponível localmente</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
              Densidade de Motion (Animações de Câmera)
            </label>
            <div className="flex gap-3">
              {["baixa", "media", "alta"].map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDensidadeMotion(d)}
                  className={`px-4 py-2 rounded-btn text-xs font-medium border capitalize transition-colors ${
                    densidadeMotion === d
                      ? "bg-surf border-brasa text-tx"
                      : "bg-surf/60 border-line text-mut hover:border-zinc-500"
                  }`}
                >
                  {d} {densidadeMotion === d && "✓"}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ================= PASSO 4: REVISÃO ================= */}
      {passo === 4 && (
        <div className="space-y-6">
          <div className="bg-surf border border-line rounded-card p-6 space-y-4">
            <h2 className="text-lg font-bold text-tx">Resumo do Planejamento</h2>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="py-2 border-b border-line/50">
                <span className="text-mut block">Tema</span>
                <span className="font-medium text-tx text-sm">{nome}</span>
              </div>
              <div className="py-2 border-b border-line/50">
                <span className="text-mut block">Formato</span>
                <span className="font-medium text-tx capitalize">{tipo}</span>
              </div>
              <div className="py-2 border-b border-line/50">
                <span className="text-mut block">Duração Estimada</span>
                <span className="font-mono text-tx font-medium">{minutosEstimados} minutos ({palavras} palavras)</span>
              </div>
              <div className="py-2 border-b border-line/50">
                <span className="text-mut block">Idiomas</span>
                <span className="font-medium text-tx">{idiomaPrincipal}, {idiomasExtras.join(", ")}</span>
              </div>
              <div className="py-2">
                <span className="text-mut block">Preset & Kit</span>
                <span className="font-medium text-tx capitalize">{preset} · {kit}</span>
              </div>
              <div className="py-2">
                <span className="text-mut block">Tempo Estimado de Produção</span>
                <span className="font-mono text-brasa font-semibold">≈ 120 minutos (Preset Padrão)</span>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-card bg-info/5 border border-info/20 flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-info shrink-0 mt-0.5" />
            <p className="text-xs text-mut leading-relaxed">
              Ao clicar em <strong>"Começar planejamento"</strong>, o DocForja criará a pasta do projeto em disco,
              iniciará o executor de etapas em background e analisará o roteiro para gerar o plano completo.
            </p>
          </div>
        </div>
      )}

      {/* Navegação entre Passos */}
      <div className="flex items-center justify-between pt-6 border-t border-line">
        {passo > 1 ? (
          <button
            onClick={() => setPasso(passo - 1)}
            className="px-4 py-2 rounded-btn bg-surf border border-line hover:bg-elev text-tx text-sm font-medium flex items-center gap-2 transition-colors cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
            Voltar
          </button>
        ) : <div />}

        {passo < 4 ? (
          <button
            onClick={() => setPasso(passo + 1)}
            className="px-5 py-2 rounded-btn bg-brasa hover:bg-orange-600 text-white text-sm font-medium flex items-center gap-2 transition-colors cursor-pointer shadow-lg shadow-brasa/20"
          >
            Avançar
            <ChevronRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            disabled={carregando}
            onClick={handleCriarProjeto}
            className="px-6 py-2.5 rounded-btn bg-gradient-to-r from-brasa to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white text-sm font-semibold flex items-center gap-2 transition-all cursor-pointer shadow-xl shadow-brasa/25 disabled:opacity-50"
          >
            {carregando ? "Criando projeto…" : "Começar planejamento"}
            <Sparkles className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};
