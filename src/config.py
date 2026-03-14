import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Fallbacks for cross-checking if running standalone or dynamically integrated
_DEFAULT_ENGINE = BASE_DIR.parent / "calculo-avanzado-asistido"
_DEFAULT_PROJECT = BASE_DIR

PROJECT_ROOT = Path(os.getenv("MERSENNE_PROJECT_ROOT", str(_DEFAULT_PROJECT)))
ENGINE_ROOT = Path(os.getenv("MERSENNE_ENGINE_ROOT", str(_DEFAULT_ENGINE)))

def inject_paths():
    """Injects core laboratory paths into sys.path to allow legacy imports."""
    paths_to_add = [
        str(PROJECT_ROOT),
        str(ENGINE_ROOT),
        str(ENGINE_ROOT / "core")
    ]
    for p in paths_to_add:
        if p not in sys.path and os.path.exists(p):
            sys.path.append(p)

    return paths_to_add

# Trigger injection on import
INJECTED_PATHS = inject_paths()
