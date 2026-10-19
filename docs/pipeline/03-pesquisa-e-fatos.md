# 03 — Pesquisa Histórica, Banco de Fatos e Timeline

> **Para a IA executora:** este é o dossiê inicial produzido por A01 + A02. Ele **não dispensa** a etapa E03 (fact-check independente): toda linha precisa ser reconferida na fonte antes do G1. Os IDs `F-xxx` são usados no roteiro (`04`), na decupagem (`05`) e nos motion graphics (`06`). Se um fato mudar de status, propague a mudança para todos os `used_in`.

---

## 1. O ângulo editorial: "da forma que você nunca viu"

O público já "conhece" Pompeia: vulcão, lava, corpos de gesso, 24 de agosto. O vídeo entrega o "nunca viu" em **quatro camadas**:

1. **Tempo real.** As últimas ~19 horas contadas hora a hora, com relógio na tela (HUD), alternando três pontos de vista: Pompeia, Herculano e os dois Plínios.
2. **Desmontar mitos.** Não foi lava. Não foi instantâneo. Muita gente fugiu. A data provavelmente não é 24 de agosto.
3. **Ciência que só existe agora (2018–2025).** A inscrição a carvão de outubro (2018), o cérebro que virou vidro (2020/2025), o DNA que reescreveu as histórias dos moldes (2024), a IA lendo os papiros carbonizados (2023–2025).
4. **O presente.** O vulcão está vivo; ~700 mil pessoas na zona vermelha; plano de evacuação de 72 h.

Estrutura circular: começa e termina na inscrição a carvão.

---

## 2. Pautas obrigatórias (checklist de cobertura do A01/A02)

- [ ] Geologia do Somma-Vesúvio e o pico único de 79 d.C.
- [ ] Como os romanos viam a montanha (Estrabão, afresco de Baco, Espártaco)
- [ ] Vida em Pompeia (população, ruas, termopólios, grafites, pães)
- [ ] Terremoto de 62/63 d.C. e os tremores dos dias finais
- [ ] Debate da data (agosto × outubro)
- [ ] Cronologia física da erupção (fase pliniana → colapso → correntes piroclásticas)
- [ ] Narrativa dos dois Plínios (Ep. 6.16 e 6.20)
- [ ] Herculano: fornici, esqueletos, cérebro vitrificado, profundidade do soterramento
- [ ] Esquecimento e redescoberta (Fontana, 1709/1738, 1748, 1763, Fiorelli 1863)
- [ ] DNA dos moldes (2024)
- [ ] Papiros de Herculano e Vesuvius Challenge (2023–2025)
- [ ] Erupções posteriores (472, 1631, 1944)
- [ ] Risco atual: zona vermelha, plano de evacuação, Osservatorio Vesuviano
- [ ] Mitos populares a desmentir

---

## 3. Banco de fatos (base de `facts.json`)

Legenda de status: **V** = VERIFICADO · **CR** = CONSENSO_COM_RESSALVA · **D** = DEBATIDO · **M** = MITO (só aparece para ser desmentido) · **NV** = NÃO VERIFICADO (não pode ir ao vídeo).
A coluna "Conferir" indica onde o A03 deve checar primeiro.

### 3.1 A montanha antes de 79

