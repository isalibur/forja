# 01 — Decisões, Escopo e Orçamento

## 1. Princípios (valem para todo o código)

1. **Planejar antes de produzir.** Nenhum pixel final é gerado antes de existir um Plano de Vídeo validado. O plano é revisável, versionado e suficiente para reproduzir o vídeo.
2. **Escolhas fechadas, não livres.** O planejador escolhe templates de um catálogo e preenche parâmetros validados. Isso dá consistência, funciona com LLMs gratuitos e mantém a operação simples.
3. **Dosagem por regras explícitas.** "Quanto motion", "quanto texto", "quando respirar" são regras numéricas no verificador de plano (`02 §5`), ajustáveis por preset. O LLM propõe; as regras decidem.
4. **Reaproveitar antes de criar.** Ferramentas open source maduras (`06`) e ativos da biblioteca do canal (`03`) vêm antes de código novo e de imagens novas.
5. **Um ponto humano.** Depois de "Produzir", nada pede intervenção; o que falhar usa o plano B do shot e vai para o relatório.
6. **Idioma é variante, não projeto novo.** Um plano gera N idiomas; imagens não carregam texto embutido.
7. **Respeito às vítimas e honestidade visual** (regras da pasta `docs/pipeline`, `../pipeline/07-assets-e-direitos.md §6`): reconstituições rotuladas, nada de gore, vítimas reais só com movimento mínimo.

## 2. Escopo

| Dentro da v2 | Fora da v2 |
|---|---|
| Roteiro colado (formato de `10` ou texto livre) | Escrever o roteiro (é você, no Gemini) |
| Plano de Vídeo completo + prévia | Vídeo gerado por IA (i2v) |
| Fotos reais pesquisadas, imagens geradas, imagens suas | Mapas 3D (Blender) |
| Ken Burns, parallax 2.5D, recorte de sujeito, textos, gráficos, mapas 2D/2,5D, linhas do tempo, citações | Motion "livre" fora do catálogo de templates |
| TTS local ou narração pronta, multi-idioma | Upload automático no YouTube |
| Trilha da biblioteca, SFX, mix | Geração de música por IA (opcional futuro) |
| Exportação MP4 + SRT + metadados + OTIO (DaVinci Resolve) | — |

## 3. Máquina e orçamento de VRAM

Ryzen 5 5500 · RTX 3060 12 GB · 24 GB de RAM · Windows 11 (interpretação: "24 GB" = RAM do sistema).

| Carga | Ferramenta | VRAM aprox. | Quando |
|---|---|---|---|
| Imagem gerada | ComfyUI + modelo escolhido no benchmark (Chroma1-HD / Qwen-Image GGUF / FLUX.1 schnell) | 9–11 GB | Planejamento (rascunho) e produção |
| Rascunho rápido | SDXL (ou o mesmo modelo com poucos passos) | 6–8 GB | Prévia do plano |
| TTS | Chatterbox Multilingual (inclui variante pt-BR) / Kokoro | 3–5 GB / ~1 GB | Planejamento |
| Alinhamento | WhisperX large-v3 | 5–6 GB | Planejamento |
| LLM e visão locais | Ollama: Qwen3 8B / Qwen2.5-VL 7B | 6–8 GB | Planejamento |
| Profundidade + parallax | DepthFlow (Depth Anything V2 Small) | 1–3 GB | Produção |
| Recorte | BiRefNet (via rembg) | 1–2 GB | Produção |
| Upscale | Real-ESRGAN | 2–4 GB | Produção |

Regra: **uma carga pesada por vez** (semáforo de GPU, agrupamento por modelo, descarregar antes de trocar).

## 4. Presets de qualidade e orçamento de tempo

Você escolhe na entrada. O planejador estima o tempo de produção com os números do `docforja benchmark` e ajusta o plano ao orçamento (ex.: troca imagens geradas por fotos de arquivo ou templates quando o tempo estoura).

| Preset | Resolução | Narração | Imagens geradas | Parallax | Meta (vídeo de 10 min) |
|---|---|---|---|---|---|
| **Rápido** | 1080p | 1 take | 1 variação; ≤ 15% dos shots | ≤ 15% dos shots | ~45–75 min |
| **Padrão** (recomendado) | 1080p | 1 take + refazer só os reprovados | 2 variações; ≤ 30% dos shots | ≤ 30% | **~1–2 h** |
| **Caprichado** | 1440p | 2–3 takes | 3 variações; ≤ 40% | ≤ 40% | ~2,5–4 h |

As imagens geradas podem ser feitas **durante sua revisão do plano** (opção ligada por padrão), o que tira ~30–60 min da produção.

**Estimativa do Padrão, vídeo de 10 min (~100 shots), a confirmar no benchmark:**

| Etapa | Tempo |
|---|---|
| Planejamento: narração + alinhamento | 20–30 min |
| Planejamento: plano + verificador + pesquisa de fotos + curadoria + rascunhos + prévia | 25–45 min |
| Produção: ~25 imagens geradas × 2 variações (se não pré-geradas) | 40–60 min |
| Produção: recortes, parallax, upscale | 15–25 min |
| Produção: trilha, SFX, mix | 5–10 min |
| Produção: render 1080p + QA + legendas + pacote | 45–75 min |
| **Produção total** | **~1–2 h** (≈ 1 h com imagens pré-geradas) |
| Cada idioma extra | +narração (10–15 min) + render (40–60 min) |

## 5. Custos

| Item | Custo |
|---|---|
| Ferramentas e modelos locais | R$ 0 (licenças em `06`) |
| **9Router** (seu roteador, combo de IAs gratuitas em rotação) | R$ 0. É o provedor principal de LLM do sistema: ~40–80 pedidos por vídeo + ~15 por idioma extra. Endpoint compatível com OpenAI (`http://localhost:20128/v1`). OpenRouter `:free` fica só como reserva opcional — **não é preciso recarga** |
| APIs de acervo | R$ 0 (chaves gratuitas) |
| **Remotion** | **No seu caso (você trabalha sozinho): gratuito.** A regra geral: gratuito para pessoa física e empresas de até 3 funcionários. Se os vídeos forem produzidos por uma empresa maior, é preciso a licença paga ("Creators", ~US$ 25/mês por pessoa, segundo a página de preços). Alternativa 100% MIT: Revideo (ver `06`) |

## 6. Licenças: regra do produto

- Projeto marcado `monetizado: true` só usa modelos, assets e trilhas com uso comercial permitido.
- Cada adaptador declara a licença do motor; o sistema recusa motores `non_commercial` em projetos monetizados.
- Ferramentas AGPL (DepthFlow, VoiceStudio) rodam **como programas separados** na sua máquina; o vídeo gerado não fica sujeito à AGPL. Não embutir o código delas no DocForja.
- Imagens trazidas por você têm ficha de crédito (fonte, autor, licença ou "minha").
