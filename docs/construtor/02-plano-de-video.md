# 02 — O Plano de Vídeo (o coração do produto)

> **Para a IA que vai programar:** o Plano de Vídeo é o artefato central. Todo o resto (imagens, render, idiomas) **consome** o plano. Ele precisa ser completo (cada segundo da narração coberto), validado por código (verificador de dosagem) e legível para o usuário (`plano.md` + prévia).

---

## 0. Tipos de plano

O mesmo formato de plano serve a quatro tipos de produção (campo `tipo`):

| `tipo` | O que muda no planejamento | Documento |
|---|---|---|
| `longo` | Tudo o que está neste documento | este |
| `short_derivado` | Parte de um plano `longo`: escolhe os momentos, recorta, verticaliza, acrescenta gancho e frase-ponte | `11 §3` |
| `short_avulso` | Parte de um tema + objetivo + fórmula; usa templates V01–V10 e o verificador de shorts | `11 §4` |
| `musica` | Sem roteiro: lista de faixas + 1–2 imagens + animações em loop L01–L06 | `12` |

Todos terminam com a mesma estrutura de saída e os mesmos metadados estratégicos (`13`).

## 1. O que o planejamento entrega

| Arquivo | Para quem | Conteúdo |
|---|---|---|
| `01_plano/plano.json` | sistema | Plano completo (formato §4) |
| `01_plano/plano.md` | você | Plano legível por bloco: tempo, narração, template, imagem, texto na tela, som |
| `01_plano/previa.mp4` | você | Animatic em 540p com rascunhos/placeholders, narração e trilha provisória |
| `01_plano/lista_de_busca.md` | você | Imagens que o sistema precisa que você traga (com termos, sites, nome do arquivo e plano B) |
| `01_plano/numeros_na_tela.md` | você | Todo número, data, nome e citação que vira texto na tela, para conferir |
| `01_plano/estimativa.md` | você | Tempo estimado de produção por etapa e por idioma; o que foi cortado para caber no orçamento |
| `01_plano/verificacao.md` | você | Regras de dosagem aplicadas e ajustes feitos |

## 2. Etapas do planejamento

| # | Etapa | Quem | O que faz |
|---|---|---|---|
| P1 | **Leitura do roteiro** | LLM (`structured`) + código | Segmenta (sem mudar palavras), identifica blocos, intensidade 1–10 e **batidas** de cada segmento (`gancho`, `contexto`, `dado`, `revelação`, `tensão`, `respiro`, `transição_lugar`, `transição_tempo`, `citação`, `fechamento`) e extrai **entidades** (pessoas, lugares, datas, números, obras, objetos, citações) |
| P2 | **Narração principal + tempos** | código (TTS/WhisperX) ou narração pronta | Duração real de cada segmento e de cada palavra |
| P3 | **Estratégia visual por bloco** | LLM | Para cada bloco: modo visual dominante (`arquivo`, `reconstituição`, `dados`, `geografia`, `misto`), elementos recorrentes (ex.: relógio de contexto), callbacks, clima musical |
| P4 | **Lista de shots** | LLM, por bloco | Para cada segmento, 1–3 shots: template do catálogo (§3), parâmetros, necessidade de imagem, textos, SFX, transição, plano B |
| P5 | **Consolidação de ativos** | código + LLM | Junta necessidades iguais (a mesma foto em 3 shots = 1 ativo), procura primeiro na **biblioteca do canal** (`03`), define a origem de cada ativo: `biblioteca` · `pesquisar` · `gerar` · `pedir_ao_usuário` · `dados` (gráfico/mapa) |
| P6 | **Verificador de dosagem** | código | Aplica as regras (§5), corrige o que dá por código e devolve ao LLM só os blocos que precisam de reescrita (máx. 3 voltas) |
| P7 | **Resolução de ativos** | APIs + visão local + ComfyUI | Pesquisa fotos reais, curadoria, rascunhos das imagens a gerar, monta a lista de busca (`04`) |
| P8 | **Estimativa e prévia** | código | Estima o tempo de produção (benchmark), ajusta ao orçamento do preset, renderiza `previa.mp4`, escreve `plano.md` |

P2 roda em paralelo com P1/P3; P4 começa com tempos estimados (145 palavras/min) e é recalculado assim que P2 termina.

## 3. Catálogo de templates (escolha fechada)

