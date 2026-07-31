"""Non-Newtonian flow curve models, curve fitting, and goodness-of-fit metrics."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import curve_fit

from rheology_fit.data import FlowCurveData


def power_law(gamma_dot: np.ndarray, k: float, n: float) -> np.ndarray:
    """Ostwald-de Waele power-law model: tau = K * gamma_dot^n."""
    return k * np.power(gamma_dot, n)


def herschel_bulkley(gamma_dot: np.ndarray, tau0: float, k: float, n: float) -> np.ndarray:
    """Herschel-Bulkley model: tau = tau0 + K * gamma_dot^n."""
    return tau0 + k * np.power(gamma_dot, n)


def casson(gamma_dot: np.ndarray, tau0: float, eta_c: float) -> np.ndarray:
    """Casson model: sqrt(tau) = sqrt(tau0) + sqrt(eta_c * gamma_dot)."""
    return np.square(np.sqrt(tau0) + np.sqrt(eta_c * gamma_dot))


@dataclass
class ModelSpec:
    name: str
    func: callable
    param_names: tuple[str, ...]
    p0: callable
    bounds: callable


def _power_law_p0(data: FlowCurveData) -> list[float]:
    mid = len(data) // 2
    g, t = data.shear_rate[mid], max(data.shear_stress[mid], 1e-6)
    k0 = t / (g**0.5)
    return [max(k0, 1e-6), 0.5]


def _power_law_bounds(data: FlowCurveData):
    return ([1e-9, 1e-3], [np.inf, 3.0])


def _hb_p0(data: FlowCurveData) -> list[float]:
    tau0_0 = max(float(data.shear_stress.min()) * 0.5, 1e-6)
    mid = len(data) // 2
    g, t = data.shear_rate[mid], max(data.shear_stress[mid] - tau0_0, 1e-6)
    k0 = t / (g**0.5)
    return [tau0_0, max(k0, 1e-6), 0.5]


def _hb_bounds(data: FlowCurveData):
    return ([0.0, 1e-9, 1e-3], [float(data.shear_stress.max()), np.inf, 3.0])


def _casson_p0(data: FlowCurveData) -> list[float]:
    tau0_0 = max(float(data.shear_stress.min()) * 0.5, 1e-6)
    span_g = float(data.shear_rate.max() - data.shear_rate.min())
    span_t = float(data.shear_stress.max() - data.shear_stress.min())
    eta0 = max(span_t / span_g, 1e-6) if span_g > 0 else 1.0
    return [tau0_0, eta0]


def _casson_bounds(data: FlowCurveData):
    return ([0.0, 1e-9], [float(data.shear_stress.max()), np.inf])


MODEL_REGISTRY: dict[str, ModelSpec] = {
    "PowerLaw": ModelSpec("PowerLaw", power_law, ("K", "n"), _power_law_p0, _power_law_bounds),
    "HerschelBulkley": ModelSpec(
        "HerschelBulkley", herschel_bulkley, ("tau0", "K", "n"), _hb_p0, _hb_bounds
    ),
    "Casson": ModelSpec("Casson", casson, ("tau0", "eta_c"), _casson_p0, _casson_bounds),
}


@dataclass
class FitResult:
    model_name: str
    params: dict[str, float]
    param_errors: dict[str, float]
    r2: float
    rmse: float
    aic: float
    n_points: int
    predict: callable = field(repr=False, default=None)


def _compute_metrics(y: np.ndarray, y_pred: np.ndarray, n_params: int) -> tuple[float, float, float]:
    residuals = y - y_pred
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    n = y.size
    rmse = float(np.sqrt(ss_res / n))
    aic = n * np.log(ss_res / n) + 2 * n_params
    return r2, rmse, aic


def fit_model(data: FlowCurveData, model_name: str) -> FitResult:
    """Fit a single named model (PowerLaw, HerschelBulkley, or Casson)."""
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model '{model_name}'. Available: {list(MODEL_REGISTRY)}")
    spec = MODEL_REGISTRY[model_name]

    p0 = spec.p0(data)
    bounds = spec.bounds(data)
    popt, pcov = curve_fit(
        spec.func, data.shear_rate, data.shear_stress, p0=p0, bounds=bounds, maxfev=20000
    )
    perr = np.sqrt(np.diag(pcov))

    y_pred = spec.func(data.shear_rate, *popt)
    r2, rmse, aic = _compute_metrics(data.shear_stress, y_pred, len(popt))

    params = dict(zip(spec.param_names, (float(v) for v in popt)))
    param_errors = dict(zip(spec.param_names, (float(v) for v in perr)))

    return FitResult(
        model_name=model_name,
        params=params,
        param_errors=param_errors,
        r2=r2,
        rmse=rmse,
        aic=aic,
        n_points=data.shear_rate.size,
        predict=lambda g, _f=spec.func, _p=popt: _f(g, *_p),
    )


def fit_all(
    data: FlowCurveData, model_names: tuple[str, ...] = ("PowerLaw", "HerschelBulkley", "Casson")
) -> list[FitResult]:
    """Fit all requested models, skipping (with a warning) any that fail to converge."""
    results = []
    for name in model_names:
        try:
            results.append(fit_model(data, name))
        except RuntimeError as exc:
            import warnings

            warnings.warn(f"Model '{name}' failed to converge: {exc}")
    if not results:
        raise RuntimeError("No model converged on the given data")
    return results


def select_best_model(results: list[FitResult]) -> FitResult:
    """Select the model with the lowest AIC. All models here are fit on the
    same full dataset (no restricted-range subset issue like isotherm-fit's
    BET model), so AIC values are always directly comparable."""
    return min(results, key=lambda r: r.aic)


def classify_flow_behavior(best: FitResult) -> str:
    """Human-readable flow-behavior classification from the best-fit model's
    parameters: presence of a yield stress and the flow behavior index n."""
    tau0 = best.params.get("tau0")
    tau0_err = best.param_errors.get("tau0")
    has_yield_stress = (
        tau0 is not None and tau0_err is not None and tau0 > 3 * tau0_err and tau0 > 1e-6
    )

    n = best.params.get("n")
    if n is None:
        # Casson has no explicit n; classify from tau0 alone.
        return "Bingham-like plastic (yield stress + Casson viscosity)" if has_yield_stress else "Near-Newtonian (Casson)"

    if n < 0.9:
        behavior = "shear-thinning (pseudoplastic)"
    elif n > 1.1:
        behavior = "shear-thickening (dilatant)"
    else:
        behavior = "approximately Newtonian"

    if has_yield_stress:
        return f"Yield-stress fluid, {behavior} above yield (Herschel-Bulkley)"
    return behavior.capitalize()
