# DocForja

Construtor de documentários, shorts e vídeos de música com IA, rodando localmente (Windows 11 · RTX 3060 12 GB).

| Para quem | Comece por |
|---|---|
| **Você (humano)** | [GUIA-DE-DESENVOLVIMENTO.md](GUIA-DE-DESENVOLVIMENTO.md) — o passo a passo do desenvolvimento |
| **A IA de programação** (OpenCode / Antigravity) | [AGENTS.md](AGENTS.md) → [docs/construtor/README.md](docs/construtor/README.md) → [docs/construtor/08-marcos-de-construcao.md](docs/construtor/08-marcos-de-construcao.md) |

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
