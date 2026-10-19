# Pipeline de Produção de Vídeo com IA — "O Vesúvio de Pompeia da forma que você nunca viu"

Este conjunto de documentos descreve, de ponta a ponta, como produzir um documentário de YouTube profissional (estilo Magnates Media, dosado ao tema) **usando somente IA e agentes orquestrados**: da pesquisa histórica ao vídeo final narrado, editado, mixado e pronto para publicar.

> **Para a IA que vai executar:** você assume o papel do **Orquestrador (Showrunner)**. Estes documentos são suas instruções, seu roteiro já escrito e sua decupagem. Siga o DAG de `01`, instancie os agentes de `02`, respeite os gates. Onde estes documentos trouxerem um fato, **reconfira-o** (etapa E03/E07) antes de usar: o dossiê é um ponto de partida verificável, não uma verdade final.

---

## Ordem de leitura

| # | Documento | O que contém | Quem usa |
|---|---|---|---|
| 01 | [Arquitetura e orquestração](01-arquitetura-e-orquestracao.md) | Princípios, stack, estrutura de pastas, DAG de etapas, `project.json`, contratos JSON entre agentes, gates, retries | Orquestrador |
| 02 | [Catálogo de agentes](02-agentes.md) | 19 agentes (A00–A18): missão, prompt de sistema, critérios de aceite | Orquestrador → subagentes |
| 03 | [Pesquisa e fatos](03-pesquisa-e-fatos.md) | Ângulo editorial, banco de ~80 fatos com status e fonte, mitos, timeline histórica e timeline hora a hora, bibliografia | A01, A02, A03, A05 |
| 04 | [Roteiro](04-roteiro.md) | Conceito, beat sheet, Curva de Intensidade, mapa de open loops, **roteiro final completo** (~2.300 palavras, ~16 min) com marcações de voz | A05, A06, A07, A09 |
| 05 | [Decupagem](05-decupagem.md) | Regras de montagem, ritmo por bloco, **155 shots** com visual, fonte, câmera, overlay, transição, SFX e plano B | A09, A11–A16 |
| 06 | [Direção de arte e motion](06-direcao-de-arte-e-motion.md) | Conceito "Cinza e Brasa", tokens de design, color script por bloco, regras históricas, character sheets, **21 componentes de motion** com specs, esqueleto Remotion, mapas 3D | A08, A11, A13, A14 |
| 07 | [Assets e direitos](07-assets-e-direitos.md) | Política de licenças (incl. lei italiana de bens culturais), 38 assets de arquivo, fluxo de geração IA, **prompts por shot**, ética com vítimas | A10, A11, A12 |
| 08 | [Áudio](08-audio-narracao-trilha-sfx.md) | Casting e parâmetros de TTS, dicionário de pronúncia, alinhamento, cue sheet musical (M01–M10), biblioteca de SFX, momentos sonoros, mix e loudness | A07, A15 |
| 09 | [Montagem, render e QA](09-montagem-render-qa.md) | Algoritmo de montagem, regras de corte, specs de render, QA técnico (FFmpeg) e criativo, loop de correção, legendas | A16, A17 |
| 10 | [Metadados e publicação](10-metadados-e-publicacao.md) | Títulos, 3 thumbnails, descrição com capítulos e fontes, tags, Shorts, checklist de publicação | A18 |

> **Produto de software:** a pasta [`docs/construtor`](../construtor/README.md) especifica o **DocForja**, o programa que transforma tema + roteiro num Plano de Vídeo completo e depois produz o vídeo automaticamente. Onde estes documentos divergirem de `docs/construtor` (ex.: vídeo gerado por IA, API do Gemini, vários gates), vale `docs/construtor`.

---

## O vídeo em uma página

- **Tema:** O Vesúvio de Pompeia da forma que você nunca viu
- **Ângulo:** as últimas ~19 horas em tempo real (relógio na tela) + mitos desmontados + ciência de 2018–2025 + o risco de hoje. Estrutura circular: abre e fecha na inscrição a carvão de "17 de outubro".
- **Duração:** ~16–17 min · 4K · 24 fps · PT-BR (legendas PT-BR e EN)
- **Blocos:** B0 A data errada → B1 A montanha verde → B2 O aviso → B3 Dia 1: a coluna → B4 A noite: Herculano → B5 Dia 2: o fim → B6 O esquecimento → B7 O que você nunca viu → B8 O vulcão hoje
- **Assinaturas visuais:** HUD do relógio da erupção, mapas 3D da baía, régua de soterramento, documentos antigos com destaque animado, dossiês do DNA, scan dos papiros, paleta que vai do dourado à cinza com a brasa como fio condutor.
- **Assinatura sonora:** silêncios no ponto mais alto (a morte de Pompeia acontece no silêncio, não na música épica).

## Fluxo resumido

```
Brief → Pesquisa (A01+A02) → Fact-check (A03) → Beat sheet (A04) → Roteiro (A05) → Retenção (A06)
→ Fact-check do roteiro → [G1] → Narração scratch + Direção de arte → Decupagem com tempos reais
→ Animatic → [G2] → (paralelo) arquivo · stills IA · i2v/parallax · mapas 3D · motion · narração final · trilha · SFX
→ Montagem → Mix → Preview → QA (loop) → Legendas → Master → Metadados/Thumb/Shorts → [G3] → aprovação humana → publicação
```

## Definição de pronto

O vídeo está pronto quando: os três gates estão aprovados; o QA final não tem itens bloqueantes; todo fato na tela e na narração está verificado; todo asset tem licença registrada; o master está em −14 LUFS; e um humano aprovou explicitamente o pacote de publicação.

## Como adaptar para outro tema

Mantenha `01`, `02`, `06 §5` (biblioteca de motion), `08 §2/§6`, `09` e `10 §6` como estão: são o pipeline. Refaça `03`, `04`, `05`, `07 §2/§4` e os cues de `08 §4` para o novo tema, seguindo o mesmo formato. A Curva de Intensidade (`04 §3`) é sempre o primeiro artefato criativo a ser definido depois da pesquisa, porque todo o resto (ritmo, motion, música, som) deriva dela.
