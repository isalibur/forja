# 05 — Decupagem (Shot List Completa)

> **Para a IA executora:** esta é a decupagem base que o A09 converte em `shotlist.json` (contrato D). As durações aqui são **estimadas**; depois do alinhamento da narração (`vo_words.json`), o A09 recalcula cada duração cortando nas palavras-âncora. Se a duração real de um shot passar de 9 s, divida-o; se ficar abaixo de 1 s (fora de montagens rápidas intencionais), funda com o vizinho.
>
> IDs: `B{bloco}-{nn}`. Referências: `S{nn}` = segmento do roteiro (`04-roteiro.md`); `MG-xx` = componente de motion (`06`); `AR-xx` = asset de arquivo (`07`); `SFX-*` = som (`08`); `M0x` = cue musical (`08`).

---

## 1. Regras de montagem que valem para todos os shots

1. **Corte em palavra.** Cortes entram 2–4 frames antes da palavra-âncora (antecipação visual). Hits de SFX e entradas de motion sincronizam com a sílaba tônica da palavra-âncora (tolerância ± 2 frames).
2. **Movimento interno sempre.** Nenhum plano fica 100% estático por mais de 3 s, exceto os planos marcados como "estático" para efeito dramático (B2-09, B5-12, B8-14). Mesmo nesses, partículas de cinza/grão mantêm o quadro vivo.
3. **Escala alternada.** Evite aberto → aberto → aberto. Padrão desejado: aberto (contexto) → médio (ação) → detalhe (emoção/prova) → motion graphic (informação).
4. **Contraponto > ilustração literal.** Quando a frase já é visual, use a imagem para acrescentar (ex.: "cidade viva" sobre a mesma rua que depois será soterrada).
5. **Rótulos obrigatórios.** Todo `AI_IMAGE`, `AI_VIDEO` e mapa com costa antiga leva `MG-LABEL: RECONSTITUIÇÃO ARTÍSTICA` (canto inferior esquerdo, 60% opacidade, 2,2% da altura). Todo `ARCHIVE_*` leva crédito (canto inferior direito).
6. **Vítimas reais** (moldes, esqueletos): só `ARCHIVE_PHOTO` com parallax ≤ 1–2% ou push lentíssimo; nunca i2v, nunca shake, nunca hit de SFX agressivo, nunca close de crânio. Música baixa ou silêncio.
7. **Plano B.** Se o asset principal falhar (licença negada, IA com artefato após 3 tentativas), aplique a coluna "Plano B".
8. **Proporção de fontes (alvo do vídeo todo):** ~35% reconstituição IA (stills + vídeo), ~30% arquivo real (fotos, pinturas, documentos), ~25% motion graphics/mapas, ~10% stock contemporâneo. O A17 verifica se nenhum bloco passa de 60% de IA (fadiga e perda de credibilidade).

## 2. Ritmo por bloco (derivado da Curva de Intensidade)

| Bloco | Intensidade | Duração média de shot | Nº de shots | Cue | Grade (LUT) | Densidade de MG |
|---|---|---|---|---|---|---|
| B0 | 5→8 | 3–4 s, montagem final 1,5 s | 13 | M01 → M02 (título) | LUT-B0 "carvão" | média (documento, contador) |
| B1 | 3→4 | 4–6 s | 17 | M03 | LUT-B1 "dourado" | baixa |
| B2 | 4→5 | 4–5 s | 9 | M04 | LUT-B2 "sombra" | baixa (sismógrafo) |
| B3 | 6→8 | 2,5–4 s | 34 | M05 | LUT-B3 progressivo | **alta** (HUD, mapas, régua, comparador, documento) |
| B4 | 7→9 | 3–4 s, com silêncios | 19 | M06 | LUT-B4 "noite" | média-alta (explicador, termômetro) |
| B5 | 8→10→2 | 3–5 s; ápice 2 s; pós-ápice 5–9 s | 18 | M07 (corta em B5-12) | LUT-B5 "alvorada de cinza" | média → **zero no ápice** |
| B6 | 3 | 5–7 s | 10 | M08 | LUT-B6 "arquivo" | baixa (timeline, etiquetas) |
| B7 | 5→7 | 3–5 s | 19 | M09 | LUT-B7 "laboratório" | alta (dossiê, scan) |
| B8 | 6→8→2 | 3–5 s; final 3–5 s | 16 | M10 | LUT-B8 "contemporâneo" | média (zona vermelha, 72 h) |
| **Total** | | | **155** | | | |

---

## 3. Decupagem por bloco

Colunas: **ID** · **Seg** (segmento do roteiro) · **Dur** (s, estimada) · **Visual** · **Fonte** · **Câmera / Motion** · **Overlay / texto** · **Trans.** (transição de entrada) · **SFX** · **Plano B**

### B0 — Cold open · 0:00–1:15 · M01 (drone escuro + pulso que cresce) → M02 (sting do título) · LUT-B0

