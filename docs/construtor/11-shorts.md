# 11 — Shorts (vertical 9:16)

Dois tipos, mesmo motor (plano → verificador → produção), mesmo kit em versão vertical.

| | **Short derivado ("âncora")** | **Short avulso** |
|---|---|---|
| Origem | Um vídeo longo já planejado/produzido | Um tema e um objetivo escolhidos por você |
| Objetivo | Levar o espectador ao vídeo longo e ao canal | Vendas, promoção do canal, engajamento, educação, anúncio, bastidores… |
| Roteiro | Trechos da narração do longo + pequenas frases-ponte | Seu roteiro **ou** gerado a partir de uma fórmula |
| Imagens | Reaproveita os ativos do longo | Suas mídias, pasta global, pesquisa, geradas, clipes seus |
| Destinos | YouTube Shorts (+ Reels) | YouTube Shorts, Instagram Reels (e onde mais você quiser postar) |
| Tempo de produção | ~5–15 min por short | ~10–25 min por short |

---

## 1. Regras comuns a todo short

- **Formato:** 1080×1920, 24 ou 30 fps, 15–60 s (até 90 s nos Reels).
- **Gancho em ≤ 2 s:** primeira imagem forte + texto grande na tela + primeira frase falada já com a promessa.
- **Legendas palavra a palavra queimadas** (componente de legendas do kit, via `@remotion/captions`), sempre — muita gente assiste sem som.
- **Zonas seguras das plataformas:** nada importante nos 15% de cima, nos 25% de baixo e na faixa de 12% da direita (ícones e legenda do app). O verificador confere (regra DS1).
- **Ritmo:** troca visual a cada 1,5–3 s; nenhum quadro parado > 2,5 s.
- **Fim que convida a repetir (loop):** a última imagem/frase conversa com a primeira quando possível.
- **CTA claro** no fim (e opcionalmente no meio): um só por short.
- **Multi-idioma:** igual ao longo (narração, textos e legendas por idioma).

## 2. Kit vertical

Todo template do catálogo (`02 §3`) tem layout `9x16` além do `16x9` (textos maiores, sujeito centralizado, fundo desfocado quando a imagem é horizontal). Templates exclusivos de short:

| ID | Template | Uso |
|---|---|---|
| V01 | `GanchoTexto` | Frase de gancho gigante sobre imagem escurecida, entrando palavra a palavra |
| V02 | `ImagemLegendada` | Imagem (Ken Burns/parallax) com legenda dinâmica em destaque |
| V03 | `ItemLista` | "1 · 2 · 3" com número grande e frase curta |
| V04 | `Oferta` | Produto/serviço: imagem, benefício, condição documentada sem preço, selo (ex.: "só até sexta", se verdadeiro) |
| V05 | `AntesDepois` | Comparação vertical (cima/baixo) |
| V06 | `Pergunta` | Pergunta para comentários com opções (A/B) |
| V07 | `CTA` | Inscreva-se / vídeo completo / link na bio / comente / salve — com ícone animado |
| V08 | `Marca` | Logo/assinatura do canal (≤ 1 s) |
| V09 | `ClipeProprio` | Um clipe de vídeo seu (ex.: você falando, demonstração do produto), recortado e legendado |
| V10 | `Prova` | Depoimento, número de resultado, print — **só material real fornecido por você** |
| V11 | `CartaoProduto` | Produto de afiliado: imagem, nome, até 3 benefícios, condição real documentada (sem preço), selo da loja em texto |

## 3. Short derivado ("âncora do canal")

### 3.1 Escolha dos momentos

Ao terminar o plano do longo (ou depois da produção), o sistema propõe **3–5 candidatos** a short. Pontuação de cada trecho contínuo de 20–55 s:

| Critério | Peso |
|---|---|
| Começa numa batida `gancho`, `revelação` ou `dado` forte | 30% |
| Faz sentido sozinho (entende-se sem o resto do vídeo) | 25% |
| Abre uma curiosidade que o vídeo longo responde (para levar até ele) | 25% |
| Tem imagens fortes e verticalizáveis | 10% |
| Duração e ritmo dentro da faixa | 10% |

Você escolhe na tela "Shorts" (ou deixa o sistema fazer os 3 melhores).

**Exemplos no Vesúvio:** "O cérebro que virou vidro" (B4) · "A IA que leu um livro de 2.000 anos" (B7) · "Pompeia não morreu em agosto" (B0 + B7).

### 3.2 Estrutura

```
0–2 s    GANCHO     frase mais forte do trecho (pode vir de outro ponto do mesmo trecho) + V01
2–40 s   CORPO      narração original do longo, reenquadrada em 9:16
final    PONTE+CTA  frase-ponte curta ("O resto dessa história está no vídeo completo.") + V07
```

- **As palavras do seu roteiro não são reescritas.** O gancho é um recorte de frase do próprio trecho; só a frase-ponte final é nova. O sistema propõe 3 opções de frase-ponte e você aprova (ou escreve a sua).
- Narração: reaproveita o áudio do longo; frases-ponte geradas com a **mesma voz** (ou gravadas por você).
- Imagens: os mesmos ativos, reenquadrados pelo ponto de foco do plano (ou fundo desfocado + imagem inteira).
- Metadados apontam para o longo: título curioso, descrição com o link/título do longo, comentário fixado e instrução para usar o recurso de "vídeo relacionado" do YouTube Shorts apontando para o longo.