Cada shot usa **exatamente um template** + até 2 sobreposições. Os templates são componentes Remotion do **kit do canal** (`03`), com a identidade visual aplicada.

| ID | Template | Para quê | Parâmetros principais | Duração típica | Intensidade |
|---|---|---|---|---|---|
| T00 | `Respiro` | Preto ou textura com cinza/grão; pausa dramática | cor, partículas on/off | 1–3 s | qualquer |
| T01 | `Foto` | Foto/pintura/imagem com movimento de câmera (Ken Burns) | ativo, movimento (`push_in`, `pull_out`, `pan_esq`, `pan_dir`, `estático`), amplitude, foco (x,y) | 3–7 s | 1–10 |
| T02 | `FotoProfundidade` | Parallax 2.5D (DepthFlow) | ativo, movimento (`dolly`, `orbita`, `zoom`), intensidade do efeito | 3–6 s | 3–8 |
| T03 | `FotoRecorte` | Sujeito recortado (BiRefNet) sobre fundo desfocado/escurecido/da paleta, com leve deslocamento entre camadas | ativo, fundo (`desfocado`, `paleta`, `outra_imagem`), entrada do sujeito | 3–5 s | 4–9 |
| T04 | `FotoDetalhe` | Zoom numa região + caixa/círculo de destaque e linha de anotação | ativo, região, rótulo | 3–5 s | 3–8 |
| T05 | `Comparacao` | Lado a lado / antes e depois | ativo A, ativo B, rótulos | 4–6 s | 3–7 |
| T06 | `TextoImpacto` | Uma frase/palavra-chave grande | texto (≤ 7 palavras), estilo (`limpo`, `riscado`, `carvão`), fundo (preto/imagem escurecida) | 2–4 s | 5–10 |
| T07 | `Citacao` | Citação de fonte (documento, carta, inscrição) com destaque | texto, tradução, fonte, estilo (`papel`, `pedra`, `escuro`) | 4–7 s | 3–8 |
| T08 | `Numero` | Número grande com contexto (contador) | valor, prefixo (`≈`, `+`), unidade, legenda | 3–5 s | 4–9 |
| T09 | `Grafico` | Barras, linha, comparação de escala | tipo, dados (do roteiro), rótulos | 4–7 s | 3–7 |
| T10 | `Mapa` | Mapa 2D/2,5D com pinos, rotas, áreas, setas, zoom | região, pontos, linhas, áreas, câmera | 4–8 s | 3–8 |
| T11 | `LinhaDoTempo` | Datas em sequência | eventos (data, rótulo, ativo opcional), destaque | 5–8 s | 2–6 |
| T12 | `Capitulo` | Cartão de início de bloco | número, título | 2–3 s | qualquer |
| T13 | `Abertura` | Título do vídeo | título, subtítulo | 3–5 s | — |
| T14 | `Encerramento` | Tela final (espaço para elementos do YouTube) | — | 15–20 s | — |

**Sobreposições (combináveis com qualquer template):** `O1 Identificacao` (nome + descrição; só na primeira aparição de pessoa/lugar) · `O2 Rotulo` ("RECONSTITUIÇÃO ARTÍSTICA" ou crédito do arquivo — **automático**, o planejador não escolhe) · `O3 Contexto` (relógio/lugar/ano persistente, se o bloco usar) · `O4 Destaque` (seta, círculo).

**Transições:** `corte` (padrão) · `dissolve` · `fade_preto` (só entre blocos) · `transicao_kit` (a transição assinada do kit, uso raro).

Novos templates entram no catálogo **só** pelo kit (`03 §3`), com versão, nunca inventados pelo LLM.

## 4. Formato do plano (`plano.json`)