| ID | Seg | Dur | Visual | Fonte | Câmera / Motion | Overlay / texto | Trans. | SFX | Plano B |
|---|---|---|---|---|---|---|---|---|---|
| B0-01 | pré | 1.5 | Preto absoluto; partículas de cinza quase invisíveis | MOTION_GFX (MG-15) | partículas lentas | — | fade de preto | SFX-WIND-LOW, room tone | — |
| B0-02 | S01 | 3.5 | Macro de reboco antigo com luz rasante quente | AI_IMAGE → PARALLAX | push-in 4% | MG-LABEL | corte | SFX-WIND-LOW | Foto de parede pompeiana (AR-12) |
| B0-03 | S01 | 2.5 | Mão em contraluz segurando carvão toca o reboco | AI_VIDEO | estático; mão entra em quadro | MG-LABEL | corte | SFX-CHARCOAL-SCRATCH no toque | Still + MG |
| B0-04 | S02 | 5 | "XVI K NOV" escrito traço a traço sobre o reboco | MOTION_GFX (MG-14 var. "carvão") | traços em sync com "Dezesseis dias antes…" | "= 17 DE OUTUBRO" (Plex Mono) | corte | SFX-CHARCOAL-SCRATCH ×3, tick | — |
| B0-05 | S03 | 5 | Foto real da inscrição de 2018; ela "esmaece" como carvão e volta | ARCHIVE_PHOTO (AR-14) | push 3% + máscara de apagamento | Crédito PAP | corte | SFX-WIND, drone grave | Reconstituição tipográfica (B0-04) |
| B0-06 | S03 "enterrada" | 2.5 | Drone descendo sobre as ruínas, Vesúvio ao fundo | STOCK_VIDEO (AR-33) | descida | — | corte com hit | SFX-SUB-HIT-SOFT | Still com parallax |
| B0-07 | S04 | 5 | Página de livro "24 DE AGOSTO, 79 d.C." → risco vermelho em "errada" | MOTION_GFX (MG-07 var. livro) | zoom 10% | data riscada | corte | SFX-PAPER, SFX-MARKER-STRIKE | MG tipográfico puro |
| B0-08 | S05 | 2 | Flash de 3 imagens (molde, papiro, vulcão), 6 frames cada | ARCHIVE mix | flash cuts | — | corte rápido | SFX-WHOOSH-SHORT ×3 | — |
| B0-09 | S06 | 4 | Molde "adulto com criança", P&B, anotação "MÃE?" | ARCHIVE_PHOTO (AR-31) + MG-11 | push 2% | "MÃE E FILHO?" com "?" pulsando | corte | SFX-UI-TICK, drone | Foto Sommer (AR-09) |
| B0-10 | S07 | 4 | Papiro carbonizado → visualização em camadas de raio-X | ARCHIVE (AR-17) + MG-12 | push-in | — | match cut pela forma do rolo | SFX-SCANNER-HUM | — |
| B0-11 | S08 | 5 | Nápoles hoje com o Vesúvio dominando; polígono vermelho pulsa 1× | STOCK_VIDEO + MG-10 | pan lento | MG-09 "≈ 700.000 PESSOAS" | corte | SFX-CITY-DISTANT, SFX-SUB-PULSE | Satélite (AR-21) |
| B0-12 | S09 | 7 | Montagem crescente: HUD MG-01 aparece pela 1ª vez sobre o Vesúvio verde com coluna nascendo; 1,5 s cada: Plínio olhando o céu, pomes caindo, navio | AI_VIDEO mix | ritmo acelera | MG-01 (teaser) | cortes na batida | SFX-RISER, SFX-HEARTBEAT | Stills com Ken Burns |
| B0-13 | título | 4 | "VESÚVIO — AS ÚLTIMAS HORAS DE POMPEIA" com cinza caindo sobre as letras | MOTION_GFX (MG-13) | letras surgem com brasa | — | hit → preto | SFX-SUB-BOOM-TITLE | — |

### B1 — A montanha verde · 1:15–3:15 · M03 "Campania Felix" (cordas quentes, harpa/lira, mediterrâneo) · LUT-B1

| ID | Seg | Dur | Visual | Fonte | Câmera / Motion | Overlay / texto | Trans. | SFX | Plano B |
|---|---|---|---|---|---|---|---|---|---|
| B1-01 | S01 | 4 | Vesúvio atual ao amanhecer, névoa | STOCK_VIDEO (AR-29) | push lento | — | fade de preto | SFX-WIND-SOFT, pássaros | Foto |
| B1-02 | S02 | 4 | Transformação: foto atual → monte verde de pico único coberto de vinhas | AI_IMAGE → PARALLAX | push 2%; morph por máscara de luz | MG-LABEL | dissolve 24f | SFX-WIND, cigarras | Só a imagem IA |
| B1-03 | S03 | 4 | Vinhedos em terraços, sol da tarde, villa ao fundo | AI_VIDEO (folhas ao vento) | dolly lateral | MG-LABEL | corte | SFX-VINEYARD-AMB | Still + parallax |
| B1-04 | S03 | 3.5 | Terraço de villa com afrescos vermelhos e vista para a baía | AI_IMAGE → PARALLAX | push-in | MG-LABEL | corte | SFX-SEA-DISTANT | — |
| B1-05 | S03 "Baco" | 6 | Afresco de Baco e o Vesúvio: do detalhe das uvas, recua até a montanha | ARCHIVE_PAINTING (AR-01) + PARALLAX (3 camadas) | pull-out 8% | crédito MANN; seta fina "VESÚVIO?" | corte | SFX-ROOM-MUSEUM sutil | Ilustração IA em estilo afresco (rotulada) |
| B1-06 | S04 | 5 | Split-screen: afresco (pico único) × foto atual (Somma + cone); contornos desenhados | MOTION_GFX (MG-18) | — | "79 d.C." / "HOJE" | corte | SFX-UI-DRAW | — |
| B1-07 | S05 | 6 | Gravura de Estrabão → texto grego com trecho destacado | ARCHIVE + MG-07 | push | MG-08 "ESTRABÃO · geógrafo grego" | corte | SFX-PAPER, pena | MG tipográfico |
| B1-08 | S05 "queimadas" | 3 | Macro de rocha vulcânica porosa, luz rasante | STOCK_VIDEO / AI_IMAGE | slider lento | — | corte | SFX-ROCK-CRUNCH sutil | — |
| B1-09 | S06 | 5 | Silhuetas de rebeldes junto à fogueira no alto → corda de videira descendo o penhasco (2 × 2,5 s) | AI_VIDEO ×2 | handheld leve | MG-LABEL; MG-08 "ESPÁRTACO · 73 a.C." | corte | SFX-FIRE-CRACKLE, SFX-ROPE-CREAK | Stills |
| B1-10 | S07 | 3 | Monte verde, céu limpo, plano simétrico e calmo | AI_IMAGE → PARALLAX | push 1% | — | corte | SFX-WIND-SOFT | — |
| B1-11 | S08 | 4 | **Plano-âncora:** grua sobe atrás de um muro e revela Pompeia viva ao sol, Vesúvio atrás | AI_VIDEO | crane up | MG-LABEL; MG-08 "POMPEIA" | corte | SFX-CITY-ROMAN-AMB (cresce) | Still + parallax |
| B1-12 | S09 "onze mil" | 3 | Planta ilustrada de Pompeia preenchida por pontinhos (pessoas) | MOTION_GFX (MG-09) | — | "≈ 11.000 HABITANTES*" (*estimativa) | corte | SFX-UI-COUNT | — |
| B1-13 | S09 "ruas" | 3 | Foto atual das pedras de travessia → mesma rua reconstituída, carroça passando | ARCHIVE_PHOTO (AR-34) → AI_VIDEO | push; match cut | — | match cut | SFX-CART-WHEELS-STONE | Só a foto |
| B1-14 | S09 "termopólios" | 4 | Foto do termopólio da Regio V → reconstituição com pessoas comendo | ARCHIVE (AR-11) → AI_IMAGE | parallax; match cut | crédito PAP | match cut | SFX-TAVERN-CHATTER, potes de barro | Só a IA |
| B1-15 | S10 | 6 | Grafites reais, 1,5 s cada, com tradução curta animada | ARCHIVE (AR-12) + MG-14 | push-ins alternados | traduções (Plex Sans) | cortes na batida | SFX-CHALK-SCRATCH, murmúrio | — |
| B1-16 | S11 | 4 | Vida: padeiro tirando pão do forno; crianças correndo; feira | AI_VIDEO ×3 | — | MG-LABEL | cortes | SFX-CITY-ROMAN-AMB no pico | Stills |
| B1-17 | S12 | 3 | Mesma rua de B1-11: nuvem cobre o sol, sombra desce sobre a cidade | AI_VIDEO | estático | — | corte | SFX-WIND-SHIFT; música escurece | Still com sombra animada |

