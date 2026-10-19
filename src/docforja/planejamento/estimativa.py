"""Estimativa de tempo de produção e adequação orçamentária (Etapa P8).

Calcula tempo estimado de cada etapa a partir dos benchmarks reais (config/benchmark.json)
e garante conformidade com o teto de minutos do preset (Regra D15).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from docforja.esquemas import OrigemAtivo, Plano


@dataclass
class ItemEstimativa:
    etapa: str
    descricao: str
    tempo_minutos: float
    quantidade: int | float
    unidade: str


@dataclass
class RelatorioEstimativa:
    preset: str
    orcamento_minutos: int
    tempo_total_minutos: float
    aprovado: bool
    itens: list[ItemEstimativa] = field(default_factory=list)
    ajustes_realizados: list[str] = field(default_factory=list)


def carregar_benchmark_medias(
    caminho_json: Path = Path("config/benchmark.json"),
) -> dict[str, float]:
    """Extrai taxas médias de processamento medidas na máquina a partir do benchmark.json."""
    padroes: dict[str, float] = {
        "tts_s_por_s_audio": 0.10,  # ~1.8s para 18s audio
        "align_s_por_s_audio": 0.58,  # ~35s para 60s audio
        "gerar_imagem_s": 15.0,  # FLUX.1 schnell
        "parallax_s": 4.0,  # DepthFlow small
        "recorte_s": 5.5,  # BiRefNet / rembg
        "upscale_s": 4.5,  # Real-ESRGAN x4plus
        "render_1080p_s_por_s": 1.6,  # Remotion 1080p
        "render_1440p_s_por_s": 2.0,  # Remotion 1440p
        "mix_audio_min": 5.0,  # Cadeia e masterização
    }

    if not caminho_json.is_file():
        return padroes

    try:
        dados = json.loads(caminho_json.read_text(encoding="utf-8"))
        for res in dados.get("results", []):
            cid = res.get("id", "")
            metrics = res.get("metrics", {})
            if "kokoro" in cid and "inference_seconds" in metrics and "audio_seconds" in metrics:
                audio_s = metrics["audio_seconds"]
                inf_s = metrics["inference_seconds"]
                if audio_s > 0:
                    padroes["tts_s_por_s_audio"] = inf_s / audio_s
            elif (
                "whisperx" in cid and "alignment_seconds" in metrics and "audio_seconds" in metrics
            ):
                audio_s = metrics["audio_seconds"]
                al_s = metrics["alignment_seconds"]
                if audio_s > 0:
                    padroes["align_s_por_s_audio"] = al_s / audio_s
            elif "flux1-schnell" in cid and res.get("status") == "ok":
                dur = res.get("duration_seconds", 0)
                if 5.0 < dur < 60.0 and not metrics.get("includes_model_load"):
                    padroes["gerar_imagem_s"] = dur
            elif "depthflow" in cid and res.get("status") == "ok":
                padroes["parallax_s"] = res.get("duration_seconds", 4.0)
            elif "rembg" in cid and res.get("status") == "ok":
                padroes["recorte_s"] = res.get("duration_seconds", 5.5)
            elif "realesrgan" in cid and res.get("status") == "ok":
                padroes["upscale_s"] = res.get("duration_seconds", 4.5)
            elif cid == "render_1080p" and "video_seconds" in metrics:
                vid_s = metrics["video_seconds"]
                dur = res.get("duration_seconds", 16.0)
                if vid_s > 0:
                    padroes["render_1080p_s_por_s"] = dur / vid_s
            elif cid == "render_1440p" and "video_seconds" in metrics:
                vid_s = metrics["video_seconds"]
                dur = res.get("duration_seconds", 20.0)
                if vid_s > 0:
                    padroes["render_1440p_s_por_s"] = dur / vid_s
    except Exception:
        pass

    return padroes


def estimar_tempo_plano(
    plano: Plano,
    benchmark_rates: dict[str, float] | None = None,
    variacoes_imagem: int = 2,
) -> RelatorioEstimativa:
    """Calcula a estimativa completa de produção do plano por etapa e valida orçamento."""
    rates = benchmark_rates or carregar_benchmark_medias()

    duracao_total_s = sum(shot.duracao_s for bloco in plano.blocos for shot in bloco.shots)

    # Contagem de shots e templates
    shots_t02 = sum(1 for b in plano.blocos for s in b.shots if s.template == "T02")
    shots_t03 = sum(1 for b in plano.blocos for s in b.shots if s.template == "T03")

    # Contagem de ativos a gerar
    ativos_gerar = sum(
        1 for a in plano.ativos.values() if a.origem == OrigemAtivo.GERAR or a.origem == "gerar"
    )

    # 1. Narração e alinhamento principal
    t_tts_s = duracao_total_s * rates["tts_s_por_s_audio"]
    t_align_s = duracao_total_s * rates["align_s_por_s_audio"]
    t_narracao_min = (t_tts_s + t_align_s) / 60.0

    # 2. Imagens geradas (com variações)
    total_geracoes = ativos_gerar * variacoes_imagem
    t_imagens_min = (total_geracoes * rates["gerar_imagem_s"]) / 60.0

    # 3. Efeitos (parallax, recorte, upscale)
    t_parallax_s = shots_t02 * rates["parallax_s"]
    t_recorte_s = shots_t03 * rates["recorte_s"]
    t_upscale_s = max(ativos_gerar, 10) * rates["upscale_s"]
    t_efeitos_min = (t_parallax_s + t_recorte_s + t_upscale_s) / 60.0

    # 4. Trilha, SFX e mixagem
    t_mix_min = rates["mix_audio_min"]

    # 5. Renderização e QA
    is_1440p = plano.preset == "caprichado"
    render_rate = rates["render_1440p_s_por_s"] if is_1440p else rates["render_1080p_s_por_s"]
    t_render_min = (duracao_total_s * render_rate) / 60.0

    # 6. Idiomas extras
    extras = plano.idiomas.get("extras", [])
    t_extras_min = 0.0
    for _ in extras:
        # Cada idioma extra: nova narração + render de vídeo
        t_extras_min += (duracao_total_s * (rates["tts_s_por_s_audio"] + render_rate)) / 60.0

    itens = [
        ItemEstimativa(
            etapa="Narração e alinhamento (pt-BR)",
            descricao="Síntese TTS e alinhamento WhisperX",
            tempo_minutos=round(t_narracao_min, 1),
            quantidade=round(duracao_total_s, 1),
            unidade="s áudio",
        ),
        ItemEstimativa(
            etapa="Geração de imagens",
            descricao=f"ComfyUI FLUX ({variacoes_imagem} variações)",
            tempo_minutos=round(t_imagens_min, 1),
            quantidade=total_geracoes,
            unidade="imagens",
        ),
        ItemEstimativa(
            etapa="Tratamento e efeitos (2.5D, recorte, upscale)",
            descricao="DepthFlow, BiRefNet e Real-ESRGAN",
            tempo_minutos=round(t_efeitos_min, 1),
            quantidade=shots_t02 + shots_t03,
            unidade="shots c/ efeitos",
        ),
        ItemEstimativa(
            etapa="Áudio (trilha, SFX e mixagem)",
            descricao="Mixagem estéreo e normalização EBU R128 (-14 LUFS)",
            tempo_minutos=round(t_mix_min, 1),
            quantidade=len(plano.blocos),
            unidade="blocos",
        ),
        ItemEstimativa(
            etapa="Renderização Remotion e QA",
            descricao=f"Composição de vídeo e export MP4 ({'1440p' if is_1440p else '1080p'})",
            tempo_minutos=round(t_render_min, 1),
            quantidade=round(duracao_total_s, 1),
            unidade="s vídeo",
        ),
    ]

    if extras:
        itens.append(
            ItemEstimativa(
                etapa=f"Idiomas adicionais ({', '.join(extras)})",
                descricao="TTS e render Remotion localizado",
                tempo_minutos=round(t_extras_min, 1),
                quantidade=len(extras),
                unidade="idiomas",
            )
        )

    tempo_total = sum(it.tempo_minutos for it in itens)
    orcamento = plano.orcamento_producao_min or 120

    ajustes: list[str] = []

    # Regra D15: Se exceder o orçamento, aplica correções automáticas
    if tempo_total > orcamento:
        # Ação 1: reduzir variações de imagem para 1 se estava em 2 ou 3
        if variacoes_imagem > 1:
            tempo_economizado = (
                ativos_gerar * (variacoes_imagem - 1) * rates["gerar_imagem_s"]
            ) / 60.0
            tempo_total -= tempo_economizado
            ajustes.append(
                f"Redução de variações de imagem gerada de {variacoes_imagem} para 1 "
                f"(economia: {tempo_economizado:.1f} min)"
            )

        # Ação 2: se ainda estourar, converter excesso de T02 em T01
        if tempo_total > orcamento and shots_t02 > 0:
            qtd_converter = min(
                shots_t02, int((tempo_total - orcamento) * 60 / rates["parallax_s"]) + 1
            )
            tempo_economizado = (qtd_converter * rates["parallax_s"]) / 60.0
            tempo_total -= tempo_economizado
            ajustes.append(
                f"Conversão de {qtd_converter} shots T02 para T01 "
                f"(economia: {tempo_economizado:.1f} min)"
            )

        # Ação 3: se ainda estourar, trocar 'gerar' por 'pesquisar' ou 'biblioteca'
        if tempo_total > orcamento and ativos_gerar > 5:
            qtd_trocar = min(
                ativos_gerar - 5, int((tempo_total - orcamento) * 60 / rates["gerar_imagem_s"]) + 1
            )
            tempo_economizado = (qtd_trocar * rates["gerar_imagem_s"]) / 60.0
            tempo_total -= tempo_economizado
            ajustes.append(
                f"Substituição de {qtd_trocar} ativos 'gerar' por fotos de acervo "
                f"(economia: {tempo_economizado:.1f} min)"
            )

    aprovado = tempo_total <= orcamento

    return RelatorioEstimativa(
        preset=plano.preset,
        orcamento_minutos=orcamento,
        tempo_total_minutos=round(tempo_total, 1),
        aprovado=aprovado,
        itens=itens,
        ajustes_realizados=ajustes,
    )
