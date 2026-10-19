# 14 — Interface (UI): intuitiva, moderna e agradável

> **Para a IA que vai programar (Antigravity):** esta é a especificação da plataforma. O protótipo visual de referência está em [`mockups/docforja-ui.html`](mockups/docforja-ui.html) (abra no navegador). A interface substitui a versão simples (HTMX) citada em versões anteriores: agora é uma aplicação web moderna servida localmente pelo próprio DocForja.

---

## 1. Princípios de experiência

1. **Sempre um próximo passo claro.** Toda tela de projeto mostra, no topo, a etapa atual e **um** botão principal ("Revisar plano", "Enviar 5 imagens", "Produzir", "Ver resultado").
2. **Visual primeiro.** Miniaturas, prévias que tocam e linha do tempo em vez de tabelas cruas. Tabela existe como visão alternativa.
3. **Simples por padrão, avançado sob demanda.** Campos raros ficam em "Avançado" recolhido. O usuário iniciante cria um vídeo só com tema, roteiro e um clique.
4. **Tempo real.** Progresso, filas e miniaturas aparecem enquanto o sistema trabalha (sem recarregar a página), com tempo restante estimado.
5. **Nada se perde.** Toda edição do plano gera uma versão; "desfazer" e "voltar para a versão X" sempre disponíveis.
6. **Status com cores fixas** em todo o produto:

| Status | Cor | Uso |
|---|---|---|
| Pronto | verde | etapa/shot/ativo concluído |
| Precisa de você | âmbar | lista de busca, aprovações, números a conferir |
| Processando | azul (animado) | etapa rodando |
| Erro / bloqueado | vermelho | falhou, sem cota, sem licença |
| Aguardando | cinza | ainda não começou |

7. **Acessível e confortável:** contraste AA, foco visível, textos ≥ 14 px, navegação por teclado, tema escuro (padrão) e claro.

## 2. Tecnologia (toda gratuita e com licença livre)

| Camada | Escolha | Licença | Por quê |
|---|---|---|---|
| Base | **React 18 + TypeScript + Vite** | MIT | Padrão de mercado; ótimo para vibe coding |
| Estilo | **Tailwind CSS** | MIT | Consistência rápida |
| Componentes | **shadcn/ui** (sobre Radix UI) | MIT | Visual moderno, acessível, código dentro do projeto (personalizável) |
| Ícones | **lucide-react** | ISC | Mesmo estilo em todo o produto |
| Dados do servidor | **TanStack Query** | MIT | Cache, atualização e estados de carregamento |
| Tabelas | **TanStack Table** | MIT | Visão tabela do plano, ativos, faixas |
| Arrastar e soltar | **dnd-kit** + **react-dropzone** | MIT | Reordenar faixas/shots; soltar imagens |
| Prévia de vídeo ao vivo | **@remotion/player** | Licença Remotion (`01 §5`) | Toca o plano como vídeo **sem renderizar**, com os mesmos templates do kit; edições aparecem na hora |
| Notificações | **Sonner** | MIT | Avisos discretos |
| Paleta de comandos | **cmdk** | MIT | `Ctrl+K` para buscar projetos, ativos, ações |
| Gráficos pequenos | **Recharts** | MIT | Curva de intensidade, uso de cota, tempos |
| Tempo real | **SSE** (Server-Sent Events) do FastAPI a partir de `events.jsonl` | — | Progresso e miniaturas ao vivo |
| Servidor | FastAPI serve a API e o build estático em `127.0.0.1:7860` | — | Abre no navegador; pode ser "instalada" como app (PWA) |

Estrutura: `web/` (projeto Vite) → `npm run build` → `src/docforja/web_dist/` servido pelo FastAPI. Tipos TypeScript gerados a partir dos esquemas Pydantic (OpenAPI → `openapi-typescript`), para a interface nunca divergir da API.

## 3. Identidade visual da plataforma

| Token | Escuro (padrão) | Claro |
|---|---|---|
| Fundo | `#0B0B0E` | `#F7F7F8` |
| Superfície | `#141418` | `#FFFFFF` |
| Superfície elevada | `#1C1C22` | `#FFFFFF` + sombra |
| Borda | `#2A2A33` | `#E4E4E7` |
| Texto | `#EDEDEF` / secundário `#A1A1AA` | `#18181B` / `#52525B` |
| **Destaque (marca "forja")** | `#FF6A2B` (brasa) | `#E8551A` |
| Informação | `#38BDF8` | `#0284C7` |
| Sucesso / Atenção / Erro | `#22C55E` / `#F59E0B` / `#EF4444` | iguais, 10% mais escuros |

- Tipografia: **Inter** (interface) e **JetBrains Mono** ou IBM Plex Mono (tempos, IDs, números técnicos). Ambas OFL.
- Cantos 12 px (cartões), 8 px (botões/campos); sombras suaves; cabeçalho com leve desfoque de fundo.
- Animações de 150–200 ms; *skeletons* no carregamento; nada pisca.
- A identidade da **plataforma** é independente dos **kits** dos vídeos (o kit aparece só nas prévias).

