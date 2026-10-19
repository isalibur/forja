# DocForja — estado atual para troca de agentes

Atualizado em 19 de outubro de 2026. Este arquivo registra somente o estado operacional; requisitos continuam em `docs/construtor/` e regras permanentes em `AGENTS.md`. Confirme sempre o HEAD e as alterações locais com Git antes de editar.

## Ponto de partida

- Branch de trabalho: `m4.1-integracao-real`; marco-base da integração: `e2585eb`.
- Implementado: CLI e API registram os mesmos handlers para E00 (entrada), P1 (leitura), P2 (Kokoro), P2b (WhisperX), P3 (estratégia), P4 (shots), P5 (consolidação de ativos) e P6 (verificação de dosagem). P3 grava `estrategia.json`; P4 grava `shots.json`; P5 grava `ativos.json`; P6 exige alinhamento aprovado, grava `plano_verificado.json` e `verificacao.json` e publica `plano.json`, `plano.md`, `verificacao.md`, `estimativa.md` e `numeros_na_tela.md` como rascunho M4 anterior à resolução de ativos. A retomada valida os hashes das entradas e saídas. A opção `--ate` executa só as dependências da etapa pedida. Etapas sem handler falham explicitamente.
- Resolução de lacunas M3/M4:
  1. Worker WhisperX e `AlinhadorWhisperX` agora aceitam seleção do modelo ASR (`--model`/`modelo`), com padrão `"base"`.
  2. Refação seletiva de áudio agora compara a nova tomada com a anterior e descarta novas tomadas que piorem o WER do segmento, preservando a melhor tomada e atualizando o áudio mestre.
  3. P4 integra tempos reais do áudio (`03_audio/<idioma>/segmentos.json` com marcação `"tempos": "reais"`); o validador `shots_validos` invalida shots estimados se a narração real estiver presente, e a conclusão de P2 e o início de P6 recalculam shots e ativos com tempos reais.
  4. P6 integra loop de reenvio ao LLM (`loop_llm: 3`) via `RoteadorLLM` para blocos com violações não sanadas por código, atualizando shots e ativos e re-verificando antes de reprovar o plano.
- Verificação atual: 94 testes unitários passaram; Ruff passou sem avisos. Os testes automatizados de áudio usam adaptadores simulados. Há um teste manual reproduzível em `scripts/smoke_real_p6.py`, com artefatos fora do repositório em E:.
- Prova com motores reais em um projeto temporário: Kokoro gerou WAV; WhisperX com ASR `base` transcreveu “A história com Mesa Raki” para a referência “A história começa aqui.” e reprovou WER de 75%, mesmo após refação. A amostra tem apenas quatro palavras e não demonstra a qualidade em um roteiro representativo. Os arquivos estão em `.pytest_tmp/m3_real_smoke/` (ignorado pelo Git).
- Amostra real adicional: três segmentos do roteiro oficial foram narrados como um único áudio (~62 palavras). O ASR errou uma palavra e escreveu três números em algarismos; WER bruto 6,90%, WER com equivalência entre números escritos e falados 1,72%. O limite permanece 2% e o WER bruto é preservado no relatório de qualidade. Artefatos em `.pytest_tmp/m3_wer_amostra/` (ignorado pelo Git). Isso não equivale a validar toda a narração do projeto.
- Teste real E00→P6 com os mesmos três segmentos, desta vez separados: E00, P1, P2 e P3–P5 concluíram; P2b reprovou e P6 não rodou. A primeira execução tinha WER global normalizado de 1,72%, mas uma exigência adicional por segmento curto provocou refação e piorou para 3,45%. Essa exigência foi removida: o limite de 2% agora se aplica ao áudio completo, preservando WER por segmento para diagnóstico. Na repetição, o ASR `base` transcreveu “Dezesseis” como “Dese seis” e reprovou com 3,45%. O alinhamento forçado também perdia IDs quando o WhisperX dividia frases; o mapeamento foi corrigido e confirmado no áudio real (62 palavras distribuídas por B0-S01/02/03). Artefatos: `E:/05_PROJETOS/forja/smoke-p6-qb_iq7w4/` e `smoke-p6-k1mo2u9d/`.

## Pendências e próxima tarefa

- Validar a qualidade na narração completa com modelo ASR adequado (e.g. teste com modelo Whisper mais preciso ou benchmark local) e confirmar execução real até P6 em projeto completo.
- O grafo preserva P7 (resolução de ativos, M5) antes de P8 (estimativa final e prévia em vídeo); nenhuma das duas tem handler. Os relatórios de M4 não incluem `previa.mp4` nem equivalem ao planejamento completo de M5. P5 usa a heurística existente de origem de ativos, sem consultar a biblioteca do canal. Próxima tarefa: validação real fim a fim e preparação dos handlers de P7 (resolução de ativos, M5).
- `docs/contexto/M3.md` e `M4.md` descrevem o estado histórico das respectivas branches; não usar suas contagens de testes ou alegações de conclusão como estado atual.

## Entrega entre Codex e Antigravity

Com a mesma pasta aberta nos dois aplicativos, mantenha apenas um agente editando por vez. O segundo pode revisar em modo de leitura. Para implementação simultânea, use branches/worktrees distintos e delimite arquivos. Ao concluir uma tarefa, registre aqui somente mudanças materiais, evidência de testes, limitações e próxima ação; informe commit/branch na resposta. Não copie conversas nem saídas extensas de comandos para este arquivo.
