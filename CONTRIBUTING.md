# Contributing to rheology-fit

Thanks for your interest in improving `rheology-fit`.

## Reporting bugs or requesting features

Please open an issue at [github.com/karenkhachatryan-lab/rheology-fit/issues](https://github.com/karenkhachatryan-lab/rheology-fit/issues). For bug reports, include:

- Your OS and Python version (`python --version`)
- The `rheology-fit` version (`rheology-fit cite` prints it)
- A minimal example CSV (or the one you used) and the exact command that failed
- The full error output

## Getting help

For usage questions, open a [GitHub issue](https://github.com/karenkhachatryan-lab/rheology-fit/issues) — there is no separate mailing list or chat.

## Contributing code

1. Fork the repository and create a branch from `main`.
2. Install the development environment:
   ```bash
   python -m venv .venv
   .venv/Scripts/python.exe -m pip install -e ".[dev]"
   ```
3. Make your change. Add or update tests in `tests/` for any behavior change.
4. Run the test suite:
   ```bash
   .venv/Scripts/python.exe -m pytest
   ```
5. Open a pull request describing the change and why it's needed.

## Adding a new rheology model

New models belong in `src/rheology_fit/models.py`, following the existing `ModelSpec` pattern (function, parameter names, initial guess, bounds). Add a corresponding entry to `MODEL_REGISTRY`, a unit test with synthetic data of known ground-truth parameters (see `tests/test_models.py`), and update `classify_flow_behavior` if the model needs its own interpretation logic.
