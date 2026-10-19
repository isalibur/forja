# 06 — Direção de Arte e Motion Graphics

> **Para a IA executora:** o A08 (Diretor de Arte) produz `styleguide.json` a partir da seção 2; o A14 (Motion Designer) implementa os componentes da seção 5 no Remotion. Nada de cor, fonte ou easing "na mão": tudo sai dos tokens.

---

## 1. Conceito visual: "Cinza e Brasa"

- **Ideia:** o vídeo começa dourado e vivo e vai sendo literalmente coberto de cinza. A paleta perde saturação a cada hora do HUD. A única cor quente que sobrevive é a **brasa** (laranja), que vira o fio visual da destruição. No final (ciência e presente), entram cores frias e limpas: o olhar do século XXI.
- **Referências de linguagem (não copiar, absorver):** Magnates Media (documentos com destaque animado, recortes em papel, tipografia serifada grande, ritmo de revelação); LEMMiNO (minimalismo, preto, silêncio); Johnny Harris (mapas como personagem); documentários de museu (luz rasante em objetos).
- **Dosagem:** motion graphics servem para três coisas — **orientar** (onde/quando: HUD, mapas), **provar** (documentos, dados, dossiês) e **dimensionar** (régua, comparadores, termômetro). Se um MG não faz nenhuma das três, ele sai.

---

## 2. Tokens (`styleguide.json`)

```json
{
  "color": {
    "ink":        "#0E0E10",
    "basalt":     "#1C1C21",
    "ash":        "#6E6A66",
    "ashLight":   "#B9B3AB",
    "parchment":  "#E9DFC9",
    "bone":       "#F4F0E8",
    "pompeiiRed": "#9E2B20",
    "ochre":      "#C08A3E",
    "ember":      "#FF6A2B",
    "emberDeep":  "#C2410C",
    "scienceCyan":"#5CC8D6",
    "dataRed":    "#E5484D",
    "purpleScroll":"#7B4FA0"
  },
  "font": {
    "title":  {"family": "Cinzel", "weight": 600, "tracking": "0.08em", "case": "upper"},
    "quote":  {"family": "Cormorant Garamond", "weight": 500, "style": "italic"},
    "body":   {"family": "Inter", "weight": 500},
    "data":   {"family": "IBM Plex Mono", "weight": 500, "tracking": "0.04em"}
  },
  "size4k": {
    "title": 220, "h1": 140, "h2": 96, "body": 64, "label": 48, "hud": 52, "credit": 34
  },
  "safeArea": {"x": 0.05, "y": 0.07, "title": 0.10},
  "easing": {
    "in":  [0.16, 1, 0.3, 1],
    "out": [0.7, 0, 0.84, 0],
    "move":[0.65, 0, 0.35, 1]
  },
  "durationFrames": {"enter": 14, "exit": 10, "stagger": 3},
  "texture": {
    "grain": {"opacity": 0.06, "size": "35mm", "animated": true},
    "vignette": {"amount": 0.22, "feather": 0.6},
    "dust": {"opacity": 0.04, "onlyBlocks": ["B6"]}
  },
  "label": {
    "aiReconstruction": "RECONSTITUIÇÃO ARTÍSTICA",
    "realOtherVolcano": "IMAGEM REAL · OUTRO VULCÃO",
    "position": "bottom-left",
    "opacity": 0.6
  }
}
```

Todas as fontes acima são livres (SIL Open Font License) e disponíveis no Google Fonts → podem ser embutidas no render sem custo de licença. Registrar em `licenses.csv` mesmo assim.

**Contraste:** texto `bone` sobre `ink`/`basalt` (≥ 12:1); texto sobre imagem sempre com faixa ou sombra suave (`0 0 40px rgba(0,0,0,.6)`), contraste ≥ 4,5:1.

---

## 3. Color script (grade por bloco)