## 4. Short avulso

### 4.1 Entrada

| Campo | Opções |
|---|---|
| Tema | texto livre |
| Objetivo | `vendas` · `promocao_canal` · `engajamento` · `educativo` · `anuncio` · `bastidores` · `autoridade` · `outro` |
| Fórmula | escolhida pelo sistema conforme o objetivo, ou por você (§4.2) |
| Roteiro | **seu** (colado) · **gerado** pela fórmula (LLM `structured`, revisável) · **Gemini manual** (o sistema exporta o pedido pronto) |
| Duração | 15 · 30 · 45 · 60 · 90 s |
| Narração | TTS · narração pronta · **sem narração** (só texto na tela + música) |
| Mídias | suas (pasta `manual`), pasta global, pesquisa, geradas, clipes seus |
| CTA | inscrever-se · vídeo do canal (qual) · link na bio · comentar · salvar/compartilhar · comprar (link/oferta) |
| Plataformas | YouTube Shorts · Instagram Reels (metadados específicos por plataforma) |
| Kit | o do canal ou um kit próprio de shorts/campanha |
| Lote | opcional: uma planilha (CSV) com vários temas → uma campanha de shorts de uma vez |

### 4.2 Fórmulas (catálogo, editável em `global/formulas_shorts/`)

| Fórmula | Estrutura | Objetivos típicos |
|---|---|---|
| `gancho_problema_solucao` | gancho → dor → solução → CTA | vendas, educativo |
| `lista_3` | gancho → item 1 → item 2 → item 3 → CTA | educativo, engajamento |
| `mito_verdade` | "Você acredita que…?" → mito → verdade → CTA | educativo, promoção do canal |
| `curiosidade_1_fato` | fato surpreendente → explicação curta → "segue para mais" | promoção do canal |
| `pergunta_comentarios` | provocação → 2 opções → "comenta A ou B" | engajamento |
| `teaser_video` | cena forte → pergunta aberta → "vídeo completo no canal" | promoção do canal |
| `oferta` | gancho de benefício → prova real → oferta/condição → urgência verdadeira → CTA de compra | vendas |
| `antes_depois` | antes → processo → depois → CTA | vendas, autoridade |
| `bastidores` | "como fazemos X" → 3 cenas → CTA | bastidores, autoridade |
| `anuncio` | novidade → o que muda → quando → CTA | anúncio |
| `produto_afiliado` | gancho do problema → produto em uso → 3 benefícios → convite para conferir a oferta atual no link, sem preço → CTA "link na bio/comentário" | afiliados (ver `15 §2.1`) |

Cada fórmula define: sequência de templates V/T, duração de cada parte, limites de texto, onde entra o CTA e o que o verificador exige.

### 4.3 Regras de honestidade (vendas e prova)

- **Afiliados:** imagens só as permitidas pelo programa de afiliados ou fotos suas; não incluir preço ou desconto numérico na planilha, narração, vídeo, legendas ou textos de publicação. Falar da oferta de forma genérica e encaminhar às condições atuais pelo link. Aviso de publicidade/link de afiliado nos textos de publicação; URL nos metadados e na agenda, nunca queimado no vídeo (`15 §2.1`).
- Nada de depoimentos, números de resultado, prints ou avaliações inventados: `V10 Prova` só aceita material que **você** forneceu.
- Urgência só se for verdadeira (o sistema pede a data/condição real).
- Se for publicidade/parceria paga, o metadado inclui a marcação de conteúdo pago e o lembrete de ativar o recurso da plataforma.
- Imagens geradas de produtos reais não substituem fotos reais do produto em ofertas.

## 5. Verificador de shorts (regras extras)

| # | Regra |
|---|---|
| DS1 | Texto e elementos importantes fora das zonas da interface das plataformas |
| DS2 | Gancho visual + textual em ≤ 2 s |
| DS3 | Troca visual a cada ≤ 3 s |
| DS4 | Legendas presentes do início ao fim (se houver fala) |
| DS5 | Exatamente 1 CTA principal |
| DS6 | Texto na tela ≤ 6 palavras por vez, legível em celular |
| DS7 | Duração dentro do alvo ±2 s |
| DS8 | Short derivado: frase-ponte aprovada; metadado aponta para o longo |
| DS9 | Áudio: −14 LUFS; música mais presente que no longo, sem cobrir a voz |

## 6. Saída de cada short

```
05_saida/<idioma>/shorts/S01-cerebro-de-vidro/
├── video.mp4                 # 1080×1920
├── capa.jpg                  # quadro de capa sugerido (com texto) para Reels/Shorts
├── legendas.srt
└── metadados/
    ├── metadados.json
    ├── titulos.md            # 5–8 opções otimizadas para Shorts (≤ 40 caracteres)
    ├── youtube.md            # título, descrição, hashtags, vídeo relacionado a vincular
    ├── instagram.md          # legenda (com gancho na 1ª linha), hashtags, sugestão de capa, texto alternativo
    └── comentario_fixado.md
```
Formato completo dos metadados em `13`.
