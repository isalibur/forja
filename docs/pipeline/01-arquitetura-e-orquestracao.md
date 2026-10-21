# 01 — Arquitetura e Orquestração do Pipeline

> **Para a IA executora:** este documento é o "sistema operacional" da produção. Ele define a stack, a estrutura de pastas, a ordem das etapas (DAG), os contratos de dados entre agentes, os portões de qualidade (gates) e as regras de retry. Leia antes de qualquer outro. Você **é** o Orquestrador (Showrunner). Os demais agentes são subagentes que você cria, alimenta com contexto e avalia.

---

## 1. Princípios de produção (não negociáveis)

1. **A narração manda no tempo ("VO-locked edit").** Nenhum corte é decidido antes de existir a narração com timestamps por palavra. A decupagem traz durações *estimadas*; as durações *reais* vêm do alinhamento forçado (WhisperX) da narração.
2. **Fato antes de estética.** Nenhum número, data ou nome aparece na tela ou na narração sem estar em `facts.json` com `status: "VERIFICADO"` ou `status: "CONSENSO_COM_RESSALVA"` (e a ressalva tem que estar no texto).
3. **Animatic antes de gerar caro.** Imagens/vídeos de IA de alta qualidade, mapas 3D e motion graphics finais só são produzidos depois que o animatic (storyboard + narração) é aprovado no Gate G2.
4. **Intensidade dosada.** Toda decisão de ritmo (cortes por minuto, densidade de motion, energia da música, densidade de SFX) é derivada da **Curva de Intensidade** definida no roteiro (`04-roteiro.md`, seção 3). Motion graphics não são enfeite: cada um precisa responder "que informação isso torna mais clara ou que emoção isso amplifica?".
5. **Respeito às vítimas.** Moldes de gesso e esqueletos são restos humanos reais. Nada de gore, nada de jump-scare com corpos, nada de som de grito sobre imagem de vítima. Ver `07-assets-e-direitos.md`, seção 6.
6. **Reconstituição por IA é sempre rotulada.** Qualquer imagem/vídeo gerado que represente o passado recebe o selo discreto "RECONSTITUIÇÃO ARTÍSTICA" no canto (componente `MG-LABEL`). Fotos de arquivo e de museu recebem crédito.
7. **Tudo é arquivo, tudo é versionado.** Cada agente escreve em sua pasta, nunca sobrescreve a versão anterior (`_v1`, `_v2`...). O Orquestrador mantém `project.json` como fonte única de verdade do estado.

---

## 2. Stack técnica recomendada

| Função | Ferramenta principal | Alternativa | Observação |
|---|---|---|---|
| Orquestração / raciocínio | Claude (modelo mais capaz disponível, ex. Opus) como Orquestrador | — | Subagentes podem usar modelos menores para tarefas mecânicas (renomear arquivos, gerar SRT) |
| Pesquisa web | Ferramenta de busca + fetch de páginas | — | Priorizar fontes primárias e acadêmicas (ver `03`) |
| Roteiro | Claude | — | Duas passadas: roteirista + script doctor |
| Narração (TTS) | ElevenLabs (modelo multilíngue mais recente, PT-BR) | Azure Neural TTS / voz humana | Ver `08` |
| Alinhamento palavra a palavra | WhisperX (modelo large-v3, idioma `pt`) | stable-ts, aeneas | Gera `vo_words.json` |
| Imagens IA | Midjourney / Flux Pro / Imagen (o mais recente disponível) | SDXL local + LoRA | Precisa suportar referência de estilo e de personagem |
| Vídeo IA (image-to-video) | Veo / Kling / Runway (o mais recente disponível) | — | Sempre image-to-video a partir de um still aprovado, nunca text-to-video "às cegas" |
| Parallax 2.5D | Depth Anything V2 (mapa de profundidade) + câmera 3D no Remotion (three.js) ou After Effects | — | Para pinturas e fotos de arquivo |
| Upscale | Topaz Photo/Video AI | Real-ESRGAN | Todo asset final ≥ 3840 px de largura |
| Motion graphics / composição | **Remotion** (React + TypeScript) | After Effects + scripts JSX | Remotion é preferido: é código, logo é gerável e revisável por IA |
| Mapas 3D / terreno | Blender (Python API) + DEM TINITALY 10 m ou Copernicus GLO-30 | QGIS + Mapbox | Render em EXR/PNG sequence |
| SFX | Biblioteca licenciada (Epidemic Sound / Artlist / Soundly) + ElevenLabs Sound Effects + Freesound (apenas CC0) | — | Ver `08` |
| Música | Faixas inseridas pelo usuário sob declaração geral de autorização | Biblioteca de terceiros com licença comercial e créditos aplicáveis | Ver `08` |
| Mix | Pipeline FFmpeg + `pyloudnorm` / ou DAW (Reaper via ReaScript) | — | Alvo −14 LUFS integrado, −1 dBTP |
| QA visual | Modelo com visão (Claude) sobre frames amostrados | — | Ver `09` |
| QA técnico | FFmpeg (`blackdetect`, `silencedetect`, `ebur128`, `freezedetect`) | — | Ver `09` |
| Legendas | WhisperX → SRT, revisado contra o roteiro final | — | PT-BR + EN |

