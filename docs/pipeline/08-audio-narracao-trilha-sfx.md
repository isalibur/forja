# 08 — Áudio: Narração, Trilha, Sound Design e Mix

> **Para a IA executora:** o A07 cuida da narração (seções 1–3), o A15 da trilha, SFX e mix (seções 4–7). O áudio é metade da sensação "cinematográfica": trate o silêncio como elemento de primeira classe.

---

## 1. Escolha da voz

**Perfil:** PT-BR neutro (sem sotaque regional marcado), timbre grave e quente, idade aparente 35–55, dicção limpa, capaz de sussurrar sem perder inteligibilidade. Referência de energia: narrador de documentário premium — íntimo, nunca "locutor de rádio".

**Processo de casting (A07):**
1. Selecionar 5 vozes candidatas na biblioteca do motor TTS (ou clonar uma voz humana **com autorização documentada** do dono da voz).
2. Gerar com cada uma 3 trechos de teste: B0-S01–S03 (íntimo), B3-S04 (físico/crescendo), B5-S10–S11 (ápice/quase sem voz).
3. Avaliar às cegas (A17 com contexto limpo): calor, credibilidade, variação emocional, artefatos, pronúncia. Escolher a de maior média.
4. Alternativa premium: locutor humano. Nesse caso, o A07 vira diretor de sessão: entrega roteiro com marcações, pede 2 takes por segmento, faz a edição e segue o mesmo pipeline de alinhamento.

## 2. Geração por TTS

### 2.1 Parâmetros por intensidade (motor tipo ElevenLabs; adaptar nomes a outro motor)

| Intensidade do segmento | stability | similarity | style | Velocidade | Observação |
|---|---|---|---|---|---|
| 1–3 (íntimo, reflexivo) | 0.55 | 0.80 | 0.15 | 0.92× | Mais "ar", frases mais lentas |
| 4–6 (narrativo) | 0.45 | 0.80 | 0.25 | 1.00× | Base |
| 7–8 (tensão, ação) | 0.38 | 0.80 | 0.35 | 1.03× | Mais variação, mais ataque |
| 9–10 (ápice) | 0.60 | 0.85 | 0.10 | 0.88× | **Contenção**: o ápice é dito baixo e devagar, não gritado |

Sempre: modelo multilíngue mais recente com PT-BR; `speaker_boost` ligado; saída WAV 48 kHz (ou a maior qualidade disponível).

### 2.2 Estratégia de geração

- **Um arquivo por segmento** (`06_audio/vo/B3-S04_take{1..3}.wav`). As pausas `[PAUSA-*]` **entre** segmentos são inseridas na montagem como silêncio real (room tone); as pausas **dentro** do segmento viram tags de pausa do motor ou divisão do segmento em sub-arquivos.
- Passe ao motor o **contexto**: texto do segmento anterior e do seguinte (campos de "previous/next text" quando o motor suportar), para que a entonação flua.
- Ênfases (`*palavra*`): o motor não lê markup; gere 3 takes e selecione o que acertou a ênfase. Se nenhum acertar, reescreva a frase para que a ênfase caia naturalmente (ex.: palavra no fim da frase).
- Números sempre por extenso no texto de TTS (já estão no roteiro).

### 2.3 Dicionário de pronúncia

| Termo | Como deve soar (PT-BR) | Grafia de apoio para o TTS, se errar |
|---|---|---|
| Vesúvio | ve-ZÚ-vio | Vezúvio |
| Pompeia | pom-PÉI-a | Pompéia |
| Herculano | er-ku-LA-no | Erculano |
| Miseno | mi-ZÊ-no | Mizêno |
| Estábia | es-TÁ-bia | — |
| Plínio | PLÍ-nio | — |
| Rectina | rec-TI-na | Réctina → **não**; usar "Rec-tína" |
| Tácito | TÁ-si-to | Tássito |
| Estrabão | es-tra-BÃO | — |
| Sêneca | SÊ-ne-ca | — |
| Espártaco | es-PAR-ta-co | — |
| Campânia | cam-PÂ-nia | — |
| termopólios | ter-mo-PÓ-lios | termopólios |
| calendas | ca-LEN-das | — |
| piroclástica | pi-ro-CLÁS-ti-ca | — |
| pliniana | pli-ni-A-na | — |
| Domenico Fontana | do-MÉ-ni-co fon-TA-na | Doménico Fontána |
| Giuseppe Fiorelli | dju-ZÉ-pe fio-RÉ-li | Djuzépe Fiorélli |
| Vesuvius Challenge | ve-ZÚ-vius TCHÉ-lendj | Vezúvius Tchálendj |
| Júlio César | JÚ-lio CÉ-zar | — |