### B2 — O aviso · 3:15–4:25 · M04 "Fault Line" (piano esparso, violoncelo, tensão baixa) · LUT-B2

| ID | Seg | Dur | Visual | Fonte | Câmera / Motion | Overlay / texto | Trans. | SFX | Plano B |
|---|---|---|---|---|---|---|---|---|---|
| B2-01 | S01 | 4 | Sismógrafo: linha calma no papel começa a vibrar | MOTION_GFX (MG-21) | — | "5 DE FEVEREIRO · 62/63 d.C." | corte | SFX-SEISMO-SCRATCH, SFX-SUB-RUMBLE | — |
| B2-02 | S01 "tremeu" | 2.5 | Poeira caindo do teto de um templo, colunas tremendo | AI_VIDEO | shake 3 px | MG-LABEL | corte | SFX-EARTHQUAKE-RUMBLE, pedras | Still + shake |
| B2-03 | S02 | 5 | Relevo do terremoto (larário de Cecílio Jucundo) | ARCHIVE (AR-03) + PARALLAX | push | crédito; MG-08 "RELEVO DO TERREMOTO" | corte | SFX-STONE-CRACK | Gravura PD |
| B2-04 | S02 "ovelhas" | 3 | Rebanho numa colina sob névoa estranha (sugerir, nunca mostrar animais mortos) | AI_IMAGE → PARALLAX | push | MG-07 citação curta de Sêneca; MG-LABEL | corte | SFX-SHEEP-DISTANT → silêncio | — |
| B2-05 | S03 | 3.5 | Rachadura na parede em primeiro plano; Vesúvio verde desfocado ao fundo | AI_IMAGE (rack focus via parallax) | rack focus | — | corte | SFX-WIND | — |
| B2-06 | S04 | 5 | Andaimes de madeira, operários → foto real de parede inacabada | AI_VIDEO + ARCHIVE | — | — | corte | SFX-HAMMER-CHISEL distante | Só IA |
| B2-07 | S05 | 5 | Taça de vinho sobre a mesa; superfície do líquido treme | AI_VIDEO | macro estático | MG-21 mini no canto | corte | SFX-GLASS-RATTLE sutil | Still + MG |
| B2-08 | S06 | 5 | Natureza-morta de outono: romãs, castanhas, nozes; ânfora sendo lacrada | AI_IMAGE → PARALLAX | push lento | — | corte | SFX-ROOM-TONE, lacre de barro | — |
| B2-09 | S07 | 4 | Pompeia ao meio-dia, Vesúvio ao fundo; pássaros param | AI_VIDEO | **estático travado** | — | corte seco no silêncio | SFX-BIRDS → corte para silêncio | Still |

### B3 — Dia 1 · A coluna · 4:25–7:20 · M05 "Pliniana" (entra em B3-04: ostinato de cordas + percussão híbrida em construção) · LUT-B3 progressivo

