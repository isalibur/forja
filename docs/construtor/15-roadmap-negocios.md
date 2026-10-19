# 15 — Roadmap: módulos para a carteira de negócios

> **Para a IA que vai programar:** este documento separa o que **entra já na v1** (pequeno, dentro dos marcos existentes) do que fica para **versões futuras**. Não implemente nada das fases futuras sem um pedido explícito. A carteira de negócios que motiva estes módulos está em [`../negocios/carteira-de-negocios.md`](../negocios/carteira-de-negocios.md).

---

## 1. Avaliação: construir agora ou depois?

Critério: entra na v1 só se (a) reaproveita o que a v1 já produz, (b) custa poucos dias, (c) não traz dependência externa difícil (aprovação de app, pagamento, servidor público) e (d) já gera valor para um negócio da carteira.

| Módulo | Serve a | Esforço | Dependências difíceis | Decisão |
|---|---|---|---|---|
| Fórmula de short **"produto/afiliado"** + template de cartão de produto + entrada por planilha | Afiliados | ~1 dia | nenhuma | **v1 (M8)** |
| **Pacote para bancos de imagens** (clipes elegíveis + planilha de metadados) | Banco de imagens | ~1–2 dias | nenhuma | **v1 (M6)** |
| **Planilha de publicação** (agenda + textos por plataforma) para ferramentas de agendamento | Afiliados, canais, shorts | ~0,5 dia | nenhuma | **v1 (M6/M8)** |
| **Marca do projeto** (logo, cores, contato e cartão final sobre o kit) | Pacotes personalizados, serviços | ~1 dia | nenhuma | **v1 (M2/M6)** |
| **Versão internacional (M&E) e master limpo** | Licenciamento, dublagem | ~0,5 dia | nenhuma | **v1 (M6)** |
| Livro (KDP: EPUB/DOCX + capa) e audiolivro | KDP | 1–2 semanas | regras de cada plataforma; pipeline de texto longo é outro produto | **Fase A** |
| Kit educativo (vídeo curto + atividade em PDF + gabarito) | Biblioteca educativa | ~1 semana | nenhuma, mas exige curadoria pedagógica | **Fase A** |
| Publicação automática pelas APIs oficiais | Afiliados, canais | 1–2 semanas + espera de aprovação | OAuth por plataforma, revisão de app (Meta, TikTok), cotas | **Fase B** |
| "Um tema, cinco produtos" (orquestrador de saídas múltiplas) | Todos | ~1 semana | depende da Fase A | **Fase B** |
| Loja de autoatendimento com Pix (pedido → render → entrega automática) | Pacotes personalizados, site de imóveis | 3–6 semanas | servidor público, pagamento, LGPD, segurança, disponibilidade, licença do Remotion para render automático para terceiros | **Fase C** |
| Painel de receitas (importa relatórios das plataformas) | Todos | ~1 semana | formatos de relatório mudam | **Fase D** |

**Total que entra na v1:** ~4–5 dias de trabalho a mais, distribuídos em M2, M6 e M8 — sem atrasar o caminho principal.

---

## 2. O que entra na v1

### 2.1 Fórmula "produto/afiliado" (M8)
- Nova fórmula em `global/formulas_shorts/produto_afiliado.yaml`: **gancho do problema** (0–2 s) → **produto em uso** → **3 benefícios** (ItemLista) → **preço/condição** (opcional) → **CTA** ("link na bio", "link no comentário fixado").
- Novo template **V11 `CartaoProduto`**: imagem do produto, nome, até 3 benefícios, preço/condição e selo da loja (texto, sem logo de terceiros).
- **Entrada em lote:** planilha CSV com `nome, descricao, beneficios, preco, link_afiliado, imagens, nicho, plataforma` → 1 short por linha. O link nunca vai queimado no vídeo; vai para os metadados e para a planilha de publicação.
- Regras de honestidade (somam-se a `11 §4.3`): imagens só as que o programa de afiliados permite usar ou fotos suas; nada de "melhor do mundo", "garantido" ou preço inventado; aviso de publicidade/link de afiliado na legenda; o verificador recusa preço sem fonte na planilha.

### 2.2 Pacote para bancos de imagens (M6, opcional por projeto)
- **Elegíveis:** só o que é **seu**: imagens geradas, cenas em loop, animações de mapa feitas pelo sistema, fundos e texturas do kit. **Nunca** fotos de acervo de terceiros, imagens da pasta manual sem licença própria, nem trechos com narração.
- **Saída:** `05_saida/stock/` com clipes curtos (5–30 s, sem texto queimado, sem rótulos), quadros em alta resolução e `metadados_stock.csv` (título, palavras-chave, categoria, marcação de IA, descrição). Títulos e palavras-chave em inglês, gerados pelo LLM a partir do plano.
- Envio: manual, pela planilha de metadados aceita pelo banco (você revisa e sobe). Nada de envio automático na v1.