```json
{
  "versao": 3,
  "projeto": "vesuvio",
  "kit": "cinza-e-brasa@1.2",
  "preset": "padrao",
  "idiomas": {"principal": "pt-BR", "extras": ["en", "es"]},
  "orcamento_producao_min": 120,
  "estimativa_producao_min": 104,
  "blocos": [
    {
      "id": "B3",
      "titulo": "Dia 1 — A coluna",
      "modo_visual": "misto",
      "clima_musical": "construção épica controlada",
      "contexto": {"usar": true, "itens": [{"apos_segmento": "B3-S01", "texto": "DIA 1 · ≈ 13:00 · POMPEIA"}]},
      "shots": [
        {
          "id": "B3-05",
          "segmentos": ["B3-S04"],
          "ancora": {"entra_em": "Gás", "sai_em": "comercial"},
          "duracao_s": 6.1,
          "template": "T09",
          "params": {"tipo": "escala", "dados": [
            {"rotulo": "Everest", "valor": 8.8, "unidade": "km"},
            {"rotulo": "Avião comercial", "valor": 11, "unidade": "km", "prefixo": "≈"},
            {"rotulo": "Coluna eruptiva", "faixa": [26, 33], "unidade": "km"}]},
          "sobreposicoes": [],
          "ativos": [],
          "textos": ["Everest", "Avião comercial", "Coluna eruptiva"],
          "sfx": ["riser_curto", "tick_ui"],
          "transicao": "corte",
          "plano_b": {"template": "T08", "params": {"valor": 30, "prefixo": "até ≈", "unidade": "km"}},
          "motivo": "Dado de escala: gráfico deixa o número compreensível."
        },
        {
          "id": "B3-08",
          "segmentos": ["B3-S05"],
          "duracao_s": 3.6,
          "template": "T02",
          "params": {"movimento": "dolly", "intensidade": 0.4},
          "ativos": ["A-041"],
          "sobreposicoes": [{"tipo": "O1", "texto": "PLÍNIO, O JOVEM · 17 anos"}],
          "transicao": "corte",
          "plano_b": {"template": "T01", "params": {"movimento": "push_in"}}
        }
      ]
    }
  ],
  "ativos": {
    "A-041": {
      "descricao": "Plínio, o Jovem, 17 anos, num terraço em Miseno olhando a nuvem ao longe",
      "origem": "gerar",
      "personagem": "plinio_jovem",
      "prompt": "...",
      "usado_em": ["B3-08", "B3-09"],
      "proibicoes": []
    },
    "A-017": {
      "descricao": "Afresco 'Baco e o Vesúvio' (Casa do Centenário)",
      "origem": "pedir_ao_usuario",
      "motivo": "Fotos encontradas são de bem cultural italiano (exige autorização) ou de baixa resolução",
      "busca": {"termos": ["Bacco e Vesuvio affresco Casa del Centenario", "Bacchus Vesuvius fresco"], "sites": ["Wikimedia Commons", "site do MANN"]},
      "nome_arquivo": "A-017.jpg",
      "plano_b": "gerar"
    }
  },
  "musica": [{"bloco": "B3", "clima": "construção épica controlada", "faixa": null}],
  "verificacao": {"aprovado": true, "ajustes": 7}
}
```

**Regras do formato:**
- Textos na tela ficam em `textos[]`/`params` do plano no idioma principal e são traduzidos para `i18n/<idioma>.json` (`05 §3`) — os templates leem as strings dali.
- `duracao_s` é derivada da narração **do idioma principal**; cada idioma recalcula por proporção dentro do segmento (`05 §3`).
- Quando uma fala exige mais de um shot, os shots repetem o ID em `segmentos[]` e usam `inicio_segmento_s`/`fim_segmento_s` (segundos relativos ao começo da fala). As fatias devem ser contíguas, sem lacunas nem sobreposição, e somar a duração real do segmento. `inicio_s`/`fim_s` continuam sendo os tempos absolutos da prévia final.
- `ativos` é a lista consolidada: uma imagem, vários usos.

## 5. Verificador de dosagem (regras)

Valores do preset **Padrão** com densidade **média**. Densidade `baixa` multiplica os limites de texto/gráfico por 0,6; `alta`, por 1,4.

