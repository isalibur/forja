import React, { useMemo } from "react";

interface AutoAjusteTextoProps {
  texto: string;
  tamanhoPadrao: number; // tamanho em px para a resolucao atual
  larguraMaximaPx: number; // largura maxima do container
  fatorEncolhimentoMinimo?: number; // padrao 0.7 (70%)
  alturaLinha?: number;
  cor?: string;
  fontFamily?: string;
  fontWeight?: number;
  letterSpacing?: string;
  textTransform?: "uppercase" | "none" | "capitalize" | "lowercase";
  fontStyle?: "normal" | "italic";
  textAlign?: "left" | "center" | "right";
  className?: string;
  style?: React.CSSProperties;
}

export const AutoAjusteTexto: React.FC<AutoAjusteTextoProps> = ({
  texto,
  tamanhoPadrao,
  larguraMaximaPx,
  fatorEncolhimentoMinimo = 0.7,
  alturaLinha = 1.2,
  cor = "#F4F0E8",
  fontFamily,
  fontWeight,
  letterSpacing,
  textTransform,
  fontStyle = "normal",
  textAlign = "center",
  style,
}) => {
  // Estima a largura do texto considerando o tamanho da fonte e quantidade de caracteres na maior linha
  const tamanhoAjustado = useMemo(() => {
    const linhas = texto.split("\n");
    let maiorLinha = "";
    for (const l of linhas) {
      if (l.length > maiorLinha.length) maiorLinha = l;
    }

    // Coeficiente medio de largura por caractere para fontes proporcionais / serifadas
    const coeficienteLargura = 0.58;
    const larguraEstimada = maiorLinha.length * tamanhoPadrao * coeficienteLargura;

    if (larguraEstimada <= larguraMaximaPx) {
      return tamanhoPadrao;
    }

    const escalaNecessaria = larguraMaximaPx / larguraEstimada;
    const escalaFinal = Math.max(fatorEncolhimentoMinimo, escalaNecessaria);
    return Math.round(tamanhoPadrao * escalaFinal);
  }, [texto, tamanhoPadrao, larguraMaximaPx, fatorEncolhimentoMinimo]);

  return (
    <div
      style={{
        fontSize: `${tamanhoAjustado}px`,
        lineHeight: alturaLinha,
        color: cor,
        fontFamily,
        fontWeight,
        letterSpacing,
        textTransform,
        fontStyle,
        textAlign,
        wordBreak: "break-word",
        whiteSpace: "pre-wrap",
        maxWidth: `${larguraMaximaPx}px`,
        ...style,
      }}
    >
      {texto}
    </div>
  );
};
