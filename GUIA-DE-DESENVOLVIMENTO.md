# Guia de Desenvolvimento do DocForja (para você)

Este guia é **para você**, não para a IA. Ele diz o que fazer em cada etapa, o que pedir para a IA, o que conferir antes de seguir e o que fazer quando algo der errado.

**A divisão de papéis:**
- **A IA de programação** (OpenCode ou Antigravity) escreve o código, os testes e corrige os erros.
- **Você** prepara o computador, cola os pedidos certos, confere os resultados com os próprios olhos e ouvidos, e decide quando um marco está pronto.

**Duração estimada:** 3 a 6 semanas trabalhando algumas horas por dia, em 10 marcos (M0 a M9). A primeira coisa útil (colar um roteiro e receber o plano completo do vídeo) aparece no M5, mais ou menos na metade.

---

## Parte 1 — Preparar o computador (uma vez)

### 1.1 Conferências rápidas
- [ ] Windows 11 atualizado e driver da NVIDIA recente. Abra o PowerShell e rode `nvidia-smi`: deve aparecer a RTX 3060.
- [ ] Arquivo de paginação fixo de **32 GB**. Caminho: Configurações → Sistema → Sobre → Configurações avançadas do sistema → Desempenho → Avançado → Memória virtual.
- [ ] Disco com **≥ 200 GB livres**. Crie `D:\DocForja\projetos\` e `D:\DocForja\global\` (pode ser outro disco; anote qual).

### 1.2 Programas
Rode no PowerShell, um por vez:
```powershell
winget install --id Git.Git
winget install --id astral-sh.uv
winget install --id OpenJS.NodeJS.LTS
winget install --id Gyan.FFmpeg
winget install --id Ollama.Ollama
```
Depois feche e abra o PowerShell de novo e confira: `git --version`, `uv --version`, `node -v` (precisa ser 20 ou mais), `ffmpeg -version`, `ollama --version`.

Modelos do Ollama:
```powershell
ollama pull qwen3:8b
ollama pull qwen2.5vl:7b
```

### 1.3 ComfyUI (gera as imagens)
1. Baixe o **ComfyUI portable para Windows/NVIDIA** na página oficial de releases e extraia em `D:\DocForja\ComfyUI\`.
2. Abra-o (`run_nvidia_gpu.bat`) e instale o **ComfyUI-Manager**. Pelo Manager, instale o suporte a modelos **GGUF**.
3. Ainda não baixe modelos grandes: no M0 a IA vai dizer exatamente quais arquivos testar (`docs/construtor/09-instalacao.md §3`).

### 1.4 O seu 9Router
- Deixe o 9Router rodando nesse computador, com um **combo** de IAs gratuitas configurado. Anote o nome do combo e confirme que o endereço é `http://localhost:20128/v1`.
- Teste rápido no PowerShell (troque `SEU_COMBO`):
  ```powershell
  curl.exe http://localhost:20128/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"SEU_COMBO\",\"messages\":[{\"role\":\"user\",\"content\":\"responda só OK\"}]}"
  ```
  Se voltar um texto com "OK", está pronto.

### 1.5 Chaves gratuitas (crie as contas e guarde as chaves)
| Serviço | Para quê | Obrigatória no início? |
|---|---|---|
| Pexels | fotos contemporâneas | não (M5) |
| Pixabay | fotos contemporâneas | não (M5) |
| Europeana | gravuras e fotos históricas | não (M5) |
| Smithsonian (api.data.gov) | acervo de museu | não (M5) |
| Freesound | efeitos sonoros CC0 | não (M6) |
| OpenTopography | relevo dos mapas | não (M6) |
| Copernicus Data Space | imagens de satélite | não (M6) |

Wikimedia, Art Institute of Chicago, Met, Library of Congress e NASA não pedem chave.

### 1.6 Ferramentas de programação
- **OpenCode:** configure-o para usar o seu 9Router como provedor. O OpenCode aceita provedores compatíveis com OpenAI no arquivo `opencode.json`; confira o formato exato na documentação do OpenCode. A ideia é esta:
  ```json
  {
    "$schema": "https://opencode.ai/config.json",
    "provider": {
      "9router": {
        "npm": "@ai-sdk/openai-compatible",
        "name": "9Router",
        "options": { "baseURL": "http://localhost:20128/v1" },
        "models": { "SEU_COMBO": { "name": "Combo gratuito" } }
      }
    }
  }
  ```
- **Antigravity:** usa o Gemini embutido. Ao abrir o projeto, cadastre o `AGENTS.md` como regra do workspace ou peça no início de cada conversa: *"Leia o AGENTS.md antes de qualquer coisa."*