| # | Regra | Limite | Correção automática |
|---|---|---|---|
| D1 | Duração do shot por intensidade | 1–3: 4–8 s · 4–6: 3–6 s · 7–8: 2–4 s · 9–10: 1,5–3 s | dividir/fundir shots |
| D2 | Nenhum shot sem movimento por mais de | 4 s (exceto `T00`, `estático` marcado como intencional) | trocar para `push_in` 2% |
| D3 | Mesmo template em sequência | máx. 3 (T01 `Foto`: máx. 4) | trocar o do meio por T02/T03/T04 |
| D4 | Templates "de informação" (T06–T11) | intensidade ≤ 4: ≤ 1 a cada 25 s · 5–7: ≤ 1 a cada 15 s · ≥ 8: ≤ 1 a cada 12 s · nunca 2 seguidos | converter excedente em T01 com `O4` ou remover |
| D5 | Texto na tela | ≤ 7 palavras por item; duração ≥ 1 s + 0,3 s por palavra | encurtar (LLM) ou estender o shot |
| D6 | Sobreposições simultâneas | ≤ 2 (fora O2) | remover a de menor prioridade |
| D7 | Identificação (O1) | só na primeira aparição de cada pessoa/lugar; ≥ 2,5 s | remover repetidas |
| D8 | Depois de batida `revelação` | ≥ 1 s sem texto novo (respiro visual) | inserir T00 ou estender o shot |
| D9 | Proporção de imagens geradas | ≤ 30% dos shots; **proibido** para pessoas reais contemporâneas e para vítimas | trocar por arquivo/template/pedido |
| D10 | Âncora real por bloco (temas históricos) | ≥ 1 ativo real por bloco | marcar ativo para pesquisa/pedido |
| D11 | Reuso do mesmo ativo | ≤ 3 usos (callbacks marcados são exceção) | buscar ativo alternativo |
| D12 | Transições | `dissolve` ≤ 15% dos cortes; `fade_preto` só entre blocos | trocar por corte |
| D13 | Números/datas na tela | precisam existir no texto do roteiro (comparação normalizada) | marcar em `numeros_na_tela.md` |
| D14 | Cobertura | 100% da narração coberta, sem sobreposição de shots | recalcular tempos |
| D15 | Orçamento de tempo | estimativa ≤ orçamento do preset | reduzir variações, trocar `gerar` por `biblioteca/pesquisar`, trocar T02 por T01 |
| D16 | Capítulos | T12 no início de cada bloco (se ≥ 4 blocos) | inserir |
| D17 | Vítimas reais | só T01 (`estático`/`push_in` ≤ 2%) ou T02 com intensidade ≤ 0,15; sem SFX de impacto | ajustar |

O verificador grava em `verificacao.md` cada regra aplicada e o que mudou. As regras ficam em `config/dosagem.yaml` — você ajusta o "gosto" do canal sem mexer no código.

## 6. Prompt do planejador (resumo)

O planejador recebe, **por bloco**: segmentos com tempos e batidas, entidades, estratégia do bloco, catálogo de templates (IDs + quando usar), ativos já existentes na biblioteca do canal (descrições curtas) e as regras D1–D17 resumidas. Devolve JSON no formato de `blocos[].shots[]`. Princípios no prompt:
- **A imagem acrescenta, não repete:** se a frase já é visual, use contraponto ou detalhe.
- **Informação vira template de informação** (número, gráfico, mapa, linha do tempo), **emoção vira imagem** (foto, recorte, respiro).
- **Menos é mais:** na dúvida, `T01 Foto` bem escolhida.
- Reaproveite ativos da biblioteca quando servirem.
- Nunca invente fatos: textos na tela só com o que está no roteiro.

Modelo `structured` (9Router, fallback Ollama), temperatura 0,4, um bloco por chamada (~8–12 chamadas por vídeo).

## 7. Exemplo de `plano.md` (trecho)

```markdown
## B3 — Dia 1 · A coluna  (04:31–07:24 · intensidade 6→8 · clima: construção épica)
| Shot | Tempo | Narração | Template | Imagem | Texto na tela | Som |
|---|---|---|---|---|---|---|
| B3-01 | 04:31 · 2,0 s | "A montanha se abriu." | Foto (estático + tremor) | A-030 gerar: erupção vista de Pompeia | contexto "DIA 1 · ≈ 13:00" | boom grave |
| B3-03 | 04:36 · 4,0 s | "Não foi lava. Esse é o primeiro mito." | TextoImpacto (riscado) | — | ~~LAVA~~ · MITO | risco |
| B3-05 | 04:44 · 6,1 s | "…mais de vinte, trinta quilômetros…" | Gráfico (escala) | — | Everest · Avião · Coluna | riser |
| B3-08 | 05:02 · 3,6 s | "…um rapaz de dezessete anos…" | FotoProfundidade | A-041 gerar: Plínio, o Jovem | PLÍNIO, O JOVEM · 17 anos | porto |
| B3-12 | 05:20 · 3,0 s | "…erupção pliniana." | Foto (push-in) | A-052 pesquisada: Pinatubo 1991 (USGS, domínio público) nota 8 | ERUPÇÃO PLINIANA | — |
Ativos do bloco: 11 (6 gerar · 3 pesquisadas · 1 biblioteca · 1 **pedir a você**)
```
