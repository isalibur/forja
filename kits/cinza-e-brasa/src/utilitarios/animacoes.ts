import { Easing, interpolate } from "remotion";
import { tokens } from "../tokens";

export const easingEntrada = Easing.bezier(...tokens.easing.in);
export const easingSaida = Easing.bezier(...tokens.easing.out);
export const easingMovimento = Easing.bezier(...tokens.easing.move);

/**
 * Calcula a curva de entrada padrao de um componente (0 -> 1)
 */
export const animarEntrada = (
  frame: number,
  duracaoFrames: number = tokens.durationFrames.enter,
  delay: number = 0
): number => {
  return interpolate(frame - delay, [0, duracaoFrames], [0, 1], {
    easing: easingEntrada,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
};

/**
 * Calcula a saida padrao de um componente (1 -> 0) nos ultimos frames
 */
export const animarSaida = (
  frame: number,
  duracaoTotalFrames: number,
  duracaoSaidaFrames: number = tokens.durationFrames.exit
): number => {
  const frameInicioSaida = duracaoTotalFrames - duracaoSaidaFrames;
  return interpolate(frame, [frameInicioSaida, duracaoTotalFrames], [1, 0], {
    easing: easingSaida,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
};

/**
 * Movimento Ken Burns para T01
 */
export interface KenBurnsParams {
  movimento: "push_in" | "pull_out" | "pan_esq" | "pan_dir" | "estatico";
  amplitude: number; // 0.05 a 0.25 (5% a 25%)
  foco?: { x: number; y: number }; // 0 a 1
}

export const calcularKenBurns = (
  frame: number,
  duracaoTotalFrames: number,
  params: KenBurnsParams
) => {
  const progresso = interpolate(frame, [0, duracaoTotalFrames], [0, 1], {
    easing: Easing.linear,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const amp = params.amplitude || 0.12;
  const focoX = params.foco ? params.foco.x * 100 : 50;
  const focoY = params.foco ? params.foco.y * 100 : 50;

  let escala = 1.0;
  let translacaoX = 0;
  let translacaoY = 0;

  switch (params.movimento) {
    case "push_in":
      escala = 1.0 + progresso * amp;
      break;
    case "pull_out":
      escala = 1.0 + amp - progresso * amp;
      break;
    case "pan_esq":
      escala = 1.0 + amp * 0.5;
      translacaoX = (progresso - 0.5) * amp * 100;
      break;
    case "pan_dir":
      escala = 1.0 + amp * 0.5;
      translacaoX = -(progresso - 0.5) * amp * 100;
      break;
    case "estatico":
    default:
      escala = 1.0;
      break;
  }

  return {
    transform: `scale(${escala}) translate(${translacaoX}px, ${translacaoY}px)`,
    transformOrigin: `${focoX}% ${focoY}%`,
  };
};
