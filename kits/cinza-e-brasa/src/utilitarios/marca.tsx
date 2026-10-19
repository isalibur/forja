import React, { createContext, useContext } from "react";
import { MarcaProjeto } from "../schemas/marca";

const MarcaContext = createContext<MarcaProjeto | null>(null);

export const MarcaProvider: React.FC<{
  marca?: MarcaProjeto;
  children: React.ReactNode;
}> = ({ marca, children }) => {
  return (
    <MarcaContext.Provider value={marca || null}>
      {children}
    </MarcaContext.Provider>
  );
};

export const useMarca = (): MarcaProjeto | null => {
  return useContext(MarcaContext);
};