| ID | Afirmação | Status | Frase segura para narração | Conferir |
|---|---|---|---|---|
| F-001 | O Vesúvio é um estratovulcão do complexo Somma-Vesúvio. Em 79 d.C. o perfil era de um cume único (o do atual Monte Somma); o cone moderno cresceu depois, dentro da caldeira. | V | "um pico só, bem diferente do que existe hoje" | Smithsonian GVP; INGV-OV |
| F-002 | Erupção de Avellino (~2000–1900 a.C., Idade do Bronze) soterrou aldeias; há pegadas de fuga preservadas na região de Nola. | CR | "há quase quatro mil anos, ele já tinha destruído aldeias inteiras" | Mastrolorenzo et al. 2006 (PNAS) |
| F-003 | Estrabão (Geografia 5.4.8) descreve o topo do Vesúvio como plano, estéril, com rochas cor de cinza que pareciam consumidas pelo fogo, e deduz que ali houve fogo no passado. | V | "as rochas pareciam queimadas, como se tivessem sido consumidas pelo fogo" | Texto de Estrabão (Loeb / Perseus) |
| F-004 | Em 73 a.C., Espártaco e os rebeldes acamparam no Vesúvio e desceram os penhascos com escadas trançadas de videiras selvagens (Plutarco, Crasso 9). | V | "desceram pelos penhascos usando escadas feitas de videiras selvagens" | Plutarco, Vida de Crasso 9 |
| F-005 | Afresco do larário da Casa do Centenário (Pompeia, IX.8) mostra Baco coberto de uvas ao lado de uma montanha verde de cume único, interpretada como o Vesúvio. Hoje no MANN. | CR | "uma montanha, interpretada como o Vesúvio, verde e pacífica" | MANN; Beard 2008 |
| F-006 | Os romanos não reconheciam o Vesúvio como uma ameaça vulcânica; nem Plínio, o Jovem, usa uma palavra equivalente a "vulcão" para a montanha. O termo moderno deriva do deus Vulcano. | CR | "os romanos não viam um vulcão. Viam uma montanha." | Ep. 6.16 e 6.20; etimologia |

### 3.2 Pompeia viva

| ID | Afirmação | Status | Frase segura | Conferir |
|---|---|---|---|---|
| F-007 | População estimada de Pompeia em 79: ~10–12 mil (estimativas vão de ~6 mil a 20 mil). | CR | "talvez onze mil pessoas" | Parco Archeologico di Pompei; Beard 2008 |
| F-008 | Herculano: ~4–5 mil habitantes; cidade menor, à beira-mar. | CR | "uma cidade menor, à beira-mar" | Parco Archeologico di Ercolano |
| F-009 | Mais de 10 mil inscrições foram registradas em Pompeia (programas eleitorais, grafites, anúncios) — CIL IV. | CR | "mais de dez mil inscrições" | CIL IV; Ancient Graffiti Project |
| F-010 | Pompeia tinha dezenas de termopólios (balcões de comida); um exemplar totalmente decorado foi escavado na Regio V em 2019–2020. | V | "bares de rua, os termopólios" | Comunicado PAP dez/2020 |
| F-011 | As ruas tinham pedras elevadas para atravessar (faixas de pedestres), com espaço para as rodas das carroças. | V | "ruas de pedra com faixas de pedestres elevadas" | — |
| F-080 | Pães carbonizados foram encontrados em Pompeia (ex.: 81 pães no forno da padaria de Modesto). | CR | "pães que ainda estavam no forno" | MANN |
| F-081 | Em 2023 foi descoberto afresco de natureza-morta com um pão achatado com coberturas, apelidado "ancestral da pizza". | V | (reserva) | Comunicado PAP jun/2023 |

### 3.3 Os avisos

| ID | Afirmação | Status | Frase segura | Conferir |
|---|---|---|---|---|
| F-012 | Um forte terremoto atingiu a Campânia num 5 de fevereiro; Sêneca data pelos cônsules (correspondendo a 63 d.C.), Tácito o coloca em 62 d.C. A literatura usa "62 d.C." por convenção. | D | "dezessete anos antes — no ano 62 ou 63, as fontes antigas discordam" | Sêneca, NQ 6.1; Tácito, Anais 15.22 |
| F-013 | Sêneca relata que um rebanho de seiscentas ovelhas morreu (NQ 6.1.3; discutido em 6.27). | V | "um rebanho de seiscentas ovelhas morreu de uma só vez" | Sêneca, NQ VI |
| F-014 | Em 79, Pompeia ainda tinha edifícios em reparo/reconstrução (possivelmente também por tremores posteriores). | CR | "ainda havia obras pela cidade" | Beard 2008 |
| F-015 | Um relevo do larário da casa de Lúcio Cecílio Jucundo retrata edifícios tombando — interpretado como o terremoto. | CR | (visual) | MANN / PAP |
| F-016 | Plínio, o Jovem, relata tremores por muitos dias antes, "pouco assustadores porque comuns na Campânia" (Ep. 6.20.3). | V | "na Campânia, tremor era rotina. Ninguém se assustou." | Ep. 6.20.3 |

