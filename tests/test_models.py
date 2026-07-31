from pathlib import Path

import numpy as np
import pytest

from rheology_fit.data import FlowCurveData
from rheology_fit.models import (
    casson,
    classify_flow_behavior,
    fit_all,
    fit_model,
    herschel_bulkley,
    power_law,
    select_best_model,
)

RNG = np.random.default_rng(42)


def _make_data(true_func, params, gamma=None, noise_sd=0.5) -> FlowCurveData:
    if gamma is None:
        gamma = np.linspace(1, 100, 15)
    tau = true_func(gamma, *params) + RNG.normal(0, noise_sd, size=gamma.size)
    tau = np.clip(tau, 0.01, None)
    return FlowCurveData(shear_rate=gamma, shear_stress=tau, shear_stress_std=None, source=Path("synthetic"))


def test_power_law_fit_recovers_known_parameters():
    true_k, true_n = 3.0, 0.6
    data = _make_data(power_law, (true_k, true_n), noise_sd=0.3)
    result = fit_model(data, "PowerLaw")

    assert result.r2 > 0.98
    assert result.params["K"] == pytest.approx(true_k, rel=0.2)
    assert result.params["n"] == pytest.approx(true_n, rel=0.15)


def test_herschel_bulkley_fit_recovers_known_parameters():
    true_tau0, true_k, true_n = 20.0, 5.0, 0.4
    data = _make_data(herschel_bulkley, (true_tau0, true_k, true_n), noise_sd=1.0)
    result = fit_model(data, "HerschelBulkley")

    assert result.r2 > 0.98
    assert result.params["tau0"] == pytest.approx(true_tau0, rel=0.15)
    assert result.params["K"] == pytest.approx(true_k, rel=0.3)
    assert result.params["n"] == pytest.approx(true_n, rel=0.3)


def test_casson_fit_recovers_known_parameters():
    true_tau0, true_eta = 15.0, 0.8
    data = _make_data(casson, (true_tau0, true_eta), noise_sd=0.8)
    result = fit_model(data, "Casson")

    assert result.r2 > 0.98
    assert result.params["tau0"] == pytest.approx(true_tau0, rel=0.2)
    assert result.params["eta_c"] == pytest.approx(true_eta, rel=0.2)


def test_select_best_model_picks_the_true_generating_model():
    true_tau0, true_k, true_n = 20.0, 5.0, 0.4
    data = _make_data(herschel_bulkley, (true_tau0, true_k, true_n), noise_sd=0.5)
    results = fit_all(data, ("PowerLaw", "HerschelBulkley", "Casson"))
    best = select_best_model(results)
    assert best.model_name == "HerschelBulkley"


def test_classify_flow_behavior_shear_thinning_no_yield():
    data = _make_data(power_law, (3.0, 0.5), noise_sd=0.2)
    result = fit_model(data, "PowerLaw")
    behavior = classify_flow_behavior(result)
    assert "shear-thinning" in behavior.lower()


def test_classify_flow_behavior_yield_stress_fluid():
    data = _make_data(herschel_bulkley, (30.0, 5.0, 0.4), noise_sd=0.5)
    result = fit_model(data, "HerschelBulkley")
    behavior = classify_flow_behavior(result)
    assert "yield" in behavior.lower()


def test_unknown_model_raises():
    data = _make_data(power_law, (3.0, 0.5))
    with pytest.raises(ValueError, match="Unknown model"):
        fit_model(data, "Bingham")
