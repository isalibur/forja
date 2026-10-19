# 07 — Assets: Arquivo Real, Geração por IA e Direitos

> **Para a IA executora:** este documento alimenta o A10 (Curador de Arquivo e Direitos), o A11 (Imagens IA) e o A12 (i2v/Parallax). Nenhum asset entra na timeline sem linha completa em `05_assets/licenses.csv`.

---

## 1. Política de direitos (resumo operacional)

| Situação | Pode usar em vídeo monetizado? | Ação |
|---|---|---|
| Obra em domínio público + foto "fiel" (reprodução 2D) de museu com política aberta (CC0, ex.: Art Institute of Chicago, Yale Center for British Art, Met Open Access) | Sim | Creditar museu e autor |
| Foto em Wikimedia Commons CC BY / CC BY-SA | Sim, com atribuição (CC BY-SA: atribuição + licença na descrição) | Copiar autor, licença e link exatos |
| Licenças NC (não comercial) / ND | **Não** (NC); ND só sem alteração — e parallax/LUT é alteração | Substituir |
| Obras do governo dos EUA (NASA, USGS, US Army/USAAF) | Sim (domínio público; não sugerir endosso) | Creditar órgão |
| Copernicus Sentinel | Sim, com atribuição "Contains modified Copernicus Sentinel data [ano]" | Creditar |
| **Bens culturais do Estado italiano** (Pompeia, Herculano, MANN) | **RISCO_IT** — o *Codice dei beni culturali* (arts. 107–108) prevê autorização/taxa para reprodução com fins lucrativos, mesmo de obras antigas, e isso pode alcançar fotos de terceiros | Pedir autorização ao parque/museu **ou** licenciar via banco de imagens que já cobre esse uso **ou** substituir por reconstituição |
| Fotos de imprensa de descobertas recentes (Parco Archeologico di Pompei, revistas científicas) | Normalmente exige autorização | Pedir; plano B: reconstituição gráfica rotulada |
| Artigos científicos open access CC BY (ex.: *Scientific Reports*) | Sim, com atribuição e indicação de modificação | Creditar autores e revista |
| Stock licenciado (Artgrid, Storyblocks, Getty, Shutterstock etc.) | Sim, conforme a licença do plano | Guardar comprovante |
| Imagem/vídeo gerado por IA | Sim, conforme os termos da ferramenta (planos pagos geralmente concedem uso comercial) | Registrar ferramenta, plano e data |

> **Decisão-padrão do Orquestrador para `RISCO_IT`:** tentar autorização (e-mail aos parques, ver modelo na seção 7) em paralelo à produção; se não houver resposta até o G3, usar o plano B do shot. Nunca publicar um `RISCO_IT` sem decisão registrada.

---

## 2. Lista de assets de arquivo (AR)

