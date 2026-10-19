# 12 — Módulo Canal de Música (vídeo longo musical)

Você insere uma lista de músicas e 1–2 imagens. O sistema junta as faixas numa trilha contínua e coloca sobre uma cena com **movimento sutil em loop** (para parecer viva), com qualidade e sem render pesado.

---

## 1. Entrada

| Campo | Detalhe |
|---|---|
| Músicas | Arquivos (WAV/FLAC/MP3) ou uma pasta; ordem manual ou automática |
| Ficha de cada faixa | Título, artista, **direito de uso** (composição própria · licenciada · domínio público · CC BY com crédito · gerada por IA com licença comercial), link da licença |
| Imagens | 1 ou 2 (suas, da pasta global ou geradas pelo sistema a partir de uma descrição) |
| Estilo | `lofi` · `piano` · `ambiente` · `estudo/foco` · `dormir` · `jazz` · `épico` · outro (define o tipo de animação e a paleta) |
| Duração alvo | "só a playlist" ou repetir a playlist até X horas |
| Transição entre faixas | crossfade (2–6 s) · pausa curta · sem pausa |
| Camada de ambiente (opcional) | chuva, lareira, café, mar — da biblioteca de SFX (licença registrada) |
| Elementos visuais opcionais | nome da faixa ao começar · barra de progresso discreta · visualizador de áudio · logo do canal |
| Troca de imagem | com 2 imagens: alternar por faixa ou a cada N minutos, com crossfade lento |

## 2. Animações em loop (escolha fechada)

| ID | Animação | Ferramenta | Bom para |
|---|---|---|---|
| L01 | **Respiração de profundidade**: parallax muito sutil, ida e volta perfeita | DepthFlow (ciclo que termina igual ao início) | quase tudo |
| L02 | **Partículas**: chuva, neve, poeira, vaga-lumes, folhas | Remotion (procedural com semente, ciclo exato) | lofi, ambiente, dormir |
| L03 | **Luz viva**: brilho de abajur/vela/janela pulsando, raios de sol | Remotion (máscara de luz) | piano, jazz, estudo |
| L04 | **Elemento animado**: fumaça de xícara, nuvens passando, água tremulando (região mascarada da imagem) | Remotion (deslocamento por ruído só na máscara) | lofi, café |
| L05 | **Zoom pulsante** muito lento, sincronizado ao andamento | Remotion | épico |
| L06 | **Visualizador de áudio** discreto (barras/onda) | Remotion `visualizeAudio` (renderizado por faixa) | qualquer, opcional |

Combinações permitidas: até 3 (ex.: L01 + L02 chuva + L03 abajur). O verificador recusa combinações que poluem (ex.: L05 + L06 + L02 densa).

Máscaras (onde fica a fumaça, a janela, a vela): o sistema propõe por visão local e você ajusta na tela com um pincel simples, ou desenha à mão.

## 3. Como fica eficiente (render de horas em minutos)

```
1. Gera a cena em loop UMA vez: clipe de 10–30 s cujo último quadro emenda perfeitamente no primeiro
   (Remotion + DepthFlow, 1080p ou 1440p)                                         ~2–6 min
2. Confere a emenda (diferença entre o último e o primeiro quadro ≈ 0)              segundos
3. Monta o áudio: normaliza cada faixa, aplica crossfades, ambiente opcional,
   e calcula os tempos de início de cada música                                   ~1–3 min
4. Repete o clipe até a duração do áudio com FFmpeg (-stream_loop), sem recodificar
   a cena a cada volta                                                              ~1–2 min
5. Sobrepõe só onde precisa (nome da faixa, troca de imagem, visualizador):
   pequenos clipes com transparência nos tempos certos, codificação NVENC          ~5–20 min para 1–3 h de vídeo
6. QA: emendas, loudness, picos, silêncios entre faixas                            ~2–5 min
```

Um vídeo de 1 hora fica pronto em ~15–35 min (a confirmar no benchmark), quase todo o tempo em codificação.

## 4. Áudio

- Cada faixa normalizada para o mesmo volume percebido (−14 LUFS integrado na mix final; picos ≤ −1 dBTP), sem mudar a dinâmica interna além do necessário.
- Crossfades em curva de potência constante; nenhuma faixa cortada no meio.
- Ambiente opcional bem baixo (−30 a −24 LUFS) e contínuo.
- Detecção de silêncio indevido e de faixas duplicadas.

## 5. Saída

```
projetos\musica-<slug>\05_saida\
├── video/video.mp4
├── audio/mix.wav                        # a playlist mixada
├── elementos/cena_loop.mp4 · imagem_1.png · imagem_2.png · mascaras/
├── tracklist.txt                        # 00:00 Faixa 1 — Artista ...
├── creditos.txt                         # licença de cada faixa e imagem
├── metadados/ titulos.md · descricao.md (com a tracklist) · tags.txt · thumbs_briefing.md · comentario_fixado.md · metadados.json
├── thumbnails/ (3 opções prontas a partir da cena)
└── shorts/ (opcional: 2–3 cortes verticais de 15–30 s de uma faixa sobre a cena reenquadrada, com CTA para o vídeo)
```

A cena em loop e as máscaras vão para a pasta global (`global/loops/`) para reaproveitar em novos vídeos da mesma série.

## 6. Direitos (obrigatório)

- O sistema não aceita uma faixa sem ficha de direito de uso; faixas "geradas por IA" precisam indicar a ferramenta e a licença comercial.
- Aviso automático no relatório: sistemas de identificação de conteúdo (Content ID) podem reivindicar faixas de bibliotecas mesmo licenciadas — guardar os comprovantes em `creditos.txt`.
