from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from docforja.benchmark import BenchmarkRunner
from docforja.doctor import Doctor
from docforja.models import CheckStatus
from docforja.settings import load_settings

app = typer.Typer(no_args_is_help=True, help="Ferramentas locais do DocForja.")
console = Console()

STATUS_LABEL = {
    CheckStatus.OK: "[green]OK[/green]",
    CheckStatus.WARNING: "[yellow]![/yellow]",
    CheckStatus.ERROR: "[red]X[/red]",
    CheckStatus.SKIPPED: "[dim]-[/dim]",
}


@app.command()
def doctor(
    config: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = Path(
        "config/adaptadores.yaml"
    ),
) -> None:
    """Confere máquina, serviços, ferramentas e configuração sem revelar segredos."""
    load_dotenv()
    report = Doctor(load_settings(config)).run()
    table = Table(title="DocForja doctor", show_lines=False)
    table.add_column("Estado", justify="center")
    table.add_column("Item")
    table.add_column("Resultado")
    for item in report.checks:
        table.add_row(STATUS_LABEL[item.status], item.label, item.summary)
    console.print(table)
    if not report.healthy:
        raise typer.Exit(code=1)


@app.command()
def benchmark(
    config: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = Path(
        "config/adaptadores.yaml"
    ),
    real: Annotated[bool, typer.Option(help="Executa ensaios reais do M0.")] = False,
    category: Annotated[
        list[str] | None,
        typer.Option(
            help="Categoria: imagem, tts, alinhamento, parallax, recorte, upscale ou render."
        ),
    ] = None,
) -> None:
    """Mede os adaptadores disponíveis e registra ausências sem abortar a bateria inteira."""
    settings = load_settings(config)
    if real:
        from docforja.real_benchmark import RealBenchmarkRunner

        runner = RealBenchmarkRunner(settings, config.parent)
        report = runner.run(category or ["imagem", "tts"])
        console.print(f"Execução preservada: {runner.output}")
    else:
        report = BenchmarkRunner(
            output_dir=settings.paths.benchmark_output,
            python_environments=settings.python_environments,
        ).run()
    table = Table(title="DocForja benchmark")
    table.add_column("Estado", justify="center")
    table.add_column("Categoria")
    table.add_column("Candidato")
    table.add_column("Tempo")
    table.add_column("Observação")
    for item in report.results:
        table.add_row(
            STATUS_LABEL[item.status],
            item.category,
            item.candidate,
            f"{item.duration_seconds:.2f}s",
            item.message,
        )
    console.print(table)
    console.print("Resultados: [bold]config/benchmark.json[/bold]")
    console.print(f"Arquivos para avaliação: [bold]{settings.paths.benchmark_output}[/bold]")
    if any(item.status == CheckStatus.ERROR for item in report.results):
        raise typer.Exit(code=1)


@app.command()
def novo(
    nome: Annotated[str, typer.Argument(help="Nome ou tema do projeto")],
    tipo: Annotated[
        str, typer.Option(help="Tipo: longo, short_derivado, short_avulso, musica")
    ] = "longo",
    roteiro: Annotated[
        Path | None, typer.Option(help="Caminho do arquivo markdown de roteiro")
    ] = None,
    idioma: Annotated[str, typer.Option(help="Idioma principal")] = "pt-BR",
    preset: Annotated[str, typer.Option(help="Preset: rapido, padrao, caprichado")] = "padrao",
    kit: Annotated[str, typer.Option(help="Identificador do kit visual")] = "cinza-e-brasa@1.0",
) -> None:
    """Cria um novo projeto DocForja com toda a árvore de diretórios oficial."""
    from docforja.nucleo.projeto import Projeto

    roteiro_texto = ""
    if roteiro:
        if not roteiro.is_file():
            console.print(f"[red]Arquivo de roteiro não encontrado: {roteiro}[/red]")
            raise typer.Exit(code=1)
        roteiro_texto = roteiro.read_text(encoding="utf-8")

    projeto = Projeto.criar(
        nome=nome,
        tipo=tipo,
        roteiro=roteiro_texto,
        idioma_principal=idioma,
        preset=preset,
        kit=kit,
    )
    console.print(f"[green][OK] Projeto criado com sucesso:[/green] [bold]{projeto.slug}[/bold]")
    console.print(f"Diretório: [dim]{projeto.raiz}[/dim]")