> Se uma ferramenta não estiver disponível no ambiente de execução, o Orquestrador escolhe a alternativa e registra a troca em `project.json → decisions[]`.

---

## 3. Estrutura de pastas do projeto do vídeo

```
vesuvio/
├── project.json                  # estado global (fonte única de verdade)
├── 00_brief/
│   └── brief.md                  # tema, público, duração, tom, referências
├── 01_research/
│   ├── dossie.md                 # dossiê narrativo
│   ├── facts.json                # banco de fatos (contrato F)
│   ├── sources.json              # bibliografia com URLs e licenças
│   └── factcheck_report_vN.md
├── 02_script/
│   ├── beat_sheet.md
│   ├── roteiro_vN.md
│   ├── script.json               # roteiro estruturado (contrato S)
│   └── retention_report_vN.md
├── 03_breakdown/
│   ├── shotlist.json             # decupagem (contrato D)
│   └── animatic/                 # storyboards baixa resolução + animatic.mp4
├── 04_art/
│   ├── styleguide.json           # tokens de cor, fontes, LUTs
│   ├── style_frames/             # 1 frame de referência por bloco
│   ├── characters/               # character sheets (Plínio Jovem, Plínio Velho...)
│   ├── fonts/
│   └── luts/
├── 05_assets/
│   ├── archive/                  # fotos/pinturas/documentos reais
│   ├── generated_img/            # stills de IA (com prompt no sidecar .json)
│   ├── generated_vid/            # clipes i2v
│   ├── parallax/                 # depth maps + renders 2.5D
│   ├── maps/                     # renders Blender
│   └── licenses.csv              # 1 linha por asset (contrato L)
├── 06_audio/
│   ├── vo/                       # takes por segmento + vo_master.wav
│   ├── vo_words.json             # timestamps por palavra
│   ├── sfx/
│   ├── music/
│   ├── cue_sheet.json
│   └── mix/                      # stems + mix final
├── 07_motion/                    # projeto Remotion
│   ├── src/components/           # MG-01 ... MG-20
│   ├── src/Video.tsx
│   └── public/                   # links simbólicos para 05_assets
├── 08_edit/
│   └── timeline.json             # montagem final (contrato T)
├── 09_render/
│   ├── preview_vN.mp4            # 1080p rápido para QA
│   └── master_final.mov / .mp4
├── 10_publish/
│   ├── metadata.json
│   ├── thumbnails/
│   ├── captions_pt-BR.srt
│   ├── captions_en.srt
│   └── shorts/
└── qa/
    ├── qa_report_vN.md
    └── frames/                   # frames amostrados para revisão visual
```

---

## 4. O DAG (ordem das etapas e dependências)

