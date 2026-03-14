# AMALGAMA — Gahenax Unified Research Platform

## Overview

This repository is the canonical integration of four Gahenax research lines:

| Repo | Integrated Path | Core Contribution |
|------|----------------|-------------------|
| **Riemman-Zero** (base) | `/` | Riemann zero spectral analysis, Mersenne certification, DOMINO-WAVE protocol, OUROBOROS v2.0 governance |
| **OEDA_Calculo2** | `lab/ouroboros/` | OUROBOROS limit cycle experiments, adaptive parameter tuning, prometheus metrics, falsification results |
| **Mersenne-Gahen** | `research/`, `scripts/`, `src/`, `tests/`, `tools/` | Extended Mersenne orchestrators (100B scale), forensic falsifiers, dataset generation, ouroboros src module |
| **OEDA_CalculoIA** | `riemann_ouroboros/`, `core/`, `web/`, root scripts | Riemann-GUE pipeline (ODLYZKO, Dyson, Floquet), React visualization frontend, hardened computation core |

---

## Architecture Map

```
Riemman-Zero/
├── CORE COMPUTATION
│   ├── antigravity/              # Base execution engine (contracts, roles, Lucas-Lehmer)
│   ├── core/                     # [NEW: OEDA_CalculoIA] Hardened utilities, UA engines, governance runtime
│   │   ├── GAHENAX_UA_ENGINE.py
│   │   ├── governance_runtime.py
│   │   ├── riemann_pipeline_utils.py
│   │   └── safe_math.py
│   └── src/                      # [NEW: Mersenne-Gahen] Modular src package
│       ├── config.py
│       ├── mersenne/             # domino_coordinator, ghost_hunter_lab, trampoline_coordinator
│       └── ouroboros/            # ouroboros_v2, ouroboros_prompt
│
├── RIEMANN ANALYSIS
│   ├── riemann_avalanche.py      # DOMINO-WAVE exponential protocol
│   ├── riemann_domino_wave.py    # 6 parallel probes (ALPHA-FOXTROT)
│   ├── riemann_domino_converge.py
│   ├── mine_riemann_zeros.py     # [NEW: OEDA_CalculoIA] Tri-filter zero mining (L0/L1/L2)
│   ├── riemann_auditable_wrapper.py # [NEW] SHA256-auditable wrapper
│   ├── riemann_collider.py       # [NEW] Particle collider metaphor for zero interaction
│   ├── collider_resonance_analyzer.py # [NEW] Breit-Wigner prime resonance
│   ├── RIEMANN_DYSON_FORCE_ANALYSIS.py # [NEW] Dyson force spectral analysis
│   ├── RIEMANN_GUE_STATS.py      # [NEW] GUE statistical comparison
│   ├── TIME_CRYSTAL_FLOQUET_SPECTRUM.py # [NEW] Floquet time-crystal analysis
│   ├── ZETA_ENTROPY_GENERATOR.py # [NEW] Entropy production from zeta zeros
│   ├── ANTIGRAVITY_EXPERIMENT_CRONOS_RIEMANN_GUE_V1.py # [NEW] CRONOS GUE experiment
│   ├── riemann_ouroboros/        # [NEW: OEDA_CalculoIA] Full Riemann-OUROBOROS pipeline
│   │   ├── audit.py, controls.py, embeddings.py
│   │   ├── entropy_reducer.py, farmer_adapter.py
│   │   ├── flow_on_cloud.py, io_utils.py, run_cycle.py
│   │   ├── GAP_RATIO_KS_DISCRIMINATOR.py
│   │   └── POINT_CLOUD_LAPLACIAN_FLOW_HARDENED_V2_1.py
│   └── research/riemann/
│       ├── riemann_ouroboros/    # [NEW] Local riemann_ouroboros module
│       ├── riemann_ouroboros_heavy/ # [NEW] ODLYZKO heavy pipeline
│       │   └── src/              # ODLYZKO_FULL_AUDIT, MULTI_AUDIT, PIPELINE
│       ├── DEPLOY_RIEMANN_DOMINO.py # [NEW]
│       ├── spectral_gate.py      # [NEW]
│       ├── sweep_memory.py       # [NEW]
│       ├── forensic_falsifier.py
│       ├── compare_rigidity.py
│       └── eligibility.py
│
├── MERSENNE RESEARCH
│   ├── research/mersenne/        # Extended orchestrators (100M → 100B scale)
│   │   ├── MERSENNE_100B_ORCHESTRATOR.py   # [NEW]
│   │   ├── MERSENNE_10B_ORCHESTRATOR.py    # [NEW]
│   │   ├── MERSENNE_1B_ORCHESTRATOR.py     # [NEW]
│   │   ├── MERSENNE_500M_ORCHESTRATOR.py   # [NEW]
│   │   ├── MERSENNE_200M_ORCHESTRATOR.py   # [NEW]
│   │   ├── MERSENNE_100M_FRONTIER_ORCHESTRATOR.py # [NEW]
│   │   ├── MERSENNE_MULTI_PROBE_ORCHESTRATOR_V2.py # [NEW]
│   │   ├── MERSENNE_MULTI_PROBE_ORCHESTRATOR_V3_DOMINO.py # [NEW]
│   │   ├── MERSENNE_WARP_MINER.py / V2    # [NEW]
│   │   ├── MERSENNE_TURBO_MINER.py        # [NEW]
│   │   ├── MERSENNE_SEISMOGRAPH_V2.py     # [NEW]
│   │   ├── ghost_validation_gate.py        # [NEW]
│   │   ├── campaign_dashboard.py           # [NEW]
│   │   └── search_memory.py / semantic_mapper.py # [NEW]
│   └── research/supercomputing/
│       └── mpi_mersenne_sieve.py  # [NEW] MPI Mersenne sieve
│
├── OUROBOROS GOVERNANCE
│   ├── tools/ouroboros_v2.py     # Core OUROBOROS v2.0 protocol
│   ├── lab/ouroboros/            # [NEW: OEDA_Calculo2] Governance experiments
│   │   ├── OUROBOROS_RUNNER.py           # Parameter sweep (dps=60/80/120)
│   │   ├── OUROBOROS_LAB_AUTOPILOT.py    # Adaptive tuning + stagnation detection
│   │   ├── OUROBOROS_BSD_37A1_EXPERIMENT.py # Core limit cycle validation
│   │   ├── ANTIGRAVITY_INTEGRATION_OUROBOROS_LAB.py # Framework integration
│   │   ├── find_cycle.py                 # Cycle detection utility
│   │   ├── prometheus_exporter.py        # Metrics export
│   │   ├── experiments/ouroboros_lab/    # Lab execution environment
│   │   └── results/                      # Falsification verdicts (GREEN/RED)
│   └── generate_master_dataset.py        # [NEW: Mersenne-Gahen] Master dataset aggregation
│
├── COMPUTE INFRASTRUCTURE
│   ├── scripts/supercomputing/   # SLURM/PBS/HTCondor/MPI templates
│   ├── research/supercomputing/  # [NEW] MPI Mersenne sieve
│   └── jules_orders/
│       ├── JULES_ORDER_RIEMANN_P3.json
│       └── jules_riemann_domino_adapter.py # [NEW]
│
├── WEB FRONTEND
│   └── web/src/                  # [NEW: OEDA_CalculoIA] React 19 + TypeScript
│       ├── App.tsx               # Main application
│       ├── StructureMinerUI.tsx  # Structure mining visualization
│       ├── main.tsx
│       └── core/StructureMiner.ts
│
├── TESTS
│   └── tests/
│       ├── test_ouroboros_basic.py # [NEW: OEDA_Calculo2]
│       ├── test_mersenne_v2.py     # [NEW: Mersenne-Gahen]
│       ├── test_ouroboros.py       # [NEW: Mersenne-Gahen]
│       └── test_riemann_v2.py      # [NEW: Mersenne-Gahen]
│
└── AGENT SKILLS
    └── .agent/skills/
        ├── [existing 9 skills]
        ├── adversarial-phase-transition   # [NEW: Mersenne-Gahen]
        ├── gahenax-architectural-standards # [NEW]
        ├── lovable-web-builder            # [NEW] React UI generation
        ├── oeda-marketing-funnel          # [NEW]
        ├── skill-creator                  # [NEW] Meta-skill creation
        ├── systematic-debugging           # [NEW]
        ├── yang-mills-mass-gap            # [NEW] Physics research
        ├── discord-b2b-crm               # [NEW]
        └── riemann-spectral-chaos/scripts/ # [NEW: OEDA_CalculoIA]
            ├── core_math.py
            ├── floquet_engine.py
            └── spectral_engine.py
```

