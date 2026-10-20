import React from "react";

export const ErroCarregamento: React.FC<{ tentarNovamente: () => void }> = ({ tentarNovamente }) => (
  <div className="p-8 max-w-xl mx-auto space-y-3" role="alert">
    <h1 className="text-xl font-semibold text-err">Não foi possível carregar esta tela</h1>
    <p className="text-sm text-mut">Tente novamente. Se o problema continuar, verifique se o DocForja local está em execução.</p>
    <button onClick={tentarNovamente} className="rounded-btn bg-brasa text-bg px-4 py-2 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brasa">
      Tentar novamente
    </button>
  </div>
);
