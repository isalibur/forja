# 13 — Saídas, Pasta Global e Metadados Estratégicos

> Vale para **todos** os tipos de produção: vídeo longo, short derivado, short avulso e canal de música.

---

## 1. Duas pastas: projeto e global

```
D:\DocForja\
├── projetos\<tipo>-<slug>\      # um por vídeo/short/campanha: tudo daquele trabalho
└── global\                      # tudo que pode ser reaproveitado em qualquer projeto
```

**Regra:** o que é específico do vídeo fica no projeto; o que serve para outros vídeos é **promovido** para `global\` (com ficha de origem e licença) e, a partir daí, os projetos passam a **referenciar** o item global pelo ID em vez de duplicá-lo.

## 2. Estrutura da saída de um projeto

```
projetos\longo-vesuvio\05_saida\
├── pt-BR\
│   ├── video\video.mp4
│   ├── legendas\legendas.srt
│   ├── thumbnails\thumb_A.jpg · thumb_B.jpg · thumb_C.jpg
│   ├── metadados\
│   │   ├── metadados.json            # tudo em formato de máquina (para uma ferramenta de upload, se você usar)
│   │   ├── titulos.md                # ideias de títulos para CTR (§4.1)
│   │   ├── descricao.md              # descrição pronta (§4.2)
│   │   ├── tags.txt · hashtags.txt · palavras_chave.md
│   │   ├── capitulos.txt
│   │   ├── thumbs_briefing.md        # descrição das thumbs possíveis (§4.3)
│   │   ├── comentario_fixado.md
│   │   ├── post_comunidade.md        # texto de divulgação
│   │   └── checklist_publicacao.md   # tela final, cards, vídeo relacionado, playlist, divulgação de IA
│   ├── publicacao\agenda.csv         # planilha de publicação para ferramentas de agendamento (15 §2.3)
│   └── shorts\S01-..\ S02-..\ (cada um com video.mp4, capa.jpg, legendas.srt, metadados\ — ver `11 §6`)
├── en\ …  es\ …                     # mesma estrutura por idioma
├── elementos\                        # os "ingredientes" do vídeo, organizados
│   ├── imagens\                      # imagem final de cada ativo (A-017.jpg …) + ficha .json
│   ├── animacoes\                    # clipes de parallax, recortes (PNG com alfa)
│   ├── mapas\
│   ├── narracao\<idioma>.wav
│   ├── trilha\ · sfx\                # versões editadas usadas no vídeo
│   ├── plano\plano.json · plano.md
│   └── projeto.otio                  # linha do tempo para abrir no DaVinci Resolve
├── stock\                           # opcional: clipes e quadros elegíveis + metadados_stock.csv (15 §2.2)
├── licenciamento\                   # trilha M&E, master sem legendas, legendas separadas, ficha técnica (15 §2.5)
├── creditos.txt
├── relatorio.md                      # o que foi feito, fallbacks, avisos, licenças a revisar
└── promover_para_global.md           # o que o sistema sugere guardar na pasta global (você confirma)
```

Para shorts avulsos e campanhas: `projetos\short-<slug>\05_saida\<idioma>\` com `video.mp4`, `capa.jpg`, `legendas.srt` e `metadados\` por plataforma. Para música: estrutura de `12 §5`.

## 3. Pasta global

```
D:\DocForja\global\
├── kits\                 # identidades visuais versionadas (cores, fontes, templates 16:9 e 9:16, sons, LUTs)
├── imagens\              # imagens aprovadas (pesquisadas, geradas, suas) + ficha (descrição, tags, licença, crédito)
├── personagens\          # referências e variações para consistência
├── mapas\                # fundos de relevo/satélite por região + GeoJSON
├── loops\                # cenas em loop do canal de música + máscaras
├── musica\ · sfx\        # bibliotecas indexadas, cada arquivo com license.json
├── vozes\                # configuração da voz do canal por idioma (+ consentimento, se for clonada)
├── ctas\                 # cartões de CTA, logo, assinatura, tela final
├── formulas_shorts\      # fórmulas de short (11 §4.2), editáveis
├── metadados\            # blocos fixos da descrição (links, redes, aviso de IA), hashtags por nicho, modelos de comentário fixado
├── glossarios\           # glossários por tema/série e idioma
├── series\               # agrupamento de projetos que compartilham kit, personagens e mapas
└── indice.sqlite         # busca por texto + similaridade de imagem (CLIP)
```

**Promoção automática sugerida** ao final de cada projeto (você confirma em lote na tela "Resultado"):
| Item | Sugerido quando |
|---|---|
| Imagens finais | nota da curadoria ≥ 7 e licença comercial |
| Personagens | usados em ≥ 2 shots |
| Mapas | sempre (regiões tendem a se repetir) |
| Cenas em loop | sempre (canal de música) |
| Trilhas e SFX novos | usados no vídeo e com licença registrada |
| Glossário | sempre |

## 4. Metadados estratégicos (agente Estrategista)

Gerados pelo tier `structured` (9Router, fallback Ollama) a partir do plano (gancho, entidades, blocos, revelações), do objetivo e do tipo de vídeo. Opcional: `docforja exportar-metadados` gera um pedido pronto para você refinar no chat do Gemini.

### 4.1 `titulos.md` — ideias para CTR

- **10 títulos** para o longo (≤ 60 caracteres), **6–8** para cada short (≤ 40), em ângulos diferentes:

| Ângulo | Exemplo (Vesúvio) |
|---|---|
| Quebra de crença | Pompeia não morreu em agosto (e não foi a lava) |
| Curiosidade específica | O cérebro que virou vidro em Herculano |
| Número | As últimas 19 horas de Pompeia, hora por hora |
| Contraste passado × presente | 700 mil pessoas vivem onde Pompeia morreu |
| Pergunta | O que realmente matou Pompeia? |
| Descoberta recente | O que a ciência descobriu sobre Pompeia (2018–2025) |

- Cada título com: ângulo, gatilho (curiosidade, surpresa, urgência, identificação), palavra-chave principal, e uma **nota** (0–10) por critérios explícitos: clareza, curiosidade, especificidade, tamanho, palavra-chave nas primeiras palavras, **coerência com a thumbnail e com o gancho do vídeo**.
- **Top 3 recomendados para teste A/B** (recurso de teste de títulos/thumbnails da plataforma, quando disponível).
- **Regra:** nenhum título promete o que o vídeo não entrega nos primeiros 60 s (o sistema confere contra o gancho do plano).

### 4.2 `descricao.md`

1. Duas primeiras linhas com o gancho e a palavra-chave (o que aparece antes do "mais").
2. Resumo em 3–4 frases.
3. Capítulos com os tempos reais (`00:00` obrigatório no primeiro).
4. Fontes (as do roteiro e dos documentos que você anexou) e créditos de imagens/música (de `creditos.txt`).
5. Blocos fixos do canal (`global/metadados/`): links, redes, aviso de reconstituições por IA.
6. 3 hashtags.
Shorts: versão curta + link/título do vídeo longo (derivado) ou do CTA (avulso). Instagram: legenda com gancho na primeira linha, CTA, 5–10 hashtags, texto alternativo.

### 4.3 `thumbs_briefing.md` — descrição das thumbnails possíveis

Para cada um de **3 conceitos**:
```markdown
## Conceito A — "A cidade e o relógio"
- Ideia em uma frase: a mesma rua viva e soterrada, com um relógio marcando o fim
- Elemento principal: rua de Pompeia (ativo A-011), dividida na diagonal (metade dourada, metade cinza)
- Texto (≤ 3 palavras): "19 HORAS"
- Cores do kit: dourado × cinza + laranja-brasa no texto
- Emoção/gatilho: urgência, contraste
- Combina com os títulos: #3, #7
- Por que funciona em miniatura: um contraste forte, uma palavra, sem detalhes pequenos
- Arquivo de rascunho: thumbnails/thumb_A.jpg
```
O sistema **renderiza um rascunho de cada conceito** com os ativos do projeto e o texto nas fontes do kit, e testa a legibilidade reduzindo para 120 px (visão local lê o texto).

### 4.4 Outros

- `tags.txt` e `palavras_chave.md`: principal, secundárias e de cauda longa (das entidades do roteiro + LLM), por idioma.
- `comentario_fixado.md`: pergunta que gera conversa, coerente com o vídeo.
- `post_comunidade.md`: texto curto de divulgação + sugestão de imagem.
- `checklist_publicacao.md`: tela final e card sugeridos (nunca no meio do clímax), playlist, vídeo relacionado dos shorts, divulgação de conteúdo sintético quando houver reconstituições realistas, legendas enviadas.
- `metadados.json`: tudo acima em formato de máquina.

## 5. Verificação dos metadados (regras M1–M6)

| # | Regra |
|---|---|
| M1 | Títulos dentro do limite de caracteres por formato |
| M2 | Nenhum título/thumbnail promete algo ausente do vídeo (comparação com o plano) |
| M3 | Capítulos batem com os tempos reais |
| M4 | Todo crédito de `creditos.txt` aparece na descrição |
| M5 | Shorts derivados apontam para o vídeo longo |
| M6 | Conteúdo pago/parceria: marcação incluída |
