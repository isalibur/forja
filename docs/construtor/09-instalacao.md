# 09 — Instalação (Windows 11 + RTX 3060)

> O `docforja doctor` confere cada item. Fixe as versões que passarem no benchmark em `config/lock.yaml`.

## 1. Sistema
- Driver NVIDIA recente (`nvidia-smi`).
- Arquivo de paginação fixo de 32 GB no SSD.
- Pastas: `D:\DocForja\projetos\` e `D:\DocForja\global\` (kits, imagens, personagens, mapas, loops, musica, sfx, vozes, ctas, formulas_shorts, metadados — ver `13 §3`). ~200 GB livres recomendados.

## 2. Ferramentas
```powershell
winget install --id Git.Git
winget install --id astral-sh.uv
winget install --id OpenJS.NodeJS.LTS
winget install --id Gyan.FFmpeg
winget install --id Ollama.Ollama
```

## 3. ComfyUI (imagens)
1. ComfyUI portable (Windows/NVIDIA), em `D:\DocForja\ComfyUI\`; ComfyUI-Manager; nós GGUF e de imagem de referência.
2. `run_nvidia_gpu.bat --listen 127.0.0.1 --port 8188`.
3. Baixar 1–2 candidatos de modelo (Chroma1-HD / Qwen-Image GGUF / FLUX.1 schnell) + encoders + VAE, e um SDXL para rascunhos. Escolher no benchmark e apagar os que não usar.
4. Exportar os workflows em formato API para `docforja/workflows/` (+ `.bindings.yaml`).

## 4. Python
```powershell
git clone <seu-repo> D:\DocForja\docforja
cd D:\DocForja\docforja
uv venv --python 3.11
uv pip install -e ".[gpu,dev]"
```
- Núcleo: typer, fastapi, uvicorn, jinja2, python-multipart, sqlmodel, pydantic, litellm, httpx, tenacity, structlog, watchdog, python-docx, pillow, pyyaml, opentimelineio.
- `[gpu]`: torch (CUDA 12.x), whisperx, chatterbox-tts, kokoro, rembg (com BiRefNet), realesrgan, librosa, jiwer, pyloudnorm, rasterio, colour-science, open_clip (busca na biblioteca).
- **Ambientes separados** (chamados por subprocesso): `envs/depthflow` (`uv pip install depthflow`) e, se o torch conflitar, `envs/tts` e `envs/align`.
- **Alinhamento em português no Windows:** o ambiente `envs/align` também precisa dos dados NLTK `punkt_tab/portuguese` em `envs/align/nltk_data/tokenizers/`. Reaproveite a cópia local já instalada ou instale-os nesse diretório na preparação do ambiente. Evite depender de `%APPDATA%/nltk_data` quando o aplicativo virtualiza essa pasta: o NLTK pode localizar o arquivo, mas recusar sua abertura por segurança. Confira com `.\envs\align\Scripts\python.exe -c "import nltk; nltk.data.load('tokenizers/punkt_tab/portuguese.pickle'); print('punkt OK')"` antes de produzir vídeos.

## 5. Remotion + skills
```powershell
cd D:\DocForja\docforja
npx skills add remotion-dev/skills       # skills para o OpenCode/Antigravity (.agents/skills)
cd kits\cinza-e-brasa\templates
npm install
npx remotion studio
```
Licença do Remotion: grátis para pessoa física e empresas de até 3 funcionários (ver `01 §5`).

## 6. Ollama
```powershell
ollama pull qwen3:8b
ollama pull qwen2.5vl:7b
```
`OLLAMA_KEEP_ALIVE=0`.

## 7. Opcionais
- **Hermes Agent:** instalar pelo README oficial (`NousResearch/hermes-agent`), no WSL2 com `networkingMode=mirrored` em `%UserProfile%\.wslconfig`; provedor = endpoint do 9Router (`http://localhost:20128/v1`); copiar `hermes/skills/docforja/`; Telegram só com o seu chat ID.
- **DaVinci Resolve (gratuito):** para abrir o `projeto.otio` e finalizar à mão, se quiser.