### 2.3 Planilha de publicação (M6 e M8)
- `05_saida/<idioma>/publicacao/agenda.csv`: arquivo, plataforma, título, legenda/descrição, hashtags, link (afiliado ou vídeo longo), data e hora sugeridas, capa.
- Formato genérico, fácil de importar em ferramentas de agendamento; você revisa e importa. A publicação continua sendo uma ação sua.

### 2.4 Marca do projeto (M2 e M6)
- Por projeto, uma camada **sobre** o kit: logo, 1–2 cores de destaque, nome, contato (telefone, @, site) e um cartão final.
- Templates com espaço reservado para logo e cartão final; o verificador confere contraste e legibilidade.
- É a base para os pacotes personalizados da Fase C, e já serve para produzir conteúdo de terceiros manualmente.

### 2.5 Versão internacional e master limpo (M6)
- `05_saida/licenciamento/`: trilha **M&E** (música + efeitos, sem narração), master sem legendas queimadas, legendas separadas e uma ficha técnica (duração, idiomas, créditos, licenças).
- Custo quase zero: o mix já é feito por camadas.

---

## 3. Fases futuras

### Fase A — Livros e kits educativos (v1.1)
**Livro (KDP) e audiolivro**
- Novo tipo de projeto `livro`: entrada = texto do livro (feito por você no Gemini) + imagens do projeto/pasta global.
- Saídas: DOCX com estilos (python-docx, MIT) e EPUB (via Pandoc como programa externo); capa de ebook e de livro impresso (com cálculo de lombada pelo número de páginas); ficha de metadados (título, subtítulo, descrição, 7 palavras-chave, categorias, **marcação de conteúdo gerado por IA** quando for o caso).
- Audiolivro: narração por capítulo com a voz do canal, em arquivos separados, normalizados e com silêncio no início e no fim, conforme a especificação da plataforma escolhida (conferir na época — regras de narração por IA variam por plataforma e país).
- Série: vários livros do mesmo tema compartilham capa-modelo, glossário e pasta global.

**Kit educativo**
- Novo tipo `educativo`: vídeo de 3–6 min (plano `longo` reduzido) + **atividade em PDF** (questões, mapa para completar, linha do tempo para ordenar) + **gabarito**, com campo de habilidade da BNCC.
- Saída pronta para área de membros (vídeo + PDFs + descrição).

### Fase B — Publicação automática e "um tema, cinco produtos" (v1.2)
- **Adaptadores de publicação:** YouTube (Data API), Instagram/Facebook (API oficial de publicação de Reels), TikTok (API de publicação de conteúdo), Pinterest. Cada um exige app próprio, login autorizado por você e, em alguns casos, revisão da plataforma antes de publicar como público.
- **Aprovação em lote obrigatória:** o sistema monta a fila da semana; você aprova uma vez; ele publica nos horários. Sem aprovação, nada sai.
- **Orquestrador "um tema, cinco produtos":** ao planejar um tema, opcionalmente gera também os planos de shorts, livro, kit educativo e pacote stock, reaproveitando pesquisa, imagens e narração.

### Fase C — Loja de autoatendimento (v2.0)
- Site público simples: escolher produto (ex.: "30 vídeos de dicas para dentistas com a sua marca", "vídeo do seu imóvel") → enviar logo/fotos/dados → pagar (Pix por um gateway) → o pedido entra na fila → o DocForja renderiza com a **marca do projeto** → entrega por link com validade.
- Arquitetura: página e pagamentos num servidor barato; o seu PC como "worker" que busca pedidos na fila (ou GPU na nuvem, se crescer); armazenamento temporário dos arquivos; e-mails automáticos.
- Requisitos: termos de uso e política de privacidade (LGPD), limite de tamanho de upload, verificação de conteúdo enviado, reembolso automático se o render falhar.
- **Licença:** confirmar com a Remotion se o render automático para clientes exige o plano pago de automação; alternativa: Revideo (MIT) para esse produto.

### Fase D — Painel de receitas
- Importa relatórios (CSV) de afiliados, KDP, bancos de imagens, plataformas de vídeo e loja; mostra receita por fonte, por tema e por idioma; indica quais temas e formatos rendem mais, para orientar o próximo planejamento.

---

## 4. Regras que valem para tudo isso

1. Nada é publicado, enviado ou vendido em seu nome sem aprovação explícita (na v1, publicar e enviar continuam sendo ações suas).
2. Conteúdo de terceiros (acervo, imagens da pasta manual) nunca vai para banco de imagens nem para revenda.
3. Toda peça de afiliado ou publicidade leva a sinalização de publicidade.
4. Conteúdo gerado por IA é declarado onde a plataforma pede (KDP, bancos de imagens, YouTube).
5. As regras de cada plataforma mudam: cada adaptador guarda a data da última conferência das regras.
