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
