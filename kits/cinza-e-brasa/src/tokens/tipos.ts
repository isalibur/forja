export interface TokenCores {
  ink: string;
  basalt: string;
  ash: string;
  ashLight: string;
  parchment: string;
  bone: string;
  pompeiiRed: string;
  ochre: string;
  ember: string;
  emberDeep: string;
  scienceCyan: string;
  dataRed: string;
  purpleScroll: string;
}

export interface TokenFonte {
  family: string;
  weight: number;
  tracking?: string;
  style?: string;
  case?: string;
}

export interface TokenFontes {
  title: TokenFonte;
  quote: TokenFonte;
  body: TokenFonte;
  data: TokenFonte;
}

export interface TokenTamanhos4k {
  title: number;
  h1: number;
  h2: number;
  body: number;
  label: number;
  hud: number;
  credit: number;
}

export interface TokenSafeArea {
  x: number;
  y: number;
  title: number;
}

export interface TokenEasings {
  in: [number, number, number, number];
  out: [number, number, number, number];
  move: [number, number, number, number];
}

export interface TokenDuracoes {
  enter: number;
  exit: number;
  stagger: number;
}

export interface TokenTexturas {
  grain: { opacity: number; size: string; animated: boolean };
  vignette: { amount: number; feather: number };
  dust: { opacity: number; onlyBlocks: string[] };
}

export interface TokenRotulos {
  aiReconstruction: string;
  realOtherVolcano: string;
  position: string;
  opacity: number;
}

export interface TokensKit {
  nome: string;
  versao: string;
  color: TokenCores;
  font: TokenFontes;
  size4k: TokenTamanhos4k;
  safeArea: TokenSafeArea;
  easing: TokenEasings;
  durationFrames: TokenDuracoes;
  texture: TokenTexturas;
  label: TokenRotulos;
}
