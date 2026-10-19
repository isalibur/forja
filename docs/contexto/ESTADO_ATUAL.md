# DocForja — estado atual para troca de agentes

Atualizado em 19 de outubro de 2026. Este arquivo registra somente o estado operacional; requisitos continuam em `docs/construtor/` e regras permanentes em `AGENTS.md`. Confirme sempre o HEAD e as alterações locais com Git antes de editar.

## Ponto de partida

- Branch de trabalho: `m4.1-integracao-real`; marco-base da integração: `e2585eb`.
- Implementado: CLI e API registram os mesmos handlers para E00 (entrada), P1 (leitura), P2 (Kokoro), P2b (WhisperX), P3 (estratégia), P4 (shots), P5 (consolidação de ativos) e P6 (verificação de dosagem). P3 grava `estrategia.json`; P4 grava `shots.json`; P5 grava `ativos.json`; P6 exige alinhamento aprovado e grava `plano_verificado.json` e `verificacao.json` em `01_plano/`. A retomada valida as saídas e os hashes das entradas de P6. A opção `--ate` executa só as dependências da etapa pedida. Etapas sem handler falham explicitamente.
- Verificação atual: 85 testes unitários passaram; Ruff passou. Os testes automatizados de áudio usam adaptadores simulados.
- Prova com motores reais em um projeto temporário: Kokoro gerou WAV; WhisperX com ASR `base` transcreveu “A história com Mesa Raki” para a referência “A história começa aqui.” e reprovou WER de 75%, mesmo após refação. A amostra tem apenas quatro palavras e não demonstra a qualidade em um roteiro representativo. Os arquivos estão em `.pytest_tmp/m3_real_smoke/` (ignorado pelo Git).
- Amostra real adicional: três segmentos do roteiro oficial foram narrados como um único áudio (~62 palavras). O ASR errou uma palavra e escreveu três números em algarismos; WER bruto 6,90%, WER com equivalência entre números escritos e falados 1,72%. O limite permanece 2% e o WER bruto é preservado no relatório de qualidade. Artefatos em `.pytest_tmp/m3_wer_amostra/` (ignorado pelo Git). Isso não equivale a validar toda a narração do projeto.

## Pendências e próxima tarefa

- Validar a qualidade na narração completa e considerar a seleção do modelo ASR pela configuração. O worker `src/docforja/workers/whisperx_worker.py` ainda usa o modelo `base` fixo; `config/modelos.yaml` lista `whisperx-large-v3`, mas o benchmark desse candidato foi pulado e sua disponibilidade local não foi comprovada. Não reduzir o limite de WER de 2% sem evidência.
- O pipeline completo ainda não chega ao plano final: P7 pertence ao escopo de M5 e P8 não está conectado. P6 aplica correções por código, mas o reenvio ao LLM dos blocos ainda reprovados (até três voltas) não está integrado ao executor. P5 reutiliza a heurística existente de origem de ativos, mas ainda não consulta a biblioteca do canal antes de sugerir pesquisa/geração. P4 processa blocos em uma única etapa, sem retomada independente por bloco, e usa tempos estimados; falta invalidar/recalcular shots quando P2 produzir tempos reais. Próxima tarefa: revisar essas lacunas antes de ligar P8, que hoje depende de P7 no grafo.
- `docs/contexto/M3.md` e `M4.md` descrevem o estado histórico das respectivas branches; não usar suas contagens de testes ou alegações de conclusão como estado atual.

## Entrega entre Codex e Antigravity

Com a mesma pasta aberta nos dois aplicativos, mantenha apenas um agente editando por vez. O segundo pode revisar em modo de leitura. Para implementação simultânea, use branches/worktrees distintos e delimite arquivos. Ao concluir uma tarefa, registre aqui somente mudanças materiais, evidência de testes, limitações e próxima ação; informe commit/branch na resposta. Não copie conversas nem saídas extensas de comandos para este arquivo.