O A07 valida cada termo ouvindo o take (ou transcrevendo e comparando) — erro de pronúncia em nome próprio é **bloqueante**.

### 2.4 Seleção de take (automática + revisão)

1. Transcrever cada take (WhisperX `large-v3`, `language="pt"`), normalizar texto (minúsculas, sem pontuação) e calcular WER vs. texto do segmento. **WER > 3% → descartar.**
2. Detectar artefatos: cliques, respirações artificiais longas, "metalização", mudança de timbre no meio, cortes de palavra final. (Análise espectral simples + escuta pelo modelo de áudio, se disponível.)
3. Prosódia: o A07 pontua 0–10 (ênfase, pausa, emoção vs. direção `{...}`). Escolhe o maior.
4. Se nenhum take ≥ 7: regenerar com ajuste de parâmetros (±0.1 em stability/style) ou reescrever levemente a frase (avisar A03 se o sentido mudar).

### 2.5 Tratamento da voz (cadeia)

1. Remoção de ruído/respirações artificiais exageradas (manter respirações naturais curtas — elas humanizam).
2. HPF 80 Hz (12 dB/oit).
3. EQ: +1,5 dB @ 150 Hz (calor, shelf suave); −2 dB @ 300–400 Hz se "embolado"; +2 dB @ 3–5 kHz (presença); de-esser 6–8 kHz.
4. Compressor 3:1, ataque 10 ms, release 120 ms, 3–5 dB de redução.
5. Opcional: reverb de sala curtíssima (plate ~0,5 s, 5–8% wet) só para "colar" na mix; em B5-S10–S11 e B8-S11–S12, voz **seca** e mais próxima.
6. Normalizar cada segmento para −18 LUFS (curto prazo médio) antes da concatenação.

### 2.6 Montagem e alinhamento

- Concatenar segmentos na ordem com as pausas definidas (`[PAUSA-C]` 0,4 s · `[PAUSA-M]` 0,75 s · `[PAUSA-L]` 1,5 s · `[SILÊNCIO n s]` = n s), preenchendo com room tone (não silêncio digital absoluto).
- Gerar `vo_master.wav` + `vo_segments.json` (`{id, start, end}`) + `vo_words.json` via alinhamento forçado (WhisperX) contra o texto conhecido:

```json
{"segment": "B3-S21", "words": [
  {"w": "Meio", "start": 412.36, "end": 412.58},
  {"w": "metro", "start": 412.58, "end": 412.95}
]}
```

- Precisão exigida: erro de alinhamento ≤ 40 ms nas palavras-âncora da decupagem. Conferir por amostragem 20 âncoras.

---

## 3. Narração "scratch" × final

- **E08 (scratch):** take único por segmento, parâmetros base, para timing do animatic.
- **E12f (final):** 3 takes por segmento, seleção completa. Se a duração de um segmento final divergir > 8% do scratch, o A09 recalcula os shots daquele segmento antes da montagem.

---

## 4. Trilha musical (cue sheet)

Fonte: as músicas inseridas pelo usuário são usadas conforme sua declaração geral de autorização, sem ficha ou `licenses.csv` por faixa. Se o sistema buscar música de biblioteca de terceiros, exigir licença comercial compatível e os créditos aplicáveis. **Nunca** usar trilhas de filmes/séries sem autorização.

