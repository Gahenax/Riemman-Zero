# REPRODUCIBILITY — RSH-Riemann-Latido

## Environment
- Python 3.13+
- `numpy` (only dependency)
- No GPU required
- OS: any (tested on Windows 11)

## Data Provenance
- Zeros computed via `mpmath.zetazero()` (arbitrary precision)
- Stored as JSONL with field `"T"` (imaginary part of non-trivial zero)
- Sorted ascending, contiguous, no gaps
- Source file: `data/raw/merged_results_5000plus.jsonl`

## Reproduce Micro-Probe (~2 min, local)
```bash
python src/latido_certified_plugin.py \
  --certified-config configs/latido_certified_2000.json \
  --profile micro --seed 1337
```
**Expected output:** `reports/latido_certified_2000_certified_replay_micro.json`

## Reproduce Full Audit (~2 hours, Jules)
See `JULES_DELEGATION_ORDER.md` for the 4-step sequential protocol:
1. Calibrate GUE baseline (nmat, edge_trim)
2. Certified Replay FULL (300 GUE + 800 shuffle)
3. Null Factory standalone cross-check
4. GUE³ TwoNN k=5

## Null Factory
- **Method:** GUE Dumitriu-Edelman tridiagonal, β=2
- **Shuffle:** block-shuffle (block_len=50) over observed gaps
- **Pipeline-symmetric:** YES (same observables on null and observed)
- **Calibrated:** NO — `edge_trim` pending from `calibrate_rtilde_target.py`

## Seed Reproducibility
- All stochastic components seeded via `numpy.random.default_rng(1337)`
- Deterministic for same (seed, N, profile)

## Known Limitations
- Micro-probe has low power (5 GUE sims → z-scores compressed)
- Full verdict requires Jules execution
- `edge_trim=0.0` is uncalibrated default