@app.command()
def status(
    slug_ou_caminho: Annotated[str | None, typer.Argument(help="Slug ou pasta do projeto")] = None,
) -> None:
    """Exibe o estado de etapas do projeto, semáforo de GPU e cotas."""
    from docforja.nucleo.banco import BancoProjeto
    from docforja.nucleo.cotas import gerenciador_cotas
    from docforja.nucleo.gpu import semaforo_gpu
    from docforja.nucleo.projeto import Projeto

    # Exibe resumo de GPU e Cotas
    gpu_info = semaforo_gpu.obter_status()
    estado_gpu = (
        "[bold red]Ocupada[/bold red]" if gpu_info["ocupada"] else "[bold green]Ociosa[/bold green]"
    )
    console.print(f"GPU: {estado_gpu} (Modelo ativo: {gpu_info['modelo_atual'] or 'nenhum'})")

    cotas_info = gerenciador_cotas.obter_resumo()
    console.print(f"Cotas: Requisições hoje: {cotas_info['requisicoes']}")

    if not slug_ou_caminho:
        return

    projeto = Projeto.carregar(slug_ou_caminho)
    banco = BancoProjeto(projeto.banco_file)
    etapas = banco.listar_etapas()

    table = Table(title=f"Projeto: {projeto.slug}")
    table.add_column("Etapa", style="bold")
    table.add_column("Status")
    table.add_column("Duração")
    table.add_column("Observações")

    for e in etapas:
        cor = (
            "green"
            if e["status"] == "concluida"
            else ("yellow" if e["status"] == "pausada_revisao" else "white")
        )
        table.add_row(
            e["id"],
            f"[{cor}]{e['status']}[/{cor}]",
            f"{e['duracao_s']:.2f}s" if e["duracao_s"] else "-",
            e["erro"] or "",
        )
    console.print(table)
    status_por_id = {e["id"]: e["status"] for e in etapas}
    gate_m3_m4 = {
        "P2_narracao",
        "P4_shots",
        "P6_verificador",
        "P8_estimativa_previa",
        "REVISAO",
    }
    if gate_m3_m4.issubset(status_por_id) and all(
        status_por_id[etapa] == "concluida" for etapa in gate_m3_m4
    ):
        ausentes = projeto.artefatos_m3_m4_ausentes()
        if ausentes:
            console.print(
                "[bold yellow]Saídas obrigatórias de M3/M4 ausentes:[/bold yellow]"
            )
            for caminho in ausentes:
                console.print(f" - {caminho}")


@app.command()
def executar(
    slug_ou_caminho: Annotated[str, typer.Argument(help="Slug ou pasta do projeto")],
    aprovar_gate: Annotated[str | None, typer.Option(help="Aprova um gate como REVISAO")] = None,
    concorrencia: Annotated[int, typer.Option(help="Máximo de tarefas em paralelo")] = 4,
) -> None:
    """Executa o pipeline do projeto até o próximo gate ou conclusão."""
    import asyncio

    from docforja.nucleo.executor import ExecutorPipeline
    from docforja.nucleo.projeto import Projeto

    projeto = Projeto.carregar(slug_ou_caminho)
    executor = ExecutorPipeline(projeto)
    if aprovar_gate:
        executor.aprovar_gate(aprovar_gate)
        console.print(f"[green][OK] Gate {aprovar_gate} aprovado com sucesso.[/green]")

    console.print(f"Iniciando pipeline para [bold]{projeto.slug}[/bold]...")
    resultados = asyncio.run(executor.executar(max_concorrencia=concorrencia))
    for etapa, st in resultados.items():
        console.print(f" - {etapa}: {st}")
    falhadas = [etapa for etapa, st in resultados.items() if st == "falhou"]
    if falhadas:
        console.print(
            "[bold red]Execução interrompida por falha nas etapas: "
            f"{', '.join(falhadas)}.[/bold red]"
        )
        raise typer.Exit(code=1)
    console.print("[bold green]Execução finalizada.[/bold green]")


@app.command()
def ui(
    host: Annotated[str, typer.Option(help="Host de escuta")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Porta HTTP")] = 7860,
    open_browser: Annotated[bool, typer.Option(help="Abrir no navegador")] = True,
) -> None:
    """Inicia a interface web local do DocForja em 127.0.0.1:7860."""
    import webbrowser

    import uvicorn

    url = f"http://{host}:{port}"
    console.print(f"[bold green][OK] DocForja UI disponível em {url}[/bold green]")
    if open_browser:
        webbrowser.open(url)
    uvicorn.run("docforja.api:app", host=host, port=port, log_level="info")
