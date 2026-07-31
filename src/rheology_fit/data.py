"""Loading and validation of flow curve (shear rate / shear stress) data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ("shear_rate", "shear_stress")
STD_COLUMN = "shear_stress_std"


@dataclass
class FlowCurveData:
    """Experimental shear rate / shear stress pairs (a flow curve)."""

    shear_rate: np.ndarray
    shear_stress: np.ndarray
    shear_stress_std: np.ndarray | None
    source: Path

    def __post_init__(self) -> None:
        if self.shear_rate.shape != self.shear_stress.shape:
            raise ValueError("shear_rate and shear_stress arrays must have the same shape")
        if self.shear_stress_std is not None and self.shear_stress_std.shape != self.shear_rate.shape:
            raise ValueError("shear_stress_std must have the same shape as shear_rate")

    def __len__(self) -> int:
        return self.shear_rate.size


def load_flow_curve_csv(path: str | Path) -> FlowCurveData:
    """Load a CSV file with columns `shear_rate` (1/s), `shear_stress` (Pa),
    and optional `shear_stress_std`.

    Parameters
    ----------
    path : str | Path
        Path to a CSV file. `shear_rate` must be > 0 (models are undefined
        or trivial at zero shear rate); `shear_stress` must be >= 0.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"CSV is missing required column(s): {missing}. "
            f"Expected at least: {REQUIRED_COLUMNS}"
        )

    df = df.dropna(subset=list(REQUIRED_COLUMNS))
    if len(df) < 4:
        raise ValueError(
            f"At least 4 valid (shear_rate, shear_stress) data points are required "
            f"for fitting a 3-parameter model; got {len(df)}"
        )

    shear_rate = df["shear_rate"].to_numpy(dtype=float)
    shear_stress = df["shear_stress"].to_numpy(dtype=float)

    if np.any(shear_rate <= 0):
        raise ValueError("shear_rate values must be strictly positive")
    if np.any(shear_stress < 0):
        raise ValueError("shear_stress values must be non-negative")

    shear_stress_std = None
    if STD_COLUMN in df.columns:
        shear_stress_std = df[STD_COLUMN].to_numpy(dtype=float)

    return FlowCurveData(
        shear_rate=shear_rate,
        shear_stress=shear_stress,
        shear_stress_std=shear_stress_std,
        source=path,
    )
