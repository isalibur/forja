# Integração Hermes Agent + DocForja

Este diretório contém a skill do **DocForja** para ser utilizada com o [Hermes Agent](https://github.com/NousResearch/hermes-agent).

---

## 1. Arquitetura e Limites de Operação

O Hermes Agent atua como um **operador conversacional local**:
- Cria projetos estruturados.
- Monitora status de etapas, semáforo de GPU e cotas.
- Avisa quando o planejamento (`P8_estimativa_previa`) estiver concluído, resumindo a lista de busca pendente (`lista_de_busca.md`).
- Alerta sobre imagens recebidas na pasta manual não atribuídas (`02_midias/manual/nao_atribuidas/`).
- **Portão de segurança**: Inicia a produção apenas quando o usuário humano digitar o código de confirmação `PRODUZIR`. O Hermes está proibido de autogerar esse código.
- Avisa quando o pacote de entrega e o vídeo final estiverem concluídos.

O Hermes **não tem acesso direto à GPU**: suas chamadas de linguagem operam através do 9Router (`http://localhost:20128/v1`). O pipeline DocForja acionado por ele continua utilizando a GPU local (Kokoro, WhisperX, ComfyUI) sob o controle do semáforo `nucleo/gpu.py`.

---

## 2. Instalação no WSL2

Conforme especificado em `docs/construtor/09-instalacao.md §7`:

1. Configure a rede espelhada no Windows em `%UserProfile%\.wslconfig`:
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```
2. No WSL2, clone e configure o Hermes Agent:
   ```bash
   git clone https://github.com/NousResearch/hermes-agent.git
   cd hermes-agent
   pip install -r requirements.txt
   ```
3. Aponte o provedor de inferência do Hermes para o 9Router local:
   ```bash
   export OPENAI_BASE_URL="http://localhost:20128/v1"
   export OPENAI_API_KEY="dummy"
   ```
4. Copie esta pasta de skill para a pasta de skills do Hermes:
   ```bash
   cp -r /mnt/d/IA/forja/docforja/hermes/skills/docforja/ ~/.hermes/skills/
   ```
5. Configure as variáveis de ambiente em seu `.env`:
   ```dotenv
   TELEGRAM_BOT_TOKEN=seu_token_aqui
   TELEGRAM_CHAT_ID=seu_chat_id_aqui
   ```
   *Nota de segurança: O bot responderá estritamente às mensagens originadas do `TELEGRAM_CHAT_ID` autorizado.*
