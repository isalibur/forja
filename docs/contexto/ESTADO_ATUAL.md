# DocForja — estado atual para troca de agentes

Atualizado em 19 de outubro de 2026. Este arquivo registra somente o estado operacional; requisitos continuam em `docs/construtor/` e regras permanentes em `AGENTS.md`. Confirme sempre o HEAD e as alterações locais com Git antes de editar.

## Ponto de partida

- Branch de trabalho: `m4.1-integracao-real`; marco-base da integração: `e2585eb`.
- Implementado: CLI e API registram os mesmos handlers para E00 (entrada), P1 (leitura), P2 (Kokoro), P2b (WhisperX), P3 (estratégia), P4 (shots), P5 (consolidação de ativos) e P6 (verificação de dosagem). P3 grava `estrategia.json`; P4 grava `shots.json`; P5 grava `ativos.json`; P6 exige alinhamento aprovado, grava `plano_verificado.json` e `verificacao.json` e publica `plano.json`, `plano.md`, `verificacao.md`, `estimativa.md` e `numeros_na_tela.md` como rascunho M4 anterior à resolução de ativos. A retomada valida os hashes das entradas e saídas. A opção `--ate` executa só as dependências da etapa pedida. Etapas sem handler falham explicitamente.
- Verificação atual: 86 testes unitários passaram; Ruff passou. Os testes automatizados de áudio usam adaptadores simulados.
- Prova com motores reais em um projeto temporário: Kokoro gerou WAV; WhisperX com ASR `base` transcreveu “A história com Mesa Raki” para a referência “A história começa aqui.” e reprovou WER de 75%, mesmo após refação. A amostra tem apenas quatro palavras e não demonstra a qualidade em um roteiro representativo. Os arquivos estão em `.pytest_tmp/m3_real_smoke/` (ignorado pelo Git).
- Amostra real adicional: três segmentos do roteiro oficial foram narrados como um único áudio (~62 palavras). O ASR errou uma palavra e escreveu três números em algarismos; WER bruto 6,90%, WER com equivalência entre números escritos e falados 1,72%. O limite permanece 2% e o WER bruto é preservado no relatório de qualidade. Artefatos em `.pytest_tmp/m3_wer_amostra/` (ignorado pelo Git). Isso não equivale a validar toda a narração do projeto.

## Pendências e próxima tarefa

- Validar a qualidade na narração completa e considerar a seleção do modelo ASR pela configuração. O worker `src/docforja/workers/whisperx_worker.py` ainda usa o modelo `base` fixo; `config/modelos.yaml` lista `whisperx-large-v3`, mas o benchmark desse candidato foi pulado e sua disponibilidade local não foi comprovada. Não reduzir o limite de WER de 2% sem evidência.
- O grafo preserva P7 (resolução de ativos, M5) antes de P8 (estimativa final e prévia em vídeo); nenhuma das duas tem handler. Os relatórios de M4 não incluem `previa.mp4` nem equivalem ao planejamento completo de M5. P6 aplica correções por código, mas o reenvio ao LLM dos blocos ainda reprovados (até três voltas) não está integrado. P5 usa a heurística existente de origem de ativos, sem consultar a biblioteca do canal. P4 processa blocos em uma única etapa, sem retomada independente por bloco, e usa tempos estimados; falta invalidar/recalcular shots quando P2 produzir tempos reais. Próxima tarefa: conferir um projeto real completo até P6 e corrigir essas lacunas de M3/M4 antes de iniciar P7.
- `docs/contexto/M3.md` e `M4.md` descrevem o estado histórico das respectivas branches; não usar suas contagens de testes ou alegações de conclusão como estado atual.

## Entrega entre Codex e Antigravity

Com a mesma pasta aberta nos dois aplicativos, mantenha apenas um agente editando por vez. O segundo pode revisar em modo de leitura. Para implementação simultânea, use branches/worktrees distintos e delimite arquivos. Ao concluir uma tarefa, registre aqui somente mudanças materiais, evidência de testes, limitações e próxima ação; informe commit/branch na resposta. Não copie conversas nem saídas extensas de comandos para este arquivo.
