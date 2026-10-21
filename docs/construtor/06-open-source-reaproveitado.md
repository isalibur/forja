# 06 — Open Source Reaproveitado

> Critérios: (1) gratuito, (2) licença que permita uso comercial **do vídeo gerado**, (3) roda na RTX 3060 12 GB / Windows, (4) maduro o bastante para não virar projeto paralelo. Licenças conferidas em páginas públicas em out/2026 — **o Marco M0 reconfere cada uma no arquivo LICENSE oficial** e registra a data.

---

## 1. Usar (caminho padrão)

| Projeto | Licença | Para quê no DocForja | Como integrar |
|---|---|---|---|
| **Remotion** + pacotes oficiais (`@remotion/transitions`, `captions`, `google-fonts`, `media-utils`, `shapes`, `paths`) | Licença Remotion: grátis para pessoa física e empresas de até 3 funcionários; empresas maiores pagam | Templates T00–T14, composição, render | Pacote Node dentro do kit; render por CLI |
| **Remotion Agent Skills** (`remotion-dev/skills`) | do repositório (conferir) | Ensinar o OpenCode/Antigravity a programar Remotion do jeito certo (boas práticas, render, captions, mapas) | `npx skills add remotion-dev/skills` na raiz do repo; o OpenCode lê `.agents/skills` e `.claude/skills` |
| **DepthFlow** (BrokenSource) | AGPL-3.0 ("commercial use is encouraged") | Parallax 2.5D (T02), exporta MP4 com NVENC | Processo separado (CLI/Python em ambiente próprio); usar Depth Anything V2 **Small** |
| **rembg** + **BiRefNet** | MIT / MIT | Recorte de sujeito (T03) | Biblioteca Python; modelo BiRefNet |
| **Real-ESRGAN** | BSD-3 | Upscale de imagens | Python |
| **WhisperX** / faster-whisper | BSD-2 / MIT | Alinhamento por palavra, WER, legendas | Python (ambiente próprio se o torch conflitar) |
| **Chatterbox Multilingual** (Resemble AI) | MIT | TTS principal (tem variante pt-BR; 20+ idiomas) | Adaptador `chatterbox` |
| **Kokoro-82M** | Apache-2.0 | TTS leve (pt-BR, inglês, espanhol, francês, italiano...) | Adaptador `kokoro` |
| **ComfyUI** + ComfyUI-Manager + nós GGUF | GPL-3.0 (processo separado) / conferir nós | Geração de imagens | API HTTP local |
| Modelos de imagem: **Chroma1-HD**, **Qwen-Image**, **FLUX.1 [schnell]**, **SDXL** | Apache-2.0 / Apache-2.0 / Apache-2.0 / OpenRAIL++ | Imagens geradas (escolha no benchmark) | Workflows do ComfyUI |
| **Ollama** + **Qwen3 8B** + **Qwen2.5-VL 7B** | MIT / Apache-2.0 / Apache-2.0 | LLM local e curadoria visual | HTTP local |
| **LiteLLM** | MIT | Uma interface para 9Router, Ollama (e OpenRouter, se usar), com fallback | Python |
| **9Router** (`decolua/9router`) | conferir no repositório | Seu roteador de LLM: combos de IAs gratuitas com rotação e fallback, endpoint único compatível com OpenAI | Serviço local (`http://localhost:20128/v1`); o DocForja o chama como provedor OpenAI-compatível |
| **OpenTimelineIO** | Apache-2.0 | Exportar a linha do tempo para o **DaVinci Resolve** (finalização manual opcional) | Python |
| **D3** (escalas, geo) + **Natural Earth** | ISC / domínio público | Gráficos (T09) e mapas vetoriais (T10) | Dentro dos templates |
| Ícones **Lucide** / **Phosphor** / **Tabler** | ISC / MIT / MIT | Ícones nos templates | SVG no kit |
| **Google Fonts** (Cinzel, Cormorant, Inter, IBM Plex) | OFL | Tipografia do kit | Arquivos no kit |
| **librosa**, **pyloudnorm**, **jiwer**, **colour-science**, **rasterio** | ISC / MIT / Apache-2.0 / BSD / BSD | Batidas, loudness, WER, LUTs, relevo dos mapas | Python |
| **FFmpeg** | LGPL/GPL | Encode NVENC, mix, LUT, QA | CLI |
| **Hermes Agent** (Nous Research) | MIT | Operador pelo chat (opcional) | Skill + CLI/API local |