| ID | Asset | Onde buscar | Licença provável | Risco | Shots |
|---|---|---|---|---|---|
| AR-01 | Afresco "Baco e o Vesúvio", Casa do Centenário | MANN; Wikimedia Commons | Obra PD; foto variável | RISCO_IT | B1-05, B1-06 |
| AR-02 | Foto atual do Vesúvio visto de Pompeia | Stock licenciado / Commons CC BY-SA | — | baixo | B1-06 |
| AR-03 | Relevo do terremoto (larário de Cecílio Jucundo) | Commons / PAP | Obra PD; foto variável | RISCO_IT | B2-03 |
| AR-04 | Karl Briullov, *O Último Dia de Pompeia* (1830–33), Museu Russo | Commons | PD | baixo | B3-29 (plano B) |
| AR-05 | Pierre-Jacques Volaire, pinturas da erupção do Vesúvio (déc. 1770) | Art Institute of Chicago (CC0) e outros | PD/CC0 | baixo | B3-01, B3-34 (plano B) |
| AR-06 | J. M. W. Turner, *Vesuvius in Eruption* (1817) | Yale Center for British Art (open access) | PD | baixo | B3-18 (plano B) |
| AR-07 | Joseph Wright of Derby, pinturas do Vesúvio | Commons | PD | baixo | reserva |
| AR-08 | William Hamilton / Pietro Fabris, *Campi Phlegraei* (1776), gravuras | Commons; bibliotecas digitais | PD | baixo | B5-18 (B), B6-03 |
| AR-09 | Fotos do séc. XIX dos moldes (ex.: Giorgio Sommer, c. 1870) | Commons; acervos fotográficos | PD | baixo (conteúdo sensível) | B0-09 (B), B5-14, B6-06, B6-07, B8-11 |
| AR-10 | Fotos modernas dos moldes | Stock licenciado / Commons | variável | RISCO_IT | B5-14 |
| AR-11 | Termopólio da Regio V | PAP (imprensa) / Commons | variável | RISCO_IT | B1-14 |
| AR-12 | Grafites e programas eleitorais; paredes pompeianas | Commons | CC BY-SA comum | RISCO_IT (baixo) | B0-02 (B), B1-15 |
| AR-13 | Pães carbonizados | Commons / MANN | variável | RISCO_IT | reserva |
| AR-14 | Inscrição a carvão de 2018 ("XVI K NOV") | PAP (comunicado de out/2018) | autorização | RISCO_IT (alto) | B0-05, B7-17, B8-12 — **plano B pronto: recriação tipográfica MG-14 "charcoal" rotulada "RECRIAÇÃO GRÁFICA DA INSCRIÇÃO"** |
| AR-15 | Esqueletos nos fornici de Herculano | PAE / Commons | variável | RISCO_IT + sensível | B4-05 |
| AR-16 | Imagens do vidro cerebral | Artigo de 2025 em *Scientific Reports* (CC BY — confirmar) / NEJM 2020 (não aberto) | CC BY (Sci Rep) | médio | B4-14, B4-15 |
| AR-17 | Papiros carbonizados de Herculano | Commons; Biblioteca Nazionale di Napoli; Institut de France | variável | RISCO_IT / FR | B0-10, B4-18/19, B7-07, B7-09 |
| AR-18 | Imagens do Vesuvius Challenge (tinta detectada, segmentações) | scrollprize.org | **conferir termos** (pedir permissão) | médio | B7-11, B7-13 |
| AR-19 | Fotos da erupção de 1944 | Commons (USAAF / US Army Signal Corps) | PD-USGov | baixo | B8-03 |
| AR-20 | B-25 cobertos de cinza (340th Bomb Group, 1944) | Commons / acervos USAF | PD-USGov | baixo | B8-04 |
| AR-21 | Satélite da Baía de Nápoles | Copernicus Browser (Sentinel-2) / USGS (Landsat) | livre com atribuição / PD | baixo | B0-11 (B), MG-10 |
| AR-22 | Vesúvio fotografado da ISS | NASA Earth Observatory / Gateway to Astronaut Photography | PD | baixo | B8-06 |
| AR-23 | Manuscrito medieval da *Naturalis Historia* ou das *Cartas* | Bibliotecas digitais (conferir licença de cada uma) | variável | médio | B3-14 |
| AR-24 | Representações posteriores de Plínio, o Velho (gravuras; estátua da Catedral de Como) | Commons | PD | baixo | B3-13 (plano B) |
| AR-25 | Retrato de Giuseppe Fiorelli | Commons | PD | baixo | B6-04 |
| AR-26 | Pinturas/gravuras do séc. XVIII da região do Vesúvio | Commons / museus abertos | PD | baixo | B6-01 |
| AR-27 | Filme da erupção de 1944 (cinejornal militar dos EUA) | National Archives (NARA) / Internet Archive | PD-USGov (conferir; cinejornais comerciais **não** são PD) | médio | B8-03 |
| AR-28 | Prédio histórico do Osservatorio Vesuviano | Commons | CC BY-SA | baixo | B8-09 |
| AR-29 | Nápoles + Vesúvio hoje (drone) | Stock licenciado | licença | baixo | B1-01, B8-01 |
| AR-30 | Mosaico "Cave Canem" (Casa do Poeta Trágico) | Commons | variável | RISCO_IT | reserva |
| AR-31 | Moldes da Casa do Bracelete de Ouro | PAP / imprensa do estudo de 2024 | autorização | RISCO_IT (alto) | B0-09, B7-03 — **plano B: dossiê só com silhuetas desenhadas** |
| AR-32 | Molde do cão | Commons | variável | RISCO_IT | B6-07 |
| AR-33 | Drone das ruínas de Pompeia | Stock licenciado | licença | RISCO_IT (baixo) | B0-06 |
| AR-34 | Pedras de travessia numa rua de Pompeia | Commons / stock | variável | RISCO_IT (baixo) | B1-13 |
| AR-35 | Corrente piroclástica real (ex.: Unzen 1991, Mayon, Sinabung) | USGS (PD) / stock | PD / licença | baixo | B4-09 |
| AR-36 | Pluma pliniana moderna (ex.: Pinatubo 1991) | USGS (PD) | PD | baixo | B3-12 |
| AR-37 | Laboratório de DNA antigo | Stock licenciado | licença | baixo | B7-01 |
| AR-38 | Pinturas/gravuras da erupção de 1631 | Commons | PD | baixo | B8-02 |

