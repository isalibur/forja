# 07 — Arquitetura e Integrações

> **Para a IA que vai programar:** núcleo em Python, templates em Remotion, ferramentas pesadas como processos separados, tudo ligado por **adaptadores** declarados em config. Fluxo determinístico; LLM só dentro das etapas, sempre com JSON validado.

---

## 1. Etapas (`config/pipeline.yaml`)

```yaml
# ENTRADA
E00_entrada:        {needs: []}
# PLANEJAMENTO
P1_leitura:         {needs: [E00_entrada], llm: structured}
P2_narracao:        {needs: [P1_leitura], gpu: tts, skip_if: narracao_pronta}
P2b_alinhamento:    {needs: [P2_narracao], gpu: whisper}
P3_estrategia:      {needs: [P1_leitura], llm: structured}
P4_shots:           {needs: [P3_estrategia], llm: structured, por: bloco}
P5_ativos:          {needs: [P4_shots]}
P6_verificador:     {needs: [P5_ativos, P2b_alinhamento], loop_llm: 3}
P7_resolucao:       {needs: [P6_verificador], por: ativo}        # biblioteca → pesquisa → curadoria → rascunho → lista de busca
P8_estimativa_previa: {needs: [P7_resolucao]}
T1_traducao:        {needs: [P1_leitura], por: idioma_extra}      # roda já no planejamento
T2_narracao_idiomas:{needs: [T1_traducao], gpu: tts, por: idioma_extra}
PRE_imagens:        {needs: [P8_estimativa_previa], gpu: imagem, opcional: pre_gerar}
REVISAO:            {gate: true, needs: [P8_estimativa_previa]}   # você revisa e clica "Produzir"
# PRODUÇÃO
R1_imagens:         {needs: [REVISAO], gpu: imagem, por: ativo_gerar}
R2_tratamento:      {needs: [R1_imagens], gpu: leve, por: ativo}  # upscale, recorte, parallax (DepthFlow)
R3_mapas:           {needs: [REVISAO]}
R4_trilha_sfx:      {needs: [REVISAO]}
R5_montagem:        {needs: [R2_tratamento, R3_mapas, R4_trilha_sfx, T2_narracao_idiomas], por: idioma}
R6_mix:             {needs: [R5_montagem], por: idioma}
R7_render:          {needs: [R6_mix], por: idioma}                 # por bloco, depois concat
R8_qa:              {needs: [R7_render], por: idioma, autocorrecao: 2}
R9_pacote:          {needs: [R8_qa], por: idioma, llm: structured} # legendas, títulos, descrição, thumbnails, créditos, OTIO
R10_biblioteca:     {needs: [R9_pacote], opcional: true}           # propor ativos para a biblioteca
```

**Etapas por tipo de projeto** (o executor escolhe a lista conforme `tipo`):

| Tipo | Etapas |
|---|---|
| `longo` | as de cima |
| `short_derivado` | `S1_candidatos` (pontua trechos do plano longo) → `S2_ponte` (frases-ponte para aprovar) → `S3_verticalizar` (reenquadra ativos, layout 9:16) → `P6_verificador` (regras DS) → `R5…R9` em 9:16 com legendas queimadas |
| `short_avulso` | `E00_entrada` → `SA1_roteiro` (seu, por fórmula ou Gemini manual) → `P1…P8` com templates V/T e regras DS → `REVISAO` → `R1…R9` em 9:16; suporta **lote** (CSV de temas → N projetos) |
| `musica` | `MU1_faixas` (fichas de direito, ordem, normalização) → `MU2_cena` (imagens, máscaras, animações L01–L06) → `MU3_loop` (clipe que emenda) → `REVISAO` → `MU4_audio` (crossfades, ambiente) → `MU5_montagem` (stream_loop + sobreposições, NVENC) → `R8_qa` → `R9_pacote` (tracklist, metadados, thumbs, shorts opcionais) |

Ao final de qualquer tipo: `R10_global` propõe o que promover para a pasta global (`13 §3`).

**Mecanismos (iguais à v1, simplificados):** estado em SQLite + arquivos; retomada após queda; idempotência por hash de entrada; invalidação seletiva (trocar uma imagem refaz só o tratamento, o trecho da montagem e o render daquele bloco); **um semáforo de GPU** com agrupamento por modelo; cotas por provedor com fallback para o Ollama; escrita atômica.

