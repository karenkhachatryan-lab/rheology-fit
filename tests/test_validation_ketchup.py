"""Validation against a literature-referenced flow curve (see examples/README.md).

These points were computed from the Herschel-Bulkley parameters reported for
control (no added hydrocolloid) tomato ketchup at 25 degC by Koocheki et al.
(2009), Int. J. Food Sci. Technol. 44(3):596-602
(doi: 10.1111/j.1365-2621.2008.01868.x): tau0=4.41, K=16.18, n=0.250.
"""

from pathlib import Path

import pytest

from rheology_fit.data import load_flow_curve_csv
from rheology_fit.models import fit_model

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

PUBLISHED_TAU0 = 4.41
PUBLISHED_K = 16.18
PUBLISHED_N = 0.250


def test_herschel_bulkley_recovers_published_ketchup_parameters():
    data = load_flow_curve_csv(EXAMPLES_DIR / "ketchup_koocheki2009_25C.csv")
    result = fit_model(data, "HerschelBulkley")

    assert result.r2 > 0.9999
    assert result.params["tau0"] == pytest.approx(PUBLISHED_TAU0, abs=0.01)
    assert result.params["K"] == pytest.approx(PUBLISHED_K, abs=0.01)
    assert result.params["n"] == pytest.approx(PUBLISHED_N, abs=0.001)