### 3.4 A data

| ID | Afirmação | Status | Frase segura | Conferir |
|---|---|---|---|---|
| F-017 | A data tradicional, 24 de agosto de 79, vem dos manuscritos medievais de Plínio ("nonum kal. Septembres"), que têm variantes de leitura. | V | "por séculos, os livros disseram 24 de agosto" | Edições críticas de Plínio |
| F-018 | Em 2018, na Regio V (Casa com Jardim), achou-se uma inscrição a carvão "XVI K NOV" — 16 dias antes das calendas de novembro = 17 de outubro. O ano não está escrito, mas o carvão é efêmero, o que sugere que foi feita pouco antes da erupção. | D | "uma inscrição que muitos pesquisadores leem como 17 de outubro" | Comunicado PAP out/2018 |
| F-019 | Outros indícios de outono: frutas de outono (romãs, castanhas, nozes) nas casas, braseiros em uso, vítimas com roupas mais pesadas, vinho já armazenado em dólios lacrados. | CR | "tudo aponta para o outono" | Rolandi et al. 2008; Stefani |
| F-019b | Hipótese mais aceita hoje: 24 de outubro de 79. Ainda há defensores de agosto. | D | "muitos pesquisadores hoje acreditam que foi em outubro" | — |

### 3.5 A erupção (física)

| ID | Afirmação | Status | Frase segura | Conferir |
|---|---|---|---|---|
| F-020 | Em 79 d.C. o Vesúvio praticamente não emitiu lava; Pompeia foi destruída por queda de pomes e por correntes de densidade piroclástica. | V | "Não foi lava." | Sigurdsson et al. 1985 |
| F-021 | A nuvem foi vista por volta da "sétima hora" romana (≈ início da tarde, ~13h) (Ep. 6.16.4). | V | "por volta de uma da tarde" | Ep. 6.16.4 |
| F-023 | A coluna eruptiva pliniana chegou a ~26–33 km de altura, segundo modelos. | CR | "mais de vinte, trinta quilômetros" | Carey & Sigurdsson 1987 |
| F-024 | Pico da taxa de erupção de massa na ordem de 10⁸ kg/s (~100–150 mil toneladas por segundo). | NV | **não usar até verificar** | Carey & Sigurdsson 1987 |
| F-025 | Volume total de material ejetado: alguns km³ (estimativas ~3–4 km³ de tefra). | CR | (reserva; não citar número sem fonte conferida) | Sigurdsson 1985; GVP |
| F-085 | Altitude de cruzeiro de um avião comercial: ~10–12 km. | V | "três vezes a altitude de um avião" (33/11) | — |
| F-035 | O vento soprava para sudeste, levando a pluma sobre Pompeia e Estábia. | V | "o vento soprava para o sudeste, exatamente na direção da cidade" | Sigurdsson 1985 |
| F-036 | Pomes acumulou em Pompeia a ~12–15 cm por hora. | CR | "cerca de quinze centímetros por hora" | Sigurdsson 1985 |
| F-037 | Primeiro pomes branco, depois cinza; total de ~2,5–2,8 m de pomes em Pompeia. | CR | "quase três metros" | Sigurdsson 1985 |
| F-038 | Muitas vítimas morreram pelo colapso de telhados/paredes durante a queda de pomes; a maioria das vítimas encontradas, porém, está nos depósitos das correntes piroclásticas. | CR | "pessoas que se abrigaram dentro de casa morreram esmagadas" | Luongo et al. 2003 |
| F-039 | Estima-se que a maior parte dos habitantes deixou a cidade durante a fase de pomes. | CR | "hoje se estima que a maioria conseguiu escapar" | Beard; PAP |
| F-043 | O colapso da coluna gerou correntes piroclásticas; a primeira atingiu Herculano por volta da meia-noite/1h do segundo dia (horários são reconstituições de modelos). | CR | "por volta da meia-noite" | Sigurdsson 1985; Giacomelli 2003 |
| F-044 | Correntes de densidade piroclástica: misturas de gás quente, cinza e rocha que descem a encosta a mais de 100 km/h, a centenas de graus. | V | "mais de cem quilômetros por hora; centenas de graus" | USGS; GVP |
| F-045 | Temperaturas estimadas das correntes em Herculano: algumas centenas de °C (estudos variam de ~250 a ~500 °C+). | CR | "algumas centenas de graus" | Mastrolorenzo 2001; Caricchi 2014 |
| F-056 | Em Pompeia, as primeiras correntes não entraram em cheio na cidade; a que matou os sobreviventes chegou por volta de 6h30–7h30 do segundo dia. | CR | "por volta das sete da manhã, uma delas atravessou os muros" | Sigurdsson 1985; Luongo 2003 |

