# 09 — Montagem, Render e Controle de Qualidade

> **Para a IA executora:** o A16 (Montador) transforma `shotlist.json` + `vo_words.json` + assets em `timeline.json` e renderiza no Remotion. O A17 (QA Crítico) audita. O Orquestrador só libera o master depois de zero itens BLOQUEANTES.

---

## 1. Algoritmo de montagem (E13)

```
entrada: shotlist.json, vo_segments.json, vo_words.json, cue_sheet.json, assets aprovados
para cada shot em ordem:
    t_in  = tempo da palavra anchor_words.in  − antecipação (2–4 frames; 0 se o shot começa num silêncio)
    t_out = t_in do shot seguinte (cortes contíguos; sem buracos)
    se shot é "silêncio"/"respiro": usar a duração do silêncio definida em vo_segments
    dur = t_out − t_in  (em frames, 24 fps)
    se dur > 9 s e shot não é marcado "contemplativo": dividir (pedir ao A09 um sub-shot)
    se dur < 1 s e shot não é parte de montagem rápida: fundir com o vizinho
    escolher trecho do asset de vídeo: o "melhor miolo" (evitar 0,5 s iniciais/finais de i2v, onde há mais artefatos)
    aplicar transform (push/pull) proporcional à dur: escala total constante por shot (ex.: 3%) independentemente da duração
    aplicar grade do bloco (LUT) + MG-15 global
    instanciar overlays (MG-xx) com syncFrame = frame da palavra-âncora
    instanciar MG-LABEL conforme source_type
gerar faixas de áudio: VO master; música editada por cue (A15); SFX posicionados por shot (A15 refina)
validar: cobertura total da VO, nenhum frame sem V1, sem sobreposição indesejada de overlays
```

### Regras finas de corte

- **J-cut:** o som do próximo shot (ambiência/SFX) pode começar até 12 frames antes do corte visual — usar nas trocas de local (Pompeia ↔ Miseno ↔ Herculano).
- **L-cut:** a ambiência do shot anterior pode cair por até 18 frames depois do corte — usar ao sair de momentos emocionais.
- **Corte seco obrigatório:** B2-09→B3-01, B5-12→B5-13, B6-10→B7-01, B8-14→B8-15.
- **Match cuts planejados:** B0-10 (forma do rolo), B1-13 e B1-14 (foto real → reconstituição), B3-11 (pinheiro → coluna), B6-06 (gesso → molde), B7-16 (papiro → coluna).
- **Respiros:** após B3-S13, B4-S03, B4-S11, B5-S07, B5-S10, B5-S15, B6-S06, B7-S11 — imagem continua sem narração pelo tempo do `[PAUSA-L]`/`[SILÊNCIO]`.
- **Direção de movimento:** mapas e travellings de B3 movem da esquerda para a direita (Miseno → Vesúvio → Pompeia, sentido geográfico oeste → leste) para criar coerência espacial.
- **Reuso de plano-âncora:** a rua de B1-11 aparece 5 vezes — garantir que o enquadramento seja idêntico (mesmo crop e mesma escala inicial).

### Transições permitidas

| Transição | Uso | Duração |
|---|---|---|
| Corte seco | padrão (≥ 85% dos cortes) | — |
| Dissolve | passagem de tempo, memória (B1-02, B4-12, B6, B7-16) | 12–24 f |
| Fade de/para preto | abertura, fim de ato (B0, B3-34, B5-18, B6-01) | 8–36 f |
| Match cut | ver lista | — |
| Flash cuts | só B0-08 | 6 f por imagem |
| Film burn / light leak | no máximo 3 no vídeo, só em B1 | 10–14 f |

> Proibido: wipes, zooms digitais rápidos de transição, glitches (exceto B0-08), transições "de template".

---

## 2. Especificações de render

| Item | Preview (QA) | Master |
|---|---|---|
| Resolução | 1920×1080 | 3840×2160 |
| FPS | 24 | 24 (constante) |
| Codec | H.264, CRF 23 | ProRes 422 HQ (arquivo) **e** H.264 High, 50–68 Mbps VBR 2 passes (upload) |
| Cor | Rec.709, full → limited correto | Rec.709 |
| Áudio | AAC 192 kbps | PCM 48 kHz/24-bit no ProRes; AAC-LC 320 kbps no MP4 |
| Duração | igual ao master | ~16–17 min + end card |

Comandos de referência:

```bash
# Render Remotion (master 4K)
npx remotion render src/index.ts Video 09_render/master_nomix.mov --codec=prores --prores-profile=hq --concurrency=50%

# Juntar a mix final (o Remotion renderiza sem áudio ou com a VO de referência)
ffmpeg -i 09_render/master_nomix.mov -i 06_audio/mix/final_mix.wav -map 0:v -map 1:a -c:v copy -c:a pcm_s24le 09_render/master_final.mov

# Versão de upload
ffmpeg -i 09_render/master_final.mov -c:v libx264 -preset slow -profile:v high -pix_fmt yuv420p \
  -b:v 60M -maxrate 68M -bufsize 120M -c:a aac -b:a 320k -ar 48000 -movflags +faststart 09_render/master_final.mp4
```

---

## 3. QA técnico automatizado (A17)

