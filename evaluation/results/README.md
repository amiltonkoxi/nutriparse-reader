# Results

| folder | data | engine |
|---|---|---|
| `synth_test/` | synthetic test split (seed 2, 120 sheets, 212 PDFs), run once after the engine was frozen | v1 and v0.3 baseline |
| `synth_test_no_vision/` | same split | v1 with `NUTRIPARSE_DISABLE_VISION=1` (ablation) |
| `real/` | 10 private food specification sheets, labels in `../real_labels.json` | v1 and v0.3 baseline |

The real-world set was used during development; its numbers are optimistic.
Regenerate the synthetic split with `make bench` (same seed, same documents).
See `docs/method.md` for definitions.
