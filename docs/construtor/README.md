# DocForja v2 — Construtor de Documentários "planejamento primeiro"

**Ideia central:** o sistema transforma o roteiro num **Plano de Vídeo completo** (cada segundo decidido: imagem, movimento, texto na tela, gráfico, mapa, som) **antes** de produzir qualquer coisa. Você revisa o plano, completa as imagens que faltam, e a produção vira apenas a **execução do plano**: automática, previsível, em 1–2 horas.

> **Para a IA que vai programar (OpenCode / Antigravity):** siga `AGENTS.md` e consulte a seção do marco atual em `08-marcos-de-construcao.md`. Leia em `docs/pipeline` apenas os temas necessários à tarefa.

---

## Tipos de produção

| Tipo | Entrada | Saída | Doc |
|---|---|---|---|
| **Vídeo longo** (documentário) | tema + roteiro (+ idiomas, narração pronta opcional) | vídeo 16:9 por idioma + pacote | `02`–`05` |
| **Short derivado** ("âncora" do canal) | um vídeo longo | 3–5 shorts 9:16 que levam ao vídeo longo | `11 §3` |
| **Short avulso** | tema + objetivo (vendas, promoção, engajamento…) + fórmula; ou uma campanha em lote | shorts 9:16 para YouTube Shorts e Instagram Reels | `11 §4` |
| **Canal de música** | lista de músicas + 1–2 imagens | vídeo longo com cena viva em loop + tracklist | `12` |

Toda saída vem numa **estrutura de pastas com os elementos**, com **metadados estratégicos prontos** (títulos para CTR, descrição, tags, capítulos, descrição das thumbs possíveis + rascunhos) — e o que for reaproveitável vai para a **pasta global** (`13`).

## Decisões da v2

| Tema | Decisão |
|---|---|
| Prioridade | **Planejar bem** > produzir muito. O plano é o produto principal; a produção é determinística |
| Dosagem | O planejador escolhe de um **catálogo fechado de templates** e passa por um **verificador de plano** com regras de dosagem (ritmo, densidade de texto e gráficos, respiros). Nada de motion "livre" |
| Nível visual | Limpo e profissional: fotos animadas (Ken Burns, parallax, recortes), textos na tela, gráficos, mapas, linhas do tempo, citações. Sem vídeo gerado por IA, sem exageros |
| Tempo de produção | Meta de **1–2 h** depois do "Produzir" para vídeos de 8–12 min em 1080p (16 min: ~2–3 h); shorts em minutos; 1 h de música em ~15–35 min |
| Identidade visual | **Kit do canal** reutilizável (16:9 e 9:16) + **pasta global** de ativos que cresce a cada vídeo |
| Idiomas | **Multi-idioma**: um plano, várias saídas |
| Narração | TTS local **ou narração pronta** (por idioma) |
| Integrações | Tudo plugável por **adaptadores**; exporta também OpenTimelineIO (DaVinci Resolve) |
| Reaproveitamento | Remotion + Agent Skills, DepthFlow, BiRefNet/rembg, Real-ESRGAN, WhisperX, Kokoro/Chatterbox, ComfyUI, OpenTimelineIO, D3 + Natural Earth (ver `06`) |
| Roteiro e LLM | Roteiro feito por você no chat do Gemini 4 Argon; dentro do sistema, o seu **9Router** (combo de IAs gratuitas, compatível com OpenAI) + Ollama local |
| Ponto humano | **Um** por projeto: revisar o plano e entregar as imagens pedidas |
| Interface | Plataforma web local moderna (React + shadcn/ui), tema escuro, prévia ao vivo do plano, tudo em tempo real — ver `14` e o protótipo `mockups/docforja-ui.html` |

## Fluxo do vídeo longo

```
ENTRADA          PLANEJAMENTO (automático, ~45–75 min)                 REVISÃO (você)            PRODUÇÃO (automática, 1–2 h)
tema             1. entende o roteiro (blocos, emoção, nomes, números)  plano.md + prévia         executa o plano:
roteiro    ──►   2. narra no idioma principal e mede os tempos     ──►  lista de busca     ──►   imagens IA · animação de fotos ·
idiomas          3. monta o Plano de Vídeo com templates do kit         pasta manual              templates · trilha · SFX · mix ·
narração pronta  4. verificador de dosagem ajusta o plano               (troca o que quiser)      render por idioma · legendas ·
(opcional)       5. pesquisa fotos reais + decide o que gerar           "Produzir"                metadados · shorts · OTIO
                 6. prévia rápida (animatic de baixa resolução)
```

## Índice

| # | Documento | Conteúdo |
|---|---|---|
| — | [AGENTS.md](../../AGENTS.md) | Regras para OpenCode/Antigravity |
| 01 | [Decisões, escopo e orçamento](01-decisoes-escopo-e-orcamento.md) | Hardware, presets de qualidade, orçamento de tempo, licenças |
| 02 | [O Plano de Vídeo](02-plano-de-video.md) | **O coração**: tipos de plano, etapas, formato, catálogo de templates, verificador de dosagem |
| 03 | [Kit visual e reaproveitamento](03-kit-visual-e-reaproveitamento.md) | Kit do canal, templates Remotion, biblioteca, séries |
| 04 | [Imagens e animação de imagens](04-imagens-e-animacao.md) | Origens das imagens, curadoria, pasta manual, Ken Burns, parallax, recortes |
| 05 | [Áudio, narração e idiomas](05-audio-narracao-e-idiomas.md) | TTS, narração pronta, tradução, multi-idioma, trilha, SFX, mix |
| 06 | [Open source reaproveitado](06-open-source-reaproveitado.md) | Repositórios analisados (incluindo o VoiceStudio) |
| 07 | [Arquitetura e integrações](07-arquitetura-e-integracoes.md) | Etapas por tipo, adaptadores, pastas, interface, CLI/API, Hermes |
| 08 | [Marcos de construção](08-marcos-de-construcao.md) | 10 marcos com prompts prontos |
| 09 | [Instalação](09-instalacao.md) | Windows + RTX 3060 |
| 10 | [Roteiro e prompt para o Gemini](10-roteiro-e-prompt-gemini.md) | Formato do roteiro, tradução manual |
| 11 | [Shorts](11-shorts.md) | Short derivado (âncora) e short avulso (objetivos, fórmulas, lote) |
| 12 | [Canal de música](12-canal-de-musica.md) | Playlist + cena viva em loop, render eficiente |
| 13 | [Saídas, pasta global e metadados](13-saidas-pasta-global-e-metadados.md) | Estrutura de saída, o que vai para a pasta global, títulos para CTR, descrição, thumbs |
| 14 | [Interface (UI)](14-interface-ui.md) | Princípios, tecnologia, identidade visual, telas, interação, critérios de aceite · [protótipo](mockups/docforja-ui.html) |
| 15 | [Roadmap de negócios](15-roadmap-negocios.md) | O que entra já na v1 (afiliado, stock, agenda, marca, M&E) e as fases futuras (livros, publicação automática, loja, painel) |
