# AGENTS.md — DocForja

DocForja transforma roteiro e tema em um Plano de Vídeo revisável e depois produz documentários, shorts e vídeos de música localmente. O trabalho segue o marco pedido; não implemente fases futuras por antecipação.

## Onde consultar

- `docs/construtor/` é a fonte de verdade do software; `docs/pipeline/` define linguagem visual, som e ética. Em conflito, prevalece `docs/construtor/`.
- Antes de continuar trabalho em andamento, leia `docs/contexto/ESTADO_ATUAL.md` e confirme branch, último commit e alterações locais no Git. Os demais arquivos de `docs/contexto/` são registros históricos por marco.
- Localize o marco em `docs/construtor/08-marcos-de-construcao.md` e leia apenas as seções citadas por ele e os arquivos afetados.
- Plano e schemas: `docs/construtor/02-plano-de-video.md`; integrações: `07-arquitetura-e-integracoes.md`; instalação: `09-instalacao.md`; interface: `14-interface-ui.md`; saídas e pasta global: `13-saidas-pasta-global-e-metadados.md`.
- Código Remotion: use a skill pertinente de `.agents/skills/`; `remotion-best-practices` é o roteador. Consulte referências de mapas, legendas ou render somente quando a tarefa envolver essas áreas.
- Se faltar uma decisão que altere o produto ou o escopo, apresente a opção concreta ao usuário.

## Regras permanentes

- Python 3.11, type hints, Pydantic v2 nos dados entre módulos e `pathlib.Path`. Testes unitários sem rede nem GPU; prompts em `prompts/*.md.j2`; logs sem segredos.
- O planejador escolhe apenas templates do catálogo. Regras de dosagem ficam em `config/dosagem.yaml`; modelos e adaptadores em `config/modelos.yaml` e `config/adaptadores.yaml`, sem nomes fixos no código.
- Ferramentas externas usam adaptadores. AGPL/GPL (como DepthFlow e ComfyUI) rodam em processo ou serviço separado. Cargas de GPU, inclusive Ollama, usam o semáforo de `nucleo/gpu.py` quando ele existir.
- Escritas atômicas, versões sem sobrescrita, cache por hash e timeout/retry em chamadas externas.
- Interface: React, TypeScript, Tailwind e shadcn/ui; tokens do kit, textos em `i18n/<idioma>.json`, autoajuste e tarefas longas sem bloquear a tela. Siga o protótipo e a especificação da interface quando trabalhar nela.

## Proteções do produto

- Preserve o texto e os IDs dos segmentos do roteiro; apenas segmente e anote. Mantenha a revisão humana, o código de confirmação para produzir, o rótulo "RECONSTITUIÇÃO ARTÍSTICA", as fichas e checagens de licença, as regras éticas para vítimas e o controle de GPU.
- Em projetos monetizados, bloqueie mídia NC/ND, adaptadores `comercial: false` e pesos sem licença aprovada. Não promova ativos à pasta global sem licença e ficha.
- Não altere nem remova arquivos do usuário em `02_midias/manual/`, `00_entrada/` ou itens da pasta global sem confirmação. Não implemente upload, envio de mensagens em nome do usuário ou exclusão sem confirmação explícita.
- Para shorts de vendas, não invente depoimentos, resultados, avaliações ou urgência. Para música, exija ficha de direitos. Título e thumbnail devem cumprir a promessa do vídeo; ativos de terceiros não entram em pacote de revenda. Não queime links de afiliados no vídeo nem omita avisos de publicidade.
- Declaração do usuário para músicas: faixas que ele inserir são autorizadas por ele e geradas por IA. Registre a origem como declaração do usuário na ficha proprietária; a autorização de direitos não implica aprovação editorial para o canal. Mantenha qualquer restrição de publicação indicada pelo usuário.
- Não publique `.env`, chaves, modelos ou mídia. Antes de commit/push, confira o conjunto de arquivos incluídos. Trabalhe apenas no marco solicitado.
- As fases futuras A–D de `docs/construtor/15-roadmap-negocios.md` exigem pedido explícito.

## Verificação

Planeje brevemente os arquivos e testes relevantes. Rode `uv run pytest tests/unit` e `uv run ruff check src tests` para mudanças Python; para Remotion, use as verificações do kit afetado. Registre no resumo o que mudou, o que passou e o que ainda falta.
