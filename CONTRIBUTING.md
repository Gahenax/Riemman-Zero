# CONTRIBUTING — Gahenax Unified Research Platform

## Estructura del proyecto

```
Riemman-Zero/
│
├── ENTRY POINTS (ejecutar directamente)
│   ├── riemann_avalanche.py        # Protocolo DOMINO-WAVE exponencial
│   ├── riemann_domino_wave.py      # 6 sondas paralelas (ALPHA–FOXTROT)
│   ├── riemann_domino_converge.py  # Consolidacion multi-etapa
│   ├── booster_probe.py            # Sonda auxiliar interleaved
│   └── monitor_avalanche.py        # Monitor en vivo (60s refresh)
│
├── core/                           # Infraestructura compartida (paquete)
│   ├── ledger_writer.py            # Escritura duradera: ZeroRecord, LedgerWriter
│   ├── ledger_reader.py            # Lectura streaming: LedgerReader, ShardMerger
│   ├── riemann_pipeline_utils.py   # Dedupe, Brent, von Mangoldt
│   ├── governance_runtime.py       # Runtime de gobernanza OUROBOROS
│   └── safe_math.py                # Aritmetica segura (NaN/Inf detection)
│
├── antigravity/                    # Motor de calculo base (paquete)
│   ├── core/contracts.py           # Interfaces: AntigravityModule, ExecutionResult
│   ├── core/roles.py               # Roles: Simulator, Oracle
│   └── engines/mersenne_module.py  # Lucas-Lehmer con metricas H/M/S
│
├── src/                            # Modulos de dominio (paquete)
│   ├── config.py                   # PROJECT_ROOT, paths, inject_paths()
│   ├── mersenne/                   # Coordinadores de busqueda Mersenne
│   └── ouroboros/                  # OUROBOROS v2.0: prompts y gobernanza
│
├── research/                       # Scripts de investigacion (paquete)
│   ├── mersenne/                   # Orchestrators 100M → 100B
│   ├── riemann/                    # Analisis espectral, forensic, calibracion
│   │   ├── riemann_ouroboros/      # Pipeline Riemann-OUROBOROS completo
│   │   └── riemann_ouroboros_heavy/# ODLYZKO heavy pipeline
│   └── supercomputing/             # MPI, SLURM, PBS templates
│
├── scripts/                        # Scripts de uso general (paquete)
│   ├── data_quality_monitor.py     # Monitor de calidad (--watch, --verbose)
│   ├── riemann/                    # Analisis Riemann (GUE, Dyson, Floquet, etc.)
│   ├── experimental/               # Scripts de prueba y desarrollo
│   └── supercomputing/             # Templates HPC
│
├── lab/                            # Espacio de experimentacion (paquete)
│   ├── canon/                      # Primos de Mersenne certificados (JSON)
│   ├── ouroboros/                  # Experimentos de ciclo limite OUROBOROS
│   └── simulations/                # Simulaciones de produccion
│
├── tools/                          # Herramientas de auditoria (paquete)
│   ├── ouroboros_v2.py             # Protocolo OUROBOROS v2.0
│   └── ghost_hunter_lab.py         # Auditoria de vecindades Mersenne
│
├── tests/                          # Tests (pytest)
├── web/src/                        # Frontend React 19 + TypeScript
├── results/                        # Datos de salida (NO editar manualmente)
├── ledger_riemann_phase1/          # Ledger Phase 1 (6 shards, 332 zeros)
└── artifacts/                      # Cache de computos (430+ directorios)
```

---

## Convenciones de nombres

| Tipo | Convencion | Ejemplo |
|------|-----------|---------|
| Modulo de libreria | `snake_case.py` | `ledger_writer.py` |
| Script ejecutable legacy | `UPPERCASE_SEPARATED.py` | `RIEMANN_GUE_STATS.py` |
| Entry point principal | `snake_case.py` | `riemann_avalanche.py` |
| Test | `test_*.py` | `test_mersenne_v2.py` |
| Skill de agente | `SKILL.md` | `.agent/skills/*/SKILL.md` |

---

## Como correr los componentes

```bash
# Mineria de zeros de Riemann (DOMINO-WAVE)
python riemann_avalanche.py

# Monitor en vivo
python monitor_avalanche.py

# Monitor de calidad de datos
python scripts/data_quality_monitor.py --verbose
python scripts/data_quality_monitor.py --watch --interval 60

# Analisis GUE
python scripts/riemann/RIEMANN_GUE_STATS.py

# Tests
python -m pytest tests/ -v

# Linter
ruff check .
```

---

## Como agregar un nuevo modulo

1. **Si es infraestructura compartida** → agregar en `core/`
2. **Si es script de analisis Riemann** → agregar en `scripts/riemann/`
3. **Si es orchestrator Mersenne** → agregar en `research/mersenne/`
4. **Si es experimental** → agregar en `scripts/experimental/`
5. **Siempre** agregar un test en `tests/test_<modulo>.py`

---

## Importar modulos del proyecto

```python
# Forma correcta (desde PROJECT_ROOT)
from core import LedgerWriter, ZeroRecord
from core.ledger_reader import ShardMerger, read_phase1_shards
from antigravity.engines.mersenne_module import MersenneMinerModule

# Si necesitas ajustar el path (scripts standalone)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

---

## Gobernanza: OUROBOROS v2.0

Todos los experimentos siguen el protocolo de 6 fases:
1. **Ingestor** — normalizar datos de entrada
2. **Compresor** — reducir a variables esenciales
3. **Red Team** — atacar la hipotesis
4. **Builder** — endurecer el metodo
5. **Arbiter** — veredicto GREEN/AMBER/RED
6. **Ledger** — registro append-only con SHA256

**Regla de oro:** Las hipotesis se pre-registran antes de correr el experimento.
No se ajustan umbrales post-hoc.