### 7.1 VoiceStudio (opcional)
Ferramenta **separada** (app AGPL-3.0) para desenhar ou clonar voz, dublar, ditar, transcrever e gerar audiolivros. Ela nunca é embutida no DocForja: roda na sua máquina e entrega arquivo — ver `01 §` e `07 §`.

**Instalar (Windows 11 + RTX 3060)**
```powershell
# 1) instalador oficial (recomendado); preserva projetos, modelos e ajustes
irm https://voicestudio.sh/install | iex

# 2) ou o .exe da página de releases (debpalash/VoiceStudio/releases/latest)

# 3) ou a partir do GitHub — exige Git, Node.js 22+, Bun, Rust/Cargo e ferramentas de build
git clone https://github.com/debpalash/VoiceStudio.git
cd VoiceStudio
bun install
bun run setup:api      # dependências do backend Python antes de abrir o app
bun run dev

# 4) skill de agente, como as skills do Remotion neste repositório
npx skills add debpalash/VoiceStudio
```
O repositório traz guias por plataforma (`docs/install/windows.md`, `macos.md`, `linux.md`) e `docs/install/docker.md`.

**Aceleração:** NVIDIA (Windows/Linux) → CUDA; Apple Silicon → Metal; sem GPU dedicada → CPU (o setup instala o build pequeno do PyTorch, ~5 GB livres); Windows on ARM → experimental.

**API local e MCP (porta 3900)**
```powershell
curl http://127.0.0.1:3900/.well-known/voicestudio-speech          # capacidades do serviço
curl http://127.0.0.1:3900/v1/audio/transcriptions -F file=@voz.wav  # transcrição (formato OpenAI)
```
MCP: `POST http://127.0.0.1:3900/mcp` (HTTP) ou `python -m backend.mcp_shim` (stdio). Variáveis reconhecidas pelo app: `VOICESTUDIO_URL`, `OMNIVOICE_PORT` (3900), `OMNIVOICE_API_KEY`.

**Como usar com o DocForja (caminho suportado)**
1. No app, crie a voz (clonagem **com autorização do dono da voz** ou desenho) e exporte a narração em WAV.
2. Copie para `00_entrada/narracao_pt-BR.wav` (aceita `narracao_<idioma>.wav`/`.mp3`, `narracao.wav`/`.mp3` ou o caminho explícito em `opcoes.narracao_pronta`).
3. `docforja executar` importa, alinha com WhisperX contra o texto do roteiro e mede o WER; acima de 8% de divergência o sistema adota a transcrição como verdade de tempos e legendas e avisa no plano.
4. Registre a engine e a voz usadas em `00_entrada/opcoes.yaml` (`motor_tts`, `voz`, `monetizado`); a licença comercial da engine é responsabilidade sua e precisa estar conferida antes de publicar.

**Sintetizar direto pelo app (adaptador `voicestudio`)**
O app expõe a síntese em `POST {raiz}/v1/audio/speech`, no mesmo formato da OpenAI (`model` = engine instalada, `voice` = perfil de voz, `input` = texto). O adaptador do DocForja fala exatamente esse contrato e normaliza a saída em WAV 24 kHz mono.

```yaml
# config/adaptadores.yaml
voicestudio:
  base_url: http://127.0.0.1:3900
  engine: omnivoice          # engine instalada no app
  instrucoes: ""             # estilo (ex.: "feminina, sussurro" no OmniVoice)
```
- O projeto usa o motor com `motor_tts: voicestudio` e `voz: <perfil>`; a voz aceita o id ou o nome do perfil (`GET /v1/audio/voices` lista os disponíveis).
- **Escolha da voz:** o critério é a qualidade da voz. O app permite desenhar uma voz (sintética, sem identidade de terceiros) ou clonar uma voz **com autorização do dono** — o próprio app tem o registro de posse ("Voice ownership") e o perfil "verified own voice". O kit guarda o consentimento escrito, conforme `05 §1`.
- **Termos de uso:** a licença do app (AGPL-3.0) cobre o programa e admite uso comercial; os **pesos, as vozes e as condições da saída** têm termos próprios, gerenciados pelo app e exibidos no Model Manager. O DocForja não bloqueia a produção por isso e registra no projeto o motor, a voz e a origem usados.
- `docforja doctor` mostra o estado do serviço e a engine em uso; `docforja benchmark` faz um ping em `/v1/models`.

