# Licenças conferidas para o DocForja

**Data da conferência:** 16 de outubro de 2026  
**Escopo:** componentes e modelos previstos em `06-open-source-reaproveitado.md`.  
**Regra:** licença do programa não substitui a licença dos pesos, fontes, vozes, nós,
ativos ou modelos baixados separadamente.

Este inventário é uma verificação técnica das fontes oficiais, não aconselhamento jurídico.
Antes de fixar uma versão em `config/lock.yaml`, a licença daquela versão e de todos os seus
artefatos deve ser preservada na ficha correspondente.

## Aprovados para o caminho padrão

| Componente | Licença conferida | Uso comercial | Fonte oficial | Condição no DocForja |
|---|---|---:|---|---|
| Remotion | Licença própria Remotion | Sim, para indivíduo, organização sem fins lucrativos ou empresa com até 3 funcionários | [LICENSE.md](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md) | Empresa fora dos critérios precisa de licença paga; não redistribuir derivado do Remotion |
| Remotion Agent Skills | MIT | Sim | [repositório oficial](https://github.com/remotion-dev/skills) | Preservar avisos ao redistribuir |
| DepthFlow | AGPL-3.0 | Sim | [repositório oficial](https://github.com/BrokenSource/DepthFlow) | Executar como processo separado; conferir também a licença do modelo de profundidade |
| rembg | MIT | Sim | [LICENSE.txt](https://github.com/danielgatis/rembg/blob/main/LICENSE.txt) | Cada peso possui licença própria; RMBG-2.0 não entra no caminho comercial padrão |
| BiRefNet | MIT | Sim | [LICENSE](https://github.com/ZhengPeng7/BiRefNet/blob/main/LICENSE) | Fixar apenas pesos publicados pelo projeto oficial sob termos compatíveis |
| Real-ESRGAN | BSD-3-Clause | Sim | [LICENSE](https://github.com/xinntao/Real-ESRGAN/blob/master/LICENSE) | Preservar avisos; registrar a origem dos pesos |
| WhisperX | BSD-2-Clause | Sim para o código | [LICENSE](https://github.com/m-bain/whisperX/blob/main/LICENSE) | Modelos de alinhamento têm licença independente; ver bloqueio abaixo |
| Whisper large-v3-turbo (pesos ASR) | MIT declarada | Sim, conforme licença declarada | [ficha do modelo](https://huggingface.co/openai/whisper-large-v3-turbo) | Conversão CTranslate2 local em avaliação; desempenho do roteiro completo ainda pendente |
| wav2vec2 português (pesos do alinhador) | Apache-2.0 declarada | Sim, conforme licença declarada | [ficha do modelo](https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-portuguese) | Conferido para pt; fixação explícita no adaptador e hashes ainda pendentes |
| Chatterbox | MIT | Sim | [LICENSE](https://github.com/resemble-ai/chatterbox/blob/master/LICENSE) | Fixar código e pesos oficiais, registrando ambos |
| Kokoro | Apache-2.0 | Sim | [LICENSE](https://github.com/hexgrad/kokoro/blob/main/LICENSE) | Vozes e dependências de idioma precisam de ficha própria |
| ComfyUI | GPL-3.0 | Sim | [LICENSE](https://github.com/Comfy-Org/ComfyUI/blob/master/LICENSE) | Executar como serviço separado; conferir cada nó instalado |
| Qwen-Image original | Apache-2.0 | Sim | [modelo oficial](https://huggingface.co/Qwen/Qwen-Image) | Usar ID e revisão fixos; não substituir automaticamente por Qwen-Image 2.1 |
| FLUX.1 schnell | Apache-2.0 | Sim | [repositório oficial](https://github.com/black-forest-labs/flux) | Somente variante `schnell`; variantes `dev` não entram no caminho comercial gratuito |
| SDXL | CreativeML Open RAIL++-M | Sim, com restrições de uso responsável | [LICENSE.md](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/main/LICENSE.md) | Manter restrições e ficha da revisão exata |
| Ollama | MIT | Sim | [LICENSE](https://github.com/ollama/ollama/blob/main/LICENSE) | Licença dos modelos é separada da licença do runtime |
| Qwen3 8B | Apache-2.0 | Sim | [modelo oficial](https://huggingface.co/Qwen/Qwen3-8B) | Fixar a revisão exata |
| Qwen2.5-VL 7B | Apache-2.0 | Sim | [modelo oficial](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) | Fixar a variante 7B; outras variantes da família podem ter termos diferentes |
| LiteLLM, fora de `enterprise/` | MIT | Sim | [LICENSE](https://github.com/BerriAI/litellm/blob/main/LICENSE) | Conteúdo de `enterprise/`, se usado, segue licença própria e fica fora do núcleo |
| OpenTimelineIO | Apache-2.0 | Sim | [LICENSE.txt](https://github.com/AcademySoftwareFoundation/OpenTimelineIO/blob/main/LICENSE.txt) | Preservar avisos e marcas de terceiros |
| D3 | ISC | Sim | [LICENSE](https://github.com/d3/d3/blob/main/LICENSE) | Preservar aviso |
| Natural Earth | Domínio público | Sim | [Terms of use](https://www.naturalearthdata.com/about/terms-of-use/) | Registrar versão do conjunto de dados |
| Lucide | ISC | Sim | [LICENSE](https://github.com/lucide-icons/lucide/blob/main/LICENSE) | Preservar aviso |
| Phosphor Icons | MIT | Sim | [LICENSE](https://github.com/phosphor-icons/core/blob/main/LICENSE) | Preservar aviso |
| Tabler Icons | MIT | Sim | [LICENSE](https://github.com/tabler/tabler-icons/blob/main/LICENSE) | Preservar aviso |
| Google Fonts usadas pelo kit | OFL-1.1 | Sim | [repositório oficial](https://github.com/google/fonts) | Conferir o `OFL.txt` de cada família; não vender a fonte isoladamente |
| FFmpeg | LGPL-2.1+ ou GPL, conforme a compilação | Sim | [informação legal oficial](https://ffmpeg.org/legal.html) | Registrar a configuração da build; distribuir binário GPL exige cumprir a GPL |
| 9Router | AGPL-3.0 | Sim | [repositório oficial](https://github.com/decolua/9router) | Executar como serviço separado e não incorporar seu código ao DocForja |
| Hermes Agent | MIT | Sim | [LICENSE](https://github.com/NousResearch/hermes-agent/blob/main/LICENSE) | Integração opcional e separada |

## Bloqueios e cuidados obrigatórios

1. **WhisperX:** a licença BSD-2 do código não cobre automaticamente os modelos de
   alinhamento. Há modelos padrão para francês, alemão, espanhol e italiano publicados sob
   CC BY-NC 4.0. Projetos monetizados devem usar modelos de alinhamento comerciais registrados
   no catálogo ou bloquear o idioma. O modelo português usado no ensaio está registrado
   acima, mas a seleção explícita e a verificação dos hashes continuam pendentes. O adaptador
   nunca deve selecionar um peso apenas pelo nome do idioma.
2. **Chroma1-HD:** o candidato permanece desabilitado para projeto monetizado até que o ID
   exato do repositório e o arquivo de licença dos pesos instalados sejam registrados. O nome
   informal não é suficiente para uma aprovação de licença.
3. **Qwen-Image 2.1:** não herda a licença Apache-2.0 do Qwen-Image original. A versão 2.1
   publicada em 2026 usa licença de pesquisa e não pode substituir silenciosamente o modelo
   aprovado.
4. **FLUX:** somente `FLUX.1-schnell` está aprovado neste inventário. `FLUX.1-dev`, Krea,
   Fill, Canny, Depth e Redux possuem termos diferentes ou não comerciais.
5. **rembg:** a biblioteca ser MIT não torna todos os seus modelos comerciais. BRIA RMBG-2.0
   requer acordo comercial; o adaptador deve operar por lista positiva de pesos.
6. **ComfyUI:** cada custom node e cada workflow deve registrar licença. Um nó sem licença
   identificável não entra no ambiente de produção monetizada.
7. **Vozes e fontes:** o motor TTS e o pacote de fontes podem ser permissivos enquanto uma
   voz ou família específica tem termos próprios. A ficha deve apontar para o artefato exato.

## Revalidação

- Revalidar antes de atualizar qualquer versão ou revisão de peso.
- Revalidar anualmente mesmo sem atualização.
- Guardar em `config/lock.yaml` a versão, revisão, URL e hash do artefato aprovado.
- Falha de licença é bloqueante: não usar fallback para um ativo sem ficha.
