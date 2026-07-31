# Examples

## `ketchup_koocheki2009_25C.csv` — literature-referenced validation case

Shear stress (Pa) at a range of shear rates (1-100 s⁻¹) for tomato ketchup (control formulation, no added hydrocolloids) at 25 °C.

**Provenance:** the original raw rheometer data was not accessible to us. The values in this CSV were instead computed from the Herschel-Bulkley equation using the parameters reported for the control ketchup sample in the source publication (τ₀ = 4.41 Pa, K = 16.18 Pa·s^n, n = 0.250, R² = 0.991), evaluated at the shear rates listed above. They are therefore **literature-parameter-derived reference points, not digitized raw experimental data**.

Source: Koocheki, A., Ghandi, A., Razavi, S.M.A., Mortazavi, S.A., & Vasiljevic, T. (2009). The rheological properties of ketchup as a function of different hydrocolloids and temperature. *International Journal of Food Science and Technology*, 44(3), 596–602. https://doi.org/10.1111/j.1365-2621.2008.01868.x

**Expected validation outcome:** fitting `rheology-fit` to this CSV with the Herschel-Bulkley model should recover parameters close to the published values (τ₀ ≈ 4.41 Pa, K ≈ 16.18 Pa·s^n, n ≈ 0.250), since the points were generated from that exact model. This is a smoke test that the Herschel-Bulkley implementation is numerically correct and reproduces a well-known literature flow curve — it is *not* a test of fit quality against experimental noise (see `synthetic_noisy_flow_curve.csv` for that).

```bash
rheology-fit fit examples/ketchup_koocheki2009_25C.csv --output examples/ketchup_report
```

## `synthetic_noisy_flow_curve.csv` — illustrative noisy dataset

Synthetic (shear_rate, shear_stress) data generated from a Herschel-Bulkley curve (tau0=15, K=8, n=0.45) with added Gaussian noise, to illustrate a typical noisy experimental dataset where Power-law, Herschel-Bulkley, and Casson give visibly different fits and AIC-based model selection matters. Not tied to any real material.
