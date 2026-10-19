"""Motor de Verificação de Dosagem (Regras D1 a D17).

O coração do planejamento: validação estrita, correções automáticas e geração de verificacao.md.
Lê parâmetros e limites de config/dosagem.yaml.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from docforja.esquemas import Ativo, OrigemAtivo, Plano, Shot
from docforja.planejamento.entidades import BlocoProcessado
from docforja.planejamento.estimativa import estimar_tempo_plano


@dataclass
class Violacao:
    regra: str
    descricao: str
    bloco_id: str | None = None
    shot_id: str | None = None
    detalhes: str = ""
    corrigida: bool = False
    acao_correcao: str = ""


@dataclass
class ResultadoVerificacao:
    aprovado: bool
    total_violacoes: int
    violacoes_corrigidas: int
    violacoes: list[Violacao] = field(default_factory=list)
    ajustes: list[str] = field(default_factory=list)


class VerificadorDosagem:
    """Motor de aplicação e autocorreção das regras D1 a D17."""

    def __init__(
        self,
        caminho_config: Path = Path("config/dosagem.yaml"),
        densidade: str = "media",
    ) -> None:
        self.caminho_config = caminho_config
        self.config = self._carregar_config()
        self.densidade = densidade
        self.fator_densidade = self.config.get("fatores_densidade", {}).get(densidade, 1.0)

    def _carregar_config(self) -> dict[str, Any]:
        if self.caminho_config.is_file():
            with self.caminho_config.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def verificar_e_corrigir(
        self,
        plano: Plano,
        blocos_processados: list[BlocoProcessado] | None = None,
        autocorrige: bool = True,
    ) -> ResultadoVerificacao:
        """Executa a verificação de D1 a D17 no plano e aplica autocorreções se solicitado."""
        violacoes: list[Violacao] = []
        ajustes: list[str] = []

        # Mapa de segmentos e batidas para suporte a D8 e D14
        segmentos_map = {}
        roteiro_completo_texto = ""
        if blocos_processados:
            for b in blocos_processados:
                for s in b.segmentos:
                    segmentos_map[s.id] = s
                    roteiro_completo_texto += " " + s.texto_original

        # D14: Cobertura de 100% dos segmentos da narração
        if blocos_processados:
            segmentos_esperados = set(segmentos_map.keys())
            segmentos_cobertos = {
                seg_id for b in plano.blocos for s in b.shots for seg_id in s.segmentos
            }
            faltantes = segmentos_esperados - segmentos_cobertos
            if faltantes:
                v = Violacao(
                    regra="D14",
                    descricao="Cobertura incompleta da narração",
                    detalhes=f"Segmentos faltantes: {sorted(faltantes)}",
                )
                if autocorrige:
                    # Anexa segmentos faltantes aos shots mais próximos do bloco respectivo
                    for f_id in sorted(faltantes):
                        b_id = f_id.split("-")[0]
                        for b in plano.blocos:
                            if b.id == b_id and b.shots:
                                b.shots[-1].segmentos.append(f_id)
                                break
                    v.corrigida = True
                    v.acao_correcao = (
                        f"Segmentos {sorted(faltantes)} anexados aos shots dos blocos"
                    )
                    ajustes.append(v.acao_correcao)
                violacoes.append(v)

        # D16: Capítulos no início de cada bloco se >= 4 blocos
        if len(plano.blocos) >= 4:
            for b in plano.blocos:
                if b.id == "B0":
                    continue
                if not b.shots or b.shots[0].template != "T12":
                    v = Violacao(
                        regra="D16",
                        descricao="Início de bloco sem cartão de capítulo T12",
                        bloco_id=b.id,
                        detalhes=f"Bloco {b.id} ({b.titulo}) não inicia com T12",
                    )
                    if autocorrige:
                        novo_cap = Shot(
                            id=f"{b.id}-00",
                            segmentos=[],
                            duracao_s=2.5,
                            template="T12",
                            params={"numero": b.id.replace("B", ""), "titulo": b.titulo},
                            sobreposicoes=[],
                            ativos=[],
                            textos=[b.titulo],
                            sfx=["whoosh_grave"],
                            transicao="fade_preto",
                            motivo="Cartão de capítulo inserido por autocorreção D16",
                        )
                        b.shots.insert(0, novo_cap)
                        v.corrigida = True
                        v.acao_correcao = f"Inserido T12 no início de {b.id}"
                        ajustes.append(v.acao_correcao)
                    violacoes.append(v)

        # D1 a D13, D17: Verificação shot a shot
        entidades_o1_vistas: set[str] = set()
        ultimo_era_revelacao = False
        todos_cortes_total = 0
        dissolves_total = 0

        for b in plano.blocos:
            shots_bloco = b.shots
            for idx, shot in enumerate(shots_bloco):
                todos_cortes_total += 1
                if shot.transicao == "dissolve":
                    dissolves_total += 1

                # D1: Duração por intensidade
                # Identifica intensidade aproximada pelo segmento
                intensidade = 5
                if shot.segmentos and shot.segmentos[0] in segmentos_map:
                    intensidade = int(segmentos_map[shot.segmentos[0]].intensidade or 5)

                min_s, max_s = (3.0, 6.0)
                if intensidade <= 3:
                    min_s, max_s = (4.0, 8.0)
                elif intensidade >= 9:
                    min_s, max_s = (1.5, 3.0)
                elif intensidade >= 7:
                    min_s, max_s = (2.0, 4.0)

                # D1 só avalia shots vinculados à fala (ignora encerramento T14 ou capítulo)
                if shot.segmentos and (shot.duracao_s < min_s or shot.duracao_s > max_s):
                    v = Violacao(
                        regra="D1",
                        descricao="Duração do shot fora da faixa para sua intensidade",
                        bloco_id=b.id,
                        shot_id=shot.id,
                        detalhes=(
                            f"Duração {shot.duracao_s:.1f}s fora da faixa "
                            f"[{min_s:.1f}s, {max_s:.1f}s] (intensidade {intensidade})"
                        ),
                    )
                    if autocorrige:
                        shot.duracao_s = max(min_s, min(max_s, shot.duracao_s))
                        v.corrigida = True
                        v.acao_correcao = (
                            f"Ajustada duração de {shot.id} para {shot.duracao_s:.1f}s"
                        )
                        ajustes.append(v.acao_correcao)
                    violacoes.append(v)

                # D2: Shot estático > 4s
                movimento = shot.params.get("movimento")
                if (
                    shot.duracao_s > 4.0
                    and movimento == "estático"
                    and shot.template != "T00"
                    and not shot.params.get("intencional", False)
                ):
                    v = Violacao(
                        regra="D2",
                        descricao="Shot estático por mais de 4 s",
                        bloco_id=b.id,
                        shot_id=shot.id,
                        detalhes=f"Shot {shot.id} estático por {shot.duracao_s:.1f}s",
                    )
                    if autocorrige:
                        shot.params["movimento"] = "push_in"
                        shot.params["amplitude"] = 0.02
                        v.corrigida = True
                        v.acao_correcao = f"Adicionado push_in 2% a {shot.id}"
                        ajustes.append(v.acao_correcao)
                    violacoes.append(v)

                # D5: Texto na tela (palavras <= 7 e tempo de leitura)
                for txt_idx, texto_item in enumerate(shot.textos):
                    palavras = texto_item.split()
                    if len(palavras) > 7:
                        v = Violacao(
                            regra="D5",
                            descricao="Texto na tela excede 7 palavras",
                            bloco_id=b.id,
                            shot_id=shot.id,
                            detalhes=f"Texto '{texto_item}' tem {len(palavras)} palavras",
                        )
                        if autocorrige:
                            shot.textos[txt_idx] = " ".join(palavras[:7])
                            v.corrigida = True
                            v.acao_correcao = f"Texto de {shot.id} encurtado para 7 palavras"
                            ajustes.append(v.acao_correcao)
                        violacoes.append(v)

                    dur_necessaria = 1.0 + (0.3 * len(palavras))
                    if shot.duracao_s < dur_necessaria:
                        v = Violacao(
                            regra="D5",
                            descricao="Duração do shot insuficiente para leitura do texto",
                            bloco_id=b.id,
                            shot_id=shot.id,
                            detalhes=(
                                f"Shot tem {shot.duracao_s:.1f}s mas texto exige "
                                f"{dur_necessaria:.1f}s"
                            ),
                        )
                        if autocorrige:
                            shot.duracao_s = round(dur_necessaria, 1)
                            v.corrigida = True
                            v.acao_correcao = (
                                f"Estendida duração de {shot.id} para {dur_necessaria:.1f}s"
                            )
                            ajustes.append(v.acao_correcao)
                        violacoes.append(v)

                # D6: Sobreposições simultâneas (máx 2 fora O2)
                sobres_reais = [o for o in shot.sobreposicoes if o.get("tipo") != "O2"]
                if len(sobres_reais) > 2:
                    v = Violacao(
                        regra="D6",
                        descricao="Excesso de sobreposições simultâneas (> 2)",
                        bloco_id=b.id,
                        shot_id=shot.id,
                        detalhes=f"Shot {shot.id} possui {len(sobres_reais)} sobreposições",
                    )
                    if autocorrige:
                        # Mantém as 2 primeiras (maior prioridade) e preserva O2 se houver
                        o2_lista = [o for o in shot.sobreposicoes if o.get("tipo") == "O2"]
                        shot.sobreposicoes = sobres_reais[:2] + o2_lista
                        v.corrigida = True
                        v.acao_correcao = f"Sobreposições de {shot.id} limitadas a 2"
                        ajustes.append(v.acao_correcao)
                    violacoes.append(v)

                # D7: Identificação O1 (só primeira aparição e >= 2.5s)
                for o in list(shot.sobreposicoes):
                    if o.get("tipo") == "O1":
                        texto_entidade = o.get("texto", "").upper().strip()
                        if texto_entidade in entidades_o1_vistas:
                            v = Violacao(
                                regra="D7",
                                descricao="Identificação O1 repetida para a mesma entidade",
                                bloco_id=b.id,
                                shot_id=shot.id,
                                detalhes=f"Entidade '{texto_entidade}' já identificada",
                            )
                            if autocorrige:
                                shot.sobreposicoes.remove(o)
                                v.corrigida = True
                                v.acao_correcao = (
                                    f"Removido O1 repetido de '{texto_entidade}' em {shot.id}"
                                )
                                ajustes.append(v.acao_correcao)
                            violacoes.append(v)
                        else:
                            entidades_o1_vistas.add(texto_entidade)
                            if shot.duracao_s < 2.5:
                                v = Violacao(
                                    regra="D7",
                                    descricao="Shot com identificação O1 inferior a 2.5s",
                                    bloco_id=b.id,
                                    shot_id=shot.id,
                                    detalhes=f"Shot {shot.id} dura {shot.duracao_s:.1f}s",
                                )
                                if autocorrige:
                                    shot.duracao_s = 2.5
                                    v.corrigida = True
                                    v.acao_correcao = (
                                        f"Duração de {shot.id} ampliada para 2.5s para O1"
                                    )
                                    ajustes.append(v.acao_correcao)
                                violacoes.append(v)

                # D8: Respiro após revelação
                if ultimo_era_revelacao and shot.textos:
                    v = Violacao(
                        regra="D8",
                        descricao="Ausência de respiro visual após batida 'revelação'",
                        bloco_id=b.id,
                        shot_id=shot.id,
                        detalhes=f"Shot {shot.id} contém texto imediatamente após uma revelação",
                    )
                    if autocorrige:
                        shot.textos = []
                        v.corrigida = True
                        v.acao_correcao = (
                            f"Textos removidos de {shot.id} para respiro visual de revelação"
                        )
                        ajustes.append(v.acao_correcao)
                    violacoes.append(v)

                ultimo_era_revelacao = False
                if shot.segmentos and shot.segmentos[0] in segmentos_map:
                    seg_obj = segmentos_map[shot.segmentos[0]]
                    if getattr(seg_obj.batida, "value", str(seg_obj.batida)) == "revelação":
                        ultimo_era_revelacao = True

                # D12: Transição fade_preto apenas no primeiro shot do bloco
                if shot.transicao == "fade_preto" and idx > 0:
                    v = Violacao(
                        regra="D12",
                        descricao="Transição fade_preto usada no meio de um bloco",
                        bloco_id=b.id,
                        shot_id=shot.id,
                        detalhes=f"Shot {shot.id} com fade_preto na posição {idx}",
                    )
                    if autocorrige:
                        shot.transicao = "corte"
                        v.corrigida = True
                        v.acao_correcao = (
                            f"Transição de {shot.id} alterada de fade_preto para corte"
                        )
                        ajustes.append(v.acao_correcao)
                    violacoes.append(v)

                # D13: Números na tela presentes no roteiro
                for txt in shot.textos:
                    nums_no_texto = re.findall(r"\b\d+[\.,]?\d*\b", txt)
                    for n in nums_no_texto:
                        if n not in roteiro_completo_texto:
                            v = Violacao(
                                regra="D13",
                                descricao="Número na tela não encontrado no roteiro",
                                bloco_id=b.id,
                                shot_id=shot.id,
                                detalhes=f"Número '{n}' em '{txt}' não consta no texto do roteiro",
                            )
                            if autocorrige:
                                # Remove o número inventado ou o item
                                shot.textos.remove(txt)
                                v.corrigida = True
                                v.acao_correcao = (
                                    f"Removido texto não fundamentado '{txt}' de {shot.id}"
                                )
                                ajustes.append(v.acao_correcao)
                            violacoes.append(v)
                            break

                # D17: Vítimas reais (respeito ético)
                for aid in shot.ativos:
                    ativo_obj = plano.ativos.get(aid)
                    if ativo_obj:
                        desc_lower = ativo_obj.descricao.lower()
                        if any(
                            k in desc_lower
                            for k in ["molde", "esqueleto", "vítima", "vitima", "corpo"]
                        ):
                            # Deve ser T01 estático/push <= 2% ou T02 intensidade <= 0.15
                            if shot.template not in {"T01", "T02"}:
                                v = Violacao(
                                    regra="D17",
                                    descricao="Vítima real exibida com template não permitido",
                                    bloco_id=b.id,
                                    shot_id=shot.id,
                                    detalhes=f"Shot {shot.id} usa {shot.template} para vítima",
                                )
                                if autocorrige:
                                    shot.template = "T01"
                                    shot.params = {"movimento": "push_in", "amplitude": 0.02}
                                    v.corrigida = True
                                    v.acao_correcao = (
                                        f"Ajustado shot {shot.id} de vítima para T01 suave"
                                    )
                                    ajustes.append(v.acao_correcao)
                                violacoes.append(v)
                            elif (
                                shot.template == "T01" and shot.params.get("amplitude", 0.0) > 0.02
                            ):
                                shot.params["amplitude"] = 0.02
                            elif (
                                shot.template == "T02"
                                and shot.params.get("intensidade", 0.0) > 0.15
                            ):
                                shot.params["intensidade"] = 0.15

                            # Sem SFX de impacto
                            sfx_agressivo = [
                                s
                                for s in shot.sfx
                                if any(
                                    x in s.lower() for x in ["impacto", "hit", "boom", "explosao"]
                                )
                            ]
                            if sfx_agressivo:
                                v = Violacao(
                                    regra="D17",
                                    descricao="SFX agressivo ou de impacto usado com vítima real",
                                    bloco_id=b.id,
                                    shot_id=shot.id,
                                    detalhes=f"SFX {sfx_agressivo} em {shot.id}",
                                )
                                if autocorrige:
                                    shot.sfx = [s for s in shot.sfx if s not in sfx_agressivo]
                                    v.corrigida = True
                                    v.acao_correcao = f"Removido SFX de impacto de {shot.id}"
                                    ajustes.append(v.acao_correcao)
                                violacoes.append(v)

        # D3: Sequência do mesmo template
        for b in plano.blocos:
            seq_count = 1
            seq_template = None
            for shot in b.shots:
                if shot.template == seq_template:
                    seq_count += 1
                    limite = 4 if seq_template == "T01" else 3
                    if seq_count > limite:
                        v = Violacao(
                            regra="D3",
                            descricao="Excesso de templates consecutivos iguais",
                            bloco_id=b.id,
                            shot_id=shot.id,
                            detalhes=f"{seq_count} shots consecutivos de {seq_template}",
                        )
                        if autocorrige:
                            # Troca o atual por T02 ou T01
                            shot.template = "T02" if seq_template == "T01" else "T01"
                            shot.params = {"movimento": "push_in", "amplitude": 0.03}
                            v.corrigida = True
                            v.acao_correcao = (
                                f"Template de {shot.id} alterado para {shot.template}"
                            )
                            ajustes.append(v.acao_correcao)
                            seq_count = 1
                            seq_template = shot.template
                        violacoes.append(v)
                else:
                    seq_template = shot.template
                    seq_count = 1

        # D4: Templates de informação (T06-T11): nunca dois consecutivos
        info_templates = {"T06", "T07", "T08", "T09", "T10", "T11"}
        for b in plano.blocos:
            ultimo_info_idx = -999
            for idx, shot in enumerate(b.shots):
                if shot.template in info_templates:
                    if idx == ultimo_info_idx + 1:
                        v = Violacao(
                            regra="D4",
                            descricao="Dois templates de informação consecutivos",
                            bloco_id=b.id,
                            shot_id=shot.id,
                            detalhes=f"Shot {shot.id} ({shot.template}) após outro template info",
                        )
                        if autocorrige:
                            shot.template = "T01"
                            shot.params = {"movimento": "push_in", "amplitude": 0.03}
                            shot.sobreposicoes.append({"tipo": "O4", "texto": "Destaque"})
                            v.corrigida = True
                            v.acao_correcao = f"Shot {shot.id} convertido para T01 com O4 Destaque"
                            ajustes.append(v.acao_correcao)
                        violacoes.append(v)
                    ultimo_info_idx = idx

        # D9: Proporção de imagens geradas
        total_shots = sum(len(b.shots) for b in plano.blocos)
        max_prop_gerar = 0.30
        if plano.preset == "rapido":
            max_prop_gerar = 0.15
        elif plano.preset == "caprichado":
            max_prop_gerar = 0.40

        shots_gerar = [
            s
            for b in plano.blocos
            for s in b.shots
            if any(
                plano.ativos.get(aid)
                and (
                    plano.ativos[aid].origem == OrigemAtivo.GERAR
                    or plano.ativos[aid].origem == "gerar"
                )
                for aid in s.ativos
            )
        ]
        prop_gerar = len(shots_gerar) / max(1, total_shots)
        if prop_gerar > max_prop_gerar:
            v = Violacao(
                regra="D9",
                descricao="Proporção de imagens geradas acima do limite do preset",
                detalhes=(
                    f"{prop_gerar * 100:.1f}% shots gerados (limite: {max_prop_gerar * 100:.0f}%)"
                ),
            )
            if autocorrige:
                excesso = int(len(shots_gerar) - (total_shots * max_prop_gerar)) + 1
                for s in shots_gerar[:excesso]:
                    for aid in s.ativos:
                        if aid in plano.ativos:
                            plano.ativos[aid].origem = OrigemAtivo.PESQUISAR
                v.corrigida = True
                v.acao_correcao = f"Convertidos {excesso} ativos de 'gerar' para 'pesquisar'"
                ajustes.append(v.acao_correcao)
            violacoes.append(v)

        # D10: Âncora real por bloco em temas históricos
        for b in plano.blocos:
            origens_bloco = [
                plano.ativos[aid].origem for s in b.shots for aid in s.ativos if aid in plano.ativos
            ]
            tem_real = any(
                orig
                in {
                    OrigemAtivo.BIBLIOTECA,
                    OrigemAtivo.PESQUISAR,
                    OrigemAtivo.PEDIR_AO_USUARIO,
                    "biblioteca",
                    "pesquisar",
                    "pedir_ao_usuario",
                }
                for orig in origens_bloco
            )
            if not tem_real and b.shots:
                v = Violacao(
                    regra="D10",
                    descricao="Bloco histórico sem nenhuma âncora visual real",
                    bloco_id=b.id,
                    detalhes=f"Bloco {b.id} não possui nenhum ativo real de acervo ou museu",
                )
                if autocorrige:
                    corrigido = False
                    for s in b.shots:
                        if s.ativos and s.ativos[0] in plano.ativos:
                            plano.ativos[s.ativos[0]].origem = OrigemAtivo.PESQUISAR
                            v.corrigida = True
                            v.acao_correcao = (
                                f"Ativo {s.ativos[0]} marcado como pesquisa real em {b.id}"
                            )
                            ajustes.append(v.acao_correcao)
                            corrigido = True
                            break
                    if not corrigido and b.shots:
                        novo_aid = f"A-REAL-{b.id}"
                        plano.ativos[novo_aid] = Ativo(
                            id=novo_aid,
                            descricao=f"Ativo de acervo real adicionado em {b.id}",
                            origem=OrigemAtivo.PESQUISAR,
                            usado_em=[b.shots[0].id],
                        )
                        b.shots[0].ativos.append(novo_aid)
                        v.corrigida = True
                        v.acao_correcao = f"Ativo real {novo_aid} associado a {b.id}"
                        ajustes.append(v.acao_correcao)
                violacoes.append(v)

        # D11: Reuso do mesmo ativo (máx 3 usos)
        contagem_usos: dict[str, list[str]] = {}
        for b in plano.blocos:
            for s in b.shots:
                for aid in s.ativos:
                    contagem_usos.setdefault(aid, []).append(s.id)

        for aid, usos in contagem_usos.items():
            if len(usos) > 3:
                v = Violacao(
                    regra="D11",
                    descricao="Ativo reutilizado mais de 3 vezes sem marcação de callback",
                    detalhes=f"Ativo {aid} usado em {len(usos)} shots ({usos})",
                )
                if autocorrige:
                    # Cria ativo alternativo para os usos excedentes
                    for extra_shot_id in usos[3:]:
                        novo_aid = f"{aid}_b"
                        if aid in plano.ativos:
                            plano.ativos[novo_aid] = plano.ativos[aid].model_copy(
                                update={"id": novo_aid, "nome_arquivo": f"{novo_aid}.jpg"}
                            )
                        for b in plano.blocos:
                            for s in b.shots:
                                if s.id == extra_shot_id:
                                    s.ativos = [novo_aid if a == aid else a for a in s.ativos]
                    v.corrigida = True
                    v.acao_correcao = f"Criado ativo alternativo {aid}_b para usos excedentes"
                    ajustes.append(v.acao_correcao)
                violacoes.append(v)

        # D12: Proporção de dissolve (máx 15%)
        if todos_cortes_total > 0:
            prop_dissolve = dissolves_total / todos_cortes_total
            if prop_dissolve > 0.15:
                v = Violacao(
                    regra="D12",
                    descricao="Proporção de dissolves excede 15% dos cortes",
                    detalhes=f"{prop_dissolve * 100:.1f}% de cortes são dissolve (máx: 15%)",
                )
                if autocorrige:
                    # Converte metade dos dissolves em corte
                    for b in plano.blocos:
                        for s in b.shots:
                            if s.transicao == "dissolve" and prop_dissolve > 0.15:
                                s.transicao = "corte"
                                dissolves_total -= 1
                                prop_dissolve = dissolves_total / todos_cortes_total
                    v.corrigida = True
                    v.acao_correcao = "Excesso de transições dissolve convertido para corte"
                    ajustes.append(v.acao_correcao)
                violacoes.append(v)

        # D15: Orçamento de tempo
        rel_est = estimar_tempo_plano(plano)
        plano.estimativa_producao_min = int(rel_est.tempo_total_minutos)
        if not rel_est.aprovado:
            v = Violacao(
                regra="D15",
                descricao="Estimativa de produção excede o orçamento do preset",
                detalhes=(
                    f"Estimado: {rel_est.tempo_total_minutos} min, "
                    f"Orçamento: {rel_est.orcamento_minutos} min"
                ),
            )
            if autocorrige and rel_est.ajustes_realizados:
                v.corrigida = True
                v.acao_correcao = "; ".join(rel_est.ajustes_realizados)
                ajustes.extend(rel_est.ajustes_realizados)
            violacoes.append(v)

        corrigidas = sum(1 for v in violacoes if v.corrigida)
        todas_corrigidas = corrigidas == len(violacoes)

        plano.verificacao = {
            "aprovado": todas_corrigidas,
            "ajustes": len(ajustes),
            "total_violacoes": len(violacoes),
        }

        return ResultadoVerificacao(
            aprovado=todas_corrigidas,
            total_violacoes=len(violacoes),
            violacoes_corrigidas=corrigidas,
            violacoes=violacoes,
            ajustes=ajustes,
        )