## 4. Estrutura de navegação

```
┌──────────────┬──────────────────────────────────────────────────────────────────────┐
│  DocForja    │  🔍 Buscar (Ctrl+K)        [GPU: gerando imagens 12/48] [Cota 23/50] 🔔 👤 │
│              ├──────────────────────────────────────────────────────────────────────┤
│  Início      │                                                                      │
│  Projetos    │                         conteúdo da tela                             │
│  ＋ Criar     │                                                                      │
│  Shorts      │                                                                      │
│  Música      │                                                                      │
│  Pasta global│                                                                      │
│  Kits        │                                                                      │
│  ──────────  │                                                                      │
│  Sistema     │                                                                      │
└──────────────┴──────────────────────────────────────────────────────────────────────┘
```

- **Barra superior:** busca global, **pílula de GPU** (o que está rodando agora e quantos itens faltam; clique abre a fila), **pílula de LLM** (estado do 9Router e uso do dia), notificações.
- **Barra lateral** recolhível; no projeto, aparece também a navegação interna (Plano · Ativos · Lista de busca · Shorts · Saída).

## 5. Telas

### 5.1 Início
- **"Continuar de onde parou":** cartões grandes dos projetos ativos com capa, tipo (Longo/Short/Música), barra de etapas e o botão do próximo passo ("5 imagens esperam você").
- **Criar rápido:** três cartões — Vídeo longo · Short · Canal de música.
- **Saúde do sistema:** GPU, ComfyUI, Ollama, espaço em disco, cota do dia (verde/âmbar/vermelho).
- **Fila agora:** o que está processando e o que vem a seguir.
- Primeira execução: tour de 4 passos e projeto de exemplo (Vesúvio) já carregado.

### 5.2 Criar (assistente em 4 passos)
1. **Tipo:** cartões ilustrados (Vídeo longo · Short derivado · Short avulso/campanha · Canal de música).
2. **Conteúdo:** tema; roteiro (colar ou arrastar arquivo) com contador de palavras e **duração estimada ao vivo**; idiomas (chips com bandeira); narração (TTS ou "vou enviar minha narração", com área de envio por idioma); documentos de apoio.
3. **Estilo e voz:** kit (cartões com prévia animada), voz (botão ▶ para ouvir cada voz com uma frase do seu roteiro), **preset** (Rápido / Padrão / Caprichado com o tempo estimado em cada cartão), densidade de motion (controle deslizante com exemplo visual), orçamento de tempo.
4. **Revisar:** resumo + estimativa de planejamento e produção + "Começar planejamento". Avançado recolhido: pré-gerar imagens, monetizado, adaptadores específicos.

### 5.3 Projeto · Plano (a tela principal)

```
┌ Vesúvio · Vídeo longo ─────────────── Entrada ✓ ─ Planejamento ✓ ─ [Revisão] ─ Produção ─ Pronto ──┐
│                                                   ⚠ 5 imagens esperam você     [ Produzir ▸ ]      │
├────────────────────────────────────────────┬───────────────────────────────────────────────────────┤
│                                            │ Saúde do plano  ●●●●○  92/100                         │
│      PRÉVIA AO VIVO (Remotion Player)      │ ✓ Ritmo ok  ✓ Respiros ok  ⚠ 2 textos longos          │
│      ▶ 04:44 / 16:08     pt-BR ▾  16:9 ▾   │ Estimativa  ████████░░ 1h44 de 2h00                   │
│                                            │ Ativos  62 pesquisadas · 48 IA · 5 suas · 9 global    │
├────────────────────────────────────────────┴───────────────────────────────────────────────────────┤
│ intensidade  ╱╲__╱‾‾╲╱‾‾‾‾╲__╱‾╲___   (curva sobre a linha do tempo)                                 │
│ B0 │ B1        │ B2   │ B3              │ B4         │ B5        │ B6    │ B7          │ B8        │
│ [▢][▢][▢]...   miniaturas dos shots, cor da borda = status, ícone = template                       │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                           ↳ clicar num shot abre o PAINEL DO SHOT à direita
```

**Painel do shot** (gaveta lateral):
- Trecho narrado (com ▶ para ouvir) e tempo.
- **Template:** galeria visual com mini-prévias (só os do catálogo).
- **Imagem:** atual + alternativas (candidatas da pesquisa com licença e nota · gerar outra · escolher da pasta global · enviar a sua).
- Movimento (botões visuais: push-in, pull-out, pan, parallax), texto na tela (com contador e alerta de leitura), sobreposições, SFX, transição, plano B.
- Cada mudança atualiza a prévia na hora e roda o verificador; avisos aparecem inline ("texto longo para 2,1 s").

Outros recursos: alternar **Storyboard / Tabela**; filtros ("só o que precisa de mim", "só IA", "bloco B3"); comparar versões do plano; botão "Exportar texto do plano para o Gemini".

### 5.4 Projeto · Ativos
Grade de cartões com miniatura, **selo de origem** (Pesquisada · Gerada · Sua · Global · Precisa de você), selo de licença, nota da curadoria e em quais shots é usado. Filtros por origem/status; seleção múltipla ("gerar de novo", "trocar por candidata").

