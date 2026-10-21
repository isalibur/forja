# 08 — Marcos de Construção (OpenCode + Antigravity)

> **10 marcos (M0–M9).** O **planejamento completo** fica pronto no M5 (já útil sozinho: você recebe o plano, a prévia e a lista de busca). O vídeo completo, com saída organizada e metadados estratégicos, sai no M6; multi-idioma e integrações no M7; shorts no M8; canal de música no M9 (M9 pode ser feito logo depois do M6, se for prioridade).

## Preparação

1. A estrutura já vem montada: `AGENTS.md` na raiz, `docs/construtor/` (esta pasta) e `docs/pipeline/` (linguagem visual, som, ética e o roteiro do Vesúvio). Faça `git init` e o primeiro commit antes do M0.
2. Skills do Remotion para os agentes de programação: `npx skills add remotion-dev/skills` (instala em `.agents/skills`, que o OpenCode lê).
3. Regras de trabalho: "planeje antes, depois implemente"; testes a partir da especificação; um branch por marco; só faz merge com testes verdes.

| Ferramenta | Usar em |
|---|---|
| **OpenCode** (modelos `:free`; problema difícil → leve ao chat do Gemini) | núcleo, planejamento, áudio, mídia, produção |
| **Antigravity** (navegador embutido para conferir visualmente) | templates Remotion (M2), telas da interface (M1, M5, M6) |

```
M0 ─► M1 ─► M3 ─► M4 ─► M5 [planejamento completo] ─► M6 [vídeo completo] ─► M7 [idiomas + integrações] ─► M8 [shorts]
       └─► M2 templates (Antigravity, em paralelo) ─────────┘                    └─► M9 [canal de música] (independente do M7/M8)
```

---

### M0 — Ambiente e benchmark
```
Leia AGENTS.md e docs/construtor/01, 06 e 09. Crie o pacote `docforja` (uv, Python 3.11) com:
- `docforja doctor`: verifica GPU/VRAM, CUDA, FFmpeg com NVENC, ComfyUI (8188), Ollama (11434) e modelos,
  Node 20 + Remotion, DepthFlow, rembg/BiRefNet, WhisperX, espaço em disco, chaves do .env (sem mostrar valores).
- `docforja benchmark`: mede tempo e VRAM de: 3 imagens por candidato de modelo, 20 s de TTS por motor/voz em
  pt-BR (e en/es), 60 s de alinhamento, 1 parallax DepthFlow de 5 s, 1 recorte, 1 upscale, e 10 s de render Remotion
  em 1080p/1440p. Grava config/benchmark.json e arquivos em benchmark_out/ para eu ouvir e ver.
Planeje antes: liste os arquivos.
```
**Pronto:** doctor ✓; você escolheu o modelo de imagem e as vozes ouvindo `benchmark_out/`; licenças reconferidas e datadas em `docs/construtor/licencas-conferidas.md`.

### M1 — Núcleo e interface base
```
Implemente (docs/construtor/07 §1, §3, §4): esquemas Pydantic (Plano, Bloco, Shot, Ativo, Segmento, Candidato,
Credito, Timeline), criação da pasta do projeto (07 §4), banco SQLite, executor de etapas lendo config/pipeline.yaml
(dependências, por-bloco/por-ativo/por-idioma, retomada, hash de entrada, invalidação seletiva), semáforo de GPU
com agrupamento por modelo e descarregamento, cotas por provedor com fallback para Ollama, roteador LLM (LiteLLM) usando o 9Router como provedor
principal (endpoint OpenAI-compatível definido em config/adaptadores.yaml), com validação e reparo de JSON, eventos, CLI `novo/status`.
Testes com etapas falsas: paralelismo, exclusividade de GPU, retomada após kill, invalidação seletiva, gate REVISAO.
```
Antigravity:
```
Leia docs/construtor/14-interface-ui.md e abra docs/construtor/mockups/docforja-ui.html no navegador embutido.
Crie web/ (React 18 + TypeScript + Vite + Tailwind + shadcn/ui + lucide-react + TanStack Query + Sonner + cmdk)
com os tokens de 14 §3 (tema escuro padrão e claro), a navegação de 14 §4 (barra lateral, barra superior com
pílulas de GPU e cota, Ctrl+K), as telas Início (14 §5.1) e Criar (14 §5.2), e o fluxo de eventos em tempo real
por SSE. Tipos gerados do OpenAPI do FastAPI (openapi-typescript). Build servido pelo FastAPI em 127.0.0.1:7860.
Fique fiel ao protótipo; onde ele for omisso, siga os princípios de 14 §1 e §6.
```
**Pronto:** criar o projeto Vesúvio pela interface colando `docs/pipeline/04-roteiro.md`; testes de concorrência verdes 20× seguidas.

