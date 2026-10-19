import { loadFont as loadCinzel } from "@remotion/google-fonts/Cinzel";
import { loadFont as loadCormorantGaramond } from "@remotion/google-fonts/CormorantGaramond";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadIBMPlexMono } from "@remotion/google-fonts/IBMPlexMono";
import rawTokens from "../../tokens.json";
import { TokensKit } from "./tipos";

export const tokens: TokensKit = rawTokens as unknown as TokensKit;

let fontesCarregadas = false;

export const carregarFontesKit = () => {
  if (fontesCarregadas) return;
  loadCinzel(undefined, { weights: ["600", "700"], subsets: ["latin"], ignoreTooManyRequestsWarning: true });
  loadCormorantGaramond(undefined, { weights: ["500", "600"], subsets: ["latin"], ignoreTooManyRequestsWarning: true });
  loadInter(undefined, { weights: ["400", "500", "600"], subsets: ["latin"], ignoreTooManyRequestsWarning: true });
  loadIBMPlexMono(undefined, { weights: ["500", "600", "700"], subsets: ["latin"], ignoreTooManyRequestsWarning: true });
  fontesCarregadas = true;
};

// Funcao auxiliar para converter tamanhos 4K para a resolucao alvo (ex: 1080p = 0.5)
export const escalarTamanho = (tamanho4k: number, larguraAtual: number): number => {
  return Math.round(tamanho4k * (larguraAtual / 3840));
};

export * from "./tipos";