| ID | Seg | Dur | Visual | Fonte | Câmera / Motion | Overlay / texto | Trans. | SFX | Plano B |
|---|---|---|---|---|---|---|---|---|---|
| B3-01 | S01 | 2 | Topo do Vesúvio explode: coluna escura (plano aberto a partir de Pompeia) | AI_VIDEO (gerar 8 s, usar 2) | estático; shake 4 px no impacto | **MG-01 entra:** "DIA 1 · ≈ 13:00 · POMPEIA" | corte seco | SFX-ERUPTION-BOOM (sub 30 Hz) | Volaire (AR-05) + parallax |
| B3-02 | silêncio | 1.2 | Mesmo plano a 40% de velocidade, som some | AI_VIDEO (speed ramp) | — | — | — | SFX-TINNITUS | — |
| B3-03 | S02 | 4 | "LAVA" aparece e é riscada; ao fundo, lava genérica que congela e vira cinza | MOTION_GFX (MG-14) + STOCK | — | "LAVA" riscado + selo "MITO" | corte | SFX-MARKER-STRIKE, UI | Só tipografia |
| B3-04 | S03 | 2.5 | Base da coluna: turbulência negra, relâmpagos vulcânicos | AI_VIDEO | tilt up lento | MG-LABEL | corte | SFX-VOLCANIC-ROAR-LOW, estalos elétricos | — |
| B3-05 | S04 | 6 | Comparador: Everest 8,8 km → avião ≈ 11 km → coluna 26–33 km; câmera sobe junto | MOTION_GFX (MG-04) | tilt up virtual | "8,8 km" · "≈ 11 km" · "26–33 km" | corte | SFX-RISER, UI-TICKS | — |
| B3-06 | S04 | 3 | Vista do alto: pluma se espalhando sobre a baía | MAP_3D | top-down lento | MG-LABEL | corte | SFX-WIND-HIGH-ALT | — |
| B3-07 | S05 | 4 | Mapa 3D: voo do Vesúvio até Miseno; tracejado "≈ 30 km" | MAP_3D (MG-02) | voo | VESÚVIO · MISENO · POMPEIA · HERCULANO | corte | SFX-WHOOSH-MAP | Mapa 2D |
| B3-08 | S05 "rapaz" | 3.5 | Plínio, o Jovem, num terraço em Miseno, olhando o horizonte; nuvem ao longe | AI_VIDEO | push lento no rosto | MG-LABEL; HUD local → "MISENO" | corte | SFX-SEA-HARBOR, gaivotas | Still + parallax |
| B3-09 | S06 | 3 | Close de Plínio, o Jovem; a nuvem refletida no olho | AI_IMAGE → PARALLAX | push | MG-08 "PLÍNIO, O JOVEM · 17 anos" | corte | — | — |
| B3-10 | S07 | 6 | Carta em latim; destaque animado em *arbor… pinus*; tradução própria surge | MOTION_GFX (MG-07) | push lento | latim + tradução | corte | SFX-PAPER, pena | — |
| B3-11 | S07 "pinheiro" | 3.5 | Silhueta de pinheiro-manso → coluna com a mesma forma | STOCK + AI | estático | — | match dissolve 12f | SFX-WIND → ROAR | — |
| B3-12 | S08 | 3 | "ERUPÇÃO PLINIANA" sobre foto real de pluma moderna | ARCHIVE (PD-USGov, ex.: Pinatubo 1991) + MG-14 | — | crédito USGS | corte | SFX-UI-HIT soft | Só tipografia |
| B3-13 | S09 | 5 | Plínio, o Velho, entre rolos → de pé, no comando, no porto | AI_IMAGE → PARALLAX ×2 | push | MG-08 "PLÍNIO, O VELHO · naturalista · almirante"; MG-LABEL | corte | SFX-HARBOR, rolo | Gravura (AR-24) |
| B3-14 | S09 "37" | 2.5 | Manuscrito medieval da *Naturalis Historia* ou pilha de rolos com contador | ARCHIVE / MG-09 | — | "37 LIVROS" | corte | SFX-PAGES | MG |
| B3-15 | S10 | 3 | Plínio, o Velho, aponta a nuvem; marinheiros preparam barco | AI_VIDEO | — | MG-LABEL | corte | SFX-ROPES, vozes indistintas | Still |
| B3-16 | S11 | 4 | Mensageiro chega correndo; close na tabuinha de cera | AI_VIDEO + AI_IMAGE | — | MG-08 "RECTINA · ao pé do Vesúvio" | corte | SFX-FOOTSTEPS-RUN, SFX-WAX-TABLET | — |
| B3-17 | S11 "mar" | 3 | Villa ao pé da montanha, coluna gigante atrás, mulher na varanda olhando o mar | AI_IMAGE → PARALLAX | push | MG-LABEL | corte | SFX-ROAR distante | — |
| B3-18 | S12 | 4.5 | Quadrirremes saindo de Miseno, remos sincronizados, coluna no horizonte | AI_VIDEO | drone lateral | MG-LABEL | corte | SFX-OARS, tambor de remo sutil, ondas | Pintura (Turner, AR-06) |
| B3-19 | S12 mapa | 3 | Rota do navio Miseno → Vesúvio | MAP_3D (MG-02) | top-down | — | corte | SFX-WHOOSH-MAP | 2D |
| B3-20 | S13 | 5 | "FORTES FORTUNA IUVAT" gravado em pedra, luz passa | MOTION_GFX (MG-07 var. pedra) | — | latim + "A SORTE FAVORECE OS CORAJOSOS" | corte | SFX-STONE-CHISEL leve; música incha | — |
| B3-21 | respiro | 1.5 | Navio minúsculo diante da coluna gigante | AI_IMAGE → PARALLAX | — | — | — | música | — |
| B3-22 | S14 | 2 | Rua de B1-11, céu escurecendo | AI_VIDEO | — | HUD local → "POMPEIA" | corte | SFX-CROWD-UNEASY | — |
| B3-23 | S15 | 4 | Setas de vento levando a pluma para SE; Pompeia e Estábia na sombra | MAP_3D + MG-17 | câmera gira para mostrar a direção | "VENTO → SE" | corte | SFX-WIND-STRONG | 2D |
| B3-24 | S16 | 2.5 | Primeiras pedras-pomes quicando em telhas de terracota | AI_VIDEO | close | MG-LABEL | corte | SFX-PUMICE-ROOF-LIGHT | — |
| B3-25 | S16 "pomes" | 3 | Pedra-pomes real na palma da mão | STOCK / ARCHIVE_PHOTO | macro push | tag "PEDRA-POMES · leve, porosa" | corte | SFX-PUMICE-HANDLE | — |
| B3-26 | S16 "15 cm" | 3 | Régua lateral com silhueta humana (1,70 m) começa a subir sobre rua com pomes | MOTION_GFX (MG-03) + AI_VIDEO | — | "≈ 15 cm / HORA" | corte | SFX-UI-TICK cadenciado | — |
| B3-27 | S17 | 3.5 | Céu totalmente negro sobre o fórum; tochas acesas em pleno dia | AI_VIDEO | lento | HUD → "≈ 15:00" | corte | SFX-PUMICE-RAIN-MED, multidão | — |
| B3-28 | S18 | 5 | Split: família saindo com trouxas × família trancando a porta | AI_IMAGE → PARALLAX ×2 (MG-18) | — | "FUGIR?" / "FICAR?" | corte | SFX-DOOR-BOLT, passos | — |
| B3-29 | S19 | 4 | Multidão saindo pela porta da cidade, almofadas na cabeça, carroças | AI_VIDEO | lateral | MG-LABEL | corte | SFX-CROWD-FLEE (murmúrio, sem gritos), carroça | Briullov (AR-04) + parallax |
| B3-30 | S20 | 5 | Interior escuro: idoso sentado; escravizado à porta com lamparina; baús | AI_IMAGE → PARALLAX | push lento | MG-LABEL | corte | SFX-PUMICE-ROOF-HEAVY abafado | — |
| B3-31 | S21 | 7 | Régua em destaque: "0,5 m"… "1 m" em sync com a fala; ao fundo, pomes enchendo um pátio | MOTION_GFX (MG-03) + AI_VIDEO | — | HUD → "≈ 20:00" | corte | SFX-UI-TICK por marca, pomes | — |
| B3-32 | S21 "telhados" | 2.5 | Viga estalando, telhado cedendo, poeira (sem corpos) | AI_VIDEO | shake 3 px | MG-LABEL | corte | SFX-WOOD-CRACK, SFX-ROOF-COLLAPSE | Still |
| B3-33 | S21 "três metros" | 4 | Régua chega a "≈ 2,8 m"; silhueta humana desaparece abaixo do nível | MOTION_GFX (MG-03) | pull-out | "≈ 2,8 m" | corte | SFX-SUB-HIT | — |
| B3-34 | S22 | 4 | Noite: Pompeia meio soterrada, brasas no céu, brilho vermelho no topo do monte | AI_IMAGE → PARALLAX | push lentíssimo | — | corte → preto 8f | SFX-RUMBLE-DISTANT; música decai | Volaire (AR-05) |

