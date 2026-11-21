# RIEMMAN-ZERO — GAHENAX

Repositorio dedicado al análisis computacional de los ceros no triviales de la función zeta de Riemann, sus estadísticas espectrales y la prueba de concepto Mersenne–Riemann.

> El nombre histórico del repositorio conserva la grafía `Riemman-Zero`; en documentación científica se usa **Riemann**.

## Alcance

- Datasets y ledgers de ceros de zeta.
- Estadísticas GUE, espaciamientos, rigidez y pruebas de persistencia.
- Pipelines Phase 1–3, controles nulos y auditorías adversariales.
- POC espectral Mersenne–Riemann como **calibración supervisada**, no como certificado de primalidad.

## Límites científicos

La compatibilidad estadística con GUE no prueba la Hipótesis de Riemann. Una señal espectral no sustituye PRP, Lucas–Lehmer ni la verificación de GIMPS. Las anomalías locales permanecen exploratorias hasta reproducirse en datos nuevos, ventanas no solapadas y una implementación independiente.

## Migración

El corpus Riemann que permanecía en `Gahenax/OEDA_HodgeRigidity` fue consolidado aquí el 21 de noviembre de 2026. La procedencia exacta se registra en `MIGRATION_FROM_OEDA_HODGE.md`.

## Entradas principales

- `research/riemann/`
- `results/riemann/`
- `ledger_riemann_phase1/`
- `scripts/phase3_prereg.py`
- `scripts/poc_25_mersenne.py`
- `reports/riemann_phase1_spectral_report*.tex`
- `docs/SCIENTIFIC_INTEGRITY_AMENDMENT.md`

---
*GAHENAX — investigación falsable y reproducible.*