**Tratamento técnico de todo asset de arquivo:**
1. Baixar o original de maior resolução + salvar a página de origem (PDF/print) em `05_assets/archive/_proof/`.
2. Upscale para ≥ 3840 px (Topaz / Real-ESRGAN) **sem** "inventar" detalhes em rostos de fotos históricas (desligar face enhancement em vítimas e pessoas reais).
3. Remover poeira/arranhões com moderação (fotos antigas podem manter textura).
4. Gerar depth map para parallax (MG-16) quando indicado.
5. Nomear: `AR-09_sommer_cast_01.jpg` + sidecar `.json` com metadados de licença.

---

## 3. Fluxo de geração por IA (A11 → A12)

```
Prompt-base (seção 4) + sufixo de estilo (06 §4.1) + referência de personagem (se houver)
   → 4 variações (rascunho baixa resolução no E11; alta no E12b)
   → seleção pelo A11 (critérios: fidelidade histórica, composição 16:9, artefatos, coerência)
   → revisão rápida A17 (coerência histórica) ── reprova → nova rodada com feedback
   → upscale ≥ 3840 px
   → decisão de movimento (A12): AI_VIDEO (i2v) ou PARALLAX (MG-16)
   → i2v: 2 tentativas de 5–8 s, prompt só de movimento; escolher a melhor; reprovar artefatos
   → salvar com sidecar {modelo, versão, seed, prompt, negative, data, plano/licença}
```

**Negative prompt padrão (quando o modelo aceitar):**
```
lava flows in city, two volcanic peaks, modern buildings, medieval architecture, glass windows,
bound books, text, letters, watermark, logo, modern clothing, armor on civilians, gore, blood,
corpses, deformed hands, extra fingers, melted faces, oversaturated, cartoon, illustration
```

**Prompt de movimento i2v (modelo):** descrever **apenas** câmera e física, nunca o conteúdo:
```
slow dolly in, ash particles drifting left to right, smoke column billowing upward slowly,
subtle heat haze, no camera shake, no cuts, realistic physics
```

---

## 4. Prompts por shot (reconstituições)

> Todos em inglês (melhor desempenho dos modelos). Anexar o sufixo de estilo de `06 §4.1`. "I2V" = prompt de movimento para image-to-video; "PX" = parallax 2.5D.

### B0
| Shot | Prompt de imagem | Movimento |
|---|---|---|
| B0-02 | extreme macro of ancient Roman lime plaster wall, warm raking light from the left revealing cracks and texture, dark background, shallow depth of field | PX: push-in 4% |
| B0-03 | silhouette of a hand holding a small piece of charcoal approaching an ancient plaster wall, backlit by warm oil lamp light, dust in air | I2V: the hand slowly moves forward and touches the wall, dust particles floating, static camera |
| B0-12 | (montagem) reusar rascunhos de B3-01, B3-08, B3-24, B3-18 | I2V conforme os shots de origem |