Aplicar como LUT + ajustes no Remotion (filtro CSS/WebGL) ou pré-grade com FFmpeg (`lut3d`). Valores relativos a um grade neutro.

| LUT | Bloco | Temperatura | Saturação | Contraste | Sombras / Altas | Nota |
|---|---|---|---|---|---|---|
| LUT-B0 "carvão" | B0 | neutra | −40% | alto | pretos esmagados; altas quentes | Luz rasante, quase P&B com calor |
| LUT-B1 "dourado" | B1 | +600 K | +5% | médio | sombras ocre, altas cremosas | "Campania felix" — vida |
| LUT-B2 "sombra" | B2 | +200 K | −10% | médio | sombras esfriando | O dourado começa a apagar |
| LUT-B3 progressivo | B3 | +400 K → −300 K | −5% → −45% | médio → alto | brasa preservada (keyer de laranja) | Interpolar pela hora do HUD |
| LUT-B4 "noite" | B4 | −800 K | −50% | alto | azul-petróleo nas sombras, brasa nas altas | Único calor = fogo |
| LUT-B5 "alvorada de cinza" | B5 | −200 K | −65% | médio-baixo | lavado, leitoso | Ar cheio de cinza |
| LUT-B6 "arquivo" | B6 | +300 K | −70% (sépia) | baixo | papel; grão 2× | Memória, séc. XIX |
| LUT-B7 "laboratório" | B7 | −400 K | −20% | médio | acentos ciano | Olhar científico |
| LUT-B8 "contemporâneo" | B8 | −200 K | 0% | médio | limpo, grão 0,5× | O presente, digital |

> Fotos de arquivo P&B (moldes, 1944) **não** recebem LUT de cor — apenas ajuste de níveis e o grão global.

---

## 4. Direção de reconstituição (para A11 / A12)

### 4.1 Sufixo de estilo (anexar a TODO prompt de imagem)

```
cinematic historical reconstruction, Roman Campania 79 AD, photorealistic, 35mm film still,
anamorphic lens, natural volumetric light, subtle film grain, muted earthy palette with
pompeian red and ochre accents, historically accurate Roman architecture and clothing,
no text, no modern objects, 16:9
```

Para B4–B5 acrescente: `night or ash-darkened sky, ember-orange light as the only warm source, falling ash particles`.

### 4.2 Regras de coerência histórica (checklist do A17)