### M2 — Kit e templates (Antigravity, em paralelo)
```
Usando as Remotion Agent Skills (.agents/skills), crie kits/cinza-e-brasa/ conforme docs/construtor/03:
tokens.json a partir de docs/pipeline/06 §2, fontes OFL, texturas, e o pacote Remotion de templates T00–T14 e
sobreposições O1–O4 com as props de docs/construtor/02 §3 (schemas Zod). Use @remotion/transitions, captions,
google-fonts, shapes/paths; D3 para T09/T10 com Natural Earth. Todo texto com auto-ajuste (encolhe até 70%/quebra).
Cada template com composição de teste, snapshot e som padrão do kit. Composição "Bloco" que recebe uma fatia da
timeline. Inclua a "marca do projeto" (03 §3.1): espaço para logo e cartão final lidos de marca.yaml.
Confira no Remotion Studio em 1080p e em 360p.
```
**Pronto:** todos os templates renderizam isolados; snapshots aprovados por você; uma fatia de teste (Foto + Número + Mapa + TextoImpacto) renderiza no `Bloco`.

### M3 — Leitura do roteiro, narração e alinhamento
```
Implemente planejamento/leitura (formato de docs/construtor/10 por regex; texto livre por LLM, com verificação de que
nenhuma palavra mudou; batidas e entidades de docs/construtor/02 §2 P1), audio/narracao com adaptadores chatterbox e
kokoro (1 take + WER + refazer reprovados; cadeia FFmpeg; room tone), narração pronta por idioma, e audio/alinhamento
(WhisperX contra o texto). Teste: docs/pipeline/04-roteiro.md → 116 segmentos; texto livre → 100% preservado.
```
**Pronto:** narração completa do Vesúvio com WER < 2% e `palavras.json`; narração pronta de teste alinhada.

### M4 — Planejador e verificador de dosagem (o coração)
```
Implemente planejamento/estrategia, shots (por bloco, catálogo fechado de docs/construtor/02 §3, prompt de §6),
ativos (consolidação), verificador (regras D1–D17 de §5 lidas de config/dosagem.yaml, correções por código e
reenvio ao LLM só dos blocos com violações, máx. 3 voltas), estimativa (com config/benchmark.json e presets de 01 §4)
e relatórios plano.md, verificacao.md e estimativa.md no formato de §7.
Testes do verificador com planos sintéticos violando cada regra.
```
**Pronto:** `plano.json` do Vesúvio cobre 100% da narração, passa no verificador e a estimativa respeita o orçamento do preset Padrão.

### M5 — Ativos, pesquisa, lista de busca, pasta manual e prévia → **planejamento completo**
```
Implemente midia/biblioteca (busca por texto + similaridade CLIP), adaptadores de acervo (Wikimedia, AIC, Met,
Openverse, LoC, Europeana, NASA, Pexels, Pixabay), classificação de licença por código com marcação de patrimônio
restrito, curadoria com Ollama visão, rascunhos via ComfyUI, lista_de_busca.md e numeros_na_tela.md (docs/construtor/04),
pasta manual com watchdog (atribuição por ID, nao_atribuidas com sugestão, ficha de crédito) e a prévia 540p.
```
Antigravity: telas "Plano" (14 §5.3 — prévia ao vivo com @remotion/player, curva de intensidade, linha do tempo de shots, painel do shot), "Ativos" (§5.4) e "Lista de busca" (§5.5, com soltar arquivos), fiéis ao protótipo.
**Pronto:** roteiro colado → em ~45–75 min, plano + prévia + lista de busca; soltar arquivos na pasta manual atualiza o plano na tela.

### M6 — Produção → **vídeo completo (1 idioma)**
```
Implemente: imagens finais (ComfyUI, variações por preset, curadoria, personagens com referência), tratamento
(rembg+BiRefNet, DepthFlow como processo separado, Real-ESRGAN), fundos de mapa (rasterio hillshade + Sentinel-2),
trilha (biblioteca CLAP, cortes em compasso), SFX (sons do kit + específicos), mix (sidechain + loudnorm -14 LUFS),
montagem plano→timeline por bloco, render Remotion por bloco + concat + mux, QA (blackdetect, freezedetect, ebur128,
WER, safe area, números) com autocorreção (2 voltas, depois plano B), export OTIO para DaVinci Resolve, e a saída
completa de docs/construtor/13 §2 (pastas por idioma, elementos/, créditos, relatório, promover_para_global.md).
Implemente estrategia/ (13 §4–5): titulos.md com 10 ideias por ângulo, nota por critério e top 3 para A/B;
descricao.md; tags/hashtags/palavras-chave; capitulos.txt; thumbs_briefing.md com 3 conceitos + rascunho renderizado
de cada um e teste de legibilidade a 120 px; comentario_fixado.md; post_comunidade.md; checklist_publicacao.md;
metadados.json; verificação M1–M6. Implemente global/ (13 §3): promoção em lote e referência por ID.
Extras leves de docs/construtor/15 §2: planilha de publicação (agenda.csv), pacote opcional para bancos de
imagens (só ativos elegíveis + metadados_stock.csv em inglês) e pasta de licenciamento (trilha M&E, master sem
legendas, ficha técnica).
```
Antigravity: telas "Produção" (14 §5.6), "Resultado" (§5.7, com títulos, descrição, thumbs, shorts e promoção para a pasta global), "Pasta global" (§5.10), "Kits" (§5.11) e "Sistema" (§5.12).
**Pronto:** "Produzir" → `05_saida/` completa no formato de `13 §2`, com metadados estratégicos e thumbs, sem intervenção, dentro da estimativa (±25%); itens confirmados aparecem na pasta global.