```bash
# Frames pretos não intencionais (> 0.25 s)
ffmpeg -i preview.mp4 -vf "blackdetect=d=0.25:pix_th=0.06" -an -f null - 2>&1 | grep blackdetect

# Imagem congelada (> 4 s sem mudança) — comparar com a lista de planos estáticos intencionais
ffmpeg -i preview.mp4 -vf "freezedetect=n=0.003:d=4" -an -f null - 2>&1 | grep freeze

# Loudness
ffmpeg -i preview.mp4 -af ebur128=peak=true -vn -f null - 2>&1 | tail -n 12

# Amostragem de frames para revisão visual (1 a cada 2 s + 1 em cada corte)
ffmpeg -i preview.mp4 -vf "fps=1/2" qa/frames/t_%05d.jpg
ffmpeg -i preview.mp4 -vf "select='gt(scene,0.3)',showinfo" -vsync vfr qa/frames/cut_%05d.jpg
```

Checagens adicionais (script do A17):
1. **Inteligibilidade:** transcrever o áudio do preview (mix completo) e comparar com o roteiro → WER < 3%.
2. **Sincronia:** para 30 palavras-âncora aleatórias, conferir se o frame do corte/overlay está a ±2 frames da palavra.
3. **Texto na tela:** extrair todo texto de overlays a partir de `timeline.json` (props) → checar ortografia PT-BR e checar cada número contra `facts.json` (valor e status).
4. **Safe area:** renderizar overlays com guia de safe area em frames-chave; nenhum pixel de texto fora.
5. **Rótulos:** todo shot com `source_type` AI_* tem `MG-LABEL`; todo ARCHIVE_* tem crédito.
6. **Licenças:** todo `src` em `timeline.json` tem linha em `licenses.csv` com `commercial_ok = yes` (ou decisão registrada para `RISCO_IT`).

## 4. QA visual e criativo (A17, contexto limpo)

### 4.1 Checklist visual por frame amostrado
- [ ] Sem artefatos de IA (mãos, rostos, texto, arquitetura impossível, "derretimento")
- [ ] Vesúvio de cume único em todas as cenas de 79 d.C.
- [ ] Nenhuma lava em Pompeia/Herculano
- [ ] Figurino e arquitetura sem anacronismos (ver `06 §4.2`)
- [ ] Grade coerente com o bloco; brasa preservada em B3–B5
- [ ] Texto legível em miniatura (simular 360p)
- [ ] Vítimas reais tratadas com respeito (sem close de crânio, sem shake, sem SFX agressivo)

### 4.2 Rubric criativo (0–10, justificar cada nota)

| Critério | O que olhar | Mínimo |
|---|---|---|
| Hook (0:00–1:15) | Prende? A promessa é clara? | 8 |
| Ritmo | Corresponde à Curva de Intensidade? Há trechos arrastados? | 8 |
| Clareza | Um leigo entende fases da erupção e geografia? | 8 |
| Dosagem de motion | Nem poluído, nem pobre; cada MG com função | 8 |
| Coerência estética | Parece um único filme, não uma colagem? | 8 |
| Emoção | O ápice de B5 funciona no silêncio? | 8 |
| Payoff "nunca viu" | B7 entrega as promessas do hook? | 8 |
| Final | O callback fecha com força? | 8 |
| Respeito | Tom adequado às vítimas | 9 |

### 4.3 Formato do relatório (`qa/qa_report_vN.md`)

```markdown
| # | TC | Shot | Gravidade | Problema | Correção sugerida | Responsável |
|---|----|------|-----------|----------|-------------------|-------------|
| 1 | 05:12 | B3-29 | BLOQUEANTE | Personagem ao fundo com 6 dedos | Regerar i2v ou usar plano B (Briullov) | A12 |
| 2 | 08:40 | B4-10 | IMPORTANTE | "°C" quebra linha em 1080p | Reduzir tracking | A14 |
| 3 | 12:02 | B6-07 | MENOR | Dissolve 2 frames curto | Ajustar para 12f | A16 |
```

Gravidades: **BLOQUEANTE** (erro factual, artefato visível, problema de direitos, falha de respeito, falha técnica) → impede G3. **IMPORTANTE** → corrigir antes do master se houver tempo; senão, registrar. **MENOR** → lote final.

## 5. Loop de correção

1. O Orquestrador distribui os itens do relatório por agente.
2. Cada correção gera nova versão do asset (`_v2`) e atualiza `timeline.json`.
3. Re-render **parcial** quando possível (Remotion `--frames=início-fim`) para conferir; depois preview completo.
4. Novo QA só nos trechos alterados + 1 passada completa final.
5. Máximo de 3 ciclos; no 3º, aplicar planos B para tudo que restar.

## 6. Checklist de entrega do master (G3)

- [ ] `master_final.mov` (ProRes) e `master_final.mp4` (upload) renderizados
- [ ] Loudness −14 LUFS ±0,5 · TP ≤ −1 dBTP
- [ ] Zero BLOQUEANTES no último QA
- [ ] `licenses.csv` 100% completo; créditos na descrição
- [ ] Legendas PT-BR e EN sincronizadas (seção 7)
- [ ] Stems de áudio arquivados
- [ ] `project.json` com todos os gates e decisões registrados

## 7. Legendas (E17)

1. Gerar SRT a partir de `vo_words.json` (texto = roteiro final, não a transcrição, para evitar erros).
2. Regras: máx. 2 linhas, 42 caracteres por linha, 1–6 s por legenda, quebra em fronteira sintática, 17 caracteres/s no máximo.
3. EN: tradução feita pelo modelo a partir do roteiro final, revisada por um segundo passe (A03 confere nomes e números).
4. Não queimar legendas no vídeo longo (o YouTube exibe as faixas). Nos Shorts, legendas animadas queimadas (estilo palavra a palavra, fonte `body`, destaque `ember` na palavra falada).