### B4 — A noite · Herculano · 7:20–9:20 · M06 "Herculaneum" (coro grave elegíaco + pulsos sintéticos) · LUT-B4

| ID | Seg | Dur | Visual | Fonte | Câmera / Motion | Overlay / texto | Trans. | SFX | Plano B |
|---|---|---|---|---|---|---|---|---|---|
| B4-01 | S01 | 4 | Mapa 3D: de Pompeia para Herculano, a oeste | MAP_3D (MG-02) | voo | HUD "HERCULANO · ≈ 23:00" | corte | SFX-WHOOSH-MAP | 2D |
| B4-02 | S01 | 4 | Herculano à noite, à beira-mar, tochas, ruas sem pomes, coluna brilhando ao longe | AI_VIDEO | lento | MG-LABEL | corte | SFX-SEA-NIGHT, roar distante | Still |
| B4-03 | S02 | 4 | Herculano escavada hoje, ~20 m abaixo da cidade moderna | STOCK / ARCHIVE | pan | crédito | corte | SFX-WIND-SOFT | — |
| B4-04 | S03 "praia" | 3 | Os fornici (arcos) hoje | ARCHIVE_PHOTO | push | crédito | corte | room tone | Arcos vazios em IA |
| B4-05 | S03 "estavam eles" | 5 | Esqueletos nos fornici, P&B, plano aberto respeitoso | ARCHIVE_PHOTO (AR-15) | push 2% muito lento | crédito; MG-09 discreto "+300" | corte | room tone; música baixa | Silhuetas sob os arcos em IA (sem corpos) |
| B4-06 | S03 "esperando" | 4 | Antes: pessoas sentadas sob os arcos olhando o mar escuro; rostos sem detalhe | AI_IMAGE → PARALLAX | push | MG-LABEL | corte | SFX-SEA-WAVES, sussurros indistintos muito baixos | — |
| B4-07 | S04 | 4 | A coluna começa a afundar sobre si mesma | AI_VIDEO | estático | HUD "DIA 2 · ≈ 00:30" | corte | SFX-DEEP-GROAN | — |
| B4-08 | S05 | 8 | Explicador em corte transversal: coluna sustentada → densidade sobe → colapso → corrente desce | MOTION_GFX (MG-05) | câmera 2D lateral | "COLUNA" · "COLAPSO" · "CORRENTE PIROCLÁSTICA" | corte | SFX-UI, SFX-WHOOSH-DOWN | — |
| B4-09 | S06 | 3 | Corrente piroclástica REAL de outro vulcão descendo encosta | STOCK / ARCHIVE (PD-USGov) | — | "IMAGEM REAL · OUTRO VULCÃO"; crédito | corte | SFX-PDC-ROAR | IA |
| B4-10 | S06 "100 km/h" | 2.5 | Velocímetro "> 100 km/h" + termômetro "centenas de °C" | MOTION_GFX (MG-09 + MG-19) | — | números | corte | SFX-UI-TICKS rápidos | — |
| B4-11 | S07 | 2.5 | Nuvem cinza-avermelhada engolindo os telhados de Herculano | AI_VIDEO | estático | MG-LABEL | corte | SFX-PDC-ROAR (pico → corta) | — |
| B4-12 | S08 | 4 | Preto com cinza caindo → arcos vazios hoje | MOTION_GFX + ARCHIVE | — | — | dissolve 24f | silêncio + room tone | — |
| B4-13 | S09 | 4 | Quarto: cama de madeira, lamparina, silhueta deitada de costas | AI_IMAGE → PARALLAX | push lento | MG-LABEL; HUD local "COLLEGIUM AUGUSTALIUM" | corte | room tone, roar abafado | — |
| B4-14 | S10 | 5 | Imagem científica dos fragmentos vítreos em moldura de laboratório | ARCHIVE_DOC (AR-16) + MG-11 | macro push | crédito do artigo; "2020" | corte | SFX-LAB-HUM | Macro de obsidiana em IA (rotulada "ilustração") |
| B4-15 | S11 + silêncio | 4.5 | Close extremo do vidro negro; luz atravessa | ARCHIVE / AI macro | rotação lenta | — | — | silêncio total + 1 "ping" cristalino | — |
| B4-16 | S12 | 5 | Termômetro sobe a "> 510 °C" e despenca (curva aquece/resfria) | MOTION_GFX (MG-19) | — | "> 510 °C" | corte | SFX-HEAT-WHOOSH, estalo | — |
| B4-17 | S13 | 5 | Régua de Herculano "≈ 20 m" com prédio de 6 andares como escala | MOTION_GFX (MG-03 var.) | pull-out | "≈ 20 m" | corte | SFX-SUB-HIT | — |
| B4-18 | S13 "livros" | 4 | 4 fotos de 1 s: madeira carbonizada, alimento, tecido, papiro (o último segura 1,5 s) | ARCHIVE | push | — | cortes | SFX-UI-TICK ×4 | — |
| B4-19 | S14 | 3 | Papiro carbonizado em close, foco lento | ARCHIVE (AR-17) | rack focus | — | corte → preto | — | — |