- Vesúvio de **cume único** e encostas verdes antes da erupção. Nada do cone moderno duplo.
- **Sem lava** escorrendo nas cidades.
- Roupas: túnicas de lã/linho em tons naturais; toga só em contexto formal; mulheres com *stola*/*palla*; calçados de couro. Nada de capuzes medievais, nada de armaduras de legionário em civis.
- Arquitetura: casas de átrio, telhas de terracota, colunas estucadas, afrescos vermelho/ocre/preto, ruas de basalto com pedras de travessia; janelas pequenas sem vidro.
- Navios: quadrirremes/liburnas com remos e vela quadrada; nada de caravelas.
- Escrita: tabuinhas de cera, rolos; **nada de livros encadernados** (códices) em 79 d.C.
- Iluminação noturna: lamparinas de óleo e tochas.
- Pessoas escravizadas retratadas com dignidade, sem caricatura.

### 4.3 Character sheets

| Personagem | Descrição para referência | Uso |
|---|---|---|
| Plínio, o Jovem (17) | Jovem romano magro, cabelo escuro curto, sem barba, olhar atento, túnica clara de boa qualidade | B3-08/09, B5-16 |
| Plínio, o Jovem (~45) | O mesmo rosto envelhecido, cabelo grisalho nas têmporas, toga, à mesa de escrita | B5-17 |
| Plínio, o Velho (56) | Homem corpulento, cabelo grisalho curto, rosto largo e decidido, túnica + capa militar de comando | B3-13/15, B5-02/03/08 |
| Rectina | Mulher romana de ~40, aristocrática, *palla* escura, expressão de urgência | B3-17 |
| Habitantes (genéricos) | 6 rostos variados (idades, origens mediterrâneas diversas — coerente com o DNA de 2024) | B1, B3 |

Geração: 1 imagem "mestre" por personagem (frente, luz neutra) → variações com referência de personagem / LoRA treinada nas variações aprovadas. Não há retrato autêntico de nenhum dos Plínios: a narração nunca diz "este era o rosto dele"; o selo de reconstituição cobre isso.

---

## 5. Biblioteca de motion graphics (componentes Remotion)

Convenções para todos:
- Props sempre tipadas; tempos em frames (24 fps); `syncFrame` = frame da palavra-âncora vindo de `vo_words.json`.
- Entrada com `easing.in` em `durationFrames.enter`; saída com `easing.out` em `durationFrames.exit`.
- Cada componente tem som próprio sugerido (o A15 decide o volume final).

| ID | Componente | Função | Onde |
|---|---|---|---|
| MG-01 | `HudClock` | Orientar no tempo/espaço | B0 teaser; B3–B5 |
| MG-02 | `Map3D` | Orientar no espaço | B3, B4, B5, B7 |
| MG-03 | `DepthGauge` | Dimensionar (pomes / soterramento) | B3, B4 |
| MG-04 | `ScaleCompare` | Dimensionar (altura da coluna) | B3 |
| MG-05 | `CollapseExplainer` | Explicar a física | B4 |
| MG-06 | `HistoryTimeline` | Orientar na história | B6, B7 |
| MG-07 | `SourceDocument` | Provar (fonte antiga) | B0, B1, B3, B5 |
| MG-08 | `LowerThird` | Identificar pessoa/lugar | todos |
| MG-09 | `CounterStat` | Dimensionar (números) | B0, B1, B4, B5, B8 |
| MG-10 | `RedZoneMap` | Dimensionar o risco atual | B0, B8 |
| MG-11 | `CaseFile` | Provar / revelar (dossiê) | B0, B4, B6, B7 |
| MG-12 | `ScrollScan` | Explicar a leitura dos papiros | B0, B7 |
| MG-13 | `TitleCard` | Título | B0 |
| MG-14 | `KineticWord` | Enfatizar frase-chave | B0, B1, B3, B7 |
| MG-15 | `FilmTexture` | Unidade estética | global |
| MG-16 | `Parallax25D` | Dar vida a stills | global |
| MG-17 | `WindFlow` | Explicar direção do vento | B3 |
| MG-18 | `SplitCompare` | Comparar | B1, B3 |
| MG-19 | `Thermometer` | Dimensionar temperatura | B4 |
| MG-20 | `EarthZoom` | Zoom do espaço até o local | (reserva / Shorts) |
| MG-21 | `Seismograph` | Mostrar tremores | B2, B8 |
| MG-LABEL | `SourceLabel` | Rotular IA / creditar arquivo | global |

### Especificações detalhadas

**MG-01 `HudClock`** — o relógio da erupção, assinatura visual do vídeo.
- Layout: canto superior esquerdo dentro da safe area. Três linhas em `font.data`: `DIA 1` (label, `ash`), `≈ 13:00` (hud, `bone`), `POMPEIA` (label, `ember`). Fina barra horizontal abaixo = progresso da erupção (0% em 13:00 do Dia 1 → 100% às ~08:00 do Dia 2).
- Props: `{ day: 1|2, time: "13:00", place: string, progress: 0..1, approx: true }`.
- Transição de hora: dígitos rolam verticalmente (tipo flip, 8 frames por dígito) com tick sonoro; ao mudar de local, a palavra antiga desliza para cima e a nova entra (stagger 3f por letra).
- Estados especiais: em B5-13 o HUD **desaparece** (opacidade 1 → 0 em 6 frames, sem easing suave — é um "apagão"). Em B5-16 volta com 50% de opacidade.
- Som: SFX-UI-TICK (−28 dB) por dígito; SFX-UI-LOCATION (−24 dB) ao trocar local.

**MG-02 `Map3D`** — renders do A13 (Blender) + camada de labels no Remotion.
- Passes: `terrain.exr` (terreno escurecido, luz rasante 15°), `water`, `data` (pluma, correntes, rotas) e `labels` gerados no Remotion para nitidez.
- Labels: pinos dourados (`ochre`) + nome em `font.data`; distância em tracejado `bone` 60%.
- Dados: pluma em cinza translúcido; correntes piroclásticas em `ember` → `emberDeep` com borda difusa; rota de navio em linha `bone` com cabeça de seta.
- Câmera: voos de 3–5 s com `easing.move`; sempre terminam parados ≥ 12 frames antes do corte.
- Selo obrigatório: "LINHA DE COSTA APROXIMADA DE 79 d.C." quando a costa antiga for mostrada.

**MG-03 `DepthGauge`** — régua de soterramento.
- Régua vertical à direita do quadro com marcas a cada 0,5 m; silhueta humana de 1,70 m à esquerda da régua (traço `bone`, preenchimento 0).
- Preenchimento sobe com textura de pomes (imagem tileável) em `ashLight`; o número atual em `font.data` acompanha o topo.
- Props: `{ from: 0, to: 2.8, unit: "m", syncMarks: [{value: 0.5, frame}, {value: 1, frame}], human: true, building: false }`. Variante `building: true` (B4-17) troca a silhueta por um prédio de 6 andares para a escala de 20 m.
- Som: tick por marca; ao cobrir a cabeça da silhueta, SFX-SUB-HIT.

**MG-04 `ScaleCompare`** — Everest (8,8 km) / avião (≈ 11 km) / coluna (26–33 km).
- Câmera virtual sobe pela coluna; ícones aparecem nas altitudes reais. A coluna é mostrada como **faixa** de 26 a 33 km (gradiente com borda difusa), não como número único — reflete a incerteza.
- Som: SFX-RISER sincronizado com a subida; tick em cada ícone.

**MG-05 `CollapseExplainer`** — corte transversal estilizado (2D, traço limpo, fundo `basalt`).
- 4 estados (≈ 2 s cada): (1) coluna sustentada por convecção (setas para cima); (2) carga de material aumenta (partículas mais densas); (3) colapso (a coluna "dobra"); (4) corrente desce a encosta (massa `ember` avançando), com velocímetro pequeno.
- Rótulos curtos, nunca mais de 3 palavras na tela ao mesmo tempo.

**MG-06 `HistoryTimeline`** — linha horizontal com marcadores; câmera faz travelling lateral; cada data acende em `ochre` com tick; imagens de arquivo surgem como "fotos penduradas" acima da linha.

**MG-07 `SourceDocument`** — a assinatura "Magnates": a fonte primária vira objeto.
- Fundo: textura de pergaminho/papiro (`parchment`) com sombra e leve curvatura 3D.
- Texto latino em `font.quote`; a frase-alvo recebe **realce animado** (marca-texto `ochre` 35% passando da esquerda para a direita em sync com a narração) e a tradução própria entra embaixo em `font.body`.
- Referência sempre visível no rodapé do documento: "Plínio, o Jovem, Cartas 6.16".
- Variantes: `book` (B0-07, página de livro moderno genérico), `stone` (B3-20, inscrição gravada), `darkness` (B5-16, texto branco sobre preto, sem papel).

**MG-08 `LowerThird`** — barra fina `ember` (4 px) + nome em `font.title` + descrição em `font.data`. Entra deslizando 40 px com fade; permanece ≥ 2,5 s; nunca dois ao mesmo tempo.

**MG-09 `CounterStat`** — número contando de 0 até o valor em 18–30 frames, `easing.in`; "≈" e "+" estáticos; asterisco para estimativas com nota "*estimativa" no rodapé.

**MG-10 `RedZoneMap`** — polígono da zona vermelha (dados oficiais da Protezione Civile — limites dos 25 municípios) em `dataRed` 35% com borda 100%; pulsa 1× ao entrar; anel externo para a região metropolitana.

**MG-11 `CaseFile`** — dossiê investigativo: foto do molde presa por clipe numa ficha; campos "INTERPRETAÇÃO ANTIGA" / "O QUE O DNA MOSTROU"; carimbo animado (escala 1,3 → 1 em 6 frames com SFX-STAMP); fios vermelhos ligando evidências (B7-18). Variante "etiqueta de museu" (B6-08/10) com linha vermelha que risca.

**MG-12 `ScrollScan`** — rolo 3D (cilindro com textura carbonizada) girando; planos de corte ciano atravessam; depois a superfície "desenrola" em plano com letras gregas acendendo uma a uma. Se houver licença das imagens reais do Vesuvius Challenge, compor a imagem real da tinta detectada sobre o plano desenrolado; senão, recriação gráfica rotulada.

**MG-13 `TitleCard`** — "VESÚVIO" em `font.title` gigante, letras surgindo de brasa (máscara com ruído animado `ember` → `bone`); subtítulo "AS ÚLTIMAS HORAS DE POMPEIA" em `font.data`; cinza caindo na frente (partículas). 4 s.

**MG-14 `KineticWord`** — uma palavra/frase grande centralizada; entrada por tracking (0.3em → 0.08em) + fade; variantes: `strike` (risco vermelho), `charcoal` (traço de carvão desenhado), `greek` (B7-14, brilho `purpleScroll`).

**MG-15 `FilmTexture`** — grão animado global (seed por frame), vinheta, poeira só em B6, light leaks quentes muito raros (máx. 3 no vídeo, em B1). Desligar grão pela metade em B8.

**MG-16 `Parallax25D`** — recebe still + depth map (Depth Anything V2); separa em 3–5 camadas; câmera virtual com deslocamento ≤ 6% da largura; zoom ≤ 8%; preenchimento de bordas por outpainting prévio. Para fotos de vítimas: deslocamento ≤ 1,5%.

**MG-17 `WindFlow`** — partículas/linhas de fluxo sobre o mapa indo para SE; seta grande "VENTO" com rótulo.

**MG-18 `SplitCompare`** — divisória vertical que desliza da esquerda para o centro; rótulos no topo de cada metade; opcional: traço de contorno desenhado sobre as duas imagens (B1-06).

**MG-19 `Thermometer`** — barra vertical com escala em °C; sobe com tom `ember`; na variante "curva" (B4-16) desenha um gráfico tempo × temperatura: pico > 510 °C e queda rápida.

**MG-20 `EarthZoom`** — do globo (textura NASA Blue Marble, domínio público) até a baía; reserva para Shorts.

**MG-21 `Seismograph`** — tambor de papel com agulha; linha calma → oscilação; versão moderna digital em B8.

**MG-LABEL `SourceLabel`** — canto inferior esquerdo: "RECONSTITUIÇÃO ARTÍSTICA" (`font.data`, `credit`, 60%); canto inferior direito: crédito do arquivo. Nunca animam: entram e saem com o shot.

---

## 6. Esqueleto Remotion (referência para o A14)

```tsx
// src/components/HudClock.tsx
import {AbsoluteFill, interpolate, useCurrentFrame, Easing} from 'remotion';
import {tokens} from '../styleguide';

type Props = {day: 1 | 2; time: string; place: string; progress: number; visible?: boolean};

export const HudClock: React.FC<Props> = ({day, time, place, progress, visible = true}) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [0, tokens.durationFrames.enter], [0, 1], {
    easing: Easing.bezier(...tokens.easing.in),
    extrapolateRight: 'clamp',
  });
  const opacity = visible ? enter : 0;
  return (
    <AbsoluteFill style={{padding: `${tokens.safeArea.y * 100}% ${tokens.safeArea.x * 100}%`}}>
      <div style={{opacity, fontFamily: tokens.font.data.family, transform: `translateY(${(1 - enter) * 20}px)`}}>
        <div style={{color: tokens.color.ash, fontSize: tokens.size4k.label}}>DIA {day}</div>
        <div style={{color: tokens.color.bone, fontSize: tokens.size4k.hud}}>≈ {time}</div>
        <div style={{color: tokens.color.ember, fontSize: tokens.size4k.label}}>{place}</div>
        <div style={{width: 420, height: 4, background: tokens.color.basalt, marginTop: 16}}>
          <div style={{width: `${progress * 100}%`, height: '100%', background: tokens.color.ember}} />
        </div>
      </div>
    </AbsoluteFill>
  );
};
```

```tsx
// src/Video.tsx — a timeline vem de 08_edit/timeline.json
import {AbsoluteFill, Sequence, OffthreadVideo, Img, Audio, staticFile} from 'remotion';
import timeline from '../../08_edit/timeline.json';
import {registry} from './components/registry'; // { HudClock, DepthGauge, ... }

export const Video: React.FC = () => (
  <AbsoluteFill style={{background: '#0E0E10'}}>
    {timeline.tracks.V1.map((c) => (
      <Sequence key={c.shot} from={c.from} durationInFrames={c.dur}>
        {c.src.endsWith('.mp4')
          ? <OffthreadVideo src={staticFile(c.src)} startFrom={c.trim_in} muted />
          : <Img src={staticFile(c.src)} />}
      </Sequence>
    ))}
    {timeline.tracks.V2_overlays.map((o, i) => {
      const C = registry[o.component];
      return <Sequence key={i} from={o.from} durationInFrames={o.dur}><C {...o.props} /></Sequence>;
    })}
    {timeline.tracks.A1_vo.map((a, i) => <Sequence key={i} from={a.from}><Audio src={staticFile(a.src)} /></Sequence>)}
    {/* A2–A4: usar o mix final em um único <Audio> quando o A15 entregar o mix; stems só no preview */}
  </AbsoluteFill>
);
```

> Na versão final, o áudio entra como **um único arquivo mixado** (`06_audio/mix/final_mix.wav`), não como faixas separadas no Remotion — a mixagem é responsabilidade do A15 fora do Remotion.

---

## 7. Mapas 3D (detalhes para o A13)

1. **Dados:** DEM TINITALY (INGV, 10 m, CC BY 4.0) recortado na Baía de Nápoles (≈ 40,55–40,95 N; 13,95–14,65 E). Textura: Sentinel-2 L2A (Copernicus, livre com atribuição), dessaturada.
2. **Vesúvio de 79 d.C.:** duplicar o DEM e esculpir: remover o Gran Cono moderno e reconstruir um cume único aproximado sobre a borda do Somma. Rotular "PERFIL APROXIMADO".
3. **Costa antiga:** deslocar a linha de costa para o interior perto de Herculano e Pompeia (a costa avançou com os depósitos). Rotular "LINHA DE COSTA APROXIMADA".
4. **Estilo:** terreno `basalt`, relevo com luz rasante 15° vindo de oeste, névoa atmosférica azulada ao longe, mar `ink` com leve reflexo.
5. **Sequências:** (a) Vesúvio → Miseno com distância; (b) vento e pluma para SE; (c) Pompeia → Herculano; (d) rota de Plínio Miseno → costa → Estábia; (e) correntes piroclásticas radiais; (f) zona vermelha atual (terreno moderno, sem esculpir).
6. **Saída:** PNG 16-bit ou EXR, 3840×2160, 24 fps, passes separados; câmera exportada em JSON para o Remotion posicionar labels por projeção.