| Cue | Bloco | Duração aprox. | Caráter | BPM / pulso | Instrumentação | Palavras-chave de busca | Pontos de sync |
|---|---|---|---|---|---|---|---|
| M01 | B0 | 1:05 | Mistério escuro que cresce | livre → 70 | drone grave, pulsos sub, textura granular, cordas col legno | "dark documentary tension build", "cinematic mystery drone" | Pulso entra em B0-S04 ("errada"); cresce até B0-S09; corte no título |
| M02 | Título | 0:04 | Sting/impacto | — | hit orquestral híbrido + sub + cauda reversa | "cinematic logo hit dark" | Hit no frame 0 do MG-13 |
| M03 | B1 | 2:00 | Calor, encantamento mediterrâneo | 80–90 | cordas suaves, harpa/lira, flauta, percussão leve de mão | "ancient rome warm documentary", "mediterranean strings hopeful" | Escurece (filtro + remoção da melodia) em B1-S12 |
| M04 | B2 | 1:10 | Inquietação | 60 | piano esparso, violoncelo sul tasto, pulso grave raro | "unsettling piano cello sparse" | **Corta** em B2-S07 ("uma da tarde…") → silêncio |
| M05 | B3 | 2:45 | Construção épica controlada | 100–110 | ostinato de cordas, percussão híbrida, metais graves, sintetizador | "epic hybrid build documentary", "ostinato strings tension" | Entra após B3-S03 ("muito pior"); respiro em B3-S13/S21; diminui em B3-S22 |
| M06 | B4 | 2:00 | Elegíaco e sombrio | 70 | coro grave sem palavras, pad escuro, pulsos sintéticos | "dark choir elegy cinematic", "somber choir ambient" | Recua a quase nada em B4-S09–S12; retorna em B4-S13 |
| M07 | B5 | 1:20 (até o ápice) | Pulso de batimento, inexorável | 60 → 72 | kick grave tipo coração, cordas tremolo, ruído | "heartbeat tension minimal", "dread pulse cinematic" | **Corte seco** na última palavra de B5-S10 ("muros") — sem cauda, sem reverb |
| M08 | B6 | 1:15 | Memória, melancolia | 66 | piano solo (ou caixinha de música + piano), muito espaço | "melancholic solo piano memory" | Entra em B6-S02; para em B6-S10 ("erradas") com a linha vermelha |
| M09 | B7 | 2:15 | Descoberta, maravilha moderna | 110–120 | pulso eletrônico, arpejos, cordas em crescendo, sinos | "science discovery inspiring electronic", "documentary breakthrough pulse" | Silêncio em B7-S11 ("púrpura"), retorno com sino; clímax em B7-S13 |
| M10 | B8 + end card | 1:45 | Tensão contemporânea → reflexão | 80 | ambiente tenso, sub, cordas longas; final: um único pad | "ominous ambient modern documentary", "reflective ending pad" | Reduz a um pad em B8-S10; **some** antes de B8-S12; pad volta só no end card |

**Edição musical (A15):**
- Cortes sempre em compasso (ou frase musical); crossfade de 0,5–2 tempos.
- Ajustar a duração por loop de seções internas, nunca por time-stretch > 3%.
- "Drops" (silêncios) são marcados no roteiro e são sagrados: B2-S07, B3-S01, B4-S11, B5-S10, B7-S11, B8-S12.
- Transição entre cues: na maioria, um silêncio de 0,5–1,5 s ou um hit; evitar dois cues tocando juntos por mais de 2 s.

---

## 5. Sound design

### 5.1 Camadas

| Camada | Função | Nível relativo |
|---|---|---|
| AMB (ambiência) | Cama contínua que define o lugar e a hora | −30 a −24 LUFS |
| FOLEY / AÇÃO | Sons sincronizados ao que se vê (pomes, passos, remos) | −26 a −18 |
| HITS / TRANSIÇÕES | Impactos, whooshes, risers em cortes e MGs | −22 a −12 (picos) |
| UI | Sons de motion graphics (ticks, carimbos) | −30 a −24 (sutis) |

### 5.2 Biblioteca de SFX (IDs usados na decupagem)

