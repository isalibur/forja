# 10 — Metadados, Thumbnail, Shorts e Publicação

> **Para a IA executora:** o A18 pode começar após o G2 (o conceito do vídeo já está estável), mas capítulos e timecodes só são finalizados a partir do master. **Publicar é uma ação externa e irreversível na prática:** o Orquestrador prepara o pacote completo e pede aprovação explícita do humano responsável antes de fazer upload ou agendar.

---

## 1. Título

Regras: ≤ 60 caracteres visíveis, curiosidade + especificidade, sem prometer o que o vídeo não entrega.

| # | Título | Caracteres | Ângulo |
|---|---|---|---|
| T1 (recomendado, tema original) | O Vesúvio de Pompeia como você nunca viu | 40 | Promessa ampla, fiel ao tema |
| T2 | Pompeia não morreu em agosto (e não foi a lava) | 47 | Quebra de crença dupla |
| T3 | As últimas horas de Pompeia, hora por hora | 42 | Formato "tempo real" |
| T4 | O que a ciência descobriu sobre Pompeia (2018–2025) | 51 | Novidade |
| T5 | O cérebro que virou vidro: o fim de Pompeia | 43 | Detalhe chocante |

Usar T1 no lançamento; se o recurso de teste de título estiver disponível, testar T1 × T2 × T3.

## 2. Thumbnails (3 conceitos para teste A/B)

Princípios: 1 ideia; 1 elemento dominante; ≤ 3 palavras; legível com 120 px de largura; contraste máximo (brasa sobre preto); sem imagem gráfica de restos humanos em primeiro plano.

| Conceito | Composição | Texto | Paleta |
|---|---|---|---|
| **A — "A cidade e o relógio"** | Rua de Pompeia (plano-âncora) em 2/3 do quadro, metade dourada/viva e metade cinza/soterrada (divisão diagonal); coluna eruptiva gigante atrás; HUD "07:00" em mono no canto | "19 HORAS" | dourado × cinza + brasa |
| **B — "Erramos a data"** | Parede de reboco com "XVI K NOV" em carvão (recriação gráfica, salvo autorização da foto real); um "24 AGO" riscado em vermelho | "ERRAMOS" | pergaminho + vermelho |
| **C — "Vidro"** | Mão enluvada segurando um fragmento negro brilhante sob luz dramática (ilustração rotulada), Vesúvio desfocado em brasa ao fundo | "CÉREBRO DE VIDRO" | preto + brasa |

Especificação: 1280×720 (exportar também 3840×2160), JPG < 2 MB, sRGB. Testar leitura em modo escuro e claro do app. Elementos gerados por IA nas thumbs seguem a mesma regra de coerência histórica do vídeo.

## 3. Descrição

```
Pompeia não foi destruída pela lava — e talvez não tenha morrido em 24 de agosto.
Neste documentário, você vive as últimas horas da cidade, hora por hora, e descobre o que a
ciência revelou só nos últimos anos: o DNA dos moldes de gesso, o cérebro que virou vidro
e a inteligência artificial que começou a ler os papiros carbonizados de Herculano.

⏱️ CAPÍTULOS
00:00 A data errada
01:15 A montanha verde
03:15 O aviso
04:25 Dia 1 — A coluna
07:20 A noite — Herculano
09:20 Dia 2 — O fim
11:25 O esquecimento
12:40 O que você nunca viu
14:55 O vulcão hoje

📚 FONTES PRINCIPAIS
• Plínio, o Jovem — Cartas 6.16 e 6.20
• Sêneca — Naturales Quaestiones, livro VI
• Estrabão — Geografia 5.4.8 · Plutarco — Vida de Crasso 9
• Sigurdsson et al. (1985), The eruption of Vesuvius in A.D. 79
• Carey & Sigurdsson (1987), GSA Bulletin
• Luongo et al. (2003), J. Volcanol. Geotherm. Res.
• Petrone et al. (2020), New England Journal of Medicine
• [estudo de 2025 sobre o vidro cerebral], Scientific Reports
• Pilli et al. (2024), Current Biology
• Vesuvius Challenge — scrollprize.org
• Parco Archeologico di Pompei · Parco Archeologico di Ercolano
• INGV – Osservatorio Vesuviano · Protezione Civile – Piano Vesuvio
• Mary Beard, Pompeii: The Life of a Roman Town (2008)
(lista completa com links: [link para sources.json/página])

🎨 IMAGENS
Reconstituições artísticas criadas com ferramentas de IA estão identificadas no vídeo.
Créditos de arquivo: [gerado automaticamente a partir de licenses.csv]

🎵 Música: [créditos conforme licença] · Narração: [voz/locutor]
```

