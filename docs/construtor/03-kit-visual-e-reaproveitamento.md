# 03 — Kit Visual do Canal e Reaproveitamento

> **Objetivo:** cada vídeo novo sai mais rápido e mais coerente que o anterior. A identidade visual mora num **kit** versionado; os ativos bons de cada vídeo vão para uma **biblioteca** pesquisável.

---

## 1. Kit do canal (`D:\DocForja\global\kits\<nome>\`)

> Kits e biblioteca moram na **pasta global** (`13 §3`). Cada kit tem templates nos dois formatos: **16:9** (vídeo longo, canal de música) e **9:16** (shorts, `11 §2`).

```
kits/cinza-e-brasa/
├── kit.yaml                 # nome, versão, descrição, licenças dos itens
├── tokens.json              # cores, fontes, tamanhos, easing, durações, safe area
├── fontes/                  # arquivos de fonte (todas OFL/licença livre)
├── luts/                    # .cube por "modo" (quente, frio, arquivo, contemporâneo)
├── texturas/                # grão, poeira, papel, pedra, vinheta
├── abertura/ encerramento/  # vinheta de abertura (opcional), tela final
├── sons/                    # assinatura sonora, whooshes, ticks de UI, impactos (licenciados)
├── trilhas/                 # trilhas favoritas do canal (com license.json)
└── templates/               # pacote Remotion com T00–T14 + O1–O4 (versão própria)
```

**`tokens.json`** segue o formato de `../pipeline/06-direcao-de-arte-e-motion.md §2` (para o Vesúvio, o kit "cinza-e-brasa"). Um novo kit = copiar e mudar tokens; os templates continuam os mesmos.

**Regras do kit:**
- Os templates leem **só** tokens do kit: trocar o kit muda a cara de todos os vídeos sem mexer em código.
- O kit tem versão semântica (`1.2.0`). Um projeto registra o kit e a versão que usou; renderizar de novo dá o mesmo resultado.
- Mudanças visuais (nova transição, novo estilo de citação) entram no kit, nunca soltas num projeto.

## 2. Modos de cor por bloco

Em vez de um LUT por bloco feito à mão, o kit define **4–6 modos** e o planejador escolhe um por bloco (`P3`):

| Modo | Uso | Exemplo no Vesúvio |
|---|---|---|
| `quente` | vida, cotidiano, passado tranquilo | B1 |
| `tensao` | aviso, inquietação | B2 |
| `brasa` | ação, destruição (dessatura e preserva laranja) | B3–B5 |
| `arquivo` | memória, séc. XIX, documentos | B6 |
| `ciencia` | laboratório, descobertas | B7 |
| `contemporaneo` | o presente | B8 |

Fotos P&B de arquivo recebem só ajuste de níveis, nunca LUT de cor.

## 3. Templates Remotion (T00–T14, O1–O4)

- Pacote `@docforja/templates` dentro do kit, construído com Remotion e as **Remotion Agent Skills** (`06`).
- Cada template: componente puro + schema Zod das props + composição de teste + snapshot.
- Usar os pacotes oficiais quando existirem: `@remotion/transitions` (transições), `@remotion/captions` (legendas queimadas em Shorts), `@remotion/google-fonts` (fontes), `@remotion/media-utils` (áudio), `@remotion/paths`/`@remotion/shapes` (setas, destaques).
- Mapas (T10): D3-geo + dados Natural Earth (domínio público) para vetores; imagem de relevo/satélite pré-gerada como fundo (`04 §6`).
- Gráficos (T09): D3 (escalas) desenhando SVG no próprio componente.
- **Auto-ajuste de texto** em todos os templates: o texto encolhe (até 70%) ou quebra linha para caber, porque outros idiomas são mais longos (`05 §3`).
- Novo template = proposta no kit (componente + schema + teste + regras de uso para o planejador) → nova versão do kit.

## 3.1 Marca do projeto (camada sobre o kit)

Cada projeto pode ter uma **marca** própria sem criar um kit novo: logo, 1–2 cores de destaque, nome, contato (telefone, @, site) e cartão final. Os templates reservam espaço para logo e cartão final e leem esses dados de `00_entrada/marca.yaml`; o verificador confere contraste e legibilidade. Serve para conteúdo de terceiros e é a base dos pacotes personalizados do roadmap (`15 §2.4`).

## 4. Biblioteca de ativos (dentro de `D:\DocForja\global\` — estrutura completa em `13 §3`)

```
biblioteca/
├── imagens/      <id>.jpg + <id>.json  (descrição, tags, origem, licença, crédito, projetos que usaram, nota)
├── personagens/  <nome>/ referência + variações aprovadas + descrição para prompt
├── mapas/        recortes de relevo/satélite por região + GeoJSON de pontos/rotas/áreas
├── icones/       SVG (Lucide/Phosphor/Tabler — MIT/ISC)
└── indice.sqlite busca por texto (FTS5) + similaridade de imagem (embeddings CLIP)
```

**Entrada na biblioteca:** ao final de cada projeto, o sistema propõe promover para a biblioteca as imagens aprovadas (geradas, pesquisadas e as suas, com crédito), os personagens criados e os mapas. Você confirma em lote na tela "Resultado".

**Uso pelo planejador (P5):** antes de decidir `pesquisar` ou `gerar`, o sistema busca na biblioteca por texto e por similaridade com a descrição do ativo. Encontrou algo com nota ≥ 7 → `origem: biblioteca`. Isso economiza tempo e mantém consistência (ex.: o mesmo mapa base da Campânia em vários vídeos; o mesmo "Plínio" numa série).

**Séries:** projetos podem pertencer a uma série (`serie: roma-antiga`) que compartilha kit, personagens e mapas.

## 5. O que se reaproveita em cada vídeo novo

| Elemento | De onde vem |
|---|---|
| Visual (cores, fontes, templates, transições, texturas) | Kit |
| Vinheta, tela final, assinatura sonora | Kit |
| Trilhas favoritas e SFX recorrentes | Kit + biblioteca de som |
| Personagens recorrentes | Biblioteca (série) |
| Mapas de regiões já usadas | Biblioteca |
| Fotos de acervo já licenciadas | Biblioteca |
| Regras de dosagem (o "gosto" do canal) | `config/dosagem.yaml` |
| Prompts dos agentes | `prompts/` (versionados no repositório) |
