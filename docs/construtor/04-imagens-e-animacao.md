# 04 — Imagens e Animação de Imagens

## 1. As quatro origens de um ativo visual

| Origem | Quando | Onde fica |
|---|---|---|
| `biblioteca` | Já existe um ativo aprovado que serve (nota ≥ 7) | copiado para `02_midias/biblioteca/` |
| `pesquisar` | Pessoa, objeto, obra ou lugar **real e documentado** | `02_midias/pesquisadas/<ativo>/` |
| `gerar` | Cena do passado sem foto possível, ou ilustração | `02_midias/geradas/<ativo>_vN.png` |
| `pedir_ao_usuario` | Real, mas só existe em acervo restrito / imprensa / baixa resolução; ou a busca falhou | você coloca em `02_midias/manual/` |
| (`dados`) | Gráfico, mapa, linha do tempo, número | gerado pelo template |

Proibido `gerar` para pessoas reais contemporâneas e para retratar vítimas/corpos.

## 2. Pesquisa de fotos reais (P7)

1. O pesquisador (LLM) cria 3–6 consultas por ativo (idioma do tema + inglês + idioma local do assunto, com termos de acervo: *fresco*, *engraving*, *plaster cast*, *1944 photograph*).
2. APIs em ordem: Wikimedia Commons → Art Institute of Chicago / Met (obras) → Openverse → Library of Congress / Europeana → NASA (satélite/espaço) → Pexels / Pixabay (contemporâneo).
3. Filtro por código: licença comercial OK (PD, CC0, CC BY, CC BY-SA, licenças Pexels/Pixabay); NC/ND descartadas; lado maior ≥ 1600 px; heurística de **patrimônio restrito** (ex.: "Pompei", "Parco Archeologico", "Ministero della Cultura") → não escolhe sozinho.
4. Baixa até 5 candidatas por ativo com `.licenca.json` (URL, autor, licença, crédito) e a página de origem como prova.
5. **Curador** (visão local, Qwen2.5-VL): nota 0–10 + motivo (assunto, época, qualidade, marca d'água, texto embutido).
6. Nota ≥ 7 → escolhida (você pode trocar). Senão → `pedir_ao_usuario` com a explicação, ou `gerar` se a cena puder ser reconstituída.

## 3. Lista de busca e pasta manual

`lista_de_busca.md` (um item por ativo pedido):
```markdown
## A-017 — Afresco "Baco e o Vesúvio" (usado em B1-05, B1-06)
- Por que preciso de você: as fotos encontradas são de bem cultural italiano (uso comercial exige autorização) ou têm 900 px.
- Procure: "Bacco e Vesuvio affresco Casa del Centenario", "Bacchus and Vesuvius fresco Naples"
- Onde: Wikimedia Commons (conferir licença), site do Museo Archeologico Nazionale di Napoli, bancos de imagem pagos
- Mínimo: 1600 px · Salvar como: A-017.jpg
- Se não vier: imagem gerada no estilo de afresco, rotulada "RECONSTITUIÇÃO ARTÍSTICA"
```

**Pasta `02_midias/manual/`:**
- Nome com o ID (`A-017.jpg`, `A-017_versao2.png`) → atribuído automaticamente. Também aceita o ID do shot (`B1-05.jpg`).
- Sem ID → vai para `nao_atribuidas/` e o Curador sugere os 3 ativos mais prováveis; você confirma na interface.
- A interface pede a **ficha de crédito** (fonte, autor, licença ou "minha"). Sem ficha, o crédito sai como "fornecida pelo produtor" e entra um aviso no relatório.
- Seus arquivos nunca são movidos ou alterados: o sistema trabalha em cópias.

## 4. Imagens geradas (ComfyUI)

- **Prompt** = descrição do ativo + sufixo de estilo do kit + regras históricas do tema (ex.: Vesúvio de cume único em 79 d.C., sem lava nas cidades) + negative padrão (`../pipeline/07-assets-e-direitos.md §3`).
- **Personagens recorrentes:** imagem de referência criada uma vez (biblioteca/personagens) e usada como referência de imagem no workflow.
- **Variações:** conforme o preset (1–3). O Curador escolhe a melhor; nota < 6 em todas → 1 nova rodada com o motivo no prompt → senão, plano B.
- **Sem texto dentro da imagem** (o texto vem dos templates, e assim funciona em todos os idiomas).
- **Gerar 16:9 com margem:** 1344×768 e upscale; para shots com parallax, gerar já com área de folga nas bordas.
- Pré-geração opcional durante a sua revisão do plano.

## 5. Animação de imagens (o "movimento" do vídeo)

| Técnica | Ferramenta | Custo | Template | Observação |
|---|---|---|---|---|
| Ken Burns (zoom/pan suave) | Remotion (transform com easing) | zero, no render | T01, T04 | O padrão; bem escolhido já resolve a maioria dos shots |
| Parallax 2.5D | **DepthFlow** (CLI/Python, roda como processo separado; usa Depth Anything V2 Small) | ~10–30 s por shot | T02 | Exporta MP4 (NVENC); câmera `dolly`, `orbita`, `zoom` com intensidade baixa |
| Recorte de sujeito | **rembg + BiRefNet** (MIT) | ~2–5 s por imagem | T03 | Gera PNG com alfa; o template anima sujeito e fundo em camadas separadas |
| Detalhe/anotação | Remotion | zero | T04 | Caixa, círculo, linha, rótulo |
| Upscale | **Real-ESRGAN** x4plus | ~2–5 s por imagem | todos | Antes da montagem; desligar realce de rosto em fotos históricas |

Regras: amplitude de câmera ≤ 6% da largura (≤ 2% em vítimas reais); um movimento por shot; nenhum movimento "de ida e volta"; easing do kit.

## 6. Mapas

- **Fundo:** relevo sombreado gerado do DEM (OpenTopography COP30 / TINITALY) com `rasterio` + `numpy`, e/ou satélite Sentinel-2 dessaturado — PNG grande por região, guardado na biblioteca e reutilizado.
- **Vetores:** pontos, rotas, áreas e setas em GeoJSON; projetados no próprio template (D3-geo) sobre o fundo.
- **Animação (T10):** zoom/pan da câmera, pinos entrando, linhas tracejadas desenhando, áreas pulsando uma vez — tudo pelo kit.
- Linha de costa antiga ou perfis históricos: rotular "APROXIMADO".