### 3.6 Os dois Plínios (Ep. 6.16 e 6.20)

| ID | Afirmação | Status | Frase segura | Conferir |
|---|---|---|---|---|
| F-026 | Plínio, o Jovem, tinha 17 anos ("estava no meu décimo oitavo ano", Ep. 6.20.5). | V | "um rapaz de dezessete anos" | Ep. 6.20.5 |
| F-027 | Miseno, base da frota, fica a cerca de 30 km do Vesúvio em linha reta. | V | "a cerca de trinta quilômetros" | Medir em GIS |
| F-028 | A nuvem lembrava um pinheiro-manso: tronco alto que se abria em galhos (Ep. 6.16.5). | V | (paráfrase) | Ep. 6.16.5 |
| F-029 | As cartas foram escritas a Tácito cerca de 25–28 anos depois (c. 106–107 d.C.). | CR | "mais de vinte e cinco anos depois" | — |
| F-030 | "Erupção pliniana" é o termo vulcanológico em homenagem aos Plínios. | V | — | — |
| F-031 | Plínio, o Velho: autor da *Naturalis Historia* (37 livros) e comandante (praefectus) da frota em Miseno. | V | "uma enciclopédia em trinta e sete volumes — e almirante da frota romana" | — |
| F-032 | Chegou mensagem de Rectina, esposa de Tasco, cuja villa ficava ao pé da montanha e só tinha fuga por mar (Ep. 6.16.8). | V | "uma mulher chamada Rectina implorava por resgate" | Ep. 6.16.8 |
| F-033 | Ele mandou lançar quadrirremes (Ep. 6.16.9). | V | "os grandes navios de guerra" | Ep. 6.16.9 |
| F-034 | Ao timoneiro que sugeria voltar, disse: "A sorte ajuda os corajosos" — *Fortes fortuna iuvat* (Ep. 6.16.11). | V | "A sorte favorece os corajosos." | Ep. 6.16.11 |
| F-049 | Sem poder desembarcar no litoral bloqueado, seguiu para Estábia, à casa de Pomponiano. | V | — | Ep. 6.16.11–12 |
| F-050 | Tomou banho, jantou e dormiu; seu ronco era ouvido por quem passava à porta (Ep. 6.16.13). | V | — | Ep. 6.16.13 |
| F-051 | O pátio enchia de cinza e pomes; se ficasse mais, não conseguiria sair do quarto (Ep. 6.16.14). | V | — | Ep. 6.16.14 |
| F-052 | Saíram com travesseiros amarrados à cabeça como proteção (Ep. 6.16.16). | V | — | Ep. 6.16.16 |
| F-053 | Na praia, deitado sobre um pano, pediu água fria duas vezes; chamas e cheiro de enxofre; levantou-se apoiado em dois escravos e caiu (Ep. 6.16.18–19). O sobrinho atribui a morte ao ar denso; hipóteses modernas incluem problema cardíaco. | V | — | Ep. 6.16.18–19 |
| F-054 | Plínio, o Velho, tinha cerca de 56 anos. | CR | "tinha cinquenta e seis anos" | Nasc. 23/24 d.C. |
| F-055 | Quando a luz voltou, o corpo foi achado intacto, "mais parecido com alguém dormindo do que morto" (Ep. 6.16.20). | V | — | Ep. 6.16.20 |
| F-059 | Ep. 6.20: escuridão "não como uma noite sem lua, mas como um quarto fechado com a luz apagada"; gritos de mulheres, choro de crianças, homens chamando parentes; muitos achavam que era a última noite do mundo. | V | (paráfrase) | Ep. 6.20.14–15 |
| F-060 | Plínio, o Jovem, e a mãe sobreviveram. | V | — | Ep. 6.20 |

