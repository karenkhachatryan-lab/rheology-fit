import json
from pathlib import Path

import numpy as np

from rheology_fit.data import FlowCurveData
from rheology_fit.models import fit_all, herschel_bulkley, select_best_model
from rheology_fit.report import export_json, save_report

RNG = np.random.default_rng(7)


def _sample_data():
    gamma = np.linspace(1, 100, 12)
    tau = herschel_bulkley(gamma, 20.0, 5.0, 0.4) + RNG.normal(0, 0.5, size=12)
    return FlowCurveData(shear_rate=gamma, shear_stress=tau, shear_stress_std=None, source=Path("synthetic"))


def test_save_report_creates_expected_files(tmp_path):
    data = _sample_data()
    results = fit_all(data, ("PowerLaw", "HerschelBulkley", "Casson"))
    best = select_best_model(results)

    output = tmp_path / "report"
    paths = save_report(data, results, best, output, formats=("png",))

    assert len(paths) == 1
    assert paths[0].exists()
    assert paths[0].stat().st_size > 0


def test_export_json_contains_expected_fields(tmp_path):
    data = _sample_data()
    results = fit_all(data, ("PowerLaw", "HerschelBulkley", "Casson"))
    best = select_best_model(results)

    output = tmp_path / "report"
    json_path = export_json(data, results, best, output)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["best_model"] == best.model_name
    assert "flow_behavior" in payload
    assert len(payload["models"]) == 3
    assert payload["n_data_points"] == len(data)
