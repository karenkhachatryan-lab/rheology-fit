# rheology-fit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-in%20development-orange.svg)](#project-status)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21713809.svg)](https://doi.org/10.5281/zenodo.21713809)

Fit non-Newtonian flow curve models (Power-law, Herschel-Bulkley, Casson) to shear stress / shear rate data, with objective model selection and flow-behavior classification — for sauces, purées, doughs, and other non-Newtonian food fluids.

## Problem

Rheological characterization of non-Newtonian food fluids — the relationship between shear stress and shear rate — underpins process design (pumping, mixing, extrusion), texture/mouthfeel prediction, and quality control. Researchers typically measure a flow curve on a rheometer and then fit one or more models (Power-law, Herschel-Bulkley, Casson) by hand in a spreadsheet — a slow, inconsistent process, especially since Herschel-Bulkley requires genuine nonlinear regression that spreadsheets handle poorly. `rheology-fit` automates model fitting, objective model selection (AIC), and flow-behavior interpretation (shear-thinning/thickening, yield stress), producing a publication-ready report.

## Installation

```bash
pip install rheology-fit
```

Or from source:

```bash
git clone https://github.com/karenkhachatryan-lab/rheology-fit.git
cd rheology-fit
pip install -e ".[dev]"
```

## Usage

Input CSV with columns `shear_rate` (s⁻¹), `shear_stress` (Pa), and optionally `shear_stress_std`:

```csv
shear_rate,shear_stress,shear_stress_std
1,20.6,0.3
10,33.2,0.4
50,47.4,0.5
100,55.6,0.6
```

Fit models and generate a report:

```bash
rheology-fit fit data.csv --output report
```

This produces:
- `report.pdf` — flow curve with all fitted model curves, flow-behavior annotation, residuals plot for the best model,
- `report.json` — fitted parameters, metrics (R², RMSE, AIC), and flow-behavior classification.

Print citation information:

```bash
rheology-fit cite
```

### Desktop GUI (optional)

```bash
pip install "rheology-fit[gui]"
rheology-fit gui
```

Opens a desktop window (CustomTkinter) to load a CSV, pick models, view the flow-curve plot and metrics live, and save the PDF/PNG/JSON outputs — no command-line arguments needed.

For users without Python, a prebuilt standalone Windows GUI is attached as a `.zip` to each [GitHub Release](https://github.com/karenkhachatryan-lab/rheology-fit/releases/latest) — download, extract, and run `rheology-fit-gui.exe`, no installation needed. To build it yourself instead, see `packaging/build_exe.ps1` (PyInstaller).

## Models

- **Power-law** (Ostwald-de Waele): τ = K·γ̇ⁿ — 2 parameters, no yield stress.
- **Herschel-Bulkley**: τ = τ₀ + K·γ̇ⁿ — 3 parameters; the standard model for yield-stress food fluids (ketchup, mayonnaise, purées).
- **Casson**: √τ = √τ₀ + √(η꜀·γ̇) — 2 parameters; common for chocolate and some dairy/meat emulsions.

Unlike `isotherm-fit`'s BET model, all three models here are fit on the full dataset, so their AIC values are always directly comparable — no restricted-range caveat.

## Project status

Early development (v0.2.0) — MVP scope: 3 models, CSV loader, AIC-based model selection, PDF/PNG + JSON report generation, CLI via Typer, optional CustomTkinter desktop GUI. See [CHANGELOG.md](CHANGELOG.md).

## Citing this software

If you use `rheology-fit` in your research, please cite it — see [`CITATION.cff`](CITATION.cff) or run `rheology-fit cite` for the formatted citation and BibTeX entry. DOI: [10.5281/zenodo.21713809](https://doi.org/10.5281/zenodo.21713809).

## Contributing and support

Bug reports, feature requests, and usage questions are all welcome via [GitHub Issues](https://github.com/karenkhachatryan-lab/rheology-fit/issues).

## License

MIT — see [LICENSE](LICENSE).
