# Scientific integrity amendment

## Experimental position

The Mersenne–Riemann spectral POC is **supervised calibration**: labels and the Phase-1 result were known before the confirmatory design. It tests pipeline recovery, not a blind prediction.

## Non-negotiable invariants

1. Simulation telemetry must never be reported as arithmetic coverage.
2. A heuristic may prioritize candidates but must not discard any candidate before the deterministic route; discovery recall must remain 1.0.
3. A checkpoint must be bound to the requested exponent and contain a valid LL iteration and residue.
4. A Mersenne certification requires reproducible LL/PRP evidence and independent verification.
5. Spectral evidence cannot certify primality and must distinguish `log(2^k-1)` from the local base-2 background `k log(2) ± delta`.

## Confirmatory score

For each exponent k, use a locally corrected score

`D_k = Z(|S(log(2^k-1))|) - [Z(|S(k log 2-delta)|)+Z(|S(k log 2+delta)|)]/2`.

The primary inference must use frozen positive/control sets, exact label permutation, non-overlapping windows and both preregistered null models. Failure to distinguish the target from the local base-2 controls falsifies a Mersenne-specific interpretation.

## Claim policy

Allowed: “exploratory signal”, “simulation”, “known-prime calibration”, “candidate internal metric”.  
Forbidden without independent evidence: “verified range”, “new prime”, “confirmed anomaly”, “GUE universality confirmed”, or “predicts Mersenne primality”.
