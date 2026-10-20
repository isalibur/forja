import React from "react";
import { Check, Flame, Layers, Palette, Type } from "lucide-react";

export const Kits: React.FC = () => {
  return (
    <div className="p-6 xl:p-8 max-w-[1400px] mx-auto space-y-8 animate-in fade-in-50">
      <div>
        <p className="text-xs uppercase tracking-widest text-brasa font-semibold">
          Identidade Visual & Templates (14 §5.11)
        </p>
        <h1 className="text-2xl font-bold mt-1">Kits de Estilo Visual</h1>
        <p className="text-sm text-mut mt-1">
          Paletas de cores, tipografia, transições e biblioteca de componentes Remotion
        </p>
      </div>

      {/* Kit Ativo */}
      <div className="rounded-card border-2 border-brasa/40 bg-surf p-6 shadow-sm space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-brasa to-orange-700 grid place-items-center shadow-md">
              <Flame className="w-6 h-6 text-white fill-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-tx">Cinza e Brasa</h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brasa text-white">
                  v1.0 · Padrão Ativo
                </span>
              </div>
              <p className="text-xs text-mut">
                Estilo documental sóbrio com contrastes dramáticos em tons de carvão e acentos quentes
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-ok bg-ok/10 px-3 py-1.5 rounded-full font-medium">
            <Check className="w-4 h-4" />
            <span>Kit Ativo no Workspace</span>
          </div>
        </div>

        {/* Tokens de Cor */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-mut uppercase tracking-wider flex items-center gap-2">
            <Palette className="w-3.5 h-3.5" /> Paleta de Cores
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            {[
              { nome: "bg", hex: "#0E0E10", label: "Fundo Geral" },
              { nome: "surf", hex: "#18181B", label: "Superfície" },
              { nome: "elev", hex: "#27272A", label: "Elevado" },
              { nome: "brasa", hex: "#FF6A2B", label: "Acento Brasa" },
              { nome: "tx", hex: "#F4F0E8", label: "Texto Claro" },
              { nome: "mut", hex: "#A1A1AA", label: "Atenuado" },
            ].map((token) => (
              <div
                key={token.nome}
                className="rounded-btn border border-line bg-elev/30 p-3 space-y-2 flex flex-col justify-between"
              >
                <div
                  style={{ backgroundColor: token.hex }}
                  className="w-full h-10 rounded border border-line/60 shadow-inner"
                />
                <div>
                  <p className="text-xs font-bold text-tx font-mono">{token.hex}</p>
                  <p className="text-[11px] text-mut">{token.label}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tipografia */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-mut uppercase tracking-wider flex items-center gap-2">
            <Type className="w-3.5 h-3.5" /> Tipografia do Kit
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-btn border border-line bg-elev/30 p-4 space-y-1">
              <p className="text-xs text-mut font-semibold uppercase">Títulos e Ênfase Dramática</p>
              <p className="text-lg font-serif font-bold text-tx">Playfair Display / Serif Documental</p>
              <p className="text-xs text-mut">Proporção harmônica para cartões capitulares e citações históricas.</p>
            </div>
            <div className="rounded-btn border border-line bg-elev/30 p-4 space-y-1">
              <p className="text-xs text-mut font-semibold uppercase">Interface, HUD e Legendas</p>
              <p className="text-lg font-sans font-medium text-tx">Inter / Sans Moderna</p>
              <p className="text-xs text-mut">Alta legibilidade em tamanhos pequenos e legendas palavra a palavra.</p>
            </div>
          </div>
        </div>

        {/* Templates Suportados */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-mut uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-3.5 h-3.5" /> Catálogo de Templates Remotion (16:9 e 9:16)
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            {[
              { id: "T01", nome: "CartaoTexto", desc: "Aberturas capitulares dramáticas" },
              { id: "T02", nome: "ImagemSimples", desc: "Slow pan e zoom com vinheta 35mm" },
              { id: "T04", nome: "MapaItinerario", desc: "Animação de rotas cartográficas" },
              { id: "T08", nome: "Citacao", desc: "Documentos e manuscritos em foco" },
            ].map((t) => (
              <div key={t.id} className="p-3 rounded-btn border border-line bg-elev/40 space-y-1">
                <span className="font-mono text-brasa font-bold">{t.id}</span>
                <p className="font-semibold text-tx">{t.nome}</p>
                <p className="text-mut text-[11px]">{t.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
