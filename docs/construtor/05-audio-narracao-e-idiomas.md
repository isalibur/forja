# 05 — Áudio, Narração e Idiomas

## 1. Narração: três caminhos (por idioma)

| Caminho | Como | Quando usar |
|---|---|---|
| **TTS local** (padrão) | Adaptador `chatterbox` (Chatterbox Multilingual, MIT — tem variante pt-BR) ou `kokoro` (Kokoro-82M, Apache-2.0 — vozes pt-BR, inglês, espanhol, francês, italiano e outros) | Produção rápida, sem custo |
| **Narração pronta** | Você envia um WAV/MP3 por idioma (sua voz, locutor, ou arquivo de outra ferramenta, ex.: VoiceStudio) — colocar em `00_entrada/narracao_<idioma>.wav`; instalação e uso do VoiceStudio em `09 §7.1` | Máxima qualidade/identidade |
| **Adaptador externo** | Qualquer servidor local/remoto compatível (servidor no padrão OpenAI `/v1/audio/speech`; API paga, se você quiser) | Testar outras vozes/engines sem mudar o sistema |

**Voz do canal:** o kit guarda, por idioma, o motor, a voz/arquivo de referência e os parâmetros — a mesma voz em todos os vídeos. Clonagem de voz só com autorização escrita do dono da voz (arquivo de consentimento no kit).

**Fluxo TTS (enxuto):**
1. Um arquivo por segmento, com o dicionário de pronúncia do idioma (`kits/<kit>/pronuncia/<idioma>.yaml`).
2. 1 take; transcreve com WhisperX e mede WER; > 3% ou artefato → refazer (até 2 vezes, variando a seed); preset Caprichado: 2–3 takes e escolhe o melhor.
3. Parâmetros por intensidade (calmo/narrativo/tenso/contido) como em `../pipeline/08-audio-narracao-trilha-sfx.md §2.1`, adaptados ao motor.
4. Cadeia de voz por FFmpeg (filtro passa-alta, presença, de-esser, compressor) e concatenação com room tone nas pausas.

**Narração pronta:** alinhar com WhisperX contra o texto do roteiro (no idioma). Se o áudio divergir do texto (WER > 8%, ex.: improviso do locutor), o sistema usa a transcrição como verdade para tempos e legendas e avisa no plano.

## 2. Alinhamento

WhisperX por segmento contra o texto conhecido → `03_audio/<idioma>/palavras.json` e `segmentos.json`. É a base de todo o tempo do plano e das legendas.

## 3. Multi-idioma

**Princípio:** um plano, N saídas. Imagens, templates, trilha e SFX são compartilhados; mudam **narração, textos na tela, legendas e metadados**.

```
roteiro (pt-BR) ─► segmentos com IDs ─► tradução por segmento (mantém IDs) ─► roteiro_<idioma>.json
plano.json (textos no idioma principal) ─► i18n/<idioma>.json (strings dos templates)
narração <idioma> ─► tempos <idioma> ─► retime proporcional dos shots ─► render <idioma>
```

**Tradução (escolha na entrada, por idioma):**
| Modo | Como |
|---|---|
| `automatico` | LLM `structured` (9Router, fallback Ollama) por blocos, com o **glossário** e um guia de estilo ("tom de documentário, frases curtas, números por extenso") |
| `gemini_manual` | O sistema exporta `traducao_<idioma>.md` com os segmentos numerados; você cola no chat do Gemini; importa a resposta (validação: mesmos IDs, nenhum faltando) |
| `arquivo` | Você envia o roteiro já traduzido no formato de `10` (mesmos IDs) |

**Glossário (`00_entrada/glossario.yaml`):** nomes próprios e termos com a forma correta por idioma (ex.: Plínio → Pliny / Plinio; Herculano → Herculaneum / Herculano; termos que não se traduzem).

**Tempo por idioma:** cada shot guarda sua fração dentro do segmento (ex.: 40%/60%). Com a narração do idioma, os shots são redistribuídos na mesma proporção. O verificador roda de novo (D1, D5, D14); textos longos encolhem pelo auto-ajuste dos templates.

**Saídas por idioma:** `05_saida/<idioma>/` com vídeo, legendas, thumbnails (texto traduzido), metadados estratégicos e shorts — estrutura completa em `13 §2`.

**Alternativa barata:** "só legendas" — o vídeo sai no idioma principal com legendas traduzidas (sem nova narração nem novo render).

## 4. Trilha

- **Biblioteca local** (YouTube Audio Library, Pixabay Music, Free Music Archive CC BY, Incompetech CC BY, faixas do kit), cada faixa com `license.json`; indexação por CLAP (texto ↔ áudio) + BPM + tags.
- O plano define o **clima** por bloco; o Sonoplasta escolhe entre os 5 melhores resultados (prioridade para as trilhas do kit).
- Edição por código: cortes em compasso (`librosa.beat`), crossfades curtos, silêncios marcados no roteiro (`[SILÊNCIO]`) respeitados.
- Compartilhada entre idiomas (ajustada ao novo tempo de cada bloco por loop/corte em compasso).

## 5. Efeitos sonoros

- **Cada template já vem com seu som** no kit (T08 contador → ticks; T06 → impacto curto; T10 → whoosh de mapa; transição do kit → som próprio). Isso cobre a maior parte dos SFX sem decisão nenhuma.
- SFX específicos do shot (pomes caindo, mar, multidão) vêm do plano (`sfx[]`): biblioteca local → Freesound (só CC0).
- Ambiências por bloco (cama contínua), escolhidas pelo modo visual/clima.
- Regra: nenhum SFX sobre palavra-chave; vítimas reais sem SFX de impacto.

## 6. Mix (por idioma)

FFmpeg: voz + trilha com `sidechaincompress` (ducking) + SFX/ambiência (`adelay` + `amix`) → `loudnorm` em 2 passes → **−14 LUFS integrado, −1 dBTP**. Trilha e SFX são os mesmos; só a voz muda.