### 5.5 Projeto · Lista de busca
- Barra de progresso: "9 de 14 entregues".
- Um cartão por item: o que procurar, por que, **termos com botão copiar**, **links para os sites sugeridos**, tamanho mínimo, nome do arquivo e o plano B.
- **Área de soltar em cada cartão** e uma área geral: soltou em qualquer lugar → o sistema reconhece pelo nome ou sugere o item (animação confirmando a atribuição).
- Ficha de crédito rápida (fonte, autor, licença) logo após soltar.
- Atalho "abrir a pasta `manual` no Explorer".

### 5.6 Produção
- Anel/barra de progresso grande com **tempo restante**, etapa atual e "pode fechar esta janela; avisamos quando terminar".
- Linha das etapas com status ao vivo; galeria que vai se preenchendo com as imagens prontas.
- Detalhes técnicos recolhidos (log, fila de GPU).

### 5.7 Resultado
- Player do vídeo final com abas de idioma; botões "Abrir pasta", "Baixar pacote".
- **Painel de publicação:**
  - **Títulos:** lista com nota, ângulo e botão copiar; os 3 recomendados para A/B em destaque.
  - **Descrição:** pronta, com botão copiar; capítulos clicáveis (pulam o player para o tempo).
  - **Thumbnails:** 3 cartões com o rascunho e o briefing; prévia "em miniatura" (como aparece no celular, 120 px).
  - Tags, hashtags, comentário fixado, checklist de publicação (marcável).
- **Shorts gerados** num carrossel vertical (moldura de celular).
- **Promover para a pasta global:** grade com tudo que o sistema sugere, já selecionado; você desmarca o que não quiser.
- Relatório (fallbacks usados, avisos) e "refazer shot".

### 5.8 Shorts
- **Do vídeo longo:** candidatos em molduras de celular tocando a prévia, com nota e motivo; escolher frase-ponte (3 opções + editar).
- **Avulso:** cartões de objetivo com ícone (Vendas, Promoção, Engajamento, Educativo, Anúncio, Bastidores, Autoridade) → fórmula mostrada como **diagrama da estrutura** (gancho → … → CTA, com segundos) → conteúdo → prévia vertical.
- **Campanha:** importar planilha, ver os shorts em grade, aprovar em lote.

### 5.9 Música
- Lista de faixas arrastável: título, artista, duração, **selo de direito** (sem ficha = vermelho e bloqueia), duração total e "repetir até X h".
- Duas vagas de imagem; chips das animações L01–L06 com **prévia em loop ao vivo**; pincel de máscara sobre a imagem.
- Tracklist gerada ao lado, atualizando conforme você reordena.

### 5.10 Pasta global
- Abas: Imagens · Personagens · Mapas · Loops · Trilhas · SFX · Vozes · CTAs · Fórmulas · Metadados · Kits.
- Busca por texto e **"encontrar parecidas"** (similaridade de imagem).
- Detalhe do item: licença, crédito, origem, projetos que usaram.

### 5.11 Kits
- Galeria dos templates tocando ao vivo (16:9 e 9:16), com o kit aplicado.
- Editor de tokens (cores, fontes) com prévia instantânea; "salvar como nova versão do kit".

### 5.12 Sistema
- Saúde (resultado do `doctor`), benchmark (tempos medidos), adaptadores ativos, cotas, fila completa, configurações (pastas, presets, regras de dosagem com explicação de cada regra).

## 6. Padrões de interação

| Situação | Padrão |
|---|---|
| Ação demorada | Botão vira progresso; o resultado chega por notificação; nunca bloquear a tela |
| Ação destrutiva/irreversível | Diálogo de confirmação com o que vai acontecer |
| Edição no plano | Salva sozinho (versão nova), "desfazer" por 10 s na notificação |
| Erro | Mensagem em português simples + o que fazer ("Cota do dia acabou. Retomamos às 21:00, ou mova a tarefa para o modelo local") |
| Vazio | Ilustração + uma frase + o botão da primeira ação |
| Atalhos | `Ctrl+K` busca · `Espaço` toca/pausa a prévia · `←/→` shot anterior/próximo · `Ctrl+Z` desfazer · `?` lista de atalhos |
| Telas | Otimizada para 1440–1920 px de largura; funcional a partir de 1280 px; consultas rápidas (status, aprovações) também no celular |

## 7. Critérios de aceite da interface

- Criar um vídeo longo do zero até "planejamento iniciado" em **≤ 6 cliques** com os padrões.
- Encontrar "o que precisa de mim" em **1 clique** a partir de qualquer tela.
- Prévia do plano começa a tocar em **< 2 s** após abrir a tela.
- Toda lista longa com carregamento progressivo; nenhuma tela trava com 300 shots.
- Acessibilidade (auditoria automática) ≥ 90; contraste AA nos dois temas.
- Teste com o projeto Vesúvio: um usuário novo entende a lista de busca e entrega uma imagem sem instruções.
