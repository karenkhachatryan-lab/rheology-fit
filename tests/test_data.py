from pathlib import Path

import pytest

from rheology_fit.data import load_flow_curve_csv


def _write_csv(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "data.csv"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_valid_csv(tmp_path):
    path = _write_csv(
        tmp_path,
        "shear_rate,shear_stress\n1,25.0\n10,42.0\n50,68.0\n100,85.0\n",
    )
    data = load_flow_curve_csv(path)
    assert len(data) == 4
    assert data.shear_stress_std is None


def test_load_csv_with_std(tmp_path):
    path = _write_csv(
        tmp_path,
        "shear_rate,shear_stress,shear_stress_std\n1,25.0,1.0\n10,42.0,1.2\n50,68.0,1.5\n100,85.0,1.8\n",
    )
    data = load_flow_curve_csv(path)
    assert data.shear_stress_std is not None
    assert data.shear_stress_std.shape == data.shear_rate.shape


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_flow_curve_csv(tmp_path / "nope.csv")


def test_missing_required_column_raises(tmp_path):
    path = _write_csv(tmp_path, "shear_rate,stress\n1,25.0\n10,42.0\n50,68.0\n100,85.0\n")
    with pytest.raises(ValueError, match="missing required column"):
        load_flow_curve_csv(path)


def test_too_few_points_raises(tmp_path):
    path = _write_csv(tmp_path, "shear_rate,shear_stress\n1,25.0\n10,42.0\n")
    with pytest.raises(ValueError, match="At least 4"):
        load_flow_curve_csv(path)


def test_non_positive_shear_rate_raises(tmp_path):
    path = _write_csv(
        tmp_path, "shear_rate,shear_stress\n0,25.0\n10,42.0\n50,68.0\n100,85.0\n"
    )
    with pytest.raises(ValueError, match="strictly positive"):
        load_flow_curve_csv(path)


def test_negative_shear_stress_raises(tmp_path):
    path = _write_csv(
        tmp_path, "shear_rate,shear_stress\n1,-5.0\n10,42.0\n50,68.0\n100,85.0\n"
    )
    with pytest.raises(ValueError, match="non-negative"):
        load_flow_curve_csv(path)