### B5 — Dia 2 · O fim · 9:20–11:25 · M07 "Last Dawn" (pulso de batimento minimalista; **corta seco em B5-12**) · LUT-B5

| ID | Seg | Dur | Visual | Fonte | Câmera / Motion | Overlay / texto | Trans. | SFX | Plano B |
|---|---|---|---|---|---|---|---|---|---|
| B5-01 | S01 | 4 | Rota de Plínio desviando para Estábia | MAP_3D (MG-02) | — | HUD "ESTÁBIA · DIA 2 · ≈ 01:00" | corte | SFX-WHOOSH-MAP | 2D |
| B5-02 | S01 | 3 | Navio jogando, convés coberto de pomes, Plínio firme na proa | AI_VIDEO | handheld | MG-LABEL | corte | SFX-WAVES-ROUGH, SFX-PUMICE-ON-DECK | Still |
| B5-03 | S02 | 5 | Casa de Pomponiano: banho/jantar sereno à lamparina; caos pela janela | AI_IMAGE → PARALLAX | push lento | MG-LABEL | corte | SFX-WATER-POUR, talheres, roar abafado | — |
| B5-04 | S02 "ronco" | 3 | Porta do quarto, criados escutando no corredor, luz sob a porta | AI_IMAGE → PARALLAX | estático | — | corte | SFX-SNORE-DISTANT (muito sutil) | — |
| B5-05 | S03 | 4 | Pátio enchendo de pomes até a soleira (time-lapse) | AI_VIDEO | estático | MG-LABEL | corte | SFX-PUMICE-HEAVY | — |
| B5-06 | S04 | 4 | Grupo sai no escuro com travesseiros amarrados na cabeça, tochas | AI_VIDEO | lateral | HUD "≈ 06:00"; MG-LABEL | corte | SFX-FOOTSTEPS-PUMICE, vento | Still |
| B5-07 | S05 | 3 | Mar violento, ondas negras, cinza no ar | AI_VIDEO / STOCK | — | — | corte | SFX-WAVES-ROUGH (pico) | — |
| B5-08 | S06 | 7 | 3 stills (1 por frase): deitado sobre o pano; mão pedindo água; levantado por dois homens contra o brilho laranja. **A queda não é mostrada.** | AI_IMAGE → PARALLAX ×3 | push lento | MG-LABEL | cortes nas pausas | SFX-WAVES, vento, chiado de enxofre; batimento (música) | — |
| B5-09 | S07 | 3 | Tocha caída se apagando na areia, fumaça | AI_VIDEO | macro estático | MG-08 "PLÍNIO, O VELHO · c. 23–79 d.C." | — | SFX-TORCH-HISS | — |
| B5-10 | S08 | 4 | Mapa: primeiras correntes param perto dos muros de Pompeia | MAP_3D (MG-02) | top-down | HUD "POMPEIA · ≈ 07:00" | corte | SFX-PDC-ROAR-DISTANT | 2D |
| B5-11 | S09 | 6 | Amanhecer cinza: pessoas caminhando sobre pomes na altura das janelas; câmera segue alguém de costas | AI_VIDEO | tracking | MG-LABEL | corte | SFX-FOOTSTEPS-PUMICE, vento | Still |
| B5-12 | S10 | 3 | A pessoa para e olha para trás: parede de nuvem cinza no fim da rua. **Corte seco para preto em "muros".** | AI_VIDEO | estático | — | — | SFX-PDC-ROAR cresce → **CORTE TOTAL** | Still |
| B5-13 | silêncio | 2 | Preto; cinza quase imperceptível | MOTION_GFX | — | **HUD SOME** | — | só vento baixo | — |
| B5-14 | S11 | 6 | Molde de gesso real, P&B, plano aberto, luz lateral suave | ARCHIVE_PHOTO (AR-10 / AR-09) | push 1% lentíssimo | crédito | fade 24f | vento | Foto Sommer (AR-09) |
| B5-15 | S12 | 5 | Planta de Pompeia: área escavada clara, ~1/3 escuro | MOTION_GFX | — | "+1.150 VÍTIMAS ENCONTRADAS" · "≈ 1/3 NÃO ESCAVADO" | corte | room tone | — |
| B5-16 | S13 | 9 | Miseno na escuridão: tochas, silhuetas em fuga, Plínio segurando o braço da mãe; a frase latina surge branca sobre preto e some | AI_VIDEO + MG-07 | lento | HUD discreto "MISENO"; MG-LABEL | corte | SFX-CROWD-FLEE-DISTANT (sem gritos claros), vento | Still |
| B5-17 | S14 | 4 | Plínio, o Jovem, com ~45 anos, escrevendo à lamparina | AI_IMAGE → PARALLAX | push | MG-08 "c. 106 d.C."; MG-LABEL | corte | SFX-QUILL | — |
| B5-18 | S15 | 5 | Amanhecer cinza: planície de cinza onde havia cidade; montanha decapitada fumegando | AI_IMAGE → PARALLAX | pull-out lento | MG-LABEL | fade → preto 36f | silêncio, depois 1 nota | Gravura Hamilton/Fabris (AR-08) |

### B6 — O esquecimento · 11:25–12:40 · M08 "Plaster" (piano solo, entra em B6-02) · LUT-B6