```
E01 Brief
 └─► E02 Pesquisa histórica ──► E03 Fact-check do dossiê
                                   └─► E04 Beat sheet (estrutura)
                                         └─► E05 Roteiro v1
                                               └─► E06 Script doctor (retenção) ──► E07 Fact-check do roteiro
                                                                                     └─► [GATE G1: roteiro travado]
                                                                                           ├─► E08 Narração "scratch" + alinhamento
                                                                                           └─► E09 Direção de arte (style frames)
E08 + E09 ─► E10 Decupagem com tempos reais ─► E11 Storyboard + Animatic ─► [GATE G2: animatic aprovado]
[G2] ─┬─► E12a Curadoria de arquivo + licenças
      ├─► E12b Stills de IA ──► E12c Vídeo IA (i2v) / Parallax 2.5D
      ├─► E12d Mapas 3D (Blender)
      ├─► E12e Motion graphics (componentes Remotion)
      ├─► E12f Narração final (takes definitivos)
      ├─► E12g Trilha (seleção + edição na batida)
      └─► E12h Sound design (SFX)
E12* ─► E13 Montagem (timeline.json) ─► E14 Mix de áudio ─► E15 Render preview
       ─► E16 QA técnico + QA criativo ──(falhou)──► volta ao agente responsável (máx. 3 loops por item)
       ─► (passou) E17 Legendas ─► E18 Render master ─► E19 Metadados + Thumbnail + Shorts
       ─► [GATE G3: pacote final] ─► E20 Entrega
```

**Paralelismo permitido:** E08 ∥ E09; todo o bloco E12 roda em paralelo; E19 pode começar após o G2 (títulos e thumbnail não dependem da montagem final, mas devem ser revisados no G3).

---

## 5. `project.json` — estado global

```json
{
  "project_id": "vesuvio-79",
  "theme": "O Vesúvio de Pompeia da forma que você nunca viu",
  "language": "pt-BR",
  "target_duration_sec": 990,
  "fps": 24,
  "resolution": [3840, 2160],
  "stage": "E12",
  "gates": {
    "G1": {"status": "approved", "at": "2026-10-16T14:00:00Z", "by": "orchestrator+human"},
    "G2": {"status": "approved", "at": null, "by": null},
    "G3": {"status": "pending"}
  },
  "artifacts": {
    "facts": "01_research/facts.json",
    "script": "02_script/script.json",
    "shotlist": "03_breakdown/shotlist.json",
    "timeline": "08_edit/timeline.json"
  },
  "tasks": [
    {"id": "E12b-B3-04", "agent": "image_gen", "status": "done", "attempts": 2, "output": "05_assets/generated_img/B3-04_v2.png"},
    {"id": "E12e-MG03", "agent": "motion", "status": "in_progress", "attempts": 1}
  ],
  "decisions": [
    {"at": "...", "what": "Kling indisponível → Runway para i2v", "why": "API offline"}
  ],
  "budget": {"tts_chars_used": 0, "img_generations": 0, "vid_seconds_generated": 0}
}
```

Status possíveis de tarefa: `pending → in_progress → review → done | failed | blocked`.

---

## 6. Contratos de dados entre agentes

Todos os agentes **leem e escrevem JSON válido** nestes formatos. O Orquestrador valida o JSON (schema) antes de aceitar a entrega.

### Contrato F — `facts.json` (um item por fato)

```json
{
  "id": "F-017",
  "claim_pt": "A coluna eruptiva atingiu entre 26 e 33 km de altura.",
  "category": "vulcanologia",
  "value": {"min": 26, "max": 33, "unit": "km"},
  "status": "CONSENSO_COM_RESSALVA",
  "caveat_pt": "Estimativas variam conforme o modelo; usar 'mais de vinte, trinta quilômetros'.",
  "sources": ["SRC-004", "SRC-005"],
  "safe_phrasing_pt": "uma coluna que subiu mais de vinte, trinta quilômetros",
  "fallback_phrasing_pt": "uma coluna muitas vezes mais alta que o voo de um avião",
  "used_in": ["B3-02", "MG-04"]
}
```