Regras:
- As 2 primeiras linhas aparecem antes do "mais": elas precisam vender o vídeo.
- Capítulos: o primeiro **deve** ser `00:00`; mínimo de 3; cada um ≥ 10 s. **Substituir os timecodes acima pelos reais do master.**
- Créditos CC BY / CC BY-SA com autor, licença e link — gerados de `licenses.csv`.

## 4. Tags, idioma e configurações

- **Tags:** Pompeia, Vesúvio, Herculano, erupção do Vesúvio, Plínio o Jovem, Plínio o Velho, Roma antiga, história antiga, documentário, arqueologia, vulcão, corrente piroclástica, Vesuvius Challenge, DNA Pompeia, moldes de gesso, 79 d.C., Campânia, Nápoles, Pompeii, Vesuvius.
- **Hashtags (máx. 3 na descrição):** #Pompeia #Vesúvio #História
- **Categoria:** Educação · **Idioma do vídeo:** Português (Brasil) · **Legendas:** PT-BR + EN (SRT do E17).
- **Público:** não é conteúdo para crianças.
- **Divulgação de conteúdo alterado ou sintético:** **SIM** — há cenas realistas geradas por IA de eventos históricos. (Além do rótulo na tela.)
- **Tela final (20 s):** 1 vídeo recomendado + 1 playlist + botão de inscrição; dentro da safe area do end card (B8-16).
- **Cards:** nunca durante B3–B5 (a tensão não pode ser interrompida); usar um único card em ~14:55 (transição para o presente), apontando para um vídeo relacionado.
- **Comentário fixado:** pergunta que gera conversa sem clickbait: "Você sabia que a data de 24 de agosto está em debate? Qual descoberta mais te surpreendeu: o DNA, o vidro ou os papiros?"

## 5. Shorts (3 cortes verticais 9:16)

| Short | Origem | Duração | Hook (primeiros 2 s, texto + fala) | Final |
|---|---|---|---|---|
| S1 "O cérebro que virou vidro" | B4-S09 → S12 | ~40 s | "O cérebro dele virou VIDRO." (inverter: abrir com a frase B4-S11, depois contar) | "Vídeo completo no canal" + B4-S13 |
| S2 "A IA leu um livro de 2.000 anos" | B7-S07 → S13 | ~55 s | "Esse rolo está fechado há quase 2.000 anos. Uma IA acabou de ler." | "O mesmo vulcão que destruiu… preservou." |
| S3 "Pompeia não morreu em agosto" | B0-S01 → S04 + B7-S14 | ~45 s | Carvão escrevendo na parede + "Essa data pode estar errada." | "O debate continua." |

Regras de reenquadramento:
- Reframe a partir do master 4K (crop 9:16 = 1215×2160) acompanhando o ponto de interesse; motion graphics são **re-renderizados** em layout vertical (não cortados).
- Legendas queimadas palavra a palavra (ver `09 §7`), no terço médio-inferior, fora da área da UI do app.
- Áudio: remix a partir dos stems; música um pouco mais alta (−18 LUFS short-term sob a voz); loudness final −14 LUFS.
- Nova narração só se o hook exigir reordenação de frases (gerar com a mesma voz e parâmetros).

## 6. Checklist final de publicação (G3)

- [ ] Master MP4 conferido do primeiro ao último frame
- [ ] Título, descrição (com capítulos reais), tags, idioma, categoria
- [ ] 3 thumbnails exportadas; teste A/B configurado (se disponível)
- [ ] Legendas PT-BR e EN enviadas
- [ ] Divulgação de conteúdo sintético marcada
- [ ] Tela final e card configurados
- [ ] Créditos completos (arquivo, música, voz)
- [ ] Shorts renderizados e com descrição apontando para o vídeo longo
- [ ] **Aprovação humana explícita registrada em `project.json` antes do upload/agendamento**
