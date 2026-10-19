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
- **VoiceStudio:** instalar o app pelo release oficial, se quiser usá-lo para criar narrações (exportar WAV → "narração pronta") ou, no M7, pelo adaptador — só com engines de licença comercial conferida.
- **DaVinci Resolve (gratuito):** para abrir o `projeto.otio` e finalizar à mão, se quiser.

## 8. Bibliotecas iniciais
- Música: 60–100 faixas com licença para vídeos monetizados (YouTube Audio Library, Pixabay Music, Free Music Archive CC BY, Incompetech) com `license.json` → `docforja biblioteca indexar`.
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
WIKIMEDIA_USER_AGENT=DocForja/0.1 (contato: seu-email)
```

## 10. `config/presets.yaml` (resumo)
```yaml
rapido:     {resolucao: 1080p, takes: 1, variacoes_ia: 1, max_ia: 0.15, max_parallax: 0.15}
padrao:     {resolucao: 1080p, takes: 1, refazer_reprovados: true, variacoes_ia: 2, max_ia: 0.30, max_parallax: 0.30}
caprichado: {resolucao: 1440p, takes: 3, variacoes_ia: 3, max_ia: 0.40, max_parallax: 0.40}
orcamento_padrao_min: {rapido: 60, padrao: 120, caprichado: 240}
```