Fontes: biblioteca licenciada (Epidemic/Artlist/Soundly/BOOM), geração por IA com licença comercial (ex.: gerador de efeitos sonoros do motor de TTS), Freesound **somente CC0**.

| Grupo | IDs | Descrição / como obter |
|---|---|---|
| Vento e ar | SFX-WIND-LOW, -WIND-SOFT, -WIND-SHIFT, -WIND-STRONG, -WIND-HIGH-ALT | Vento grave, vento suave em campo, mudança de vento (rajada que vira), vento forte com partículas, vento de altitude "vazio" |
| Vulcão | SFX-ERUPTION-BOOM, -VOLCANIC-ROAR-LOW, -ROAR, -RUMBLE-DISTANT, -DEEP-GROAN, -PDC-ROAR, -PDC-ROAR-DISTANT | Boom com sub de 30 Hz e cauda longa; rugido contínuo grave (camadas de turbina + trovão + fogo filtrado); gemido grave do colapso; rugido da corrente piroclástica (avalanche + jato + fogo) |
| Pomes e colapso | SFX-PUMICE-ROOF-LIGHT, -PUMICE-RAIN-MED, -PUMICE-ROOF-HEAVY, -PUMICE-HEAVY, -PUMICE-HANDLE, -PUMICE-ON-DECK, -FOOTSTEPS-PUMICE, -WOOD-CRACK, -ROOF-COLLAPSE, -ROCK-CRUNCH, -STONE-CRACK | Gravar/compor com cascalho leve e pedra-pomes sobre telha de barro (ou granizo sobre telha filtrado); intensidade crescente; passos em cascalho fofo; madeira estalando; desabamento com poeira |
| Terremoto | SFX-EARTHQUAKE-RUMBLE, -SUB-RUMBLE, -GLASS-RATTLE, -SEISMO-SCRATCH, -SEISMO | Rumor grave com objetos tremendo; agulha de sismógrafo em papel; versão digital moderna |
| Cidade romana | SFX-CITY-ROMAN-AMB, -TAVERN-CHATTER, -CART-WHEELS-STONE, -HAMMER-CHISEL, -CROWD-UNEASY, -CROWD-FLEE, -CROWD-FLEE-DISTANT, -DOOR-BOLT, -FOOTSTEPS-RUN | Walla (murmúrio de multidão) **sem palavras inteligíveis em língua moderna** — usar walla em italiano/latim gravado ou murmúrio processado; rodas de madeira em basalto; ferramentas; tranca de madeira |
| Natureza | SFX-VINEYARD-AMB, -BIRDS, -SHEEP-DISTANT, -COUNTRYSIDE, -FIRE-CRACKLE | Insetos e folhas; pássaros mediterrâneos; ovelhas e sinos distantes |
| Mar e porto | SFX-SEA-DISTANT, -SEA-HARBOR, -HARBOR, -SEA-NIGHT, -SEA-WAVES, -WAVES-ROUGH, -OARS, -ROPES, -ROPE-CREAK | Ondas calmas; porto com gaivotas e madeira rangendo; mar noturno; mar violento; remos sincronizados |
| Interior / humano | SFX-ROOM-TONE, -ROOM-MUSEUM, -ROOM-LIBRARY, -WATER-POUR, -SNORE-DISTANT, -TORCH-HISS, -QUILL, -WAX-TABLET, -CHARCOAL-SCRATCH, -CHALK-SCRATCH | Room tones; água em bacia; ronco muito distante e abafado; tocha se apagando; pena em papiro; estilete em cera; carvão em reboco |
| Arquivo / documentos | SFX-PAPER, -PAGES, -PAPER-TAG, -MARKER-STRIKE, -STAMP, -PIN, -STRING, -PLASTER-POUR, -CRUMBLE | Papel, páginas, etiqueta, risco de marcador, carimbo, alfinete e fio no quadro, gesso líquido, papiro esfarelando |
| Ciência / moderno | SFX-SCANNER-HUM, -SCANNER-SWEEP, -LAB-HUM, -KEYBOARD, -INSTRUMENT-BEEPS, -CITY-MODERN, -CITY-EVENING, -CITY-DISTANT, -TRAFFIC, -METAL-CREAK, -HEAT-WHOOSH | Zumbido de equipamento, varredura de scanner, teclado, bipes de instrumentos, cidade moderna, trânsito, metal rangendo |
| Design / transição | SFX-SUB-HIT, -SUB-HIT-SOFT, -SUB-BOOM-TITLE, -SUB-PULSE, -SUB-TREMOR, -RISER, -WHOOSH-SHORT, -WHOOSH-MAP, -WHOOSH-DOWN, -HEARTBEAT, -TINNITUS | Impactos graves, riser, whooshes curtos; zumbido agudo pós-explosão (B3-02, máx. 1,2 s, −24 dB, filtrado para não incomodar) |
| UI | SFX-UI-TICK, -UI-TICKS, -UI-COUNT, -UI-DRAW, -UI-HIT, -UI-DATA, -UI-REVEAL, -UI-LOCATION | Ticks secos e curtos, "digitais-analógicos", nada de bipes de videogame |

