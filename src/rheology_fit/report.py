"""Report generation: flow curve plot, metrics, residuals, and JSON export."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from rheology_fit import __version__
from rheology_fit.data import FlowCurveData
from rheology_fit.models import FitResult, classify_flow_behavior

_MODEL_COLORS = {"PowerLaw": "#1b9e77", "HerschelBulkley": "#d95f02", "Casson": "#7570b3"}


def build_figure(data: FlowCurveData, results: list[FitResult], best: FitResult) -> plt.Figure:
    fig, (ax_main, ax_res) = plt.subplots(
        2, 1, figsize=(8, 9), gridspec_kw={"height_ratios": [2.5, 1]}
    )

    g_smooth = np.linspace(data.shear_rate.min(), data.shear_rate.max(), 300)
    for r in results:
        style = "-" if r.model_name == best.model_name else "--"
        lw = 2.5 if r.model_name == best.model_name else 1.3
        label = f"{r.model_name} (R²={r.r2:.4f})" + (" — best" if r.model_name == best.model_name else "")
        ax_main.plot(
            g_smooth, r.predict(g_smooth), style, lw=lw,
            color=_MODEL_COLORS.get(r.model_name, "gray"), label=label,
        )

    if data.shear_stress_std is not None:
        ax_main.errorbar(
            data.shear_rate, data.shear_stress, yerr=data.shear_stress_std, fmt="o",
            color="black", ecolor="gray", capsize=3, label="Experimental data", zorder=5,
        )
    else:
        ax_main.scatter(data.shear_rate, data.shear_stress, color="black", zorder=5, label="Experimental data")

    ax_main.set_xlabel("Shear rate, $\\dot{\\gamma}$ (s$^{-1}$)")
    ax_main.set_ylabel("Shear stress, $\\tau$ (Pa)")
    ax_main.set_title("Flow curve — model comparison")
    ax_main.legend(loc="upper left", fontsize=8)
    ax_main.grid(alpha=0.3)

    behavior = classify_flow_behavior(best)
    ax_main.text(
        0.98, 0.03, behavior, transform=ax_main.transAxes, ha="right", va="bottom",
        fontsize=8.5, style="italic", color="dimgray",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.7, "edgecolor": "lightgray"},
    )

    residuals = data.shear_stress - best.predict(data.shear_rate)
    ax_res.axhline(0, color="black", lw=1)
    ax_res.scatter(data.shear_rate, residuals, color=_MODEL_COLORS.get(best.model_name, "gray"))
    ax_res.set_xlabel("Shear rate, $\\dot{\\gamma}$ (s$^{-1}$)")
    ax_res.set_ylabel("Residual (Pa)")
    ax_res.set_title(f"Residuals — best model ({best.model_name})")
    ax_res.grid(alpha=0.3)

    fig.suptitle(f"rheology-fit v{__version__}", fontsize=9, x=0.99, y=0.995, ha="right", color="gray")
    fig.tight_layout()
    return fig


def save_report(
    data: FlowCurveData,
    results: list[FitResult],
    best: FitResult,
    output: str | Path,
    formats: tuple[str, ...] = ("pdf", "png"),
) -> list[Path]:
    """Render and save the report figure in the requested formats."""
    output = Path(output)
    fig = build_figure(data, results, best)
    saved = []
    for fmt in formats:
        path = output.with_suffix(f".{fmt}")
        fig.savefig(path, dpi=200, bbox_inches="tight")
        saved.append(path)
    plt.close(fig)
    return saved


def export_json(
    data: FlowCurveData,
    results: list[FitResult],
    best: FitResult,
    output: str | Path,
) -> Path:
    """Write fitted parameters and metrics to a JSON file for downstream use."""
    output = Path(output).with_suffix(".json")
    payload = {
        "rheology_fit_version": __version__,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(data.source),
        "n_data_points": len(data),
        "best_model": best.model_name,
        "flow_behavior": classify_flow_behavior(best),
        "models": [
            {
                "name": r.model_name,
                "params": r.params,
                "param_errors": r.param_errors,
                "r2": r.r2,
                "rmse": r.rmse,
                "aic": r.aic,
                "n_points_used": r.n_points,
            }
            for r in results
        ],
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output
