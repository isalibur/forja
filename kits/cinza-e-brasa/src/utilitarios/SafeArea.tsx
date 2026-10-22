import { useVideoConfig } from "remotion";
import { tokens } from "../tokens";

/** Area segura do Short vertical: 15% no topo, 25% embaixo e 5% nas laterais. */
export const AREA_SEGURA_VERTICAL = { x: 0.05, y: 0.15, title: 0.25 };

/** Margem lateral que a interface das plataformas cobre no formato vertical. */
export const MARGEM_DIREITA_VERTICAL = 0.12;

/** Informa se a composicao atual e vertical (9:16). */
export const useFormatoVertical = () => {
  const { width, height } = useVideoConfig();
  return height > width;
};

/** Devolve a area segura conforme a proporcao da composicao (9:16 ou 16:9). */
export const useSafeArea = () => {
  const { width, height } = useVideoConfig();
  return height > width ? AREA_SEGURA_VERTICAL : tokens.safeArea;
};