**Voz clonada do usuário (OmniVoice)**
O canal usa a voz do próprio dono, clonada no OmniVoice (`k2-fsa/OmniVoice`, 613M), que já roda local na máquina:

```yaml
# config/adaptadores.yaml
python_environments:
  omnivoice: D:/IA/audio_factory/.venv/Scripts/python.exe   # precisa do pacote `omnivoice`
omnivoice:
  modelo: k2-fsa/OmniVoice
  cache: D:/IA/audio_factory/models/voice_clone            # raiz do cache (HF_HOME)
  velocidade: 0.92
  passos: 64
```
```yaml
# config/modelos.yaml (tts)
- id: omnivoice-613m
  adaptador: omnivoice
  benchmark:
    model_repo: k2-fsa/OmniVoice
    voices:
      - id: nova_ref_7s
        language: pt-BR
        path: D:/IA/audio_factory/voices/nova_ref_7s.pt
        reference: D:/IA/audio_factory/voices/minha_voz_corte_7s.wav
```
E no projeto:
```yaml
# 00_entrada/opcoes.yaml
motor_tts: omnivoice
voz: nova_ref_7s
```
- O `.pt` é o **prompt de clonagem** (tokens da referência); o `.wav` é a referência de áudio. Os dois ficam no seu acervo de vozes, **fora do repositório**, e o consentimento do dono da voz (a sua) fica no kit, conforme `05 §1`.
- Medição real do caminho completo: 11,74 s de áudio em 28,8 s (com carga do modelo na GPU) e **WER 0,00 %** na checagem de qualidade do pipeline.
- O motor carrega o modelo a cada segmento: para um vídeo longo de muitos segmentos, o custo de carga se repete — nesse caso, prefira a "narração pronta" ou um motor mais leve.

**Limites conhecidos**
- O app é AGPL-3.0 e roda separado do DocForja; usá-lo como ferramenta local não impõe AGPL ao áudio nem aos vídeos gerados.
- A clonagem de voz de terceiros continua proibida sem autorização do dono da voz.
- Sem GPU dedicada o app roda em CPU (build pequeno do PyTorch, ~5 GB) e bem mais devagar.

## 8. Bibliotecas iniciais
- Música: as faixas inseridas pelo usuário podem ser indexadas com sua declaração geral de autorização, sem `license.json` individual. Para faixas obtidas de bibliotecas de terceiros, manter a licença comercial e os créditos exigidos pela fonte.
- SFX: pacotes royalty-free (ex.: os pacotes anuais gratuitos da Sonniss) + sons do kit.

## 9. `.env`
```dotenv
NINEROUTER_BASE_URL=http://localhost:20128/v1
NINEROUTER_API_KEY=            # se o seu 9Router exigir chave para clientes
OPENROUTER_API_KEY=            # opcional (reserva)
PEXELS_API_KEY=
PIXABAY_API_KEY=
EUROPEANA_API_KEY=
SMITHSONIAN_API_KEY=
FREESOUND_CLIENT_ID=
FREESOUND_CLIENT_SECRET=
OPENTOPOGRAPHY_API_KEY=
COPERNICUS_USER=
COPERNICUS_PASSWORD=
DOCFORJA_LOCAL_TOKEN=
OMNIVOICE_API_KEY=            # opcional: só se o seu VoiceStudio exigir bearer
WIKIMEDIA_USER_AGENT=DocForja/0.1 (contato: seu-email)
```

## 10. `config/presets.yaml` (resumo)
```yaml
rapido:     {resolucao: 1080p, takes: 1, variacoes_ia: 1, max_ia: 0.15, max_parallax: 0.15}
padrao:     {resolucao: 1080p, takes: 1, refazer_reprovados: true, variacoes_ia: 2, max_ia: 0.30, max_parallax: 0.30}
caprichado: {resolucao: 1440p, takes: 3, variacoes_ia: 3, max_ia: 0.40, max_parallax: 0.40}
orcamento_padrao_min: {rapido: 60, padrao: 120, caprichado: 240}
```
