# Estimativa de Produção e Orçamento

> **Preset:** `padrao` · **Meta Orçamentária:** `120 min` · **Tempo Estimado:** `80.5 min` [DENTRO DO ORÇAMENTO]

## Tempos por Etapa de Produção
| Etapa | Detalhes | Quantidade | Tempo Estimado |
|---|---|---|---|
| Narração e alinhamento (pt-BR) | Síntese TTS e alinhamento WhisperX | 632.9 s áudio | 6.7 min |
| Geração de imagens | ComfyUI FLUX (2 variações) | 52 imagens | 11.5 min |
| Tratamento e efeitos (2.5D, recorte, upscale) | DepthFlow, BiRefNet e Real-ESRGAN | 25 shots c/ efeitos | 5.8 min |
| Áudio (trilha, SFX e mixagem) | Mixagem estéreo e normalização EBU R128 (-14 LUFS) | 9 blocos | 5.0 min |
| Renderização Remotion e QA | Composição de vídeo e export MP4 (1080p) | 632.9 s vídeo | 16.7 min |
| Idiomas adicionais (en, es) | TTS e render Remotion localizado | 2 idiomas | 34.8 min |