### 5.3 Momentos de som assinados

| Momento | Desenho |
|---|---|
| B0 abertura | 1,5 s de vento grave em preto → primeiro som "real" é o carvão no reboco, bem perto do microfone |
| B3-01/02 | Boom (sub 30 Hz) + todo o resto da mix some por 1,2 s, só zumbido agudo filtrado → retorna o rugido grave |
| B3-21 → B3-33 | Pomes nas telhas cresce de LIGHT → MED → HEAVY, acompanhando o HUD; tick da régua no meio |
| B4-15 | Silêncio total + um único "ping" cristalino quando a luz atravessa o vidro |
| B5-12/13 | Rugido da corrente cresce por 2 s e **corta junto com a música e a imagem** no mesmo frame → 2 s só de vento muito baixo |
| B7-14 | Silêncio; "púrpura" entra com um sino suave de cauda longa |
| B8-15 | Preto + um tremor sub de 30 Hz (sentido mais do que ouvido) |

---

## 6. Mixagem

| Elemento | Alvo |
|---|---|
| Voz | −18 a −16 LUFS short-term nos trechos narrados; sempre o elemento mais inteligível |
| Música sob voz | −24 a −20 LUFS short-term; ducking por sidechain 4–8 dB (ataque 50 ms, release 400 ms) |
| Música sem voz (respiros, título) | sobe até −16 LUFS |
| SFX de impacto | picos até −6 dBFS antes do limiter, nunca mascarando palavra |
| **Master** | **−14 LUFS integrado · True Peak ≤ −1 dBTP · LRA 8–12 LU** |

Regras:
- Nenhum SFX ou hit cai em cima de uma palavra-chave da narração; se cair, mova o SFX ±6 frames ou reduza 6 dB.
- Faixas de frequência: voz domina 1–4 kHz; música recebe corte dinâmico de 2–3 dB nessa faixa quando há voz.
- Sub-graves (booms, tremores) com HPF em 25 Hz para não desperdiçar headroom.
- Verificar a mix em: fone, alto-falante de notebook e alto-falante de celular (simular com EQ de banda estreita 300 Hz–8 kHz). A narração precisa ser 100% compreensível no celular.

**Entregáveis (`06_audio/mix/`):** `final_mix.wav` (48 kHz/24-bit, estéreo), stems `VO.wav`, `MUSIC.wav`, `SFX.wav`, `AMB.wav` (para Shorts e futuras versões em outros idiomas), `loudness_report.txt` (saída do `ebur128`).

---

## 7. Comandos de verificação (A15 / A17)

```bash
# Loudness integrado, LRA e true peak
ffmpeg -i final_mix.wav -af ebur128=peak=true -f null - 2> loudness_report.txt

# Silêncios não intencionais (> 2.5 s abaixo de -50 dB) — comparar com a lista de drops do roteiro
ffmpeg -i final_mix.wav -af silencedetect=noise=-50dB:d=2.5 -f null -

# Normalização de dois passes para o alvo, se necessário
ffmpeg -i mix_pre.wav -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null -
```
