# Changelog

All notable changes to this project are documented here. Versioning follows [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-07-31

### Added
- Optional CustomTkinter desktop GUI (`rheology-fit gui`): File/Edit/Help menu bar, project save/load (`.rheofitproj`), Cite and About dialogs, live plot/metrics view.
- PyInstaller build script (`packaging/build_exe.ps1`) for a standalone Windows executable, distributed as a `.zip` on GitHub Releases.

## [0.1.0] - 2026-07-31

### Added
- Initial release: Power-law, Herschel-Bulkley, and Casson flow curve model fitting via `scipy.optimize.curve_fit`.
- AIC-based best-model selection (all three models fit on the full dataset, so AIC values are always directly comparable).
- Flow-behavior classification (shear-thinning/thickening, yield-stress detection) from the best-fit model's parameters.
- CLI (`rheology-fit fit`, `rheology-fit cite`) built with Typer.
- PDF/PNG report generation (flow curve, model curves, residuals) and JSON parameter export.
- Literature-validated example (tomato ketchup, Koocheki et al. 2009).
- 17 passing pytest tests.