`status` ∈ `VERIFICADO` | `CONSENSO_COM_RESSALVA` | `DEBATIDO` | `MITO` | `NAO_VERIFICADO`.
Regra: `NAO_VERIFICADO` **nunca** vai para o vídeo. `DEBATIDO` só vai com linguagem de debate ("muitos pesquisadores acreditam…"). `MITO` só aparece para ser desmentido.

### Contrato S — `script.json`

```json
{
  "version": 3,
  "segments": [
    {
      "id": "B3-S04",
      "block": "B3",
      "text": "Não foi lava. Esse é o primeiro mito.",
      "facts": ["F-020"],
      "intensity": 7,
      "voice_direction": {"emotion": "firme, revelação", "pace": "lento", "pause_after_ms": 700},
      "open_loops": [],
      "closes_loops": [],
      "est_duration_sec": 3.2
    }
  ]
}
```

### Contrato D — `shotlist.json` (decupagem)

```json
{
  "id": "B3-05",
  "segment_ids": ["B3-S04"],
  "anchor_words": {"in": "Não", "out": "mito"},
  "duration_est_sec": 3.2,
  "visual": "Plano detalhe de pedra-pomes caindo em câmera lenta contra céu negro",
  "source_type": "AI_VIDEO",
  "asset_refs": ["05_assets/generated_vid/B3-05_v1.mp4"],
  "motion": {"component": null, "camera": "slow push-in 3%", "speed_ramp": "100%→40%"},
  "overlay": ["MG-LABEL:RECONSTITUIÇÃO ARTÍSTICA", "MG-01:HUD"],
  "on_screen_text": null,
  "transition_in": "corte seco",
  "transition_out": "corte seco",
  "sfx": ["SFX-ROCK-PATTER-LIGHT"],
  "music_cue": "M04",
  "grade": "LUT-ATO3",
  "intensity": 7,
  "notes": "Primeiro plano sem lava — reforça o desmentido."
}
```

`source_type` ∈ `ARCHIVE_PHOTO` | `ARCHIVE_PAINTING` | `ARCHIVE_DOC` | `AI_IMAGE` | `AI_VIDEO` | `PARALLAX` | `MAP_3D` | `MOTION_GFX` | `STOCK_VIDEO` | `BLACK`.

### Contrato L — `licenses.csv`

```
asset_path,source_url,author,license,commercial_ok,attribution_text,ai_generated,reviewed_by,notes
05_assets/archive/brullov_last_day.jpg,https://commons.wikimedia.org/...,Karl Briullov,Public Domain,yes,"Karl Briullov, O Último Dia de Pompeia (1830–33)",no,compliance_agent,
```

### Contrato T — `timeline.json` (montagem)

```json
{
  "fps": 24,
  "duration_frames": 21600,
  "tracks": {
    "V1": [{"shot": "B3-05", "src": "05_assets/generated_vid/B3-05_v1.mp4", "from": 6012, "dur": 77, "trim_in": 0, "transform": {"scale_from": 1.0, "scale_to": 1.03}, "grade": "LUT-ATO3"}],
    "V2_overlays": [{"component": "HudClock", "from": 5800, "dur": 2400, "props": {"day": 1, "time": "13:00"}}],
    "V3_text": [],
    "V4_fx": [{"component": "FilmGrain", "from": 0, "dur": 21600, "props": {"opacity": 0.06}}],
    "A1_vo": [{"src": "06_audio/vo/vo_master.wav", "from": 0}],
    "A2_music": [{"cue": "M04", "src": "06_audio/music/M04_edit.wav", "from": 5760, "gain_db": -20, "duck": true}],
    "A3_sfx": [{"id": "SFX-BOOM-SUB", "src": "06_audio/sfx/boom_sub_01.wav", "from": 6000, "gain_db": -6}],
    "A4_amb": []
  }
}
```

---

## 7. Portões de qualidade (Gates)

