"""Geração da Lista de Busca para imagens manuais (P7 / M5).

Documento em 01_plano/lista_de_busca.md orientando o usuário sobre ativos que
precisam de intervenção manual (pedir_ao_usuario), termos sugeridos, acervos,
requisitos de resolução e planos B.
"""

from __future__ import annotations

from docforja.esquemas import Ativo, OrigemAtivo


def gerar_lista_de_busca_md(
    ativos: dict[str, Ativo] | list[Ativo],
    tema: str = "Pompeia e o Vesúvio",
) -> str:
    """Gera o conteúdo em Markdown de 01_plano/lista_de_busca.md."""
    lista_ativos = ativos.values() if isinstance(ativos, dict) else ativos
    pedidos = [a for a in lista_ativos if a.origem == OrigemAtivo.PEDIR_AO_USUARIO]

    linhas = [
        f"# Lista de Busca — Imagens Necessárias ({tema})",
        "",
        "> **Instruções:** Salve as imagens encontradas na pasta `02_midias/manual/` "
        "com o nome indicado.",
        "> Arquivos sem ID atribuído serão analisados pelo Curador e colocados "
        "em `nao_atribuidas/`.",
        "",
    ]

    if not pedidos:
        linhas.append("Nenhum ativo visual pendente de intervenção manual no momento.")
        linhas.append(
            "Todos os ativos foram resolvidos por acervo, biblioteca ou geração programada."
        )
        return "\n".join(linhas) + "\n"

    for ativo in sorted(pedidos, key=lambda a: a.id):
        usos = ", ".join(ativo.usado_em) if ativo.usado_em else "plano geral"
        linhas.append(f"## {ativo.id} — {ativo.descricao} (usado em {usos})")

        motivo = (
            ativo.motivo
            or "Ativo documental restrito, sob proteção de patrimônio cultural "
            "ou ausente em acervos abertos."
        )
        linhas.append(f"- **Por que preciso de você:** {motivo}")

        busca = ativo.busca or {}
        termos = busca.get("termos", [ativo.descricao])
        termos_str = ", ".join(f'"{t}"' for t in termos)
        linhas.append(f"- **Procure:** {termos_str}")

        sites = busca.get(
            "sites",
            [
                "Wikimedia Commons (conferir licença)",
                "Acervos digitais de museus",
                "Bancos de imagens pagos / editorial",
            ],
        )
        linhas.append(f"- **Onde:** {', '.join(sites)}")

        nome_arquivo = ativo.nome_arquivo or f"{ativo.id}.jpg"
        linhas.append(f"- **Mínimo:** 1600 px · **Salvar como:** `{nome_arquivo}`")

        plano_b = ativo.plano_b or "imagem gerada ou template alternativo"
        linhas.append(f"- **Se não vier:** {plano_b}")
        linhas.append("")

    return "\n".join(linhas)
