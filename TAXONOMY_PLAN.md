# TAXONOMY PLAN — Gahenax Research Ecosystem
**Generated:** 2026-02-20 19:04 | **Curator:** Antigravity

---

## A) Global Taxonomy

### Dominios de investigación

| ID | Dominio | Repos actuales | Prefijo |
|----|---------|---------------|---------|
| D1 | Riemann Zero Spectral Analysis | Riemman-Zero | RSH- |
| D2 | Hodge Structural Rigidity | Hodge-rigidity | RSH- |
| D3 | Mersenne Prime Search | Mersenne-Gahen | RSH- |
| D4 | Governed Inference Engine | GahenaxIA | TOL- |
| D5 | IA-Assisted Calculus | CalculoIA | MTH- |
| D6 | Ouroboros / BSD experiments | Calculo2 | RSH- |
| D7 | Decision Oracle (TRIKSTER) | TRIKSTER-ORACLE | TOL- |
| D8 | Web / Legacy | GahenaxWebpage, Hotelpyct, Hotel-1.1, ChechyLegis, gahenax, Project1 | DEM- |

### Dependencia entre dominios

```
D4 (GahenaxIA) ─── governs ──→ D1, D2, D3, D5, D6
D7 (TRIKSTER)  ─── visualizes → D4
D5 (CalculoIA) ─── feeds ────→ D1 (pipeline Riemann GUE)
D1 (Riemann)   ─── shares null factory with ──→ D2 (Hodge)
```

---

## B) Per-Repo Classification

### B1. Riemman-Zero

| Campo | Valor |
|-------|-------|
| **Nombre actual** | `Riemman-Zero` |
| **Nombre recomendado** | `RSH-Riemann-Latido-VERD` |
| **Estado epistémico** | `VERDICT_PENDING` |
| **Tipo** | Null-factory / baseline audit |
| **Claims** | Σ²(10) suppressed vs GUE at z=-16.4 (micro, 5 sims) |
| **Non-claims** | NOT about RH; NOT final; NOT peer-reviewed |
| **Null/baseline** | GUE Dumitriu-Edelman β=2, pipeline-symmetric. **PENDING CALIBRATION** |
| **Dataset** | N=2054 zeros, T=[5000,6319], JSONL |
| **BLOCK_PUSH** | `true` — null not calibrated, full sims pending |

#### Estructura recomendada
```
RSH-Riemann-Latido-VERD/
├── README.md                    # Panel format
├── CONTEXT_MANIFEST.json
├── REPRODUCIBILITY.md
├── JULES_DELEGATION_ORDER.md
├── data/
│   └── raw/
│       └── merged_results_5000plus.jsonl
├── configs/
│   └── latido_certified_2000.json
├── src/
│   ├── debug_riemann_3.py       # Core miner
│   ├── latido_certified_plugin.py
│   ├── latido_null_factory.py
│   ├── latido_lens_stack_config.py
│   ├── calibrate_rtilde_target.py
│   ├── gue3_probe.py
│   ├── guepp_model.py
│   └── mine_and_analyze_latido.py
├── scripts/
│   ├── jules_delegation_prompt.py
│   └── context_inference_prompt.py
├── reports/
│   ├── lens_audit_micro.json
│   └── certified_replay_micro.json
├── docs/
│   └── EPISTEMIC_STATUS.md
└── tests/
    └── [TBD: sanity checks]
```