### 3.7 Herculano

| ID | Afirmação | Status | Frase segura | Conferir |
|---|---|---|---|---|
| F-040 | Herculano, a oeste, recebeu pouca queda de pomes por causa do vento. | V | "o vento tinha poupado Herculano" | — |
| F-041 | Até os anos 1980 achavam-se poucos corpos em Herculano; a partir de 1980–82, escavações na antiga praia e nos fornici revelaram mais de 300 esqueletos. | CR | "mais de trezentas pessoas" | PAE; Bisel |
| F-042 | Os fornici: 12 câmaras abobadadas à beira-mar (galpões de barcos/armazéns). | V | "doze galpões de barcos" | PAE |
| F-046 | Cérebro vitrificado: vítima de ~20 anos achada deitada numa cama de madeira no Collegium Augustalium. Petrone et al. (NEJM, 2020) identificaram tecido cerebral vitrificado; estudo de 2025 (Scientific Reports) concluiu que exigiu aquecimento acima de ~510 °C seguido de resfriamento rápido, atribuído a uma nuvem de cinza muito quente que passou antes das correntes principais. | CR | "o cérebro dele tinha virado vidro" | NEJM 2020; Sci Rep 2025 |
| F-047 | Herculano ficou sob ~15–25 m de material vulcânico. | CR | "cerca de vinte metros" | PAE |
| F-048 | A profundidade e o tipo de soterramento preservaram madeira, alimentos, tecidos e papiros carbonizados. | V | — | — |

### 3.8 Esquecimento e redescoberta