### 1.7 Licenças que já estão resolvidas
- **Remotion:** você trabalha sozinho, então é gratuito.
- **9Router:** é o seu provedor principal; a recarga do OpenRouter **não é necessária**. O OpenRouter fica só como reserva, se você quiser.

---

## Parte 2 — Preparar o projeto (uma vez)

1. Descompacte o zip em `D:\DocForja\docforja\` (o código fica separado dos vídeos: `projetos\` e `global\` ficam fora dele).
2. No PowerShell, dentro de `D:\DocForja\docforja\`:
   ```powershell
   git init
   git add .
   git commit -m "Documentação inicial do DocForja"
   copy .env.example .env
   npx skills add remotion-dev/skills
   git add .
   git commit -m "Skills do Remotion"
   ```
3. Abra `.env` num editor e preencha `NINEROUTER_COMBO` (e `NINEROUTER_API_KEY`, se o seu 9Router pedir). As outras chaves você preenche quando o marco precisar.
4. Abra a pasta no OpenCode e no Antigravity. Abra também `docs/construtor/mockups/docforja-ui.html` no navegador, para ter a interface na cabeça.

---

## Parte 3 — O ritual de cada marco

Repita isto em **todos** os marcos:

| Passo | O que você faz |
|---|---|
| 1. Branch novo | `git checkout -b m0-ambiente` (troque o nome a cada marco) |
| 2. Conversa nova | Abra uma conversa nova na ferramenta indicada. Cole a **mensagem de abertura** (abaixo) |
| 3. Pedido do marco | Cole o prompt do marco que está em `docs/construtor/08-marcos-de-construcao.md` |
| 4. Conferir o plano | A IA responde com um plano (arquivos, funções, testes). Compare com o que o marco pede. Se ela inventar coisa fora do marco, diga: *"Fora do escopo deste marco. Remova."* |
| 5. Liberar | *"Plano aprovado. Implemente, escreva os testes e rode até ficarem verdes."* |
| 6. Conferir o resultado | Rode você mesmo os comandos de teste (abaixo) e faça as conferências do marco (Parte 4) |
| 7. Fechar | `git add .` · `git commit -m "M0 concluído"` · `git checkout main` · `git merge m0-ambiente` |

**Mensagem de abertura (cole no início de toda conversa):**
```
Leia AGENTS.md e docs/construtor/README.md. Vamos trabalhar só no marco <Mx> de
docs/construtor/08-marcos-de-construcao.md. Sempre planeje antes e espere minha aprovação.
Não mude nada fora do escopo deste marco. Se a especificação estiver ambígua, pergunte.
```

**Comandos para conferir (você roda):**
```powershell
uv run pytest tests/unit
uv run ruff check src tests
uv run docforja doctor
```

**Mensagens úteis durante o trabalho:**
| Situação | O que dizer |
|---|---|
| Deu erro | *"Rodei `<comando>` e deu este erro: <cole o erro>. Descubra a causa antes de mudar código."* |
| A IA quer "simplificar" tirando uma regra (licença, rótulo, revisão, GPU) | *"Isso está proibido no AGENTS.md (seção 'Você NÃO pode'). Mantenha e resolva de outro jeito."* |
| A conversa ficou longa e a IA começou a se perder | Feche a conversa, abra outra, cole a mensagem de abertura e: *"Continuamos o Mx. Já está pronto: <resumo>. Falta: <resumo>."* |
| Problema difícil que a IA não resolve | Cole o erro e os arquivos principais no chat do **Gemini 4 Argon**, peça a solução e traga a resposta: *"Uma revisão externa sugeriu isto: <cole>. Avalie e aplique se fizer sentido."* |
| Fim do marco | *"Revise o código deste marco procurando erros de concorrência, de retomada e de tratamento de erro. Liste antes de corrigir."* |

---

## Parte 4 — Marco a marco

> Tempos de dedicação são estimativas.

### M0 — Ambiente e testes de desempenho · OpenCode · ~1 dia
**Objetivo:** o sistema confere se tudo está instalado e mede o que sua máquina aguenta.
**Você confere:**
- [ ] `uv run docforja doctor` mostra tudo ✓ (o que estiver ✗ você instala e roda de novo).
- [ ] Na pasta `benchmark_out\`: **ouça** as vozes em pt-BR e escolha a melhor; **veja** as imagens de teste de cada modelo e escolha o melhor.
- [ ] Diga à IA as suas escolhas para ela gravar em `config/`.
- [ ] Existe `docs/construtor/licencas-conferidas.md` com a data da conferência das licenças.

### M1 — Núcleo e interface base · OpenCode + Antigravity · ~2–3 dias
**Objetivo:** a "espinha" do sistema e as primeiras telas.
**Ordem:** primeiro o núcleo no OpenCode; depois as telas no Antigravity (prompt do M1 marcado "Antigravity").
**Você confere:**
- [ ] Abre `http://127.0.0.1:7860` e aparece a tela Início parecida com o protótipo.
- [ ] Na tela Criar, você cola o roteiro de `docs/pipeline/04-roteiro.md` e o projeto aparece em `D:\DocForja\projetos\`.
- [ ] Teste de retomada: peça à IA para rodar o teste em que o processo é derrubado e retomado. Precisa passar várias vezes seguidas.

### M2 — Kit visual e templates · Antigravity · ~2–4 dias (pode correr junto com M1–M4)
**Objetivo:** os 14 "modelos de cena" (foto com movimento, número, mapa, citação…) com a identidade "Cinza e Brasa".
**Você confere:**
- [ ] No Remotion Studio (`npx remotion studio` dentro da pasta do kit), cada template toca bonito.
- [ ] Reduza a janela para tamanho de celular: os textos continuam legíveis.
- [ ] Você aprovou o visual de cada um (diga quais ajustar antes de fechar).

### M3 — Roteiro, narração e tempos · OpenCode · ~2 dias
**Objetivo:** o sistema lê o roteiro sem mudar nenhuma palavra, narra e mede o tempo de cada frase.
**Você confere:**
- [ ] O roteiro do Vesúvio virou 116 segmentos.
- [ ] Ouça trechos da narração: pronúncia de Vesúvio, Herculano, Plínio, Miseno. Se algo estiver errado, peça para corrigir no dicionário de pronúncia.
- [ ] Teste com uma narração sua (um áudio curto gravado no celular, com o texto correspondente): ela é aceita e alinhada.

### M4 — O planejador (o coração) · OpenCode · ~3 dias
**Objetivo:** do roteiro sai o Plano de Vídeo, com as regras de dosagem aplicadas.
**Você confere:**
- [ ] Abra `01_plano\plano.md` do Vesúvio e **leia um bloco inteiro**: as escolhas fazem sentido? Tem respiro depois das revelações? Não há texto demais?
- [ ] `verificacao.md` mostra as regras aplicadas e o que foi ajustado.
- [ ] `estimativa.md` mostra um tempo de produção dentro do preset escolhido.
- [ ] Se o "gosto" não estiver bom (muito gráfico, pouco gráfico), ajuste os números em `config/dosagem.yaml`, não no código.

### M5 — Imagens, lista de busca e prévia · OpenCode + Antigravity · ~3 dias → **primeiro resultado útil**
**Objetivo:** o planejamento completo: pesquisa de fotos reais, lista do que você precisa trazer, prévia do vídeo.
**Você confere:**
- [ ] Cole um roteiro novo e, em cerca de 1 hora, recebe plano, prévia e lista de busca.
- [ ] Abra a aba de pesquisa: as fotos escolhidas fazem sentido e todas têm licença.
- [ ] Solte uma imagem chamada `A-017.jpg` em `02_midias\manual\`: o item da lista vira "recebido" sozinho.
- [ ] Solte uma imagem com nome qualquer: o sistema sugere onde ela entra.
- [ ] A prévia toca na tela Plano em poucos segundos.

### M6 — Produção completa · OpenCode + Antigravity · ~4–6 dias → **vídeo completo**
**Objetivo:** clicar em "Produzir" e receber o vídeo final com tudo pronto.
**Antes de começar:** baixe 30–60 músicas com licença para vídeos monetizados (YouTube Audio Library, Pixabay Music) em `D:\DocForja\global\musica\`, e alguns pacotes gratuitos de efeitos sonoros. Preencha as chaves de Freesound, OpenTopography e Copernicus no `.env`.
**Você confere:**
- [ ] Clique em Produzir e não faça mais nada: em até cerca de 2 h aparece `05_saida\pt-BR\` com vídeo, legendas, thumbnails e metadados.
- [ ] **Assista ao vídeo inteiro.** Anote os minutos em que algo incomoda e peça as correções (ou ajustes nas regras).
- [ ] Leia `titulos.md` e `thumbs_briefing.md`: as ideias têm a ver com o vídeo?
- [ ] O relatório lista os planos B usados.
- [ ] O arquivo `projeto.otio` abre no DaVinci Resolve (gratuito), se você quiser finalizar à mão.
- [ ] Existem `publicacao\agenda.csv`, a pasta `licenciamento\` e, se você ligou a opção, a pasta `stock\` só com material seu (nenhuma foto de acervo de terceiros).
- [ ] Um projeto com `marca.yaml` (logo e contato fictícios) mostra a marca no cartão final.

### M7 — Idiomas e integrações · OpenCode · ~2–3 dias
**Você confere:**
- [ ] O Vesúvio sai em pt-BR, en e es; os nomes próprios seguem o glossário.
- [ ] Troque uma imagem e reproduza: só aquele trecho é refeito nos três idiomas.
- [ ] Teste o modo de tradução manual: exportar → colar no Gemini → importar.

### M8 — Shorts · Antigravity + OpenCode · ~2–3 dias
**Você confere:**
- [ ] Do Vesúvio saem 3 shorts que levam ao vídeo longo, com frase-ponte que você aprovou.
- [ ] Uma planilha com 5 temas e objetivos diferentes gera 5 shorts avulsos.
- [ ] Assista no **celular**: o texto não fica embaixo dos botões do app, as legendas acompanham a fala.
- [ ] Uma planilha com 10 produtos de afiliado gera 10 shorts; o link aparece só na legenda/agenda, nunca no vídeo, e a legenda avisa que é link de afiliado.

### M9 — Canal de música · OpenCode + Antigravity · ~2 dias (pode vir logo depois do M6)
**Você confere:**
- [ ] 20 faixas + 2 imagens viram um vídeo de cerca de 1 h em menos de 40 min de processamento.
- [ ] A emenda do loop é imperceptível (assista à virada várias vezes).
- [ ] A tracklist na descrição bate com os tempos reais.

---

### Depois do M9 — expansões para os negócios
As fases A a D de `docs/construtor/15-roadmap-negocios.md` (livros e audiolivros, kits educativos, publicação automática, loja de autoatendimento, painel de receitas) ficam para depois da v1 funcionando. Quando decidir começar uma, abra uma conversa nova e peça: *"Vamos criar o marco M10 a partir da Fase X de docs/construtor/15. Monte primeiro o plano do marco no mesmo formato de 08."* A estratégia de cada negócio está em `docs/negocios/carteira-de-negocios.md`.

---

## Parte 5 — Primeiro vídeo de verdade

1. Escreva o roteiro no Gemini usando o prompt de `docs/construtor/10-roteiro-e-prompt-gemini.md`.
2. Crie o projeto na interface, escolha o preset **Padrão**.
3. Revise o plano, traga as imagens da lista de busca, confira "Números na tela".
4. Clique em **Produzir** (de preferência à noite).
5. Assista, leia o relatório, escolha título e thumbnail e publique você mesmo.
6. Na tela Resultado, guarde na pasta global o que o sistema sugerir. O próximo vídeo fica mais rápido.

## Parte 6 — Problemas comuns

| Sintoma | O que fazer |
|---|---|
| "CUDA out of memory" | Feche navegador e programas pesados; confira o arquivo de paginação; peça à IA para usar o motor de reserva daquela etapa |
| O 9Router não responde | Confira se está aberto e se o combo tem cota; enquanto isso, o sistema usa o Ollama nas tarefas simples |
| ComfyUI ou Ollama "offline" no `doctor` | Abra o programa; o ComfyUI precisa estar com `--listen 127.0.0.1 --port 8188` |
| Erros de versão do `torch` | Peça à IA para isolar a ferramenta num ambiente separado (`envs/`), como prevê a documentação |
| Render muito lento | Use 1080p e o preset Padrão; confira no Gerenciador de Tarefas se a CPU está livre |
| A IA mudou algo que não devia | `git diff` para ver; `git checkout -- <arquivo>` para desfazer; repita o pedido citando o AGENTS.md |
| Você mudou de ideia sobre uma regra ou tela | **Atualize primeiro o documento** em `docs/construtor/` e depois peça à IA: *"Atualizei a seção X; ajuste o código para ficar igual."* |

## Parte 7 — Checklist final

- [ ] `doctor` todo verde
- [ ] Roteiro → plano + lista de busca sem intervenção
- [ ] "Produzir" → vídeo + metadados + thumbnails sem intervenção
- [ ] Shorts derivados e avulsos funcionando
- [ ] Canal de música funcionando
- [ ] Pasta global crescendo e sendo reaproveitada
- [ ] Desligar o PC no meio e religar retoma sem refazer nada