### B1
| Shot | Prompt de imagem | Movimento |
|---|---|---|
| B1-02 | a single-peaked green mountain covered in vineyards and forests rising above the Bay of Naples, 79 AD, Roman villas on the lower slopes, golden afternoon light, calm sea, no smoke | PX: push 2% (transição por morph a partir de AR-02) |
| B1-03 | terraced Roman vineyards on volcanic slopes, grapevines on wooden stakes, a Roman villa with red columns in the distance, late afternoon sun | I2V: slow lateral dolly right, vine leaves gently moving in the wind |
| B1-04 | terrace of a luxurious Roman villa with pompeian red frescoes and stuccoed columns, overlooking the bay, potted lemon trees, warm light | PX: push-in |
| B1-09a | night, a group of rebel gladiators around a campfire on a barren volcanic plateau, silhouettes, 73 BC, stars | I2V: fire flickering, embers rising, slight handheld feel |
| B1-09b | a rope ladder woven from wild grapevines hanging down a steep rocky cliff at night, men climbing down, moonlight | I2V: slow tilt down along the ladder, figures descending |
| B1-10 | wide symmetrical view of a lush single-peaked green mountain under a clear blue sky, Roman farmland in the foreground, peaceful | PX: push 1% |
| B1-11 | **ANCHOR** — elevated view of a Roman street in Pompeii, 79 AD, basalt paving with stepping stones, shops with open counters, people in tunics, a cart, the single-peaked green Vesuvius in the background, bright midday | I2V: crane up from behind a low wall revealing the street, people walking naturally |
| B1-13 | the same Pompeii street with stepping stones, a mule-drawn cart passing between the stones, wheels in the ruts | I2V: cart moves left to right, camera static |
| B1-14 | a Roman thermopolium counter decorated with colorful frescoes, terracotta pots embedded in the counter, customers eating standing up, steam | PX: parallax lateral (match cut com AR-11) |
| B1-16a | Roman baker pulling round loaves of bread from a stone oven with a wooden peel, warm firelight | I2V: baker pulls bread out, embers glow |
| B1-16b | children running and laughing through a sunny Pompeii alley | I2V: tracking alongside |
| B1-16c | busy Roman market stalls with fruit, fish and amphorae, people bargaining | I2V: slow push through the crowd |
| B1-17 | **ANCHOR (derivado de B1-11 por edição de céu)** — same street, a shadow from a passing cloud sweeping over the city | I2V: shadow moves across the street, people look up briefly |

### B2
| Shot | Prompt de imagem | Movimento |
|---|---|---|
| B2-02 | interior of a Roman temple, dust and small plaster fragments falling from the ceiling, columns trembling, earthquake | I2V: camera shake small amplitude, falling dust, debris |
| B2-04 | flock of sheep on a misty hillside in Campania at dawn, eerie low fog, muted colors (no dead animals) | PX: push |
| B2-05 | close-up of a fresh crack in a frescoed Roman wall in the foreground, the green single-peaked Vesuvius softly out of focus in the background | PX: rack focus from crack to mountain |
| B2-06 | wooden scaffolding on a Roman house facade under repair, workers plastering, buckets of lime | I2V: workers move, slight push-in |
| B2-07 | macro of a terracotta cup of red wine on a wooden table, the wine surface rippling in concentric circles | I2V: ripples on the liquid surface, static camera |
| B2-08 | still life of autumn food in a Roman kitchen: pomegranates, chestnuts, walnuts, dried figs, a large amphora being sealed with clay, low golden light | PX: slow push |
| B2-09 | wide view of Pompeii at noon, rooftops of terracotta, the forum, the green Vesuvius behind, birds in the sky | I2V: birds fly then the sky becomes still, locked-off camera |

