"""Resolução de ativos e curadoria de acervos (Etapa P7 do pipeline).

Coordena:
1. Verificação da pasta manual do usuário (02_midias/manual/).
2. Consulta e reuso da biblioteca do canal (02_midias/biblioteca/).
3. Pesquisa em acervos abertos com filtros rígidos de licença e resolução.
4. Curadoria via visão local Ollama (nota >= 7.0) para aprovação.
5. Geração da lista_de_busca.md para ativos que dependem do usuário.
6. Publicação de 01_plano/ativos_resolvidos.json e 02_midias/escolhas.json.
"""

from __future__ import annotations

import json
import shutil
from typing import Any

from docforja.esquemas import Ativo, OrigemAtivo
from docforja.io import atomic_write_json, atomic_write_text
from docforja.midia.acervo import AcervoAdapter, AdaptadorAcervoMock, AdaptadorWikimedia
from docforja.midia.curadoria import CuradorImagens
from docforja.midia.licenca import (
    FichaLicenca,
    carregar_ficha_licenca,
    salvar_ficha_licenca,
)
from docforja.midia.lista_busca import gerar_lista_de_busca_md
from docforja.midia.pasta_manual import escanear_pasta_manual
from docforja.nucleo.projeto import Projeto


def resolver_ativos_projeto(
    projeto: Projeto,
    acervos: list[AcervoAdapter] | None = None,
    curador: CuradorImagens | None = None,
    usar_mock_se_sem_rede: bool = True,
) -> dict[str, Ativo]:
    """Executa a resolução completa de ativos para o projeto."""
    pasta_plano = projeto.pastas.plano
    arquivo_ativos = pasta_plano / "ativos.json"
    if not arquivo_ativos.is_file():
        raise FileNotFoundError(f"Arquivo de ativos ausente: {arquivo_ativos}")

    dados_ativos = json.loads(arquivo_ativos.read_text(encoding="utf-8")).get("ativos", {})
    if not dados_ativos:
        raise ValueError("Nenhum ativo listado para resolução.")

    ativos = {aid: Ativo.model_validate(item) for aid, item in dados_ativos.items()}

    # Cria pastas de mídia do projeto
    pasta_midias = projeto.pastas.midias
    pasta_biblioteca = pasta_midias / "biblioteca"
    pasta_pesquisadas = pasta_midias / "pesquisadas"
    pasta_geradas = pasta_midias / "geradas"
    pasta_manual = pasta_midias / "manual"
    pasta_nao_atribuidas = pasta_midias / "nao_atribuidas"

    pastas_necessarias = [
        pasta_biblioteca,
        pasta_pesquisadas,
        pasta_geradas,
        pasta_manual,
        pasta_nao_atribuidas,
    ]
    for p in pastas_necessarias:
        p.mkdir(parents=True, exist_ok=True)

    # 1. Escaneia a pasta manual do usuário para associar arquivos já fornecidos
    mapa_shots = {}
    for aid, a in ativos.items():
        for shot_id in a.usado_em:
            mapa_shots[shot_id] = aid

    atribuidos_manuais, _ = escanear_pasta_manual(
        pasta_manual, pasta_nao_atribuidas, ativos, mapa_shots=mapa_shots
    )

    # 2. Configura adaptadores de acervo e curador
    if acervos is None:
        try:
            acervos = [AdaptadorWikimedia()]
        except Exception:
            acervos = [AdaptadorAcervoMock()] if usar_mock_se_sem_rede else []

    if curador is None:
        curador = CuradorImagens()

    escolhas: dict[str, dict[str, Any]] = {}

    for aid, ativo in ativos.items():
        # Caso 1: Usuário já forneceu o arquivo manualmente
        if aid in atribuidos_manuais:
            caminho_manual = atribuidos_manuais[aid]
            ativo.caminho = caminho_manual
            ficha = carregar_ficha_licenca(caminho_manual)
            if ficha:
                ativo.licenca = ficha.model_dump()
            escolhas[aid] = {
                "origem": "manual",
                "caminho": str(caminho_manual),
                "aprovado": True,
            }
            continue

        # Caso 2: Ativo com origem BIBLIOTECA
        if ativo.origem == OrigemAtivo.BIBLIOTECA:
            # Procura em biblioteca local do canal
            candidatos_locais = list(pasta_biblioteca.glob(f"{aid}.*"))
            if candidatos_locais:
                escolhido = candidatos_locais[0]
                ativo.caminho = escolhido
                escolhas[aid] = {
                    "origem": "biblioteca",
                    "caminho": str(escolhido),
                    "aprovado": True,
                }
                continue
            # Se não encontrar na biblioteca, converte para pesquisa
            ativo.origem = OrigemAtivo.PESQUISAR

        # Caso 3: Ativo com origem PESQUISAR
        if ativo.origem == OrigemAtivo.PESQUISAR:
            pasta_ativo = pasta_pesquisadas / aid
            pasta_ativo.mkdir(parents=True, exist_ok=True)
            escolhida_existente = pasta_ativo / "escolhida.jpg"

            if escolhida_existente.is_file():
                ativo.caminho = escolhida_existente
                ficha = carregar_ficha_licenca(escolhida_existente)
                if ficha:
                    ativo.licenca = ficha.model_dump()
                escolhas[aid] = {
                    "origem": "pesquisar",
                    "caminho": str(escolhida_existente),
                    "aprovado": True,
                }
                continue

            # Realiza busca com os adaptadores disponíveis
            candidatas_baixadas = []
            termos_busca = [ativo.descricao]
            if ativo.busca and "termos" in ativo.busca:
                termos_busca = ativo.busca["termos"]

            for adaptador in acervos:
                for termo in termos_busca:
                    try:
                        resultados = adaptador.buscar(termo, limite=3)
                    except Exception:
                        resultados = []

                    for idx, cand in enumerate(resultados, start=1):
                        # Se for patrimônio restrito italiano, não escolhe sozinho (04 §2)
                        if cand.patrimonio_restrito:
                            ativo.origem = OrigemAtivo.PEDIR_AO_USUARIO
                            ativo.motivo = (
                                "Foto de bem cultural restrito (Codice dei beni culturali) "
                                "ou acervo que exige autorização para uso comercial."
                            )
                            break

                        destino_cand = pasta_ativo / f"cand_{adaptador.nome}_{idx}.jpg"
                        try:
                            adaptador.baixar(cand, destino_cand)
                            candidatas_baixadas.append((cand, destino_cand))
                        except Exception:
                            continue

                    limite_cands = len(candidatas_baixadas) >= 3
                    if ativo.origem == OrigemAtivo.PEDIR_AO_USUARIO or limite_cands:
                        break
                if ativo.origem == OrigemAtivo.PEDIR_AO_USUARIO or limite_cands:
                    break

            if ativo.origem == OrigemAtivo.PEDIR_AO_USUARIO:
                # Cai no caso 5 abaixo
                pass
            elif candidatas_baixadas:
                melhor = curador.escolher_melhor_candidata(
                    candidatas_baixadas, descricao=ativo.descricao, nota_minima=7.0
                )
                if melhor:
                    cand_escolhido, caminho_origem, nota, motivo = melhor
                    shutil.copy2(caminho_origem, escolhida_existente)
                    salvar_ficha_licenca(
                        escolhida_existente,
                        FichaLicenca(
                            url_origem=cand_escolhido.url_origem,
                            autor=cand_escolhido.autor,
                            licenca=cand_escolhido.licenca,
                            comercial=cand_escolhido.comercial,
                            patrimonio_restrito=cand_escolhido.patrimonio_restrito,
                            texto_credito=f"{cand_escolhido.autor} / {cand_escolhido.licenca}",
                            detalhes={"nota_curador": nota, "motivo_curador": motivo},
                        ),
                    )
                    ativo.caminho = escolhida_existente
                    ativo.licenca = {
                        "autor": cand_escolhido.autor,
                        "licenca": cand_escolhido.licenca,
                        "comercial": cand_escolhido.comercial,
                    }
                    escolhas[aid] = {
                        "origem": "pesquisar",
                        "caminho": str(escolhida_existente),
                        "nota": nota,
                        "motivo": motivo,
                        "aprovado": True,
                    }
                    continue
                else:
                    # Nenhuma candidata atingiu nota >= 7.0
                    if ativo.plano_b == "gerar" and "proibido_gerar" not in ativo.proibicoes:
                        ativo.origem = OrigemAtivo.GERAR
                    else:
                        ativo.origem = OrigemAtivo.PEDIR_AO_USUARIO
                        ativo.motivo = (
                            "Busca em acervos encontrou apenas imagens com nota do Curador "
                            "inferior a 7.0 (baixa resolução, anacronismo ou marca d'água)."
                        )

        # Caso 4: Ativo com origem GERAR
        if ativo.origem == OrigemAtivo.GERAR:
            escolhas[aid] = {
                "origem": "gerar",
                "prompt": ativo.prompt,
                "status": "aguardando_comfyui",
            }
            continue

        # Caso 5: Ativo com origem PEDIR_AO_USUARIO
        if ativo.origem == OrigemAtivo.PEDIR_AO_USUARIO:
            escolhas[aid] = {
                "origem": "pedir_ao_usuario",
                "motivo": ativo.motivo,
                "status": "pendente_usuario",
            }

    # 3. Gera lista_de_busca.md atualizada
    opcoes = projeto.obter_opcoes()
    tema = opcoes.get("tema", projeto.slug)
    conteudo_lista_busca = gerar_lista_de_busca_md(ativos, tema=tema)
    atomic_write_text(pasta_plano / "lista_de_busca.md", conteudo_lista_busca)

    # 4. Grava ativos_resolvidos.json
    dados_resolvidos = {
        "versao": 1,
        "total_ativos": len(ativos),
        "ativos": {aid: a.model_dump(mode="json") for aid, a in ativos.items()},
    }
    atomic_write_json(pasta_plano / "ativos_resolvidos.json", dados_resolvidos)

    # 5. Grava escolhas.json em 02_midias/
    atomic_write_json(pasta_midias / "escolhas.json", escolhas)

    return ativos