| ID | Seg | Dur | Visual | Fonte | Câmera / Motion | Overlay / texto | Trans. | SFX | Plano B |
|---|---|---|---|---|---|---|---|---|---|
| B6-01 | S01 | 5 | Campos sobre colinas em pintura/gravura do séc. XVIII | ARCHIVE_PAINTING (AR-26) + PARALLAX | push | crédito | fade de preto | SFX-COUNTRYSIDE (sinos distantes, vento) | — |
| B6-02 | S02 | 6 | Mapa antigo: o canal de Fontana cruzando o contorno fantasma da cidade enterrada | MOTION_GFX | — | "CANAL DE FONTANA · c. 1594–1600" | corte | SFX-WATER-FLOW, papel | — |
| B6-03 | S03 | 7 | Timeline: 1709 → 1738 → 1748 → 1763, com gravuras de escavações | MOTION_GFX (MG-06) + ARCHIVE (AR-08) | travelling lateral | datas | corte | SFX-UI-TICK por data | — |
| B6-04 | S04 | 5 | Retrato de Giuseppe Fiorelli → escavação do séc. XIX | ARCHIVE_PHOTO (AR-25) | push | MG-08 "GIUSEPPE FIORELLI · 1863" | corte | obturador antigo sutil | — |
| B6-05 | S04 "vazios" | 4 | Corte transversal da camada de cinza com cavidade de silhueta humana abstrata | MOTION_GFX | lento | — | corte | room tone | — |
| B6-06 | S05–S06 | 7 | Gesso líquido preenche a cavidade (esquemático, branco) → foto do séc. XIX de um molde | MOTION_GFX + ARCHIVE (AR-09) | — | — | match cut | SFX-PLASTER-POUR, piano | — |
| B6-07 | S07 | 6 | 3 fotos de 2 s: mãos no rosto; corpo encolhido; o cão | ARCHIVE_PHOTO (AR-09, AR-32) | push 1% | créditos | dissolves 12f | silêncio + piano mínimo | Fotos Sommer |
| B6-08 | S08 | 6 | Vitrines de museu; etiquetas de papel surgem: "A MÃE", "AS IRMÃS", "O HOMEM RICO" | ARCHIVE + MG-11 | travelling | etiquetas | corte | SFX-PAPER-TAG | — |
| B6-09 | S09 | 2.5 | Etiqueta "A MÃE" em close, luz quente | MOTION_GFX | push | — | — | piano | — |
| B6-10 | S10 | 3 | Linha vermelha risca a etiqueta; piano para | MOTION_GFX (MG-11) | — | — | corte seco | SFX-MARKER-STRIKE; piano corta | — |

### B7 — O que você nunca viu · 12:40–14:55 · M09 "Signal" (eletrônico pulsante + cordas, sensação de descoberta) · LUT-B7

| ID | Seg | Dur | Visual | Fonte | Câmera / Motion | Overlay / texto | Trans. | SFX | Plano B |
|---|---|---|---|---|---|---|---|---|---|
| B7-01 | S01 | 5 | Laboratório de DNA antigo: luvas, pipeta, sala limpa | STOCK_VIDEO | — | MG-08 "2024 · Current Biology" | corte | SFX-LAB-HUM, clique de pipeta | Laboratório em IA |
| B7-02 | S01 | 3 | Hélice de DNA se formando sobre a foto do molde | MOTION_GFX (MG-11) | — | — | corte | SFX-UI-DATA | — |
| B7-03 | S02 | 7 | Dossiê "CASA DO BRACELETE DE OURO": molde à esquerda; ficha à direita "INTERPRETAÇÃO ANTIGA: mãe e filho" → carimbo "DNA: HOMEM ADULTO · SEM PARENTESCO" | ARCHIVE (AR-31) + MG-11 | push | carimbo na palavra "homem" | corte | SFX-STAMP, UI | Só MG com silhuetas |
| B7-04 | S03 | 5 | Dossiê 2: "PAR ABRAÇADO · mãe e filha? irmãs?" → "DNA: AO MENOS UM HOMEM" | ARCHIVE + MG-11 | — | carimbo | corte | SFX-STAMP | — |
| B7-05 | S04 | 5 | Mapa do Mediterrâneo: linhas de ancestralidade do leste convergindo para Pompeia | MAP_3D / MOTION_GFX | pull-out | "MEDITERRÂNEO ORIENTAL" | corte | SFX-WHOOSH-MAP | 2D |
| B7-06 | S05 | 5 | Molde em P&B; a luz muda de quente (séc. XIX) para fria (hoje) | ARCHIVE + grade animado | push | — | corte | música respira | — |
| B7-07 | S06 | 3 | Callback idêntico ao papiro de B4-19 | ARCHIVE | — | — | corte | SFX-UI-HIT soft | — |
| B7-08 | S07 | 6 | Reconstituição da Villa dos Papiros: peristilo, biblioteca com estantes de rolos | AI_IMAGE → PARALLAX | push | MG-LABEL; MG-08 "VILLA DOS PAPIROS · Herculano" | corte | SFX-ROOM-LIBRARY | — |
| B7-09 | S07 "carvão" | 4 | Papiros carbonizados reais; um fragmento esfarela | ARCHIVE (AR-17) + AI_VIDEO | macro | — | corte | SFX-CRUMBLE | — |
| B7-10 | S08 | 3 | Contador de anos "1752 → 2023" girando | MOTION_GFX (MG-06 var.) | — | — | corte | SFX-TICKS | — |
| B7-11 | S09 | 5 | Rolo fechado em 3D girando, fatiado por raios-X (camadas ciano translúcidas) | MOTION_GFX (MG-12) (+ AR-18 se licenciado) | órbita 3D | "VESUVIUS CHALLENGE · 2023" (tipografia própria, sem logo sem permissão) | corte | SFX-SCANNER-SWEEP | — |
| B7-12 | S10 | 5 | Monitor com UI fictícia destacando traços de tinta; silhueta de estudante em frente | AI_IMAGE / MG | push | MG-08 "ESTUDANTE · 21 anos"; MG-LABEL | corte | SFX-KEYBOARD, UI-DATA | Foto oficial licenciada |
| B7-13 | S10 "palavra" | 3 | Superfície "desenrolada" virtualmente; letras gregas acendem uma a uma | MOTION_GFX (MG-12) (+ AR-18) | push | — | corte | SFX-UI-REVEAL | — |
| B7-14 | S11 | 5.5 | ΠΟΡΦΥΡΑϹ em grande, brilho púrpura sutil → "PÚRPURA" | MOTION_GFX (MG-14) | estático | — | — | silêncio → 1 nota de sino | — |
| B7-15 | S12 | 5 | 15 colunas de texto acendendo; contador "2.000+ caracteres"; depois "2025 · título lido" | MOTION_GFX (MG-12) | pan | números | corte | SFX-UI-COUNT | — |
| B7-16 | S13 | 5 | Papiro carbonizado → coluna do Vesúvio (dissolve) | ARCHIVE + AI + MG-14 | — | "DESTRUIU." / "PRESERVOU." | dissolve | música sobe | — |
| B7-17 | S14 | 4 | Callback da inscrição a carvão "17 OUT" | ARCHIVE / MG | push | — | corte | SFX-CHARCOAL-SCRATCH | — |
| B7-18 | S14 "pistas" | 6 | Quadro de evidências: romãs, braseiro, roupa de lã, dólio de vinho, ligados por fios a "OUTONO?" | MOTION_GFX (MG-11) + ARCHIVE | travelling | — | corte | SFX-PIN, SFX-STRING | — |
| B7-19 | S14 "outubro" | 5 | Calendário romano: "24 AGO" desliza e dá lugar a "24 OUT?"; selo "DEBATE EM ABERTO" | MOTION_GFX | — | — | corte | SFX-UI-HIT | — |