## 2. Adaptadores (integrações plugáveis)

```python
class TTSAdapter(Protocol):        # chatterbox, kokoro, voicestudio, openai_compat, arquivo_pronto
    licenca: str; comercial: bool; idiomas: list[str]
    def sintetizar(self, texto: str, idioma: str, voz: VozConfig, params: dict) -> Path: ...

class ImagemAdapter(Protocol):     # comfyui (workflows), api_externa
    def gerar(self, prompt: str, negativo: str, refs: list[Path], tamanho: tuple[int,int], seed: int) -> Path: ...

class AcervoAdapter(Protocol):     # wikimedia, aic, met, openverse, loc, europeana, nasa, pexels, pixabay
    def buscar(self, consulta: str, n: int) -> list[Candidato]: ...
    def baixar(self, c: Candidato, destino: Path) -> Path: ...

class AnimacaoAdapter(Protocol):   # depthflow (parallax), rembg (recorte), realesrgan (upscale)
    def processar(self, entrada: Path, params: dict, destino: Path) -> Path: ...

class ExportAdapter(Protocol):     # mp4, srt, otio (DaVinci Resolve), zip_projeto
    def exportar(self, projeto: Projeto, idioma: str, destino: Path) -> list[Path]: ...

class Notificador(Protocol):       # hermes, telegram, nenhum
    def avisar(self, evento: Evento) -> None: ...
```

`config/adaptadores.yaml` liga cada papel a um adaptador:
```yaml
tts:        {pt-BR: chatterbox, en: kokoro, es: kokoro}
imagem:     comfyui
animacao:   {parallax: depthflow, recorte: rembg_birefnet, upscale: realesrgan}
acervo:     [wikimedia, aic, met, openverse, loc, europeana, nasa, pexels, pixabay]
exportar:   [mp4, srt, otio]
notificar:  hermes      # ou: nenhum
llm:
  structured: {provedor: openai_compat, base_url: "http://localhost:20128/v1", modelo: "<nome-do-combo-no-9router>"}
  local:      {provedor: ollama, modelo: "qwen3:8b"}
  visao:      {provedor: ollama, modelo: "qwen2.5vl:7b"}
  reserva:    {provedor: openrouter, opcional: true}
```

**LLM via 9Router:** o tier `structured` aponta para o endpoint OpenAI-compatível do seu 9Router; a rotação entre IAs gratuitas acontece **dentro** do 9Router (combos). O DocForja não conta com saída JSON nativa do provedor: pede JSON no prompt, valida com Pydantic e repara com o Ollama se vier quebrado. Visão (curadoria de imagens) usa sempre o Ollama local.

**Adicionar uma ferramenta nova** = um arquivo em `src/docforja/adaptadores/<tipo>/<nome>.py` que implementa o protocolo + uma linha no YAML. O sistema recusa adaptadores `comercial: false` em projetos monetizados.

Ferramentas AGPL (DepthFlow, VoiceStudio) e GPL (ComfyUI) são chamadas como **processos/serviços separados** (CLI ou HTTP), nunca importadas no código do DocForja.

## 3. Repositório

```
docforja/
├── AGENTS.md · pyproject.toml · .env.example
├── .agents/skills/            # Remotion Agent Skills + skills próprias do projeto
├── config/  pipeline.yaml · adaptadores.yaml · modelos.yaml · dosagem.yaml · presets.yaml
├── prompts/ leitura · estrategia · shots · pesquisa · curadoria · prompt_imagem · traducao · pacote
├── src/docforja/
│   ├── cli.py · api.py · web/
│   ├── nucleo/       projeto, banco, etapas, executor, gpu, cache, cotas, eventos
│   ├── esquemas/     Plano, Bloco, Shot, Ativo, Segmento, Candidato, Credito, Timeline
│   ├── llm/          roteador (LiteLLM), reparo de JSON
│   ├── planejamento/ leitura, estrategia, shots, ativos, verificador, estimativa, previa, relatorios
│   ├── midia/        biblioteca, pesquisa, curadoria, pasta_manual, imagens, tratamento, mapas
│   ├── audio/        narracao, alinhamento, trilha, sfx, mix
│   ├── idiomas/      traducao, glossario, retime, i18n
│   ├── producao/     montagem, render, qa, pacote
│   ├── shorts/       candidatos, ponte, verticalizar, formulas, lote
│   ├── musica/       faixas, cena, mascaras, loop, montagem_longa
│   ├── estrategia/   titulos, descricao, thumbs_briefing, tags, verificacao_metadados (13 §4–5)
│   ├── global/       promoção, índice, busca, referências por ID (13 §3)
│   └── adaptadores/  tts/ imagem/ acervo/ animacao/ exportar/ notificar/
├── kits/cinza-e-brasa/        # código-fonte do kit inicial (03); instalado em D:\DocForja\global\kits\
└── tests/  unit/ · integration/ · fixtures/roteiro_60s/
```

