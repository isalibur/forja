# DocForja — estado atual para troca de agentes

Atualizado em 19 de outubro de 2026. Este arquivo registra somente o estado operacional; requisitos continuam em `docs/construtor/` e regras permanentes em `AGENTS.md`. Confirme sempre o HEAD e as alterações locais com Git antes de editar.

## Ponto de partida

- Branch de trabalho: `m4.1-integracao-real`; marco-base da integração: `e2585eb`.
- Implementado: CLI e API registram os handlers para E00, P1, P2, P2b, P3, P4, P5, P6, P7 e P8 (estimativa final e prévia, Marco M5). A retomada valida os hashes das entradas e saídas. A opção `--ate` executa só as dependências da etapa pedida. Etapas sem handler falham explicitamente.
- Validação completa da narração M3 e P6/P7 (19/10/2026):
  1. Execução end-to-end do pipeline completo E00→P7 no roteiro oficial de 116 segmentos (9 blocos, 2.435 palavras, 845,45 s / ~14,1 min de áudio) em `E:/05_PROJETOS/forja/smoke-p6-completo-qso23j2u/p6-real-completo`.
  2. ASR `whisper-large-v3-turbo-ct2` validado: WER bruto 6,09%, WER normalizado 1,78% (abaixo do limite de 2,00%), aprovando o critério de aceite M3 na narração completa.
  3. Correção de parser em `planejamento/leitura.py`: remoção do vazamento de marcações de HUD e de seções posteriores ao roteiro (tabelas do Script Doctor e notas de TTS) no `texto_limpo`.
  4. Aperfeiçoamento de `audio/metricas.py`: normalização integral de numerais compostos em português (anos como "mil setecentos e quarenta e oito" → 1748, centenas, milhares) sem alterar palavras originais.
  5. Localização robusta de tomadas de áudio (`_localizar_audio_segmento`) em `nucleo/handlers.py` para preservação seletiva de tomadas.
  6. P6 aprovou dosagem com tempos reais do áudio após autocorreção das regras D1.
  7. Módulo `midia/` (Marco M5) implementado e integrado via handler `P7_resolucao`:
     - `licenca.py`: classificação de licenças (bloqueio de NC/ND, permissão de PD/CC0/CC-BY), detecção de patrimônio cultural italiano restrito e sidecars `.licenca.json`.
     - `lista_busca.md`: gerador de `01_plano/lista_de_busca.md` conforme `docs/construtor/04-imagens-e-animacao.md §3`.
     - `pasta_manual.py`: monitoramento de `02_midias/manual/` e roteamento de não identificados para `nao_atribuidas/`.
     - `acervo.py`: protocolo `AcervoAdapter` e adaptador Wikimedia com User-Agent e conformidade.
     - `curadoria.py`: curador visual com suporte a Ollama `qwen2.5vl:7b` e fallbacks determinísticos.
     - `resolucao.py`: orquestrador de resolução gravando `ativos_resolvidos.json` (89 ativos resolvidos no projeto oficial) e `escolhas.json`.
- P8 no roteiro oficial (19/10/2026): o plano verificado por P6 somava apenas 612,65 s de shots porque D1 encurtou suas durações, apesar de o WAV ter 845,45 s. O P8 monta a prévia a partir de `segmentos.json`, cobrindo os 116 segmentos e mantendo os cartões sem segmento sobrepostos, sem deslocar o áudio. `plano.json`/`plano.md` finais contêm `inicio_s`/`fim_s` reais; `plano_verificado.json` e a verificação P6 originais são preservados. A prévia em `01_plano/previa.mp4` foi renderizada em 960×540, H.264/AAC, 845,46 s, com placeholders identificados e narração audível; imagens sem ficha de licença não são inseridas. A estimativa final usa a duração real: 54,2 min para orçamento de 120 min. E00→P8 concluiu e a retomada repetida reutilizou os artefatos válidos. A checagem visual de um quadro foi feita em 01:35. Trilha provisória ainda não incluída.
- Verificação automatizada: 107 testes unitários passando (`uv run pytest tests/unit`) sem GPU e sem rede; Ruff e TypeScript do kit passaram. A renderização real foi verificada separadamente com FFprobe.

## Pendências e próxima tarefa

- M5 ainda não está integralmente aceito: P8 usa animatic de placeholders (não aplica os templates finais nem trilha provisória), e a interface de Plano/Ativos/Lista de busca com player e atualização da pasta manual ainda precisa de validação. Corrigir a perda de duração em D1 na etapa P6 antes de M6 consumir o plano; por ora os tempos reais são restaurados apenas no plano final de P8.
- Fixação explícita do alinhador fonético de português e registro de hashes auxiliares em `config/lock.yaml`.

## Entrega entre Codex e Antigravity

Com a mesma pasta aberta nos dois aplicativos, mantenha apenas um agente editando por vez. O segundo pode revisar em modo de leitura. Para implementação simultânea, use branches/worktrees distintos e delimite arquivos. Ao concluir uma tarefa, registre aqui somente mudanças materiais, evidência de testes, limitações e próxima ação; informe commit/branch na resposta. Não copie conversas nem saídas extensas de comandos para este arquivo.
