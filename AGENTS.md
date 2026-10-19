# AGENTS.md — Regras do repositório DocForja (v2)

> Lido por OpenCode e Antigravity. Copie para a **raiz** do repositório `docforja/`.

## O que é

DocForja transforma **tema + roteiro** (escrito pelo usuário fora do sistema) num **Plano de Vídeo** completo e depois executa esse plano: narração (TTS ou pronta), fotos reais pesquisadas, imagens geradas, imagens do usuário, animação de imagens (Ken Burns, parallax, recorte), templates de texto/número/gráfico/mapa/linha do tempo, trilha, SFX, mix, render, legendas e pacote — em vários idiomas. Roda local (Windows 11, Ryzen 5 5500, RTX 3060 12 GB, 24 GB RAM). Sem vídeo gerado por IA.

Quatro tipos de projeto com o mesmo motor: `longo`, `short_derivado`, `short_avulso` (inclusive em lote) e `musica` (`docs/construtor/11`, `12`). Toda saída segue `docs/construtor/13 §2` e traz metadados estratégicos (`13 §4`). O que é reaproveitável vai para a **pasta global** (`13 §3`) e passa a ser referenciado por ID.

## Especificação

- `docs/construtor/` — fonte de verdade do software. Comece por `02-plano-de-video.md`: o plano é o centro.
- `docs/pipeline/` — linguagem visual, sonora e ética. Em conflito, vale `docs/construtor/`.
- Ambíguo? **Pare e pergunte.**

## Skills disponíveis

- `.agents/skills/` contém as **Remotion Agent Skills** (`remotion-best-practices` e relacionadas). Use-as em todo código Remotion.

## Comandos

```powershell
uv run pytest tests/unit
uv run pytest -m gpu tests/integration
uv run ruff check src tests ; uv run ruff format src tests
uv run docforja doctor
cd kits/cinza-e-brasa/templates ; npx tsc --noEmit ; npx remotion studio
```

## Convenções

- Python 3.11, type hints, Pydantic v2 em todo dado entre módulos, `pathlib.Path`.
- O planejador só escolhe templates do **catálogo** (`02 §3`); nada de componentes inventados por LLM. Novo template = nova versão do kit, com schema, teste e regras de uso.
- Regras de dosagem ficam em `config/dosagem.yaml`, nunca fixas no código.
- Templates leem só tokens do kit; textos vêm de `i18n/<idioma>.json`; todo texto com auto-ajuste.
- Ferramentas externas só por **adaptadores** (`07 §2`). AGPL/GPL (DepthFlow, VoiceStudio, ComfyUI) só como processo/serviço separado.
- Nenhum nome de modelo no código: use `config/modelos.yaml` e `config/adaptadores.yaml`.
- Toda carga de GPU (inclui Ollama) pelo semáforo de `nucleo/gpu.py`.
- Escrita atômica; versões nunca sobrescritas; cache por hash; timeouts e retry em chamadas externas.
- Interface (`web/`): React + TypeScript + Tailwind + shadcn/ui; siga `docs/construtor/14-interface-ui.md` e o protótipo `docs/construtor/mockups/docforja-ui.html`; cores de status fixas; textos em português simples; nenhuma tela bloqueia durante tarefas longas; tipos gerados do OpenAPI.
- Testes unitários sem rede e sem GPU; prompts em `prompts/*.md.j2`; logs sem segredos.

## Você NÃO pode

- Reescrever o texto do roteiro do usuário (só segmentar e anotar) nem mudar IDs de segmentos.
- Remover o ponto de revisão, o código de confirmação para produzir via CLI/API/Hermes, o rótulo "RECONSTITUIÇÃO ARTÍSTICA", a checagem de licenças, a ficha de crédito, as regras de ética com vítimas (D9, D17) ou o semáforo de GPU.
- Usar mídia NC/ND ou adaptadores `comercial: false` em projeto monetizado.
- Mover, alterar ou apagar arquivos do usuário (`02_midias/manual/`, `00_entrada/`) ou itens da pasta global sem confirmação.
- Promover para a pasta global algo sem licença/ficha registrada.
- Gerar depoimentos, números de resultado, avaliações ou urgências falsas em shorts de vendas (`11 §4.3`); aceitar faixa de música sem ficha de direito (`12 §6`).
- Títulos/thumbnails que prometem algo que o vídeo não entrega (regra M2 de `13 §5`).
- Implementar qualquer fase futura de `docs/construtor/15-roadmap-negocios.md` (A–D) sem pedido explícito.
- Colocar ativos de terceiros (acervo, pasta manual sem licença própria) em pacote de banco de imagens ou de revenda; queimar link de afiliado no vídeo ou omitir o aviso de publicidade.
- Implementar upload, envio de mensagens em nome do usuário ou exclusão sem confirmação explícita.
- Commitar `.env`, chaves, modelos ou mídia; mudar algo fora do escopo do marco.

## Fluxo

Ler pedido e seções citadas → plano curto (arquivos, funções, testes) → testes → implementação → `pytest`/`ruff`/`tsc` verdes → resumo do que mudou e divergências encontradas.
