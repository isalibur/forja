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

    def _regra(self, nome: str) -> dict[str, Any]:
        return self.config.get("regras", {}).get(nome, {})

    def verificar_e_corrigir(
        self,
        plano: Plano,
        blocos_processados: list[BlocoProcessado] | None = None,
        autocorrige: bool = True,
        tempos_reais: dict[str, float] | None = None,
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
        minimo_blocos = self._regra("D16_capitulos").get("min_blocos_para_exigir", 4)
        if len(plano.blocos) >= minimo_blocos:
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

                if autocorrige and tempos_reais and len(shot.segmentos) == 1:
                    sid = shot.segmentos[0]
                    duracao_audio = tempos_reais.get(sid)
                    if duracao_audio is not None and abs(shot.duracao_s - duracao_audio) > 0.05:
                        anterior = shot.duracao_s
                        shot.duracao_s = duracao_audio
                        v = Violacao(
                            regra="D14",
                            descricao="Duração do shot ajustada à narração real",
                            bloco_id=b.id,
                            shot_id=shot.id,
                            detalhes=f"Plano: {anterior:.3f}s; áudio: {duracao_audio:.3f}s",
                            corrigida=True,
                            acao_correcao=f"{shot.id}: duração sincronizada ao áudio real",
                        )
                        violacoes.append(v)
                        ajustes.append(v.acao_correcao)

                # D1: Duração por intensidade
                # Identifica intensidade aproximada pelo segmento
                intensidade = 5
                if shot.segmentos and shot.segmentos[0] in segmentos_map:
                    intensidade = int(segmentos_map[shot.segmentos[0]].intensidade or 5)

                faixas_d1 = self._regra("D1_duracao_intensidade").get("faixas", {})
                faixa_d1 = next(
                    (
                        faixa_cfg
                        for intervalo, faixa_cfg in faixas_d1.items()
                        if int(intervalo.split("-")[0])
                        <= intensidade
                        <= int(intervalo.split("-")[1])
                    ),
                    faixas_d1.get("4-6", {"min_s": 3.0, "max_s": 6.0}),
                )
                min_s = float(faixa_d1["min_s"])
                max_s = float(faixa_d1["max_s"])

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
                    # A fala é imutável: D1 precisa de nova decupagem quando
                    # existem tempos reais, nunca de truncamento numérico.
                    tem_audio_real = tempos_reais is not None and any(
                        sid in tempos_reais for sid in shot.segmentos
                    )
                    if (
                        autocorrige
                        and tem_audio_real
                        and shot.duracao_s < min_s
                        and self._regra("D1_duracao_intensidade").get(
                            "permitir_excecao_fala_curta", False
                        )
                    ):
                        v.corrigida = True
                        v.acao_correcao = (
                            f"{shot.id}: exceção D1 para fala curta de {shot.duracao_s:.3f}s"
                        )
                        ajustes.append(v.acao_correcao)
                    elif autocorrige and not tem_audio_real:
                        shot.duracao_s = max(min_s, min(max_s, shot.duracao_s))
                        v.corrigida = True
                        v.acao_correcao = (
                            f"Ajustada duração de {shot.id} para {shot.duracao_s:.1f}s"
                        )
                        ajustes.append(v.acao_correcao)
                    violacoes.append(v)

                # D2: Shot estático acima do limite configurado.
                movimento = shot.params.get("movimento")
                regra_d2 = self._regra("D2_movimento_max_estatico")
                max_estatico_s = float(regra_d2.get("max_segundos", 4.0))
                excecoes_d2 = regra_d2.get("templates_excecao", ["T00"])
                if (
                    shot.duracao_s > max_estatico_s
                    and movimento == "estático"
                    and shot.template not in excecoes_d2
                    and not shot.params.get("intencional", False)
                ):
                    v = Violacao(
                        regra="D2",
                        descricao=f"Shot estático por mais de {max_estatico_s:g} s",
                        bloco_id=b.id,
                        shot_id=shot.id,
                        detalhes=f"Shot {shot.id} estático por {shot.duracao_s:.1f}s",
                    )
                    if autocorrige:
                        movimento_correcao = regra_d2.get("movimento_correcao", "push_in")
                        amplitude_correcao = float(regra_d2.get("amplitude_correcao", 0.02))
                        shot.params["movimento"] = movimento_correcao
                        shot.params["amplitude"] = amplitude_correcao
                        v.corrigida = True
                        v.acao_correcao = (
                            f"Adicionado {movimento_correcao} com amplitude "
                            f"{amplitude_correcao:.1%} a {shot.id}"
                        )
                        ajustes.append(v.acao_correcao)
                    violacoes.append(v)

                # D5: Texto na tela e tempo mínimo de leitura
                regra_d5 = self._regra("D5_texto_na_tela")
                max_palavras = max(
                    1,
                    round(
                        int(regra_d5.get("max_palavras_por_item", 7)) * self.fator_densidade
                    ),
                )
                for txt_idx, texto_item in enumerate(shot.textos):
                    palavras = texto_item.split()
                    if len(palavras) > max_palavras:
                        v = Violacao(
                            regra="D5",
                            descricao="Texto na tela excede 7 palavras",
                            bloco_id=b.id,
                            shot_id=shot.id,
                            detalhes=f"Texto '{texto_item}' tem {len(palavras)} palavras",
                        )
                        if autocorrige:
                            shot.textos[txt_idx] = " ".join(palavras[:max_palavras])
                            v.corrigida = True
                            v.acao_correcao = (
                                f"Texto de {shot.id} encurtado para {max_palavras} palavras"
                            )
                            ajustes.append(v.acao_correcao)
                        violacoes.append(v)

                    dur_necessaria = float(regra_d5.get("duracao_base_s", 1.0)) + (
                        float(regra_d5.get("duracao_por_palavra_s", 0.3)) * len(palavras)
                    )
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

                # D6: Sobreposições simultâneas, exceto tipos automáticos.
                regra_d6 = self._regra("D6_sobreposicoes_simultaneas")
                ignorar_d6 = set(regra_d6.get("ignorar", ["O2"]))
                max_sobreposicoes = max(
                    1,
                    round(
                        int(regra_d6.get("max_sobreposicoes", 2)) * self.fator_densidade
                    ),
                )
                sobres_reais = [
                    o for o in shot.sobreposicoes if o.get("tipo") not in ignorar_d6
                ]
                if len(sobres_reais) > max_sobreposicoes:
                    v = Violacao(
                        regra="D6",
                        descricao="Excesso de sobreposições simultâneas (> 2)",
                        bloco_id=b.id,
                        shot_id=shot.id,
                        detalhes=(
                            f"Shot {shot.id} possui {len(sobres_reais)} sobreposições "
                            f"(máx: {max_sobreposicoes})"
                        ),
                    )
                    if autocorrige:
                        # Descarta seguindo a prioridade declarada no YAML.
                        mantidas = list(sobres_reais)
                        prioridade_descarte = regra_d6.get(
                            "prioridade_descarte", ["O4", "O3", "O1"]
                        )
                        for tipo in prioridade_descarte:
                            while len(mantidas) > max_sobreposicoes:
                                candidato = next(
                                    (o for o in mantidas if o.get("tipo") == tipo), None
                                )
                                if candidato is None:
                                    break
                                mantidas.remove(candidato)
                        if len(mantidas) > max_sobreposicoes:
                            mantidas = mantidas[:max_sobreposicoes]
                        ignoradas = [
                            o for o in shot.sobreposicoes if o.get("tipo") in ignorar_d6
                        ]
                        shot.sobreposicoes = mantidas + ignoradas
                        v.corrigida = True
                        v.acao_correcao = f"Sobreposições de {shot.id} limitadas a 2"
                        ajustes.append(v.acao_correcao)
                    violacoes.append(v)

                # D7: Identificação O1 conforme política configurada.
                regra_d7 = self._regra("D7_identificacao_o1")
                min_duracao_o1 = float(regra_d7.get("min_duracao_s", 2.5))
                for o in list(shot.sobreposicoes):
                    if o.get("tipo") == "O1":
                        texto_entidade = o.get("texto", "").upper().strip()
                        if (
                            regra_d7.get("apenas_primeira_aparicao", True)
                            and texto_entidade in entidades_o1_vistas
                        ):
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
                            if shot.duracao_s < min_duracao_o1:
                                v = Violacao(
                                    regra="D7",
                                    descricao="Shot com identificação O1 inferior a 2.5s",
                                    bloco_id=b.id,
                                    shot_id=shot.id,
                                    detalhes=f"Shot {shot.id} dura {shot.duracao_s:.1f}s",
                                )
                                if autocorrige:
                                    shot.duracao_s = min_duracao_o1
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
                if (
                    self._regra("D12_transicoes").get("fade_preto_apenas_entre_blocos", True)
                    and shot.transicao == "fade_preto"
                    and idx > 0
                ):
                    v = Violacao(
                        regra="D12",
                        descricao="Transição fade_preto usada no meio de um bloco",
                        bloco_id=b.id,
                        shot_id=shot.id,
                        detalhes=f"Shot {shot.id} com fade_preto na posição {idx}",
                    )
                    if autocorrige:
                        shot.transicao = self._regra("D12_transicoes").get(
                            "transicao_padrao", "corte"
                        )
                        v.corrigida = True
                        v.acao_correcao = (
                            f"Transição de {shot.id} alterada de fade_preto para corte"
                        )
                        ajustes.append(v.acao_correcao)
                    violacoes.append(v)

                # D13: Números na tela presentes no roteiro
                for txt in (
                    shot.textos
                    if self._regra("D13_numeros_datas_roteiro").get("exigir_no_roteiro", True)
                    else []
                ):
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
                regra_d17 = self._regra("D17_vitimas_reais")
                lista_templates_vitimas = regra_d17.get("templates_permitidos", ["T01", "T02"])
                templates_vitimas = set(lista_templates_vitimas)
                movimentos_t01 = list(
                    regra_d17.get("t01_movimentos_permitidos", ["estático", "push_in"])
                )
                amplitude_t01 = float(regra_d17.get("t01_max_amplitude", 0.02))
                intensidade_t02 = float(regra_d17.get("t02_max_intensidade", 0.15))
                indicadores_vitima = regra_d17.get(
                    "indicadores_vitima", ["molde", "esqueleto", "vítima", "vitima", "corpo"]
                )
                for aid in shot.ativos:
                    ativo_obj = plano.ativos.get(aid)
                    if ativo_obj:
                        desc_lower = ativo_obj.descricao.lower()
                        if any(
                            k in desc_lower
                            for k in indicadores_vitima
                        ):
                            # Deve ser T01 estático/push <= 2% ou T02 intensidade <= 0.15
                            if shot.template not in templates_vitimas:
                                v = Violacao(
                                    regra="D17",
                                    descricao="Vítima real exibida com template não permitido",
                                    bloco_id=b.id,
                                    shot_id=shot.id,
                                    detalhes=f"Shot {shot.id} usa {shot.template} para vítima",
                                )
                                if autocorrige:
                                    template_seguro = (
                                        "T01"
                                        if "T01" in templates_vitimas
                                        else next(iter(lista_templates_vitimas), "T01")
                                    )
                                    shot.template = template_seguro
                                    shot.params = {
                                        "movimento": "push_in",
                                        "amplitude": amplitude_t01,
                                    }
                                    v.corrigida = True
                                    v.acao_correcao = (
                                        f"Ajustado shot {shot.id} de vítima para T01 suave"
                                    )
                                    ajustes.append(v.acao_correcao)
                                violacoes.append(v)
                            elif (
                                shot.template == "T01"
                                and (
                                    shot.params.get("movimento", "estático") not in movimentos_t01
                                    or shot.params.get("amplitude", 0.0) > amplitude_t01
                                )
                            ):
                                v = Violacao(
                                    regra="D17",
                                    descricao="Movimento T01 acima do limite para vítima real",
                                    bloco_id=b.id,
                                    shot_id=shot.id,
                                    detalhes=(
                                        f"Movimento {shot.params.get('movimento')} / amplitude "
                                        f"{shot.params.get('amplitude', 0.0)}"
                                    ),
                                )
                                if autocorrige:
                                    shot.params["movimento"] = next(
                                        iter(movimentos_t01), "estático"
                                    )
                                    shot.params["amplitude"] = amplitude_t01
                                    v.corrigida = True
                                    v.acao_correcao = f"Movimento de {shot.id} limitado por D17"
                                    ajustes.append(v.acao_correcao)
                                violacoes.append(v)
                            elif (
                                shot.template == "T02"
                                and shot.params.get("intensidade", 0.0) > intensidade_t02
                            ):
                                v = Violacao(
                                    regra="D17",
                                    descricao="Intensidade T02 acima do limite para vítima real",
                                    bloco_id=b.id,
                                    shot_id=shot.id,
                                    detalhes=f"Intensidade {shot.params.get('intensidade')}",
                                )
                                if autocorrige:
                                    shot.params["intensidade"] = intensidade_t02
                                    v.corrigida = True
                                    v.acao_correcao = f"Intensidade de {shot.id} limitada por D17"
                                    ajustes.append(v.acao_correcao)
                                violacoes.append(v)

                            # Sem SFX de impacto
                            sfx_agressivo = [
                                s
                                for s in shot.sfx
                                if regra_d17.get("proibir_sfx_impacto", True)
                                and any(
                                    x in s.lower()
                                    for x in regra_d17.get(
                                        "sfx_impacto_terms",
                                        ["impacto", "hit", "boom", "explosao"],
                                    )
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
        regra_d3 = self._regra("D3_sequencia_mesmo_template")
        max_sequencia_d3 = int(regra_d3.get("max_geral", 3))
        limites_template_d3 = regra_d3.get("max_por_template", {})
        alternativas_d3 = regra_d3.get("alternativas_correcao", ["T02", "T03", "T04"])
        for b in plano.blocos:
            seq_count = 1
            seq_template = None
            for shot in b.shots:
                if shot.template == seq_template:
                    seq_count += 1
                    limite = int(limites_template_d3.get(seq_template, max_sequencia_d3))
                    if seq_count > limite:
                        v = Violacao(
                            regra="D3",
                            descricao="Excesso de templates consecutivos iguais",
                            bloco_id=b.id,
                            shot_id=shot.id,
                            detalhes=f"{seq_count} shots consecutivos de {seq_template}",
                        )
                        if autocorrige:
                            # Escolhe alternativa declarada na configuração.
                            shot.template = next(iter(alternativas_d3), "T01")
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
        info_templates = set(
            self._regra("D4_templates_informacao").get(
                "templates", ["T06", "T07", "T08", "T09", "T10", "T11"]
            )
        )
        regra_d4 = self._regra("D4_templates_informacao")
        permitir_consecutivos_d4 = regra_d4.get(
            "permitir_consecutivos", False
        )
        for b in plano.blocos:
            tempo_bloco = 0.0
            ultima_info_s: float | None = None
            for shot in b.shots:
                intensidade = 5
                if shot.segmentos and shot.segmentos[0] in segmentos_map:
                    intensidade = int(segmentos_map[shot.segmentos[0]].intensidade or 5)
                espaçamentos = regra_d4.get("espacamento_por_intensidade", {})
                intervalo_d4 = next(
                    (
                        float(segundos)
                        for faixa, segundos in espaçamentos.items()
                        if int(faixa.split("-")[0])
                        <= intensidade
                        <= int(faixa.split("-")[1])
                    ),
                    0.0,
                )
                if shot.template in info_templates:
                    if ultima_info_s is not None:
                        intervalo_real = tempo_bloco - ultima_info_s
                        if intervalo_real < intervalo_d4 or (
                            not permitir_consecutivos_d4 and intervalo_real == 0
                        ):
                            v = Violacao(
                                regra="D4",
                                descricao="Templates de informação com espaçamento insuficiente",
                                bloco_id=b.id,
                                shot_id=shot.id,
                                detalhes=(
                                    f"Shot {shot.id} ({shot.template}) separado por "
                                    f"{intervalo_real:.1f}s; mínimo configurado: "
                                    f"{intervalo_d4:.1f}s"
                                ),
                            )
                            if autocorrige:
                                shot.template = "T01"
                                shot.params = {"movimento": "push_in", "amplitude": 0.03}
                                shot.sobreposicoes.append({"tipo": "O4", "texto": "Destaque"})
                                v.corrigida = True
                                v.acao_correcao = (
                                    f"Shot {shot.id} convertido para T01 com O4 Destaque"
                                )
                                ajustes.append(v.acao_correcao)
                            violacoes.append(v)
                    ultima_info_s = tempo_bloco
                tempo_bloco += shot.duracao_s

        # D9: Proporção de imagens geradas
        total_shots = sum(len(b.shots) for b in plano.blocos)
        preset_d9 = self.config.get("presets", {}).get(plano.preset, {})
        max_prop_gerar = float(
            preset_d9.get(
                "max_prop_gerar",
                self._regra("D9_proporcao_geradas").get("max_proporcao_padrao", 0.30),
            )
        )

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
        regra_d10 = self._regra("D10_ancora_real_por_bloco")
        origens_reais_config = set(
            regra_d10.get(
                "origens_reais", ["biblioteca", "pesquisar", "pedir_ao_usuario"]
            )
        )
        minimo_ativos_reais = int(regra_d10.get("min_ativos_reais", 1))
        for b in plano.blocos:
            ativos_reais_bloco = {
                aid
                for s in b.shots
                for aid in s.ativos
                if aid in plano.ativos and str(plano.ativos[aid].origem) in origens_reais_config
            }
            tem_ativos_reais = len(ativos_reais_bloco) >= minimo_ativos_reais
            if not tem_ativos_reais and b.shots:
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
            max_usos = int(self._regra("D11_reuso_mesmo_ativo").get("max_usos", 3))
            if len(usos) > max_usos:
                v = Violacao(
                    regra="D11",
                    descricao="Ativo reutilizado mais de 3 vezes sem marcação de callback",
                    detalhes=f"Ativo {aid} usado em {len(usos)} shots ({usos})",
                )
                if autocorrige:
                    # Cria ativo alternativo para os usos excedentes
                    for extra_shot_id in usos[max_usos:]:
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

        # D14 também cobre a duração, não apenas a presença dos IDs. A
        # autocorreção de outras regras não pode deslocar a narração real.
        if tempos_reais is not None:
            duracoes_por_segmento: dict[str, float] = {}
            for bloco in plano.blocos:
                for shot in bloco.shots:
                    if len(shot.segmentos) == 1:
                        sid = shot.segmentos[0]
                        duracoes_por_segmento[sid] = (
                            duracoes_por_segmento.get(sid, 0.0) + shot.duracao_s
                        )
            divergentes = {
                sid: (round(duracoes_por_segmento.get(sid, 0.0), 3), round(duracao, 3))
                for sid, duracao in tempos_reais.items()
                if abs(duracoes_por_segmento.get(sid, 0.0) - duracao) > 0.05
            }
            if divergentes:
                violacoes.append(
                    Violacao(
                        regra="D14",
                        descricao="Duração dos shots diverge da narração real",
                        detalhes=f"Durações (plano, áudio): {divergentes}",
                    )
                )

        # D12: Proporção de dissolve (máx 15%)
        limite_dissolve = float(
            self._regra("D12_transicoes").get("max_prop_dissolve", 0.15)
        )
        if todos_cortes_total > 0:
            prop_dissolve = dissolves_total / todos_cortes_total
            if prop_dissolve > limite_dissolve:
                v = Violacao(
                    regra="D12",
                    descricao="Proporção de dissolves excede o limite configurado",
                    detalhes=(
                        f"{prop_dissolve * 100:.1f}% de cortes são dissolve "
                        f"(máx: {limite_dissolve * 100:.1f}%)"
                    ),
                )
                if autocorrige:
                    # Converte metade dos dissolves em corte
                    for b in plano.blocos:
                        for s in b.shots:
                            if s.transicao == "dissolve" and prop_dissolve > limite_dissolve:
                                s.transicao = self._regra("D12_transicoes").get(
                                    "transicao_padrao", "corte"
                                )
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