### B8 — O vulcão hoje · 14:55–16:20 · M10 "Red Zone" (ambiente tenso → crescendo → um único pad no final) · LUT-B8

| ID | Seg | Dur | Visual | Fonte | Câmera / Motion | Overlay / texto | Trans. | SFX | Plano B |
|---|---|---|---|---|---|---|---|---|---|
| B8-01 | S01 | 4 | Drone sobre Nápoles hoje: prédios subindo até a base do vulcão | STOCK_VIDEO (AR-29) | avanço | — | corte | SFX-CITY-MODERN | Foto |
| B8-02 | S02 "1631" | 3.5 | Pintura/gravura da erupção de 1631 | ARCHIVE_PAINTING + PARALLAX | push | "1631" | corte | roar distante | — |
| B8-03 | S02 "1944" | 3.5 | Filme ou foto real da erupção de 1944 | ARCHIVE (AR-19 / AR-27) | — | "1944"; crédito USAAF | corte | projetor antigo sutil | Foto |
| B8-04 | S02 "bombardeiros" | 3 | B-25 cobertos de cinza | ARCHIVE_PHOTO (AR-20) | push | — | corte | SFX-METAL-CREAK | — |
| B8-05 | S03 | 4 | Sismógrafo moderno: linha calma; "1944 → HOJE: 80+ ANOS" | MOTION_GFX (MG-21) | — | — | corte | SFX-SEISMO, silêncio | — |
| B8-06 | S04 | 4 | Vesúvio visto da Estação Espacial | ARCHIVE_PHOTO (AR-22, NASA) | push lento | crédito NASA | corte | SFX-SUB-PULSE | Sentinel-2 |
| B8-07 | S05 | 7 | Zona vermelha (25 municípios) sobre satélite; "≈ 700.000" → anel "Nápoles: 3 mi+" | MAP_3D + MG-10 + MG-09 | pull-out | números | corte | SFX-UI-DATA, pulso | 2D |
| B8-08 | S06 | 5 | Relógio regressivo "72:00:00" correndo; rodovia congestionada ao fundo | MOTION_GFX + STOCK | — | "72 H" | corte | SFX-TRAFFIC, tick | — |
| B8-09 | S07 | 5 | Prédio histórico do Osservatorio Vesuviano → sala de monitoramento moderna | ARCHIVE (AR-28) + STOCK | — | MG-08 "OSSERVATORIO VESUVIANO · 1841" | corte | SFX-INSTRUMENT-BEEPS | — |
| B8-10 | S08 | 6 | Reuso do plano-âncora B1-11: Pompeia viva, sol, calma | AI_VIDEO (reuso) | — | MG-LABEL | corte | SFX-CITY-ROMAN-AMB baixo | — |
| B8-11 | S09 | 4 | Molde em P&B, luz suave | ARCHIVE (AR-09) | push 1% | — | corte | pad | — |
| B8-12 | S10 | 5 | A inscrição a carvão; câmera recua devagar | ARCHIVE / MG | pull-out | — | corte | SFX-WIND | — |
| B8-13 | S11 | 5 | Nápoles ao entardecer, gente comum na rua, Vesúvio calmo ao fundo | STOCK_VIDEO | estático | — | corte | SFX-CITY-EVENING, risadas distantes | — |
| B8-14 | S12 | 3 | Mesmo plano, tudo normal. **Corte seco para preto logo após "é."** | STOCK_VIDEO | estático | — | — | — | — |
| B8-15 | silêncio | 3 | Preto; um tremor sub (30 Hz) uma vez | BLACK | — | — | — | SFX-SUB-TREMOR | — |
| B8-16 | end card | 20 | Fundo de cinza animada, 2 slots de vídeo; créditos de fontes rolando discretamente | MOTION_GFX | — | end screen | — | pad final de M10 | — |

---

## 4. Planos-âncora e callbacks (consistência visual)

| Âncora | Aparece em | Regra |
|---|---|---|
| Rua de Pompeia (B1-11) | B1-11, B1-17, B3-22, B5-11, B8-10 | **Mesmo enquadramento, mesma seed/referência.** Só muda luz, céu e quantidade de pomes. Gere primeiro a versão "viva", depois derive as outras via edição de imagem (inpainting do céu e do chão) para manter a geometria idêntica. |
| Inscrição a carvão | B0-04/05, B7-17, B8-12 | Mesmo asset; em B8-12 o movimento é o inverso de B0 (recuo em vez de avanço). |
| Papiro carbonizado | B0-10, B4-19, B7-07, B7-09 | Mesmo asset AR-17. |
| Molde | B0-09, B5-14, B6-07, B7-03, B8-11 | Sempre P&B, sempre respeitoso. |
| Plínio, o Jovem | B3-08/09, B5-16, B5-17 | Character sheet obrigatória; idade 17 → ~45 em B5-17. |

## 5. Animatic (E11)

1. Gere stills **rascunho** (baixa resolução, 1 variação) para todos os shots `AI_*`; use placeholders cinza com o ID para `ARCHIVE_*` ainda não baixados e para motion graphics ainda não feitos (texto do overlay escrito no placeholder).
2. Monte no Remotion com a narração scratch e os cues musicais provisórios.
3. Exporte `03_breakdown/animatic/animatic_vN.mp4` (720p) e um PDF de contato com 1 frame por shot.
4. Revisão (G2): ritmo, clareza, densidade de motion por bloco, se o ápice em B5 funciona no silêncio, se nenhum bloco ficou monótono.
