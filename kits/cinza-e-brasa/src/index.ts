import { registerRoot } from "remotion";
import { Root } from "./Root";

// Registro da raiz do Remotion Studio
registerRoot(Root);

// Exportacoes da biblioteca para reuso no DocForja
export * from "./tokens";
export * from "./templates";
export * from "./sobreposicoes";
export * from "./schemas/templates";
export * from "./schemas/sobreposicoes";
export * from "./schemas/marca";
export * from "./utilitarios/AutoAjusteTexto";
export * from "./utilitarios/TexturaFilme";
export * from "./utilitarios/animacoes";
export * from "./utilitarios/marca";
export * from "./composicoes/Bloco";
export * from "./composicoes/BlocoTeste";