### B3
| Shot | Prompt de imagem | Movimento |
|---|---|---|
| B3-01 | view from Pompeii rooftops: the summit of the single-peaked Vesuvius erupting, a dark vertical column of ash and pumice shooting into a clear sky, 79 AD, no lava | I2V: the column surges upward rapidly and expands, static camera, brief shake at onset |
| B3-04 | close view of the base of a Plinian eruption column, roiling dark ash, volcanic lightning inside the plume | I2V: slow tilt up, turbulent billowing, lightning flashes |
| B3-08 | **CHAR: Pliny the Younger (17)** on a terrace at Misenum naval base, looking at a distant umbrella-pine shaped eruption cloud across the bay, harbor with Roman warships below | I2V: slow push-in to his face, sea breeze on his tunic |
| B3-09 | **CHAR: Pliny the Younger** extreme close-up of his eyes, the eruption cloud reflected in the iris | PX: push |
| B3-11 | Italian stone pine silhouette against a pale sky (para match com a coluna) | PX / estático |
| B3-13a | **CHAR: Pliny the Elder (56)** in a study full of scrolls and wax tablets, writing, lamp light | PX: push |
| B3-13b | **CHAR: Pliny the Elder** standing on the harbor quay of Misenum in a commander's cloak, eruption cloud in the distance | PX: push |
| B3-15 | Pliny the Elder pointing at the eruption cloud while sailors prepare a Roman liburna boat with ropes | I2V: sailors pull ropes, sail unfurls |
| B3-16 | a messenger running along a Roman harbor holding a wax tablet; close-up of the wax tablet with Latin script scratched in (illegible) | I2V: messenger running toward camera |
| B3-17 | **CHAR: Rectina** on the balcony of a seaside villa at the foot of Vesuvius, the huge eruption column towering behind, looking anxiously at the sea | PX: push |
| B3-18 | Roman quadrireme warships rowing out of Misenum harbor, oars in sync, the eruption column on the horizon | I2V: lateral drone tracking, oars moving, waves |
| B3-21 | tiny Roman warship on the bay dwarfed by a colossal umbrella-shaped eruption cloud | PX: slow push |
| B3-22 | **ANCHOR (derivado)** — same Pompeii street, sky darkening with ash cloud, people looking up anxiously | I2V: people stop and look up, light dims |
| B3-24 | close-up of white pumice stones bouncing on Roman terracotta roof tiles | I2V: pumice raining and bouncing, static camera |
| B3-26 | Pompeii street covered with a thin layer of white pumice, stones still falling | I2V: pumice falling steadily |
| B3-27 | Pompeii forum under a pitch-black sky in daytime, people with torches, pumice falling | I2V: torches flicker, figures moving |
| B3-28a | a Roman family leaving their house with bundles on their backs and cushions tied on heads, darkness and falling pumice | PX |
| B3-28b | a Roman man bolting a heavy wooden door from inside, oil lamp, worried family behind | PX |
| B3-29 | crowd fleeing through a Roman city gate at dusk-like darkness, cushions on heads, carts, falling pumice, no screaming faces | I2V: lateral tracking, crowd moving |
| B3-30 | dark interior of a Roman house, an elderly man sitting on a chair, an enslaved servant standing at the door holding an oil lamp, chests of belongings, pumice audible on the roof | PX: slow push |
| B3-31 | Roman courtyard (peristyle) filling up with pumice, timelapse look | I2V: pumice level rising, columns being buried |
| B3-32 | interior of a Roman room, wooden roof beam cracking under weight, dust and pumice pouring through (no people) | I2V: beam bends and breaks, dust falls, small shake |
| B3-34 | night view of Pompeii half-buried in grey pumice, glowing embers in the sky, the summit of the mountain glowing red | PX: very slow push |

### B4
| Shot | Prompt de imagem | Movimento |
|---|---|---|
| B4-02 | Herculaneum at night, elegant seaside Roman town with torches, streets clean of pumice, the glowing eruption column in the distance behind the mountain | I2V: torches flicker, distant flashes |
| B4-06 | people sitting under stone vaulted boathouses on a Roman beach at night, oil lamp, looking at the dark sea, faces not detailed, quiet fear | PX: slow push |
| B4-07 | the eruption column beginning to collapse onto itself, grey avalanche starting down the mountain flanks, night | I2V: column slumps and spreads down the slopes |
| B4-11 | a grey-red pyroclastic cloud engulfing the rooftops of Herculaneum at night | I2V: cloud rolls over the roofs toward camera, static camera |
| B4-13 | dark Roman room with a simple wooden bed, oil lamp, silhouette of a young man lying with his back to camera | PX: slow push |
| B4-14 (B) | macro of shiny black volcanic glass fragments on a dark lab surface (labelled "ilustração") | PX: slow rotation |