| ID | Afirmação | Status | Frase segura | Conferir |
|---|---|---|---|---|
| F-061 | Entre ~1594 e 1600, o engenheiro Domenico Fontana abriu um canal (Canale del Conte di Sarno) que atravessou o subsolo de Pompeia sem que ela fosse identificada. | CR | "no fim do século dezesseis" | — |
| F-062 | Herculano: achados a partir de 1709 (poço, príncipe d'Elbeuf); escavações oficiais em 1738 sob Carlos de Bourbon. | V | — | PAE |
| F-063 | Pompeia: escavações a partir de 1748; identificação definitiva por inscrição em 1763. | V | "só em 1763 uma inscrição confirmou" | PAP |
| F-064 | Em 1863, Giuseppe Fiorelli passou a injetar gesso nas cavidades deixadas pelos corpos na cinza. Os moldes contêm ossos em seu interior. | V | — | PAP |
| F-083 | O local nunca foi totalmente esquecido pelos camponeses (a área era chamada "La Civita"), mas a identidade e a localização exata de Pompeia se perderam. | CR | "o nome e o lugar exato se perderam" | — |

### 3.9 Ciência recente (o "nunca viu")

| ID | Afirmação | Status | Frase segura | Conferir |
|---|---|---|---|---|
| F-065 | Villa dos Papiros (Herculano): rolos encontrados em 1750–1754 (contagens variam ~1.100–1.800), provavelmente da família de Lúcio Calpúrnio Pisão, sogro de Júlio César. | CR | "provavelmente do sogro de Júlio César" | — |
| F-066 | Vesuvius Challenge lançado em março de 2023 (Nat Friedman, Daniel Gross, Brent Seales), com tomografias de raios-X de rolos fechados. | V | — | scrollprize.org |
| F-067 | Em outubro de 2023, Luke Farritor (21 anos, estudante) usou aprendizado de máquina para detectar a primeira palavra em um rolo fechado: ΠΟΡΦΥΡΑϹ ("púrpura"). Youssef Nader chegou ao mesmo trecho de forma independente. | V | "a palavra era: púrpura" | scrollprize.org; Nature news |
| F-068 | Em fevereiro de 2024, o grande prêmio (US$ 700 mil) foi para Youssef Nader, Luke Farritor e Julian Schilliger: mais de 2.000 caracteres em 15 colunas, texto filosófico sobre o prazer (atribuído a Filodemo). | V | "mais de duas mil letras" | scrollprize.org |
| F-069 | Em 2025, o título de outro rolo (PHerc. 172, Oxford) foi lido: Filodemo, *Sobre os vícios*. | CR | "em 2025, o título de outro rolo foi lido pela primeira vez" | Bodleian/Oxford, mai/2025 |
| F-070 | Pilli et al., *Current Biology*, nov/2024: DNA antigo de moldes mostrou que o adulto com bracelete de ouro segurando uma criança (Casa do Bracelete de Ouro), tido como "mãe e filho", era um homem sem parentesco com a criança; um par abraçado, interpretado como mãe/filha ou irmãs, incluía ao menos um homem; ancestralidade predominantemente ligada ao Mediterrâneo oriental. | V | — | Current Biology 2024 |
| F-071 | Estudo de 2024 (Frontiers in Earth Science) sugere vítimas mortas por desabamentos causados por terremotos durante a erupção (Insula dos Castos Amantes). | CR | (reserva) | Frontiers 2024 |

### 3.10 Depois de 79 e hoje

| ID | Afirmação | Status | Frase segura | Conferir |
|---|---|---|---|---|
| F-072 | Erupção de 16 de dezembro de 1631: milhares de mortos (estimativas ~3–6 mil). | CR | "matou milhares de pessoas" | GVP |
| F-073 | Erupção de março de 1944 (última até hoje): destruiu dezenas (~80) de bombardeiros B-25 da USAAF no campo de Terzigno. | CR | "dezenas de bombardeiros americanos" | USAF Historical; fotos Signal Corps |
| F-074 | Zona vermelha do plano Vesúvio: 25 municípios, ~700 mil residentes. | CR | "cerca de setecentas mil pessoas" | Protezione Civile |
| F-075 | O plano prevê evacuação total da zona vermelha em 72 horas. | V | "setenta e duas horas" | Protezione Civile |
| F-076 | Região metropolitana de Nápoles: ~3 milhões de habitantes. | V | "mais de três milhões" | ISTAT |
| F-077 | O Osservatorio Vesuviano, fundado em 1841, é o observatório vulcanológico mais antigo do mundo (hoje parte do INGV). | V | — | INGV-OV |
| F-079 | Pompeia: Patrimônio Mundial da UNESCO (1997); ~4 milhões de visitantes por ano. | V | (metadados/reserva) | PAP |

### 3.11 Mitos a desmontar

| ID | Mito | Realidade | Onde no roteiro |
|---|---|---|---|
| M-01 | "A lava destruiu Pompeia." | Quase não houve lava. Pomes + correntes piroclásticas. (F-020) | B3 |
| M-02 | "Foi instantâneo, ninguém teve chance." | Houve ~18 horas entre o início e a corrente fatal em Pompeia; a maioria fugiu. (F-039, F-056) | B3, B5 |
| M-03 | "Foi em 24 de agosto." | Provavelmente outubro (D). (F-018, F-019) | B0, B7 |
| M-04 | "Os moldes são estátuas / pessoas petrificadas." | São gesso derramado nas cavidades; contêm ossos. (F-064) | B6 |
| M-05 | "A 'mãe com o filho'..." | DNA: homem sem parentesco. (F-070) | B7 |
| M-06 | "O Vesúvio é um vulcão extinto/ adormecido para sempre." | Ativo; última erupção 1944. (F-073) | B8 |

---

## 4. Timeline mestra

### 4.1 Timeline longa (para MG-06)

| Ano | Evento | Fato |
|---|---|---|
| ~1900 a.C. | Erupção de Avellino | F-002 |
| 73 a.C. | Espártaco no Vesúvio | F-004 |
| 62/63 d.C. | Grande terremoto | F-012 |
| 79 d.C. | Erupção — Pompeia, Herculano, Estábia, Oplontis | F-020 |
| 472 | Grande erupção (cinzas até Constantinopla, segundo relatos) | (verificar antes de usar) |
| 1594–1600 | Canal de Fontana atravessa Pompeia | F-061 |
| 1631 | Erupção mata milhares | F-072 |
| 1709 / 1738 | Herculano redescoberta / escavações oficiais | F-062 |
| 1748 / 1763 | Escavações em Pompeia / identificação | F-063 |
| 1750–1754 | Papiros da Villa dos Papiros | F-065 |
| 1841 | Osservatorio Vesuviano | F-077 |
| 1863 | Moldes de Fiorelli | F-064 |
| 1944 | Última erupção | F-073 |
| 1980–82 | Esqueletos dos fornici em Herculano | F-041 |
| 2018 | Inscrição de 17 de outubro | F-018 |
| 2020 | Cérebro vitrificado publicado | F-046 |
| 2023 | Vesuvius Challenge: primeira palavra | F-067 |
| 2024 | Grande prêmio dos papiros; DNA dos moldes | F-068, F-070 |
| 2025 | Título de rolo lido; estudo do vidro a 510 °C | F-069, F-046 |

### 4.2 Timeline "hora a hora" (para o HUD MG-01)

> Horários são **reconstituições** (convertendo horas romanas e modelos vulcanológicos). O HUD deve exibir "≈" antes da hora. Datas mostradas como "DIA 1 / DIA 2" para não cravar 24 de agosto nem 24 de outubro (o debate é revelado no vídeo).

| HUD | Pompeia | Herculano | Miseno / Plínios | Fato |
|---|---|---|---|---|
| DIA 1 · ≈ 13:00 | Coluna surge a noroeste | Coluna visível | Mãe de Plínio Jovem avisa o tio sobre a nuvem | F-021 |
| DIA 1 · ≈ 13:30 | Começa a chuva de pomes branco | Pouca queda | Chega a mensagem de Rectina; quadrirremes lançadas | F-032, F-033 |
| DIA 1 · ≈ 15:00 | Céu escurece; ~25–30 cm de pomes; fuga em massa | Habitantes observam; parte foge | Plínio Velho se aproxima da costa; "Fortes fortuna iuvat" | F-034, F-036 |
| DIA 1 · ≈ 17:00–20:00 | Pomes cinza; telhados começam a ceder | Abrigo nos fornici | Plínio Velho em Estábia; banho, jantar | F-037, F-050 |
| DIA 1/2 · ≈ 00:00–01:00 | Pomes > 2 m | **Primeira corrente piroclástica** | Plínio dorme; pátio enchendo | F-043, F-051 |
| DIA 2 · ≈ 05:00–06:30 | Correntes param perto dos muros | Novas correntes; cidade soterrada | Plínio Velho vai à praia com travesseiros | F-052 |
| DIA 2 · ≈ 06:30–07:30 | **Corrente atravessa a cidade — fim** | — | Plínio Velho morre na praia de Estábia | F-053, F-056 |
| DIA 2 · ≈ 08:00 | Novas correntes; escuridão total | — | Miseno: escuridão "de quarto fechado"; fuga de Plínio Jovem e mãe | F-059 |
| DIA 3 | — | — | Luz volta; corpo de Plínio Velho é achado | F-055 |

---

## 5. Fontes (base de `sources.json`)

| ID | Fonte | Tipo | Uso |
|---|---|---|---|
| SRC-001 | Plínio, o Jovem, *Epistulae* 6.16 e 6.20 (texto latino em domínio público; ex.: The Latin Library, Perseus) | Primária | Narrativa dos Plínios |
| SRC-002 | Sêneca, *Naturales Quaestiones* VI | Primária | Terremoto |
| SRC-003 | Estrabão, *Geografia* 5.4.8 | Primária | Montanha antes de 79 |
| SRC-004 | Sigurdsson, H. et al. (1985). "The eruption of Vesuvius in A.D. 79". *National Geographic Research* 1(3) | Acadêmica | Fases da erupção |
| SRC-005 | Carey, S. & Sigurdsson, H. (1987). "Temporal variations in column height and magma discharge rate during the 79 A.D. eruption of Vesuvius". *GSA Bulletin* 99 | Acadêmica | Altura da coluna |
| SRC-006 | Luongo, G. et al. (2003). "Impact of the AD 79 explosive eruption on Pompeii". *J. Volcanol. Geotherm. Res.* 126 | Acadêmica | Vítimas e causas |
| SRC-007 | Petrone, P. et al. (2020). "Heat-Induced Brain Vitrification from the Vesuvius Eruption in C.E. 79". *NEJM* 382 | Acadêmica | Cérebro vitrificado |
| SRC-008 | Estudo de 2025 sobre a formação do vidro cerebral (Scientific Reports) | Acadêmica | 510 °C e resfriamento rápido |
| SRC-009 | Pilli, E. et al. (2024). DNA antigo das vítimas de Pompeia. *Current Biology* | Acadêmica | DNA dos moldes |
| SRC-010 | scrollprize.org (Vesuvius Challenge) — anúncios 2023–2025 | Institucional | Papiros |
| SRC-011 | Parco Archeologico di Pompei — comunicados (2018 inscrição; 2020 termopólio; 2023 afresco) | Institucional | Descobertas |
| SRC-012 | Parco Archeologico di Ercolano | Institucional | Herculano |
| SRC-013 | INGV — Osservatorio Vesuviano | Institucional | Monitoramento |
| SRC-014 | Dipartimento della Protezione Civile — Piano nazionale Vesuvio | Institucional | Zona vermelha, 72 h |
| SRC-015 | Smithsonian Global Volcanism Program — Vesuvius | Institucional | Histórico eruptivo |
| SRC-016 | Beard, M. (2008). *Pompeii: The Life of a Roman Town* | Livro | Vida cotidiana, ressalvas |
| SRC-017 | Plutarco, *Vida de Crasso* 9 | Primária | Espártaco |
| SRC-018 | Mastrolorenzo, G. et al. (2010). "Lethal thermal impact at periphery of pyroclastic surges". *PLoS ONE* | Acadêmica | Temperaturas |

---

## 6. Regras de citação de textos antigos

- O texto latino de Plínio é domínio público; **traduções modernas publicadas não são**. A narração usa **paráfrase própria**.
- Em motion graphics de "documento" (MG-07), mostrar a frase **em latim** + tradução própria. Trechos aprovados:
  - Ep. 6.16.5 — *"...arbor potius quam pinus expresserit"* (a forma de pinheiro).
  - Ep. 6.16.11 — *"Fortes fortuna iuvat"*.
  - Ep. 6.20.14 — *"...nox non qualis inlunis aut nubila, sed qualis in locis clausis lumine exstincto"*.
  - Ep. 6.20.5 — *"agebam duodevicensimum annum"*.
- O A03 deve conferir cada trecho latino numa edição crítica antes do G1 (grafia e numeração dos parágrafos).
