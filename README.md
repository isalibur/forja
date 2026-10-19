# DocForja

Construtor de documentários, shorts e vídeos de música com IA, rodando localmente (Windows 11 · RTX 3060 12 GB).

| Para quem | Comece por |
|---|---|
| **Você (humano)** | [GUIA-DE-DESENVOLVIMENTO.md](GUIA-DE-DESENVOLVIMENTO.md) — o passo a passo do desenvolvimento |
| **A IA de programação** (OpenCode / Antigravity) | [AGENTS.md](AGENTS.md) indica as regras e qual documentação consultar para cada tarefa |

```
docforja/
├── AGENTS.md                    regras para a IA de programação
├── GUIA-DE-DESENVOLVIMENTO.md   instruções para você
├── .env.example                 chaves (copiar para .env)
├── .gitignore
└── docs/
    ├── construtor/              especificação do software (fonte de verdade) + protótipo da interface
    ├── negocios/                carteira de negócios (estratégia, para você)
    └── pipeline/                linguagem visual, som, ética e o exemplo completo do Vesúvio
```

## Desenvolvimento

Requer Python 3.11 e `uv`:

```powershell
uv sync --python 3.11 --extra dev
uv run docforja doctor
uv run docforja benchmark
uv run pytest tests/unit
uv run ruff check src tests
```

O diagnóstico não exibe valores do `.env`. O benchmark registra resultados em
`config/benchmark.json`; mídias geradas ficam em `benchmark_out/` e não entram no Git.
As cargas de benchmark são executadas sequencialmente para não disputar a GPU.

## Ensaios reais do M0

`uv run docforja benchmark --real` executa os candidatos configurados de imagem e voz.
Use `--category imagem` ou `--category tts` para repetir somente uma categoria.
Os modelos, caminhos e vozes ficam em `config/modelos.yaml`; os textos de teste em
`config/benchmark.yaml`. Candidatos sem configuração são registrados como pendentes.

Cada execução cria uma subpasta exclusiva em `paths.benchmark_output`, com amostras,
prompts, logs e `report.json`. O `config/benchmark.json` reúne os resultados mais recentes
por categoria. O pico de VRAM é amostrado na GPU inteira, incluindo o desktop.
As amostras TTS registram separadamente duração do áudio, síntese e tempo total do processo.
Há um bloqueio entre benchmarks DocForja; mantenha outras aplicações de IA ociosas.

O modo sem `--real` continua sendo o inventário com render sintético FFmpeg/NVENC;
ele substitui o resumo `config/benchmark.json`, mas não apaga os relatórios das execuções reais.
Esses renders de referência ainda não substituem o benchmark de composição Remotion.
