# Migration from OEDA_HodgeRigidity

**Date:** 2026-11-21  
**Source repository:** https://github.com/Gahenax/OEDA_HodgeRigidity  
**Source head before purge:** `45fd8bfbf542f93edaca1f928638bb40b911092d`  
**Destination baseline:** `290502a9f1a44aac05cb019a0fd4759adc0c5536`

## Audit result

- 49 dedicated Riemann files were scoped.
- 38 files were already byte-identical in this repository.
- 11 paths had divergent histories; the destination versions were retained as canonical because this repository contains the later Riemann-specific development line.
- `scripts/poc_25_mersenne.py` was replaced by the 2026-11-21 audited correction from OEDA_HodgeRigidity: portable paths, correctly ordered Benjamini–Hochberg adjustment, scale-matched controls and explicit supervised-calibration status.
- `docs/SCIENTIFIC_INTEGRITY_AMENDMENT.md` was transferred.
- The complete pre-purge source remains recoverable from the source commit above.

## Scientific position

This corpus is exploratory computational research. It contains no proof of the Riemann Hypothesis and no new Mersenne-prime certification. The Mersenne–Riemann POC is supervised calibration over known labels until an independently executed preregistered phase succeeds.