### B5
| Shot | Prompt de imagem | Movimento |
|---|---|---|
| B5-02 | **CHAR: Pliny the Elder** standing firm at the bow of a Roman ship in rough sea, deck covered in pumice, ash in the air | I2V: ship rocking, ash falling |
| B5-03 | calm candlelit Roman dining room in a villa at Stabiae, a man dining serenely, through the window the sky is black with falling pumice | PX: slow push |
| B5-04 | servants in a dark corridor listening at a closed bedroom door, a line of lamp light under the door | PX: static, slight drift |
| B5-05 | Roman villa courtyard filling with pumice up to the threshold of a door | I2V: pumice level rising |
| B5-06 | a group of Romans walking out into darkness with pillows tied on their heads with cloth, torches, falling ash | I2V: lateral tracking |
| B5-07 | violent dark sea at night under an ash-filled sky, huge waves | I2V: waves crashing |
| B5-08a | **CHAR: Pliny the Elder** lying on a sail cloth on the beach at dawn, ash sky, orange glow on the horizon | PX |
| B5-08b | close-up of an old man's hand reaching for a cup of water held by another person | PX |
| B5-08c | two men helping a heavy older man stand up on a beach, silhouettes against an orange-grey glow | PX |
| B5-09 | a torch lying in the sand, flame dying out, smoke curling | I2V: flame shrinks and goes out, smoke rises |
| B5-11 | grey dawn in Pompeii, people walking on top of pumice at the height of window sills, camera follows one person from behind | I2V: tracking behind the person |
| B5-12 | the same person stops and turns back; at the end of the street a towering grey wall of cloud | I2V: person turns, cloud approaches, static camera |
| B5-16 | darkness at Misenum, crowd fleeing with torches as silhouettes, **CHAR: Pliny the Younger** holding his mother's arm | I2V: slow movement of the crowd, torch light |
| B5-17 | **CHAR: Pliny the Younger (~45)** writing a letter by oil lamp, scrolls on the desk | PX: push |
| B5-18 | grey dawn over a flat landscape of ash where a city used to be, the decapitated mountain smoking in the distance | PX: slow pull-out |

### B7
| Shot | Prompt de imagem | Movimento |
|---|---|---|
| B7-08 | library of the Villa of the Papyri: peristyle with bronze statues, room with wooden shelves full of papyrus scrolls, warm light | PX: push |
| B7-09 | a carbonized papyrus fragment crumbling into black flakes on a dark surface | I2V: fragment crumbles slowly |
| B7-12 | silhouette of a young student in front of a computer monitor showing a neural-network visualization highlighting faint ink strokes on a dark scan (no brand, no real faces) | PX: push |

---

## 5. Stock contemporâneo (licenciado)

| Uso | Busca sugerida | Shots |
|---|---|---|
| Vesúvio ao amanhecer | "Mount Vesuvius sunrise aerial" | B1-01 |
| Nápoles com o vulcão | "Naples skyline Vesuvius drone", "Naples street evening Vesuvius" | B0-11, B8-01, B8-13/14 |
| Ruínas de Pompeia | "Pompeii ruins aerial Vesuvius" | B0-06 |
| Herculano escavada | "Herculaneum ruins aerial" | B4-03 |
| Rocha vulcânica | "volcanic pumice macro" | B1-08, B3-25 |
| Laboratório de DNA | "ancient DNA lab clean room" | B7-01 |
| Rodovia congestionada | "Italian highway traffic jam" | B8-08 |
| Sala de monitoramento | "volcano monitoring control room" (preferir material do INGV com autorização) | B8-09 |

---

## 6. Ética e sensibilidade (obrigatório)

1. Moldes e esqueletos são **restos humanos**. Enquadramento sóbrio, movimento mínimo, sem SFX de impacto, sem música épica por cima.
2. Proibido gerar por IA cenas de morte realistas, corpos, queimaduras ou sofrimento explícito. A morte é **sugerida** (corte para preto, tocha apagando, silêncio).
3. Não colocar sons de gritos sobre imagens de vítimas reais. Multidões têm murmúrio e passos, não gritos em close.
4. Pessoas escravizadas: nomear como "escravizados", com dignidade.
5. Pessoas reais contemporâneas (pesquisadores, estudantes): não gerar seus rostos por IA. Usar foto oficial licenciada ou silhueta.
6. Reconstituições sempre rotuladas; imagens de **outros** vulcões rotuladas como tal.

---

## 7. Modelo de pedido de autorização (A10 → parques/museus)

```
Assunto: Richiesta di autorizzazione alla riproduzione di immagini — documentario divulgativo

Gentile Ufficio,
stiamo producendo un documentario divulgativo in lingua portoghese sul Vesuvio e Pompei
(durata ~16 min, pubblicazione su YouTube). Chiediamo l'autorizzazione a riprodurre le
seguenti immagini [elenco con ID, descrizione, fonte], con citazione "© Parco Archeologico
di Pompei / su concessione del Ministero della Cultura".
Restiamo a disposizione per eventuali canoni e condizioni.
Cordiali saluti,
[nome, canale, contatto]
```

> O envio de e-mails é ação externa: o Orquestrador **pede confirmação ao humano responsável** antes de enviar qualquer pedido em nome do canal.