| Gate | Quando | Quem aprova | Critérios mínimos para passar |
|---|---|---|---|
| **G1 — Roteiro travado** | Após E07 | Orquestrador + (opcional) humano | 100% dos fatos citados com status válido; duração estimada 14–17 min; retenção ≥ 8/10 no rubric do Script Doctor; hook ≤ 60 s com promessa clara; todos os open loops fechados |
| **G2 — Animatic aprovado** | Após E11 | Orquestrador + (opcional) humano | Nenhum shot > 9 s sem mudança visual; curva de cortes coerente com a Curva de Intensidade; todo shot tem fonte viável (arquivo licenciável ou prompt IA definido); estilo dos style frames aprovado |
| **G3 — Pacote final** | Após E19 | Orquestrador + humano (recomendado) | QA técnico 100% verde; QA criativo ≥ 8/10; licenças completas; disclosure de conteúdo sintético marcado; metadados e thumbnails prontos |

> **Modo autônomo:** se não houver humano no loop, o Orquestrador aprova os gates sozinho, mas deve rodar um **agente crítico independente** (contexto limpo, sem ver as justificativas dos outros agentes) para dar a nota. Se a nota for < 8, volta.

---

## 8. Regras de retry e escalonamento

- Cada tarefa tem no máximo **3 tentativas**. Na 2ª tentativa, o Orquestrador reescreve o prompt incluindo o feedback do QA. Na 3ª, muda de ferramenta ou de abordagem (ex.: trocar um vídeo IA problemático por parallax 2.5D de um still).
- Se falhar 3 vezes: status `blocked`, registrar em `decisions[]`, aplicar **plano B do shot** (todo shot da decupagem tem um plano B — normalmente uma imagem de arquivo com Ken Burns ou um motion graphic tipográfico).
- Vídeo IA com artefato (mãos deformadas, rostos derretendo, texto ilegível, física errada da erupção — ex.: lava escorrendo onde não houve lava): **descartar sempre**, nunca "dá pra passar".
- Erro factual detectado após G1: o roteiro volta para E07, o segmento é re-narrado e só os shots afetados são recalculados (o alinhamento é por segmento justamente para permitir isso).

---

## 9. Como o Orquestrador conversa com um subagente

Toda chamada de subagente segue este envelope:

```markdown
## PAPEL
Você é o {nome do agente}. {resumo do papel — copiar de 02-agentes.md}

## CONTEXTO DO PROJETO
- Tema: O Vesúvio de Pompeia da forma que você nunca viu
- Tom: documentário cinematográfico, estilo Magnates Media, dosado
- Estado atual: {stage}
- Arquivos de entrada: {lista de caminhos}
- Style guide: 04_art/styleguide.json (se aplicável)

## TAREFA
{tarefa específica, com IDs: ex. "Gerar stills para os shots B3-01 a B3-12"}

## RESTRIÇÕES
{regras do agente + regras globais da seção 1}

## FORMATO DE SAÍDA
{contrato JSON exato + caminho de gravação}

## CRITÉRIOS DE ACEITE
{checklist objetivo que o Orquestrador vai verificar}
```

O Orquestrador **sempre** verifica a saída contra os critérios de aceite antes de marcar `done`. Nunca confia no "concluído" do subagente sem abrir o arquivo.

---

## 10. Estimativa de esforço e custo (ordem de grandeza)

| Item | Quantidade estimada |
|---|---|
| Narração | ~2.300 palavras ≈ 14 000 caracteres × 3 takes ≈ 42 000 caracteres de TTS |
| Stills de IA | ~70 shots × 4 variações ≈ 280 gerações (+ retrabalho ~30%) |
| Vídeo IA | ~35 clipes × 5 s × 2 tentativas ≈ 350 s gerados |
| Mapas 3D | 6 sequências Blender |
| Motion graphics | 20 componentes Remotion reutilizáveis, ~60 instâncias |
| Assets de arquivo | ~40 itens com licença verificada |
| Render | preview 1080p ×3–5 iterações; master 4K ×1 |

Tempo de relógio típico com paralelismo: 1–3 dias, dominado por geração de vídeo IA e loops de QA.
