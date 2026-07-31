"""Command-line interface for rheology-fit."""

from __future__ import annotations

from pathlib import Path

import typer

from rheology_fit.citation import CITATION_APA, CITATION_BIBTEX
from rheology_fit.data import load_flow_curve_csv
from rheology_fit.models import classify_flow_behavior, fit_all, select_best_model
from rheology_fit.report import export_json, save_report

app = typer.Typer(
    name="rheology-fit",
    help="Fit non-Newtonian flow curve models to shear stress/rate data.",
    add_completion=False,
)


@app.command()
def fit(
    csv_path: Path = typer.Argument(..., help="Path to the input CSV (columns: shear_rate, shear_stress[, shear_stress_std])."),
    output: Path = typer.Option(Path("report"), "--output", "-o", help="Output path stem (no extension)."),
    models: str = typer.Option(
        "PowerLaw,HerschelBulkley,Casson", "--models", help="Comma-separated list of models to fit."
    ),
    formats: str = typer.Option("pdf,png", "--formats", help="Comma-separated report formats to save."),
) -> None:
    """Fit flow curve models to CSV data and generate a report."""
    data = load_flow_curve_csv(csv_path)
    model_names = tuple(m.strip() for m in models.split(","))
    results = fit_all(data, model_names)
    best = select_best_model(results)

    fmt_tuple = tuple(f.strip() for f in formats.split(","))
    saved_paths = save_report(data, results, best, output, fmt_tuple)
    json_path = export_json(data, results, best, output)

    typer.echo(f"Fitted {len(results)} model(s) on {len(data)} data points.")
    for r in results:
        marker = " <- best (lowest AIC)" if r.model_name == best.model_name else ""
        typer.echo(f"  {r.model_name}: R2={r.r2:.4f}  RMSE={r.rmse:.4f}  AIC={r.aic:.2f}{marker}")
    typer.echo(f"Flow behavior ({best.model_name}): {classify_flow_behavior(best)}")
    typer.echo("Saved: " + ", ".join(str(p) for p in [*saved_paths, json_path]))


@app.command()
def cite() -> None:
    """Print citation information (APA + BibTeX)."""
    typer.echo(CITATION_APA)
    typer.echo("")
    typer.echo(CITATION_BIBTEX)


@app.command()
def gui() -> None:
    """Launch the desktop GUI (requires the 'gui' extra: pip install rheology-fit[gui])."""
    try:
        from rheology_fit.gui import main as gui_main
    except ImportError as exc:
        typer.echo(
            "The GUI requires customtkinter. Install it with:\n"
            "  pip install rheology-fit[gui]"
        )
        raise typer.Exit(code=1) from exc
    gui_main()


if __name__ == "__main__":
    app()
