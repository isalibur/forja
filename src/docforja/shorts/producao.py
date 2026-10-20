"""Produção versionada de um short derivado no idioma principal."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from itertools import pairwise
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from docforja.audio.trilha import resolver_trilha_provisoria
from docforja.esquemas import Ativo, Plano
from docforja.io import atomic_write_json, atomic_write_text
from docforja.midia.licenca import (
    caminho_sidecar_licenca,
    carregar_ficha_licenca,
    classificar_licenca,
    detectar_patrimonio_restrito,
)
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.nucleo.gpu import semaforo_gpu
from docforja.nucleo.handlers import _criar_orquestrador
from docforja.nucleo.projeto import Projeto, slugificar
from docforja.planejamento.entidades import SegmentoProcessado
from docforja.planejamento.previa import KIT_REMOTION
from docforja.shorts.candidatos import pontuar_candidatos_do_plano
from docforja.shorts.modelos import (
    CandidatoShort,
    ElementoTelaShort,
    IntervaloLegendaShort,
    ManifestoVertical,
    ShortParaVerificar,
)
from docforja.shorts.verificador import verificar_short

FPS = 30


class CaptionRemotion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    startMs: float = Field(ge=0)
    endMs: float = Field(gt=0)
    timestampMs: float | None = None
    confidence: float | None = None


class PropsCenaShort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variante: str
    titulo: str = ""
    subtitulo: str = ""
    texto: str = ""
    imagem: str = ""
    imagem_antes: str = ""
    imagem_depois: str = ""
    clipe: str = ""
    itens: list[str] = Field(default_factory=list)
    opcao_a: str = ""
    opcao_b: str = ""
    preco: str = ""
    condicao: str = ""
    aviso_publicidade: str = ""
    prova: str = ""
    fonte_prova: str = ""
    cta: str = ""
    marca: str = ""
    foco_x: float = Field(default=0.5, ge=0, le=1)
    foco_y: float = Field(default=0.5, ge=0, le=1)
    usar_fundo_desfocado: bool = False
    legendas: list[CaptionRemotion] = Field(default_factory=list)


class CenaRenderShort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    inicio_frame: int = Field(ge=0)
    duracao_frames: int = Field(gt=0)
    props: PropsCenaShort


class PropsRenderShort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duracao_frames: int = Field(gt=0)
    audio: str = Field(min_length=1)
    cenas: list[CenaRenderShort] = Field(min_length=1)


class ResultadoProducaoShort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    idioma: str
    revisao: str
    caminho_video: str
    caminho_capa: str
    caminho_legendas: str
    duracao_s: float
    qa_aprovado: bool
    falhas_qa: list[str] = Field(default_factory=list)
    cache: bool = False


def _executar(comando: list[str], *, cwd: Path, timeout: int = 3600) -> str:
    resultado = subprocess.run(
        comando, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
    )
    if resultado.returncode:
        raise RuntimeError((resultado.stderr or resultado.stdout)[-1800:])
    return resultado.stderr + "\n" + resultado.stdout


def _carregar_aprovacao_manifesto(
    projeto: Projeto, referencia: str
) -> tuple[dict[str, Any], CandidatoShort, ManifestoVertical, str, str]:
    pasta = projeto.pastas.montagem / "shorts" / "derivados" / referencia
    atual_path = pasta / "aprovacao_atual.json"
    if not atual_path.is_file():
        raise ValueError("Aprove uma frase-ponte antes de produzir o short.")
    atual = json.loads(atual_path.read_text(encoding="utf-8"))
    aprovacao_id = str(atual.get("versao", ""))
    if not re.fullmatch(r"[a-f0-9]{64}", aprovacao_id):
        raise ValueError("A versão da aprovação é inválida.")
    aprovacao_path = pasta / f"aprovacao-{aprovacao_id}.json"
    if not aprovacao_path.is_file():
        raise ValueError("A versão aprovada não está disponível.")
    aprovacao = json.loads(aprovacao_path.read_text(encoding="utf-8"))
    candidato = CandidatoShort.model_validate(aprovacao["candidato"])
    if not any(frase.aprovada for frase in candidato.frases_ponte):
        raise ValueError("A frase-ponte ainda não foi aprovada.")
    manifesto_pointer_path = pasta / "manifesto_atual.json"
    if not manifesto_pointer_path.is_file():
        raise ValueError("Gere novamente o manifesto vertical antes de produzir o short.")
    pointer = json.loads(manifesto_pointer_path.read_text(encoding="utf-8"))
    manifesto_id = str(pointer.get("versao", ""))
    if not re.fullmatch(r"[a-f0-9]{64}", manifesto_id):
        raise ValueError("A versão do manifesto vertical é inválida.")
    if pointer.get("aprovacao_versao") != aprovacao_id:
        raise ValueError("A frase-ponte mudou; gere novamente o manifesto vertical.")
    if pointer.get("fonte_hash") != aprovacao.get("fonte_hash"):
        raise ValueError("O manifesto vertical foi criado para outra versão do plano.")
    manifesto_path = pasta / f"manifesto-vertical-{manifesto_id}.json"
    if not manifesto_path.is_file():
        raise ValueError("A versão do manifesto vertical não está disponível.")
    manifesto = ManifestoVertical.model_validate_json(manifesto_path.read_text(encoding="utf-8"))
    return aprovacao, candidato, manifesto, aprovacao_id, manifesto_id


def _opcoes_projeto(projeto: Projeto) -> tuple[dict[str, Any], str, str, str]:
    opcoes = projeto.obter_opcoes()
    idioma = str(opcoes.get("idiomas", {}).get("principal", "pt-BR"))
    motor = str(opcoes.get("tts", {}).get("motor") or opcoes.get("motor_tts") or "kokoro")
    voz = str(opcoes.get("vozes", {}).get(idioma) or opcoes.get("voz") or "")
    if opcoes.get("narracao_pronta") or any(
        (projeto.pastas.entrada / f"narracao{suffix}").is_file()
        for suffix in (".wav", ".mp3", f"_{idioma}.wav", f"_{idioma}.mp3")
    ):
        raise ValueError(
            "Este projeto usa narração gravada. Para preservar a mesma voz, grave a frase-ponte; "
            "não vamos sintetizar uma voz diferente automaticamente."
        )
    return opcoes, idioma, motor, voz


def _ativos_resolvidos(projeto: Projeto, plano: Plano) -> dict[str, Ativo]:
    saida = dict(plano.ativos)
    caminho = projeto.pastas.plano / "ativos_resolvidos.json"
    if caminho.is_file():
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        saida.update(
            {aid: Ativo.model_validate(item) for aid, item in dados.get("ativos", {}).items()}
        )
    escolhas = projeto.pastas.midias / "escolhas.json"
    if escolhas.is_file():
        dados = json.loads(escolhas.read_text(encoding="utf-8")).get("ativos", {})
        for aid, escolha in dados.items():
            if aid in saida and isinstance(escolha, dict) and escolha.get("caminho"):
                saida[aid].caminho = Path(escolha["caminho"])
    return saida


def _licenca_comercial(ativo: Ativo) -> bool:
    caminho = ativo.caminho
    if not caminho or not caminho.is_file():
        return False
    ficha = carregar_ficha_licenca(caminho)
    dados = ficha.model_dump() if ficha else (ativo.licenca or {})
    permitido, _ = classificar_licenca(str(dados.get("licenca", "")))
    return (
        permitido
        and dados.get("comercial") is True
        and not dados.get("patrimonio_restrito", False)
        and not detectar_patrimonio_restrito(ativo.id, ativo.descricao)
    )


def _palavras(path: Path, ids: set[str], inicio: float, fim: float) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValueError("Alinhamento palavra a palavra ausente para este idioma.")
    dados = json.loads(path.read_text(encoding="utf-8"))
    resultado = []
    for item in dados:
        sid = str(item.get("segmento_id", ""))
        texto = str(item.get("palavra", item.get("word", ""))).strip()
        inicio_palavra = float(item.get("inicio_s", item.get("start", 0)))
        fim_palavra = float(item.get("fim_s", item.get("end", 0)))
        if sid in ids and texto and fim_palavra > inicio and inicio_palavra < fim:
            resultado.append(
                {
                    "text": texto,
                    "start": max(0.0, inicio_palavra - inicio),
                    "end": min(fim - inicio, fim_palavra - inicio),
                }
            )
    resultado.sort(key=lambda item: item["start"])
    if not resultado:
        raise ValueError("Não há palavras alinhadas no intervalo aprovado.")
    resultado[0]["start"] = 0.0
    for anterior, atual in pairwise(resultado):
        if atual["start"] - anterior["end"] <= 0.1:
            anterior["end"] = max(anterior["end"], atual["start"])
    resultado[-1]["end"] = fim - inicio
    return resultado


def _captions_remotion(
    palavras: list[dict[str, Any]], inicio: float, fim: float
) -> list[CaptionRemotion]:
    saida = []
    for item in palavras:
        a = max(inicio, float(item["start"]))
        b = min(fim, float(item["end"]))
        if b > a:
            saida.append(
                CaptionRemotion(
                    text=item["text"], startMs=(a - inicio) * 1000, endMs=(b - inicio) * 1000
                )
            )
    return saida


def _srt(palavras: list[dict[str, Any]]) -> str:
    def timestamp(segundos: float) -> str:
        total_ms = max(0, round(segundos * 1000))
        horas, restante = divmod(total_ms, 3_600_000)
        minutos, restante = divmod(restante, 60_000)
        segundos_i, ms = divmod(restante, 1000)
        return f"{horas:02d}:{minutos:02d}:{segundos_i:02d},{ms:03d}"

    return (
        "\n\n".join(
            f"{idx}\n{timestamp(item['start'])} --> {timestamp(item['end'])}\n{item['text']}"
            for idx, item in enumerate(palavras, 1)
        )
        + "\n"
    )


def _licenca_trilha_comercial(trilha: Path) -> bool:
    sidecar = _sidecar_trilha(trilha)
    if not sidecar:
        return False
    dados = json.loads(sidecar.read_text(encoding="utf-8"))
    permitido, _ = classificar_licenca(str(dados.get("licenca", "")))
    return (
        permitido and dados.get("comercial") is True and not dados.get("patrimonio_restrito", False)
    )


def _sidecar_trilha(trilha: Path) -> Path | None:
    for sidecar in (
        trilha.with_name(f"{trilha.name}.licenca.json"),
        trilha.with_name(f"{trilha.stem}.licenca.json"),
    ):
        if not sidecar.is_file():
            continue
        return sidecar
    return None


def _mixar_audio(
    voz: Path, destino: Path, trilha: Path | None, relatorio_longo: Path
) -> tuple[float | None, bool | None]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg não está instalado ou não está no PATH.")
    volume_trilha_short = 0.22
    if trilha and trilha.is_file():
        if not _licenca_trilha_comercial(trilha):
            raise ValueError(
                "A trilha não tem ficha comercial vigente; o short não será renderizado."
            )
        filtro = (
            f"[1:a]volume={volume_trilha_short}[m];"
            "[m][0:a]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=350[duck];"
            "[0:a][duck]amix=inputs=2:duration=first:normalize=0[mix];"
            "[mix]loudnorm=I=-14:TP=-1:LRA=11:print_format=json[out]"
        )
        comando = [
            ffmpeg,
            "-y",
            "-i",
            str(voz),
            "-stream_loop",
            "-1",
            "-i",
            str(trilha),
            "-filter_complex",
            filtro,
            "-map",
            "[out]",
            "-c:a",
            "pcm_s16le",
            str(destino),
        ]
    else:
        comando = [
            ffmpeg,
            "-y",
            "-i",
            str(voz),
            "-af",
            "loudnorm=I=-14:TP=-1:LRA=11",
            "-c:a",
            "pcm_s16le",
            str(destino),
        ]
    _executar(comando, cwd=KIT_REMOTION, timeout=900)
    medicao = _executar(
        [ffmpeg, "-i", str(destino), "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
        cwd=KIT_REMOTION,
        timeout=900,
    )
    medido = re.search(r"\bI:\s*(-?[\d.]+)\s*LUFS", medicao)
    lufs = float(medido.group(1)) if medido else None
    musica_mais_presente: bool | None = None
    if trilha and trilha.is_file() and relatorio_longo.is_file():
        relatorio = json.loads(relatorio_longo.read_text(encoding="utf-8"))
        volume_longo = re.search(r"(0[.,]\d+)", str(relatorio.get("sidechain_ducking", "")))
        if volume_longo:
            volume_referencia = float(volume_longo.group(1).replace(",", "."))
            musica_mais_presente = volume_trilha_short > volume_referencia
    return lufs, musica_mais_presente


def _renderizar(
    composicao: str, props: Path, public: Path, destino: Path, *, still: bool = False
) -> None:
    npm = shutil.which("npm") or shutil.which("npm.cmd") or "npm"
    if still:
        comando = [
            npm,
            "exec",
            "--offline",
            "--",
            "remotion",
            "still",
            "src/index.ts",
            composicao,
            str(destino),
            "--frame=1",
            f"--props={props}",
            f"--public-dir={public}",
        ]
    else:
        comando = [
            npm,
            "exec",
            "--offline",
            "--",
            "remotion",
            "render",
            "src/index.ts",
            composicao,
            str(destino),
            f"--props={props}",
            f"--public-dir={public}",
            "--concurrency=2",
            "--log=error",
        ]
    _executar(comando, cwd=KIT_REMOTION)
    if not destino.is_file():
        raise RuntimeError(f"O Remotion não criou {destino.name}.")


def _escrever_ponteiro_saida(pasta_saida: Path, resultado: ResultadoProducaoShort) -> None:
    raiz_short = pasta_saida.parent.parent
    atomic_write_json(
        raiz_short / "atual.json",
        {
            "revisao": resultado.revisao,
            "idioma": resultado.idioma,
            "video": resultado.caminho_video,
            "capa": resultado.caminho_capa,
            "legendas": resultado.caminho_legendas,
        },
    )


def produzir_short_derivado(projeto: Projeto, referencia: str) -> ResultadoProducaoShort:
    """Renderiza em staging isolado e publica uma revisão imutável do short derivado."""
    if not re.fullmatch(r"[a-f0-9]{24}", referencia):
        raise ValueError("Referência de short inválida.")
    _opcoes, idioma, motor_nome, voz = _opcoes_projeto(projeto)
    pasta_aprovacao = projeto.pastas.montagem / "shorts" / "derivados" / referencia
    aprovacao, candidato, manifesto, aprovacao_id, manifesto_id = _carregar_aprovacao_manifesto(
        projeto, referencia
    )
    plano = Plano.model_validate_json(
        (projeto.pastas.plano / "plano.json").read_text(encoding="utf-8")
    )
    ativos = _ativos_resolvidos(projeto, plano)
    audio = projeto.pastas.audio / idioma / "narracao_completa.wav"
    segmentos_path = projeto.pastas.audio / idioma / "segmentos.json"
    palavras_path = projeto.pastas.audio / idioma / "palavras.json"
    if not audio.is_file() or not segmentos_path.is_file():
        raise ValueError(f"Áudio e tempos narrados são necessários para {idioma}.")
    segmentos = json.loads(segmentos_path.read_text(encoding="utf-8"))
    plano_path = projeto.pastas.plano / "plano.json"
    fonte_hash_atual = calcular_hash_dados(
        {
            "plano": calcular_hash_dados(plano_path),
            "segmentos": calcular_hash_dados(segmentos_path),
        }
    )
    if fonte_hash_atual != aprovacao.get("fonte_hash"):
        raise ValueError("O plano ou a narração mudou; atualize os candidatos e aprove novamente.")
    por_id = {str(item.get("id")): item for item in segmentos}
    if any(sid not in por_id for sid in candidato.segmento_ids):
        raise ValueError("Os segmentos do candidato não correspondem mais à narração.")
    inicio = min(float(por_id[sid]["inicio_s"]) for sid in candidato.segmento_ids)
    fim = max(float(por_id[sid]["fim_s"]) for sid in candidato.segmento_ids)
    palavras = _palavras(palavras_path, set(candidato.segmento_ids), inicio, fim)
    trilha = resolver_trilha_provisoria(projeto)
    if trilha and not _licenca_trilha_comercial(trilha):
        raise ValueError("A trilha não tem ficha comercial vigente para uso no short.")

    ponte = next(frase.texto for frase in candidato.frases_ponte if frase.aprovada)
    fontes: dict[str, str] = {
        "audio": calcular_hash_dados(audio),
        "palavras": calcular_hash_dados(palavras_path),
        "fonte": str(aprovacao["fonte_hash"]),
        "trilha": calcular_hash_dados(trilha) if trilha and trilha.is_file() else "",
    }
    sidecar_trilha = _sidecar_trilha(trilha) if trilha else None
    if sidecar_trilha:
        fontes["trilha_licenca"] = calcular_hash_dados(sidecar_trilha)
    imagens: dict[str, tuple[Path, str]] = {}
    shot_por_id = {shot.id: shot for bloco in plano.blocos for shot in bloco.shots}
    for shot_v in manifesto.shots:
        shot = shot_por_id.get(shot_v.shot_id)
        if shot is None:
            raise ValueError(f"Shot {shot_v.shot_id} não existe mais no plano mestre.")
        if not shot_v.ativos:
            raise ValueError(f"Shot {shot_v.shot_id} ainda não tem imagem liberada para o short.")
        ativo_v = shot_v.ativos[0]
        ativo = ativos.get(ativo_v.ativo_id)
        if not ativo or not _licenca_comercial(ativo):
            raise ValueError(f"O ativo {ativo_v.ativo_id} não tem licença comercial vigente.")
        if ativo.caminho.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise ValueError(
                f"O ativo {ativo_v.ativo_id} não é uma imagem suportada para Remotion."
            )
        hash_imagem = calcular_hash_dados(ativo.caminho)
        if hash_imagem != ativo_v.hash_origem:
            raise ValueError(
                f"O ativo {ativo_v.ativo_id} mudou; gere novamente o manifesto vertical."
            )
        fontes[ativo_v.ativo_id] = hash_imagem
        sidecar = caminho_sidecar_licenca(ativo.caminho)
        fontes[f"licenca:{ativo_v.ativo_id}"] = (
            calcular_hash_dados(sidecar)
            if sidecar.is_file()
            else calcular_hash_dados(ativo.licenca or {})
        )
        imagens[shot_v.shot_id] = (ativo.caminho, hash_imagem)

    motor_id = {
        "motor": motor_nome,
        "voz": voz,
        "idioma": idioma,
        "velocidade": 1.0,
        "configuracao": _opcoes.get("tts", {}),
    }
    hash_ponte = calcular_hash_dados({"texto": ponte, "tts": motor_id})
    revisao = calcular_hash_dados(
        {
            "fonte": fontes,
            "aprovacao": aprovacao_id,
            "manifesto": manifesto_id,
            "tts": motor_id,
            "candidato": candidato.model_dump(mode="json"),
        }
    )
    ordenados = pontuar_candidatos_do_plano(plano, segmentos, limite=5)
    try:
        indice_short = next(
            indice for indice, item in enumerate(ordenados, start=1) if item.id == candidato.id
        )
    except StopIteration as exc:
        raise ValueError("O candidato aprovado não consta mais na lista atual.") from exc
    slug_trecho = slugificar(candidato.texto[:54])[:48]
    pasta_saida = (
        projeto.pastas.saida
        / idioma
        / "shorts"
        / f"S{indice_short:02d}-{slug_trecho}"
        / "revisoes"
        / revisao
    )
    registro = pasta_saida / "short.json"
    if registro.is_file():
        dados = json.loads(registro.read_text(encoding="utf-8"))
        cached = ResultadoProducaoShort.model_validate({**dados["resultado"], "cache": True})
        if all(
            Path(item).is_file()
            for item in (cached.caminho_video, cached.caminho_capa, cached.caminho_legendas)
        ):
            return cached
        raise RuntimeError(
            "A revisão em cache está incompleta; preserve-a e verifique a pasta de saída."
        )

    bridge_path = pasta_aprovacao / "cache" / f"ponte-{hash_ponte}.wav"
    if not bridge_path.is_file():
        orquestrador = _criar_orquestrador(motor_tts=motor_nome, projeto=projeto)
        if not orquestrador.tts.disponivel():
            raise RuntimeError(
                f"O motor de narração configurado ({motor_nome}) não está disponível."
            )
        bridge_path.parent.mkdir(parents=True, exist_ok=True)
        modelo_gpu = motor_nome if motor_nome in {"kokoro", "chatterbox", "voicestudio"} else None
        with semaforo_gpu.adquirir_sync(
            modelo=modelo_gpu,
            tarefa=f"M8 ponte de short {referencia[:8]}",
            projeto=projeto.slug,
        ):
            orquestrador.processar_segmento(
                SegmentoProcessado(id="ponte-short", texto_original=ponte, texto_limpo=ponte),
                bridge_path.parent,
                idioma=idioma,
                voz=voz or None,
            )
        gerado = bridge_path.parent / "ponte-short.wav"
        if not gerado.is_file():
            raise RuntimeError("O TTS não gerou o áudio da frase-ponte.")
        shutil.copy2(gerado, bridge_path)

    pasta_saida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="short-render-", dir=pasta_saida.parent) as temp_dir:
        work = Path(temp_dir)
        public = work / "public"
        (public / "ativos").mkdir(parents=True)
        for shot_id, (origem, _) in imagens.items():
            destino = public / "ativos" / f"{slugificar(shot_id)}{origem.suffix.lower()}"
            shutil.copy2(origem, destino)
        trim = work / "trecho.wav"
        concat = work / "voz.wav"
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("FFmpeg não está instalado ou não está no PATH.")
        _executar(
            [
                ffmpeg,
                "-y",
                "-ss",
                f"{inicio:.3f}",
                "-i",
                str(audio),
                "-t",
                f"{fim - inicio:.3f}",
                "-c:a",
                "pcm_s16le",
                str(trim),
            ],
            cwd=KIT_REMOTION,
            timeout=900,
        )
        _executar(
            [
                ffmpeg,
                "-y",
                "-i",
                str(trim),
                "-i",
                str(bridge_path),
                "-filter_complex",
                "[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a0];"
                "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a1];"
                "[a0][a1]concat=n=2:v=0:a=1[out]",
                "-map",
                "[out]",
                "-c:a",
                "pcm_s16le",
                str(concat),
            ],
            cwd=KIT_REMOTION,
            timeout=900,
        )
        voz_mix = public / "audio.wav"
        loudness, musica_mais_presente = _mixar_audio(
            concat,
            voz_mix,
            trilha,
            projeto.pastas.audio / idioma / "relatorio_mix.json",
        )

        duracao_base = fim - inicio
        duracao_ponte = _duracao_wav(bridge_path)
        duracao_total = duracao_base + duracao_ponte
        if not 15 <= duracao_total <= 60:
            raise ValueError(
                "A ponte aprovada deixa o short fora da faixa de 15 a 60 segundos. "
                "Edite a ponte e gere novo manifesto."
            )
        hook = " ".join(candidato.texto.split()[:6])
        cenas: list[CenaRenderShort] = []
        primeira = next((shot for shot in manifesto.shots if shot.fim_s > inicio), None)
        if primeira is None:
            raise ValueError("O manifesto vertical não contém cenas dentro do trecho.")
        primeira_origem, _ = imagens[primeira.shot_id]
        primeiro_recorte = primeira.ativos[0].recorte
        cenas.append(
            CenaRenderShort(
                id="gancho",
                inicio_frame=0,
                duracao_frames=min(FPS * 2, round(duracao_base * FPS)),
                props=PropsCenaShort(
                    variante="V01",
                    titulo=hook,
                    imagem=f"ativos/{slugificar(primeira.shot_id)}{primeira_origem.suffix.lower()}",
                    foco_x=min(0.98, max(0.02, primeiro_recorte.x + primeiro_recorte.largura / 2)),
                    foco_y=min(0.98, max(0.02, primeiro_recorte.y + primeiro_recorte.altura / 2)),
                    usar_fundo_desfocado=primeiro_recorte.usar_fundo_desfocado,
                    legendas=_captions_remotion(palavras, 0, min(2.0, duracao_base)),
                ),
            )
        )
        for shot_v in manifesto.shots:
            a = max(2.0, shot_v.inicio_s - inicio)
            b = min(duracao_base, shot_v.fim_s - inicio)
            if b <= a:
                continue
            origem, _ = imagens[shot_v.shot_id]
            img_rel = f"ativos/{slugificar(shot_v.shot_id)}{origem.suffix.lower()}"
            foco_x = 0.5
            foco_y = 0.5
            recorte = next(item.recorte for item in shot_v.ativos if item.ativo_id in ativos)
            foco_x = min(0.98, max(0.02, recorte.x + recorte.largura / 2))
            foco_y = min(0.98, max(0.02, recorte.y + recorte.altura / 2))
            cursor = a
            parte = 0
            while cursor < b:
                fim_cena = min(b, cursor + 2.5)
                duracao_frames = max(1, round((fim_cena - cursor) * FPS))
                palavras_cena = _captions_remotion(palavras, cursor, fim_cena)
                cena_props = PropsCenaShort(
                    variante="V02",
                    imagem=img_rel,
                    foco_x=foco_x,
                    foco_y=foco_y,
                    usar_fundo_desfocado=recorte.usar_fundo_desfocado,
                    legendas=palavras_cena,
                )
                cenas.append(
                    CenaRenderShort(
                        id=f"{shot_v.shot_id}-{parte}",
                        inicio_frame=round(cursor * FPS),
                        duracao_frames=duracao_frames,
                        props=cena_props,
                    )
                )
                cursor = fim_cena
                parte += 1
        palavras_ponte = ponte.split()
        for idx, palavra in enumerate(palavras_ponte):
            a = duracao_base + duracao_ponte * idx / len(palavras_ponte)
            b = duracao_base + duracao_ponte * (idx + 1) / len(palavras_ponte)
            palavras.append({"text": palavra, "start": a, "end": b})
        bridge_captions = _captions_remotion(palavras, duracao_base, duracao_total)
        cenas.append(
            CenaRenderShort(
                id="cta",
                inicio_frame=round(duracao_base * FPS),
                duracao_frames=max(1, round(duracao_ponte * FPS)),
                props=PropsCenaShort(
                    variante="V07", titulo="VÍDEO COMPLETO", cta="ASSISTA", legendas=bridge_captions
                ),
            )
        )
        duracao_frames = max(1, round(duracao_total * FPS))
        props = PropsRenderShort(duracao_frames=duracao_frames, audio="audio.wav", cenas=cenas)
        props_path = work / "props.json"
        atomic_write_json(props_path, props.model_dump(mode="json", by_alias=True))
        video_tmp = work / "video.mp4"
        capa_tmp = work / "capa.jpg"
        _renderizar("Short-Derivado", props_path, public, video_tmp)
        _renderizar("Short-Derivado", props_path, public, capa_tmp, still=True)

        captions_path = work / "legendas.srt"
        atomic_write_text(captions_path, _srt(palavras))
        elementos = [
            ElementoTelaShort(id="gancho", x=0.08, y=0.18, largura=0.78, altura=0.35, texto=hook),
            ElementoTelaShort(id="legenda", x=0.08, y=0.67, largura=0.78, altura=0.06),
            ElementoTelaShort(
                id="cta", x=0.08, y=0.2, largura=0.78, altura=0.4, texto="VÍDEO COMPLETO"
            ),
        ]
        intervalos = [
            IntervaloLegendaShort(inicio_s=item["start"], fim_s=item["end"], texto=item["text"])
            for item in palavras
            if item["end"] > item["start"]
        ]
        verificacao = verificar_short(
            ShortParaVerificar(
                duracao_s=duracao_total,
                duracao_alvo_s=duracao_total,
                inicio_gancho_visual_s=0,
                inicio_gancho_textual_s=0,
                inicio_gancho_falado_s=palavras[0]["start"],
                mudancas_visuais_s=[
                    cena.inicio_frame / FPS for cena in cenas if cena.inicio_frame > 0
                ],
                elementos=elementos,
                legendas=intervalos,
                textos_tela=[hook, "VÍDEO COMPLETO", "ASSISTA"],
                quantidade_ctas_principais=1,
                derivado=True,
                frase_ponte_aprovada=True,
                video_longo_id=projeto.slug,
                audio_lufs_integrado=loudness,
                musica_mais_presente_que_longo=musica_mais_presente,
                musica_cobre_voz=False,
            )
        )
        ativos_metadados: dict[str, Any] = {}
        for shot_v in manifesto.shots:
            ativo_id = shot_v.ativos[0].ativo_id
            ativo = ativos[ativo_id]
            ficha = carregar_ficha_licenca(ativo.caminho)
            ativos_metadados[ativo_id] = {
                "hash": imagens[shot_v.shot_id][1],
                "descricao": ativo.descricao,
                "licenca": ficha.model_dump(mode="json") if ficha else ativo.licenca,
            }
        descricao_visual = next(iter(ativos_metadados.values()))["descricao"]
        opcoes_metadados = _metadados(
            projeto, candidato, ponte, idioma, descricao_visual=str(descricao_visual)
        )
        metadados_dir = work / "metadados"
        metadados_dir.mkdir()
        atomic_write_json(
            metadados_dir / "metadados.json",
            {
                **opcoes_metadados,
                "revisao": revisao,
                "ativos": ativos_metadados,
                "qa_aprovado": verificacao.aprovado,
                "falhas_qa": [item.regra for item in verificacao.violacoes if not item.aprovada],
            },
        )
        for nome, texto in opcoes_metadados["arquivos"].items():
            atomic_write_text(metadados_dir / nome, texto)
        pasta_saida.parent.mkdir(parents=True, exist_ok=True)
        resultado = ResultadoProducaoShort(
            status="concluido",
            idioma=idioma,
            revisao=revisao,
            caminho_video=str(pasta_saida / "video.mp4"),
            caminho_capa=str(pasta_saida / "capa.jpg"),
            caminho_legendas=str(pasta_saida / "legendas.srt"),
            duracao_s=duracao_total,
            qa_aprovado=verificacao.aprovado,
            falhas_qa=[item.regra for item in verificacao.violacoes if not item.aprovada],
        )
        atomic_write_json(work / "short.json", {"resultado": resultado.model_dump(mode="json")})
        shutil.rmtree(public)
        for temporario in (props_path, trim, concat):
            temporario.unlink(missing_ok=True)
        work.rename(pasta_saida)
        _escrever_ponteiro_saida(pasta_saida, resultado)
    return resultado


def _duracao_wav(caminho: Path) -> float:
    import wave

    with wave.open(str(caminho), "rb") as wav:
        return wav.getnframes() / wav.getframerate()


def _metadados(
    projeto: Projeto,
    candidato: CandidatoShort,
    ponte: str,
    idioma: str,
    *,
    descricao_visual: str = "imagem do trecho narrado",
) -> dict[str, Any]:
    opcoes = projeto.obter_opcoes()
    titulo_longo = str(opcoes.get("nome", projeto.slug))
    hook = " ".join(candidato.texto.split()[:7])
    titulos: list[str] = []
    palavras = candidato.texto.split()
    for inicio in range(min(6, len(palavras))):
        for limite in range(min(10, len(palavras) - inicio), 2, -1):
            titulo = " ".join(palavras[inicio : inicio + limite]).rstrip(".,;:!?—- ")
            if titulo and len(titulo) <= 40 and titulo not in titulos:
                titulos.append(titulo)
            if len(titulos) == 8:
                break
        if len(titulos) == 8:
            break
    descricao = (
        f"{candidato.texto.strip()}\n\nVídeo completo: {titulo_longo} "
        "(vincular como vídeo relacionado)."
    )
    instagram = (
        f"{hook}\n\n{ponte}\n\n#Shorts #Reels #Documentario #VideoCurto #DocForja\n\n"
        f"Texto alternativo: {descricao_visual}, com legendas palavra a palavra."
    )
    youtube = (
        f"Título: {titulos[0] if titulos else titulo_longo[:40]}\n\nDescrição:\n{descricao}\n\n"
        "Vídeo relacionado: selecione o vídeo longo na plataforma."
    )
    instagram += "\nCapa sugerida: capa.jpg."
    youtube += "\n\n#Shorts #Documentario #VideoCurto"
    return {
        "projeto": projeto.slug,
        "titulo_longo": titulo_longo,
        "idioma": idioma,
        "gancho": hook,
        "frase_ponte": ponte,
        "video_relacionado": projeto.slug,
        "requer_vinculo_manual": True,
        "arquivos": {
            "titulos.md": "# Títulos sugeridos (máximo 40 caracteres)\n\n"
            + "\n".join(f"{idx}. {titulo}" for idx, titulo in enumerate(titulos, 1))
            + "\n",
            "youtube.md": youtube + "\n",
            "instagram.md": instagram + "\n",
            "comentario_fixado.md": (
                f"Assista ao vídeo completo: [adicionar link de {titulo_longo}]\n"
            ),
        },
    }


def executar_producao_background(projeto: Projeto, referencia: str) -> None:
    """Registra a conclusão/falha para consulta assíncrona pela interface."""
    estado = projeto.pastas.montagem / "shorts" / "derivados" / referencia / "producao_atual.json"
    solicitado = json.loads(estado.read_text(encoding="utf-8"))
    aprovado = json.loads((estado.parent / "aprovacao_atual.json").read_text(encoding="utf-8"))
    manifesto = json.loads((estado.parent / "manifesto_atual.json").read_text(encoding="utf-8"))
    versoes = {
        "fonte_hash": solicitado.get("fonte_hash"),
        "aprovacao_versao": solicitado.get("aprovacao_versao"),
        "manifesto_versao": solicitado.get("manifesto_versao"),
    }
    if (
        aprovado.get("fonte_hash") != versoes["fonte_hash"]
        or aprovado.get("versao") != versoes["aprovacao_versao"]
        or manifesto.get("fonte_hash") != versoes["fonte_hash"]
        or manifesto.get("versao") != versoes["manifesto_versao"]
    ):
        atomic_write_json(
            estado,
            {
                "status": "falhou",
                "erro": "A aprovação mudou antes do início; atualize a tela.",
                **versoes,
            },
        )
        return
    atomic_write_json(estado, {"status": "executando", "referencia": referencia, **versoes})
    try:
        resultado = produzir_short_derivado(projeto, referencia)
        atomic_write_json(
            estado,
            {"status": "concluido", "resultado": resultado.model_dump(mode="json"), **versoes},
        )
    except Exception as exc:
        atomic_write_json(estado, {"status": "falhou", "erro": str(exc)[:1000], **versoes})


__all__ = ["ResultadoProducaoShort", "executar_producao_background", "produzir_short_derivado"]
