# 10 — Roteiro e Prompt para o Gemini (chat)

> O roteiro é escrito por você no chat do Gemini 4 Argon. O DocForja aceita **qualquer texto** (ele segmenta sozinho), mas se o roteiro vier no formato abaixo, o plano fica mais preciso: você controla blocos, intensidade, pausas e pistas visuais, e o sistema não precisa adivinhar.

---

## 1. Formato recomendado

```markdown
# <Título do vídeo>

## B0 — <Nome do bloco> · intensidade 5→8

**B0-S01** {quase sussurrado, íntimo}
Numa parede de Pompeia, alguém pegou um pedaço de carvão… [PAUSA-C] e escreveu uma data.

**B0-S02** {lento, preciso}
Dezesseis dias antes das calendas de novembro. [PAUSA-M] Ou seja: *dezessete de outubro*.
>>VISUAL: a inscrição sendo escrita traço a traço<<

[SILÊNCIO 1 s]

## B1 — <Nome do bloco> · intensidade 3→4
...

## FONTES
- Plínio, o Jovem, Cartas 6.16 e 6.20
- ...
```

| Marcação | Significado | Obrigatória? |
|---|---|---|
| `## B<n> — Nome · intensidade a→b` | Bloco/capítulo (vira capítulo na descrição) e a energia de 1 a 10 | Recomendada |
| `**B<n>-S<nn>** {direção}` | Segmento de narração (1–3 frases) e como falar | Recomendada |
| `[PAUSA-C]` `[PAUSA-M]` `[PAUSA-L]` | Pausa curta (0,4 s), média (0,75 s), longa (1,5 s) | Opcional |
| `[SILÊNCIO n s]` | Narração para, imagem continua | Opcional |
| `*palavra*` | Ênfase | Opcional |
| `>>VISUAL: ...<<` | Imagem que você quer ver nesse trecho | Opcional (o Diretor respeita) |
| `## FONTES` | Fontes usadas no roteiro (vão para a descrição) | Recomendada |

O roteiro de `../pipeline/04-roteiro.md` está exatamente neste formato e serve de exemplo completo.

## 2. Prompt para colar no Gemini (roteiro)

```
Você é roteirista de documentários cinematográficos para YouTube, em português do Brasil.
Tema: <TEMA>
Duração alvo: <N> minutos de narração (~145 palavras por minuto).
Público: curioso, sem formação na área.

Antes de escrever, pesquise o tema e me entregue (1) uma lista de 20–40 fatos com fonte para cada um,
separando o que é consenso do que é debatido, e (2) uma estrutura em blocos com gancho inicial forte,
perguntas que abrem no início e se fecham ao longo do vídeo, um clímax e um final que retoma o começo.
Espere minha aprovação da estrutura.

Depois, escreva o roteiro neste formato exato:
- Cada bloco começa com: ## B<n> — <nome> · intensidade <a>→<b>   (intensidade de 1 a 10)
- Cada trecho de narração começa com: **B<n>-S<nn>** {direção de voz em poucas palavras}
  e na linha seguinte o texto (1 a 3 frases curtas).
- Use [PAUSA-C], [PAUSA-M], [PAUSA-L] e [SILÊNCIO n s] para o ritmo; *palavra* para ênfase.
- Quando uma imagem for essencial, acrescente uma linha: >>VISUAL: descrição curta<<
- Escreva números por extenso quando a leitura puder ser ambígua; evite siglas e parênteses.
- Fatos debatidos com linguagem de debate ("muitos pesquisadores acreditam").
- Frases curtas, concretas, sem clichês; fale com o espectador ("você").
- No fim, uma seção ## FONTES com as fontes usadas.
Não escreva nada fora desse formato na versão final.
```

## 3. Prompt opcional (documento inicial / dossiê)

```
Monte um dossiê de pesquisa sobre <TEMA> para um documentário: linha do tempo, personagens, números
(com faixa de incerteza quando houver), mitos populares e a realidade, descobertas recentes, e para cada item
a fonte (preferir fontes primárias, artigos revisados e instituições oficiais). Termine com uma lista de
"imagens que provavelmente existem em acervos" (obras de arte, fotos históricas, objetos de museu), com o nome
da obra/objeto e onde ela está — isso ajuda o sistema a procurar fotos reais.
```

Anexe a resposta em **Documentos de apoio** na tela "Novo vídeo". A lista final de "imagens que provavelmente existem em acervos" é usada pelo Pesquisador de imagens como ponto de partida.

## 4. O que o sistema faz com o roteiro

1. Lê os blocos e segmentos (ou segmenta, se for texto livre — **sem mudar uma palavra**).
2. Narra cada segmento e mede o tempo real.
3. Usa intensidade e `>>VISUAL<<` para decidir ritmo de cortes, quantidade de motion graphics, origem das imagens e trilha.
4. Lista em `numeros_na_tela.md` tudo que virar texto na tela, para você conferir — o sistema não checa fatos; essa responsabilidade fica com o roteiro.

## 5. Roteiro em outros idiomas

- Os IDs (`B3-S04`) são a ponte entre idiomas: toda tradução mantém exatamente os mesmos IDs e a mesma ordem.
- Para traduzir no Gemini (modo `gemini_manual`), o sistema exporta `traducao_<idioma>.md` já no formato acima. Prompt para colar junto:

```
Traduza este roteiro de documentário para <IDIOMA>, mantendo EXATAMENTE os IDs (**B0-S01** etc.), os blocos,
as marcações [PAUSA-*], [SILÊNCIO], *ênfase* e >>VISUAL<<. Tom de documentário, frases curtas, natural para
narração em voz alta; números por extenso quando a leitura puder ser ambígua. Use este glossário: <GLOSSÁRIO>.
Não acrescente nem remova trechos.
```

- Se preferir, envie você mesmo o roteiro traduzido (modo `arquivo`), com os mesmos IDs.