#### README propuesto (headings only)
```markdown
# RSH-Riemann-Latido — Spectral Rigidity of Riemann Zeros (N=2054, T∈[5000,6319])

Riemann zero number variance (Σ²) vs GUE null factory.
Status: VERDICT_PENDING | Null: PENDING_CALIBRATION | Power: 5/300 sims.
NOT a claim about RH. NOT final.

## 01 — STATUS: VERDICT_PENDING | Last: z(Σ²@10)=-16.4 (micro) | Next: Jules calibration + full replay

## 02 — CLAIMS
- Σ²(10) in gauge gap_mean1 is suppressed vs GUE (z=-16.4, N=5 sims, NON-FINAL)
- r-tilde is NOT anomalous (z=+1.27, within null)

## 03 — NON-CLAIMS
- No claim about Riemann Hypothesis
- No claim of final result (null not calibrated, power insufficient)
- No claim of peer review or publication readiness
- r-tilde "hyper-rigidity" RETRACTED (baseline error)

## 04 — DATASET: Riemann ζ zeros | T=[5000.19, 6319.32] | N=2054 | Contiguous | JSONL

## 05 — NULL/BASELINE: GUE β=2 Dumitriu-Edelman | Pipeline-symmetric=YES | Calibrated=NO (edge_trim pending)

## 06 — PIPELINE
- Input: JSONL (T values) → Certified slice (first 2000)
- Lens: T, n, τ(rvM), boost(β=0.1), boost(β=0.2)
- Gauge: raw (none), canonical unfold (gap_mean1)
- Observables: r-tilde, Σ², κ, RQA, conditional response
- Null: GUE sims + shuffle/block-shuffle
- Output: z-scores per lens×gauge

## 07 — REPRODUCE
- `python src/latido_certified_plugin.py --certified-config configs/latido_certified_2000.json --profile micro`
- Expected: `reports/latido_certified_2000_certified_replay_micro.json`

## 08 — ARTIFACTS
- `data/raw/merged_results_5000plus.jsonl`
- `reports/*.json`
- `configs/latido_certified_2000.json`

## 09 — ROADMAP (Gates)
- [ ] Gate 1: Calibrate GUE baseline (nmat, edge_trim) — Jules
- [ ] Gate 2: Certified Replay FULL (300 GUE + 800 shuffle) — Jules
- [ ] Gate 3: Null Factory standalone cross-check — Jules
- [ ] Gate 4: GUE³ TwoNN k=5 characterization — Jules
- [ ] Gate 5: If Σ² survives full → draft preprint

## 10 — CHANGELOG
- 2026-02-20: Certified plugin + calibrator created, micro-probe executed
- 2026-02-20: Mining completed N=2054, r-stat retracted
- 2026-02-20: Null factory micro-probe: z(Σ²@10)=-16.4
- 2026-02-20: Lens stack audit (5 lenses × raw): all z < 1
- 2026-02-20: Pushed to Riemman-Zero repo (separated from Hodge)
```

#### CONTEXT_MANIFEST.json
```json
{
  "project_name": "RSH-Riemann-Latido",
  "research_type": "Null-factory / baseline audit",
  "epistemic_stage": "VERDICT_PENDING",
  "claims": [
    "Sigma2(10) suppressed vs GUE at z=-16.4 (micro-probe, 5 GUE sims, NON-FINAL)"
  ],
  "non_claims": [
    "No claim about Riemann Hypothesis",
    "No final result (null not calibrated)",
    "r-tilde hyper-rigidity RETRACTED"
  ],
  "null_status": "PENDING_CALIBRATION",
  "null_pipeline_symmetric": true,
  "null_method": "GUE Dumitriu-Edelman beta=2 tridiagonal",
  "null_sims_completed": 5,
  "null_sims_required": 300,
  "dataset": {
    "source": "mpmath zeta zeros",
    "N": 2054,
    "T_range": [5000.19, 6319.32],
    "format": "JSONL",
    "field": "T"
  },
  "dependencies_pending": [
    "Jules: calibrate_rtilde_target.py (GUE baseline lock)",
    "Jules: certified replay full (300+800 sims)",
    "Jules: null factory standalone cross-check",
    "Jules: GUE3 TwoNN k=5"
  ],
  "allowed_interpretation": "Preliminary evidence of long-range super-rigidity, pending confirmation",
  "forbidden_interpretation": "Confirmed anomaly, proof, or final scientific result",
  "push_status": "BLOCK",
  "block_reason": "Null not calibrated. Full sims not executed. Results are NON-FINAL."
}
```

#### REPRODUCIBILITY.md
```markdown
# REPRODUCIBILITY — RSH-Riemann-Latido

## Environment
- Python 3.13+
- numpy (only dependency)
- No GPU required

## Reproduce micro-probe (local, ~2 min)
```bash
python src/latido_certified_plugin.py \
  --certified-config configs/latido_certified_2000.json \
  --profile micro --seed 1337
```

## Reproduce full audit (Jules, ~2 hours)
See `JULES_DELEGATION_ORDER.md` for the 4-step sequential protocol.

## Data provenance
- Zeros computed via `mpmath.zetazero()` (arbitrary precision)
- Stored as JSONL with field "T" (imaginary part of zero)
- Sorted, contiguous, no gaps

## Null factory
- GUE: Dumitriu-Edelman tridiagonal, β=2
- Shuffle: block-shuffle (block_len=50) over observed gaps
- Pipeline-symmetric: same observables computed on null and observed data
- [TBD: edge_trim calibration pending]
```

---

### B2. Hodge-rigidity

| Campo | Valor |
|-------|-------|
| **Nombre actual** | `Hodge-rigidity` |
| **Nombre recomendado** | `RSH-Hodge-Chronos-EXPL` |
| **Estado epistémico** | `EXPLORATION` |
| **Tipo** | Exploratory analysis (VHS stability detection) |
| **Claims** | Framework classifies candidates as STRUCTURAL/ISLAND/GHOST |
| **Non-claims** | NOT a proof of Hodge Conjecture |
| **Null/baseline** | [TBD: no explicit null defined in README] |
| **BLOCK_PUSH** | `true` — no null/baseline contract |

#### Estructura recomendada
```
RSH-Hodge-Chronos-EXPL/
├── README.md
├── CONTEXT_MANIFEST.json
├── REPRODUCIBILITY.md
├── CONCEPTUAL_FRAMEWORK.md
├── src/
│   └── lab/
│       ├── simulations/
│       └── hypotheses/
├── configs/
├── reports/
├── docs/
└── tests/
```

---

### B3. Mersenne-Gahen

| Campo | Valor |
|-------|-------|
| **Nombre actual** | `Mersenne-Gahen` |
| **Nombre recomendado** | `RSH-Mersenne-Governed-EXPL` |
| **Estado epistémico** | `EXPLORATION` |
| **Tipo** | Industrial pipeline (governed PRP + Lucas-Lehmer) |
| **Claims** | Known Mersenne primes re-certified under governed protocol |
| **Non-claims** | NOT a new Mersenne prime discovery |
| **Null/baseline** | Deterministic (Lucas-Lehmer is exact — no statistical null needed) |
| **BLOCK_PUSH** | `false` — deterministic verification, no statistical claims |

---

### B4. GahenaxIA

| Campo | Valor |
|-------|-------|
| **Nombre actual** | `GahenaxIA` |
| **Nombre recomendado** | `TOL-Gahenax-Core` |
| **Estado epistémico** | `TOOLING_ONLY` |
| **Tipo** | Governed inference engine / governance framework |
| **Claims** | Provides deterministic contract enforcement for LLM outputs |
| **Non-claims** | NOT a research result; NOT an AGI claim |
| **Null/baseline** | N/A (tooling) |
| **BLOCK_PUSH** | `false` |

---

### B5. CalculoIA

| Campo | Valor |
|-------|-------|
| **Nombre actual** | `CalculoIA` |
| **Nombre recomendado** | `MTH-Calculo-Avanzado` |
| **Estado epistémico** | `METHOD_ONLY` |
| **Tipo** | Methodology (symbolic calculator + GCF engine + GUE pipeline) |
| **Claims** | GUE universality CONFIRMED for Riemann zeros in range tested |
| **Non-claims** | NOT a general proof; method-specific |
| **Null/baseline** | GUE comparison (method validated in Run 7) |
| **BLOCK_PUSH** | `false` |

---

### B6. Calculo2

| Campo | Valor |
|-------|-------|
| **Nombre actual** | `Calculo2` |
| **Nombre recomendado** | `RSH-Ouroboros-BSD-EXPL` |
| **Estado epistémico** | `EXPLORATION` |
| **Tipo** | Exploratory analysis (BSD/Ouroboros experiments) |
| **Claims** | [TBD: unclear from README] |
| **Non-claims** | [TBD] |
| **Null/baseline** | [TBD: not defined] |
| **BLOCK_PUSH** | `true` — claims/null undefined |

---

### B7. TRIKSTER-ORACLE

| Campo | Valor |
|-------|-------|
| **Nombre actual** | `TRIKSTER-ORACLE` |
| **Nombre recomendado** | `TOL-Trikster-Oracle` |
| **Estado epistémico** | `TOOLING_ONLY` |
| **Tipo** | Decision support tool (web companion) |
| **Claims** | Provides execution protocol visualization |
| **Non-claims** | NOT a decision-maker; NOT an oracle in the mathematical sense |
| **Null/baseline** | N/A (tooling) |
| **BLOCK_PUSH** | `false` |

---

### B8. Legacy/Demo repos

| Repo | Recomendación |
|------|--------------|
| `GahenaxWebpage` | `DEM-GahenaxWeb` — website, no action needed |
| `Hotelpyct` | `DEM-Hotelpyct` — academic project, archive |
| `Hotel-1.1` | `DEM-Hotel-v1` — academic project, archive |
| `ChechyLegis` | `DEM-ChechyLegis` — archive |
| `gahenax` | `DEM-gahenax-profile` — GitHub profile, no action |
| `Project1` | `DEM-Project1` — archive |

---

## C) INDEX.md (Global)

| Dominio | Repo | Estado | Objetivo | Dataset | Null/Baseline | Último veredicto | Link |
|---------|------|--------|----------|---------|---------------|-----------------|------|
| Riemann | `RSH-Riemann-Latido-VERD` | VERDICT_PENDING | Σ² anomaly vs GUE | N=2054, T=[5k,6.3k] | GUE β=2 (PENDING_CALIB) | z(Σ²@10)=-16.4 (micro) | [→](https://github.com/Gahenax/Riemman-Zero) |
| Hodge | `RSH-Hodge-Chronos-EXPL` | EXPLORATION | VHS stability detection | Synthetic | [TBD] | STRUCTURAL/ISLAND/GHOST classification | [→](https://github.com/Gahenax/Hodge-rigidity) |
| Mersenne | `RSH-Mersenne-Governed-EXPL` | EXPLORATION | Governed prime certification | GIMPS range | Deterministic (LL) | Known primes re-certified | [→](https://github.com/Gahenax/Mersenne-Gahen) |
| Governance | `TOL-Gahenax-Core` | TOOLING_ONLY | Governed inference engine | N/A | N/A | Operational | [→](https://github.com/Gahenax/GahenaxIA) |
| Calculus | `MTH-Calculo-Avanzado` | METHOD_ONLY | Symbolic calc + GUE pipeline | GCF / Riemann | GUE comparison | GUE universality confirmed | [→](https://github.com/Gahenax/CalculoIA) |
| Ouroboros | `RSH-Ouroboros-BSD-EXPL` | EXPLORATION | BSD / Ouroboros experiments | [TBD] | [TBD] | [TBD] | [→](https://github.com/Gahenax/Calculo2) |
| Oracle | `TOL-Trikster-Oracle` | TOOLING_ONLY | Decision support viewer | N/A | N/A | Deployed (beta) | [→](https://github.com/Gahenax/TRIKSTER-ORACLE) |
| Legacy | `DEM-*` (6 repos) | ARCHIVE | Academic / demo projects | N/A | N/A | N/A | — |
