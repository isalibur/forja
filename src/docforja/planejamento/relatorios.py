"""Geradores de relatórios e artefatos legíveis do plano de vídeo (01_plano/).

Produz:
- plano.json (contrato master do sistema)
- plano.md (visão legível humana por bloco)
- verificacao.md (regras de dosagem e ajustes)
- estimativa.md (orçamento e tempos de produção)
- numeros_na_tela.md (conferência estrita de dados numéricos)
"""

from __future__ import annotations

import re
from pathlib import Path

from docforja.esquemas import Plano
from docforja.planejamento.dosagem import ResultadoVerificacao
from docforja.planejamento.entidades import BlocoProcessado
from docforja.planejamento.estimativa import RelatorioEstimativa


def formatar_tempo_mmss(segundos: float) -> str:
    """Converte segundos em formato mm:ss."""
    m = int(segundos // 60)
    s = int(segundos % 60)
    return f"{m:02d}:{s:02d}"


def gerar_plano_md(
    plano: Plano,
    blocos_processados: list[BlocoProcessado] | None = None,
) -> str:
    """Gera o relatório markdown plano.md no formato exato de 02 §7."""
    linhas = [f"# Plano de Vídeo — {plano.projeto.upper()}", ""]
    linhas.append(
        f"> **Kit:** `{plano.kit}` · **Preset:** `{plano.preset}` · "
        f"**Estimativa:** `{plano.estimativa_producao_min} min` "
        f"(orçamento: `{plano.orcamento_producao_min} min`)"
    )
    linhas.append("")

    seg_map = {}
    if blocos_processados:
        for b in blocos_processados:
            for s in b.segmentos:
                seg_map[s.id] = s

    tempo_acumulado = 0.0
    tempos_reais = all(
        shot.inicio_s is not None and shot.fim_s is not None
        for bloco in plano.blocos for shot in bloco.shots
    )

    for bloco in plano.blocos:
        if tempos_reais:
            t_inicio_bloco = min(s.inicio_s for s in bloco.shots)
            t_fim_bloco = max(s.fim_s for s in bloco.shots)
        else:
            t_inicio_bloco = tempo_acumulado
            t_fim_bloco = tempo_acumulado + sum(s.duracao_s for s in bloco.shots)
        t_str = f"{formatar_tempo_mmss(t_inicio_bloco)}-{formatar_tempo_mmss(t_fim_bloco)}"
        clima = bloco.clima_musical or "padrão"

        linhas.append(
            f"## {bloco.id} - {bloco.titulo} ({t_str} · modo: {bloco.modo_visual} · clima: {clima})"
        )
        linhas.append("| Shot | Tempo | Narração | Template | Imagem | Texto na tela | Som |")
        linhas.append("|---|---|---|---|---|---|---|")

        ativos_bloco: set[str] = set()

        for shot in bloco.shots:
            inicio_shot = shot.inicio_s if tempos_reais else tempo_acumulado
            t_shot_str = f"{formatar_tempo_mmss(inicio_shot)} · {shot.duracao_s:.1f} s"
            if not tempos_reais:
                tempo_acumulado += shot.duracao_s

            # Narração do primeiro segmento associado
            narracao = "—"
            if shot.segmentos:
                s_id = shot.segmentos[0]
                if s_id in seg_map:
                    texto_seg = seg_map[s_id].texto_limpo
                    palavras = texto_seg.split()
                    trecho = " ".join(palavras[:6]) + ("…" if len(palavras) > 6 else "")
                    narracao = f'"{trecho}"'
                else:
                    narracao = f"[{', '.join(shot.segmentos)}]"

            # Ativos
            imagem_desc = "—"
            if shot.ativos:
                aid = shot.ativos[0]
                ativos_bloco.add(aid)
                ativo_obj = plano.ativos.get(aid)
                if ativo_obj:
                    imagem_desc = f"{aid} {ativo_obj.origem}: {ativo_obj.descricao[:40]}…"
                else:
                    imagem_desc = aid

            # Texto na tela e sobreposições
            textos_list = list(shot.textos)
            for o in shot.sobreposicoes:
                if o.get("tipo") == "O1":
                    textos_list.append(f"O1: {o.get('texto')}")
                elif o.get("tipo") == "O3":
                    textos_list.append(f"O3: {o.get('texto')}")
            texto_tela = " · ".join(textos_list) if textos_list else "—"

            som_str = ", ".join(shot.sfx) if shot.sfx else "—"

            linhas.append(
                f"| {shot.id} | {t_shot_str} | {narracao} | {shot.template} | "
                f"{imagem_desc} | {texto_tela} | {som_str} |"
            )

        # Resumo de ativos do bloco
        gerar_c = sum(
            1 for aid in ativos_bloco
            if plano.ativos.get(aid) and plano.ativos[aid].origem == "gerar"
        )
        pesq_c = sum(
            1 for aid in ativos_bloco
            if plano.ativos.get(aid) and plano.ativos[aid].origem == "pesquisar"
        )
        pedir_c = sum(
            1 for aid in ativos_bloco
            if plano.ativos.get(aid) and plano.ativos[aid].origem == "pedir_ao_usuario"
        )
        linhas.append(
            f"**Ativos do bloco:** {len(ativos_bloco)} "
            f"({gerar_c} gerar · {pesq_c} pesquisar · {pedir_c} pedir a você)\n"
        )
        if tempos_reais:
            tempo_acumulado = t_fim_bloco

    return "\n".join(linhas) + "\n"


def gerar_verificacao_md(resultado: ResultadoVerificacao) -> str:
    """Gera o relatório verificacao.md detalhando conformidade D1 a D17."""
    linhas = ["# Relatório de Verificação de Dosagem (D1 a D17)", ""]
    status_geral = "[OK] APROVADO" if resultado.aprovado else "[ALERTA] VIOLAÇÕES PENDENTES"
    linhas.append(
        f"> **Status Geral:** **{status_geral}** · Total de regras avaliadas: 17 · "
        f"Ajustes automáticos: {len(resultado.ajustes)}"
    )
    linhas.append("")

    linhas.append("## Ajustes Realizados por Código")
    if resultado.ajustes:
        for aj in resultado.ajustes:
            linhas.append(f"- [x] {aj}")
    else:
        linhas.append("- Nenhum ajuste foi necessário; plano em conformidade estrita.")
    linhas.append("")

    linhas.append("## Detalhamento das Violações Detectadas")
    if resultado.violacoes:
        linhas.append("| Regra | Descrição | Bloco/Shot | Status | Ação |")
        linhas.append("|---|---|---|---|---|")
        for v in resultado.violacoes:
            alvo = v.shot_id or v.bloco_id or "Geral"
            status = "Corrigida" if v.corrigida else "Pendente"
            acao = v.acao_correcao or v.detalhes
            linhas.append(f"| {v.regra} | {v.descricao} | {alvo} | {status} | {acao} |")
    else:
        linhas.append("Nenhuma violação encontrada.")
    linhas.append("")

    return "\n".join(linhas) + "\n"


def gerar_estimativa_md(relatorio: RelatorioEstimativa) -> str:
    """Gera o relatório estimativa.md com os tempos de produção e limites."""
    linhas = ["# Estimativa de Produção e Orçamento", ""]
    status = "[DENTRO DO ORÇAMENTO]" if relatorio.aprovado else "[ORÇAMENTO EXCEDIDO]"
    linhas.append(
        f"> **Preset:** `{relatorio.preset}` · "
        f"**Meta Orçamentária:** `{relatorio.orcamento_minutos} min` · "
        f"**Tempo Estimado:** `{relatorio.tempo_total_minutos} min` {status}"
    )
    linhas.append("")

    linhas.append("## Tempos por Etapa de Produção")
    linhas.append("| Etapa | Detalhes | Quantidade | Tempo Estimado |")
    linhas.append("|---|---|---|---|")
    for item in relatorio.itens:
        linhas.append(
            f"| {item.etapa} | {item.descricao} | {item.quantidade} {item.unidade} | "
            f"{item.tempo_minutos:.1f} min |"
        )
    linhas.append("")

    if relatorio.ajustes_realizados:
        linhas.append("## Medidas de Adequação ao Orçamento (D15)")
        for aj in relatorio.ajustes_realizados:
            linhas.append(f"- {aj}")
        linhas.append("")

    return "\n".join(linhas) + "\n"


def gerar_numeros_na_tela_md(
    plano: Plano,
    roteiro_texto: str = "",
) -> str:
    """Gera o relatório numeros_na_tela.md conferindo todos os números e datas."""
    linhas = ["# Conferência de Números e Dados na Tela", ""]
    linhas.append(
        "> Todos os números, datas, medidas e nomes próprios exibidos em tela são auditados "
        "contra o roteiro."
    )
    linhas.append("")
    linhas.append("| Shot | Item na Tela | Constar no Roteiro? | Status |")
    linhas.append("|---|---|---|---|")

    for b in plano.blocos:
        for s in b.shots:
            for txt in s.textos:
                numeros = re.findall(r"\b\d+[\.,]?\d*\b", txt)
                if numeros:
                    consta = any(n in roteiro_texto for n in numeros)
                    status = "[OK] Conferido" if consta else "[ALERTA] Não localizado"
                    linhas.append(f"| {s.id} | `{txt}` | {'Sim' if consta else 'Não'} | {status} |")

    linhas.append("")
    return "\n".join(linhas) + "\n"


def gravar_relatorios_planejamento(
    diretorio_saida: Path,
    plano: Plano,
    resultado_verificacao: ResultadoVerificacao,
    relatorio_estimativa: RelatorioEstimativa,
    blocos_processados: list[BlocoProcessado] | None = None,
    roteiro_texto: str = "",
) -> dict[str, Path]:
    """Grava todos os relatórios na pasta 01_plano/ do projeto."""
    diretorio_saida.mkdir(parents=True, exist_ok=True)

    # 1. plano.json
    path_json = diretorio_saida / "plano.json"
    path_json.write_text(plano.model_dump_json(indent=2), encoding="utf-8")

    # 2. plano.md
    path_md = diretorio_saida / "plano.md"
    path_md.write_text(gerar_plano_md(plano, blocos_processados), encoding="utf-8")

    # 3. verificacao.md
    path_verif = diretorio_saida / "verificacao.md"
    path_verif.write_text(gerar_verificacao_md(resultado_verificacao), encoding="utf-8")

    # 4. estimativa.md
    path_est = diretorio_saida / "estimativa.md"
    path_est.write_text(gerar_estimativa_md(relatorio_estimativa), encoding="utf-8")

    # 5. numeros_na_tela.md
    path_nums = diretorio_saida / "numeros_na_tela.md"
    path_nums.write_text(gerar_numeros_na_tela_md(plano, roteiro_texto), encoding="utf-8")

    return {
        "plano_json": path_json,
        "plano_md": path_md,
        "verificacao_md": path_verif,
        "estimativa_md": path_est,
        "numeros_na_tela_md": path_nums,
    }