### M7 — Multi-idioma, integrações e reaproveitamento
```
Implemente idiomas/ (tradução nos modos automatico, gemini_manual e arquivo; glossário; validação de IDs),
narração por idioma, retime proporcional, i18n dos templates, render/mix/pacote por idioma e o modo "só legendas".
Adaptadores extras: openai_compat (TTS por HTTP), voicestudio (atrás da checagem de licença comercial), arquivo_pronto.
Promoção de ativos para a biblioteca ao final do projeto. Hermes opcional (skill + notificador).
```
**Pronto:** Vesúvio em pt-BR + en + es; trocar uma imagem refaz só o necessário nos três idiomas; um segundo vídeo reaproveita mapas e trilhas da pasta global.

### M8 — Shorts (derivado e avulso)
**Docs:** `11`, `13 §4`
```
No kit (Antigravity + Remotion Agent Skills): layouts 9:16 de todos os templates e os templates V01–V10 de
docs/construtor/11 §2, legendas palavra a palavra com @remotion/captions, guias das zonas seguras.
No núcleo (OpenCode): shorts/candidatos (pontuação de 11 §3.1 sobre o plano longo), shorts/ponte (3 frases-ponte
para aprovação, sem reescrever o roteiro), shorts/verticalizar (reenquadramento por ponto de foco ou fundo desfocado),
verificador DS1–DS9, fórmulas de 11 §4.2 como arquivos editáveis em global/formulas_shorts/, criação de short avulso
(roteiro seu / gerado pela fórmula / pedido exportado para o Gemini), lote por CSV, regras de honestidade de 11 §4.3,
e metadados por plataforma (YouTube Shorts e Instagram Reels) conforme 11 §6.
Inclua a fórmula produto_afiliado e o template V11 CartaoProduto (15 §2.1), com entrada por planilha de produtos,
link só nos metadados e na agenda.csv, e as regras de honestidade de afiliado.
```
Antigravity: tela "Shorts" (14 §5.8, com prévias em moldura de celular e diagrama da fórmula).
**Pronto:** do Vesúvio saem 3 shorts derivados que apontam para o longo; um CSV com 5 temas gera 5 shorts avulsos (objetivos diferentes), cada um com `capa.jpg` e metadados por plataforma; uma planilha com 10 produtos gera 10 shorts de afiliado e a `agenda.csv` correspondente.

### M9 — Canal de música
**Docs:** `12`
```
Implemente musica/: declaração geral do usuário para as faixas que ele inserir (sem ficha ou bloqueio por faixa), ordem e normalização, crossfades,
ambiente opcional; cena com 1–2 imagens, máscaras sugeridas pela visão local e editáveis, animações L01–L06
(DepthFlow em ciclo e componentes Remotion com semente e ciclo exato); render do clipe em loop uma vez + checagem
da emenda; montagem longa com FFmpeg -stream_loop e sobreposições com transparência (nome da faixa, troca de imagem,
visualizador) em NVENC; tracklist; metadados e thumbs (13); shorts opcionais; promoção da cena para global/loops/.
```
Antigravity: tela "Música" (14 §5.9) com faixas arrastáveis, prévia do loop ao vivo e pincel de máscara.
**Pronto:** 20 faixas + 2 imagens → vídeo de ~1 h com tracklist e metadados em < 40 min de processamento; emenda do loop imperceptível.

---

## Depois do M9 — roadmap

As fases A–D de `15-roadmap-negocios.md` (livros/audiolivros e kits educativos; publicação automática; loja de autoatendimento; painel de receitas) **não fazem parte da v1**. Só comece qualquer uma delas com um pedido explícito, cada uma como um marco novo (M10, M11…), seguindo o mesmo ritual.

---

## Aceitação final

1. Roteiro novo de 5 min → plano em < 30 min → vídeo em < 1 h depois do "Produzir" (preset Padrão, 1080p).
2. Vesúvio (16 min) em 3 idiomas.
3. Queda de energia no meio → retoma sem refazer nada.
4. 9Router fora do ar ou combo esgotado → tarefas simples vão para o Ollama; o resto espera e retoma.
5. Novo kit (outra paleta/fontes) → mesmo plano renderiza com a nova identidade sem mudar código.
6. Todo projeto (longo, short, música) termina com a estrutura de `13 §2`, metadados estratégicos e sugestões para a pasta global.
7. Interface aprovada nos critérios de `14 §7` (≤ 6 cliques para iniciar um vídeo, acessibilidade ≥ 90, prévia em < 2 s).