## 4. Pasta de cada projeto

```
D:\DocForja\projetos\<slug>\
├── 00_entrada\    roteiro.md · glossario.yaml · narracao\<idioma>.wav (opcional) · documentos\ · opcoes.yaml
├── 01_plano\      plano.json · plano.md · previa.mp4 · lista_de_busca.md · numeros_na_tela.md · estimativa.md · verificacao.md · pesquisa\
├── 02_midias\     biblioteca\ · pesquisadas\ · geradas\ · manual\ ← você · nao_atribuidas\ · tratadas\ · escolhas.json
├── 03_audio\      <idioma>\ (narração, palavras.json, mix.wav) · trilha\ · sfx\
├── 04_montagem\   <idioma>\ (timeline.json, i18n.json, blocos\)
├── 05_saida\      <idioma>\ (video, legendas, thumbnails, metadados, shorts) · elementos\ · creditos.txt · relatorio.md · promover_para_global.md  (detalhes em 13 §2)
└── sistema\       banco, eventos, logs, cache
```

## 5. Interface (web local, `127.0.0.1:7860`)

> Especificação completa de design, tecnologia (React + TypeScript + Vite + Tailwind + shadcn/ui + @remotion/player) e telas em **`14-interface-ui.md`**, com protótipo visual em `mockups/docforja-ui.html`. A tabela abaixo é só o resumo do conteúdo de cada tela.

| Tela | O que tem |
|---|---|
| **Novo** | Escolher o tipo: **Vídeo longo** · **Short avulso** (ou campanha em lote) · **Canal de música**. Shorts derivados nascem da tela "Resultado"/"Plano" de um vídeo longo |
| **Novo vídeo longo** | Tema · roteiro (colar/enviar) · idiomas (principal + extras, modo de tradução) · narração (TTS com prévia de voz, ou enviar arquivo por idioma) · kit · preset (Rápido/Padrão/Caprichado) · densidade de motion · orçamento de tempo · pré-gerar imagens (sim/não) · monetizado |
| **Plano** | Prévia (player) · tabela por bloco (editar template, texto, imagem, plano B) · aba Ativos (origem de cada imagem, candidatas da pesquisa com licença e nota) · **Lista de busca** com envio por item · Números na tela · Estimativa · Verificação · botão **Produzir** |
| **Pasta manual** | Imagens recebidas, atribuição, sugestões, ficha de crédito |
| **Produção** | Progresso por etapa e idioma, tempo restante |
| **Resultado** | Player por idioma, arquivos, relatório, "refazer shot", "promover à biblioteca" |
| **Shorts** | Candidatos do vídeo longo (com nota e motivo), frases-ponte para aprovar; criação de short avulso por tema/objetivo/fórmula |
| **Música** | Lista de faixas com fichas de direito, imagens, máscaras, prévia do loop, tracklist |
| **Pasta global** | Kits, imagens, personagens, mapas, loops, trilhas, SFX, vozes, CTAs, fórmulas de shorts, blocos de metadados |

**CLI** (para automação e Hermes): `docforja novo [--tipo longo|short|musica] | planejar | status | produzir --codigo | refazer | shorts candidatos <slug> | shorts lote <arquivo.csv> | exportar-traducao | importar-traducao | exportar-metadados | global promover | doctor | benchmark`.
**API HTTP**: mesmas ações, só em `127.0.0.1`, com token local. Iniciar a produção pela API/CLI/Hermes exige o código de 6 dígitos mostrado na interface.

## 6. Hermes (opcional)

Operador pelo chat: cria projetos, avisa "plano pronto" com o resumo da lista de busca, pergunta sobre imagens não atribuídas, inicia a produção **só com o código que você digitar** e avisa quando o vídeo está pronto. Skill com lista fechada de comandos; usa o 9Router (não a GPU local). Detalhes de instalação em `09 §7`.