## 2. VoiceStudio (`debpalash/VoiceStudio`) — análise

**O que é:** app desktop (Electron — a versão 0.5.3 foi o último Tauri; também há Docker) para clonagem e design de voz, dublagem, ditado, transcrição e audiolivros, com dezenas de engines de TTS (OmniVoice/k2-fsa por padrão; também VoxCPM2, CosyVoice 3, IndexTTS 2.5, Sherpa-ONNX, MOSS-TTS, entre outras), aceleração CUDA (roda na RTX 3060), API local em `127.0.0.1:3900`, servidor MCP para agentes, "receitas" e pastas vigiadas. Instalação: instalador oficial (`irm https://voicestudio.sh/install | iex` no Windows), executável da página de releases, código-fonte (`git clone` + `bun install` + `bun run setup:api` + `bun run dev`) e skill de agente (`npx skills add debpalash/VoiceStudio`) — ver `09 §7.1`.

**Licença:** o **app** é AGPL-3.0. O próprio projeto avisa que **pesos de modelos, vozes e as condições de uso do áudio gerado são separados** do app, e o inventário de licenças dele informa que **nenhum modelo está liberado para uso comercial das saídas** até o momento; o OmniVoice (motor padrão) e o NLLB (tradução) aparecem com termos não comerciais.

**API:** a superfície pública documentada é de **transcrição e ditado** — `GET /.well-known/voicestudio-speech` (descoberta de capacidades), `POST /v1/audio/transcriptions` (compatível com OpenAI), WebSocket de transcrição em streaming e MCP (`POST /mcp` ou `python -m backend.mcp_shim`). A **síntese de voz não tem contrato documentado**; por isso o adaptador de TTS do DocForja, que espera `POST /v1/synthesize` em outra porta, ainda não conecta ao app.

**Decisão:**
| Uso | Status |
|---|---|
| Ferramenta à parte para você **testar vozes, desenhar uma voz, gravar/editar narração** e exportar WAV → entra no DocForja como **narração pronta** | ✔ Recomendado, desde que a engine usada tenha licença comercial conferida por você (receita em `09 §7.1`) |
| **Adaptador `voicestudio`** (o DocForja chama a API local para sintetizar) | ◐ Implementado no M7 com trava de licença comercial, mas **ainda não utilizável**: a URL e o endpoint precisam casar com a API real do app |
| Motor padrão de TTS do DocForja | ✘ Não (licenças das saídas não liberadas; mais uma aplicação grande para manter) |
| Tradução/dublagem pelo VoiceStudio | ✘ Não (NLLB não comercial) |
| Transcrição pelo VoiceStudio | ✘ Desnecessário (WhisperX já cobre) |

## 3. Alternativas mantidas em reserva

| Projeto | Licença | Quando considerar |
|---|---|---|
| **Revideo** (fork do Motion Canvas para render programático) | MIT | Se a licença do Remotion virar problema (empresa com 4+ pessoas e sem querer pagar) — exige reescrever os templates |
| **Motion Canvas** | MIT | Idem; mais voltado a editor visual |
| **Piper** | MIT (vozes variam) | TTS em CPU, se a GPU estiver ocupada |
| **ACE-Step** | Apache-2.0 | Gerar trilhas quando a biblioteca não tiver o clima certo |
| **MoneyPrinterTurbo** e similares (roteiro → vídeo com stock) | conferir | Só como referência de ideias (busca de stock, legendas); qualidade e arquitetura abaixo do que buscamos |

## 4. Excluídos (licença não comercial ou incompatível)

XTTS-v2 · pesos oficiais do F5-TTS · MusicGen · NLLB · Depth Anything V2 Base/Large · BRIA RMBG · FLUX.1 [dev]/Krea (pesos não comerciais) · OmniVoice (segundo o inventário do VoiceStudio) · qualquer banco de imagens com licença NC/ND.