---

## Complementarity Matrix

| Module | Riemman-Zero | OEDA_Calculo2 | Mersenne-Gahen | OEDA_CalculoIA |
|--------|:---:|:---:|:---:|:---:|
| Riemann zero mining | ✓ DOMINO-WAVE | — | ✓ extended | ✓ tri-filter + ODLYZKO |
| GUE spectral comparison | ✓ Phase 1-2 | — | ✓ forensic | ✓ Dyson + KS |
| Mersenne certification | ✓ Lucas-Lehmer | — | ✓ 100B scale | — |
| OUROBOROS governance | ✓ v2.0 | ✓ limit cycle | ✓ src module | ✓ pipeline |
| Distributed compute | ✓ SLURM/PBS | — | ✓ MPI sieve | ✓ Docker Jules L2 |
| Visualization | — | — | ✓ Excel dashboard | ✓ React + KaTeX |
| Falsifiability audit | ✓ OUROBOROS | ✓ GREEN/RED verdicts | ✓ forensic | ✓ pre-registered |
| Floquet / Time Crystal | — | — | — | ✓ NEW |
| LLL Warfare / SVP | — | — | — | ✓ NEW |

---

## Research Phases (Unified)

- **Phase 1 (Complete):** 332 certified zeros T∈[6340, 6640] — Riemman-Zero
- **Phase 2 (Complete):** Persistence tests, robust σ² estimator — Riemman-Zero
- **Phase 3 (Active):** ≥10,000 zeros T∈[7000, 15000] via Jules — Riemman-Zero + Mersenne-Gahen adapters
- **Phase CRONOS (New):** GUE experiment with 1,124 zeros T∈[14.13, 1896.59] — OEDA_CalculoIA
- **Phase OUROBOROS-LAB (New):** Limit cycle governance validation — OEDA_Calculo2

---

## Governance: OUROBOROS v2.0

All modules operate under the OUROBOROS v2.0 audit protocol:
1. **Ingestor** — raw data intake
2. **Compressor** — data reduction and normalization
3. **Red Team** — adversarial challenge
4. **Builder** — synthesis and construction
5. **Arbiter** — verdict (GREEN/AMBER/RED)
6. **Ledger** — append-only audit trail

Failure conditions are pre-registered and frozen. No post-hoc threshold adjustments are permitted.
