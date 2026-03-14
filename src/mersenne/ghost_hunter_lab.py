#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GHOST-HUNTER LAB PLUG v1
========================
Objetivo: Blindaje de falsabilidad para el sondeo "Ghost Loci" alrededor de anclajes (p) de Mersenne.

Este script NO asume tu implementación interna.
Define un contrato (interfaces) para enchufar tu laboratorio:
- compute_ll_residue(p) -> bytes/int/str (residuo LL)
- compute_rigidity_H(residue, meta) -> float (tu Hodge Rigidity)
- optional: compute_wall_time(p) si tu pipeline lo expone

Qué produce:
- preregistro (JSON) con hipótesis mínima y criterios PASS/FAIL
- ejecución por capas: anclajes, controles, radios, permutaciones, kernel-swap (si lo tienes)
- outputs JSONL (append-only) + summary.json

Uso típico:
  python ghost_hunter_lab.py prereg --out run_001
  python ghost_hunter_lab.py run --out run_001 --anchors 1279,2203,2281,3217,4253 --radius 20 --radii 5,10,20,50
  python ghost_hunter_lab.py summarize --out run_001

Enchufe rápido:
  Edita las funciones dentro de "LAB ADAPTER" o pásalas como módulo con --adapter path/to/adapter.py
"""

from __future__ import annotations

import argparse
import dataclasses as dc
import hashlib
import importlib.util
import json
import math
import os
import random
import statistics as stats
import sys
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

# ----------------------------
# Utilities
# ----------------------------

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def write_json(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)

def append_jsonl(path: str, obj: Any) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def to_bytes(residue: Union[int, bytes, str]) -> bytes:
    if isinstance(residue, bytes):
        return residue
    if isinstance(residue, int):
        # big-endian, minimal length
        if residue == 0:
            return b"\x00"
        length = (residue.bit_length() + 7) // 8
        return residue.to_bytes(length, "big", signed=False)
    if isinstance(residue, str):
        # Accept hex string or decimal-ish; store as utf-8 for stability
        s = residue.strip()
        # If looks like hex, normalize:
        if all(c in "0123456789abcdefABCDEF" for c in s) and len(s) >= 2:
            try:
                return bytes.fromhex(s)
            except Exception:
                pass
        return s.encode("utf-8", errors="strict")
    raise TypeError(f"Unsupported residue type: {type(residue)}")

def rotate_bits(data: bytes, k: int) -> bytes:
    """Rotate the full bitstring left by k bits (k can be any int)."""
    if not data:
        return data
    nbits = len(data) * 8
    k = k % nbits
    if k == 0:
        return data
    x = int.from_bytes(data, "big")
    y = ((x << k) & ((1 << nbits) - 1)) | (x >> (nbits - k))
    return y.to_bytes(len(data), "big")

def swap_lsb_msb(data: bytes) -> bytes:
    """Reverse bit order within the whole blob (LSB<->MSB)."""
    if not data:
        return data
    x = int.from_bytes(data, "big")
    nbits = len(data) * 8
    y = 0
    for i in range(nbits):
        y = (y << 1) | ((x >> i) & 1)
    return y.to_bytes(len(data), "big")

def permute_blocks(data: bytes, block_size: int, seed: int) -> bytes:
    """Permute byte blocks of fixed size."""
    if block_size <= 0:
        raise ValueError("block_size must be > 0")
    if len(data) <= block_size:
        return data
    blocks = [data[i:i+block_size] for i in range(0, len(data), block_size)]
    rng = random.Random(seed)
    rng.shuffle(blocks)
    return b"".join(blocks)

def lsb_corr(a: bytes, b: bytes, nbits: int = 256) -> float:
    """
    Correlación simple de los nbits menos significativos entre dos blobs:
    corr = (#bits_iguales / nbits).
    Retorna en [0,1], donde 0.5 ~ aleatorio.
    """
    if not a or not b:
        return float("nan")
    xa = int.from_bytes(a, "big")
    xb = int.from_bytes(b, "big")
    mask = (1 << nbits) - 1
    aa = xa & mask
    bb = xb & mask
    eq = 0
    for i in range(nbits):
        eq += 1 if ((aa >> i) & 1) == ((bb >> i) & 1) else 0
    return eq / float(nbits)

# ----------------------------
# Spec (Preregistro)
# ----------------------------

@dc.dataclass
class PreregSpec:
    spec_id: str
    created_at: str
    hypothesis_minimal: str
    metrics: Dict[str, Any]
    pass_fail: Dict[str, Any]
    controls: Dict[str, Any]
    invariances: Dict[str, Any]
    abort_conditions: Dict[str, Any]
    notes: str

def default_prereg(spec_id: str) -> PreregSpec:
    return PreregSpec(
        spec_id=spec_id,
        created_at=now_iso(),
        hypothesis_minimal=(
            "H₀′ (hipótesis mínima defendible): "
            "El observable de Rigidez de Hodge (H) no discrimina localmente entre un anclaje "
            "Mersenne certificado y sus vecinos inmediatos dentro de un radio finito; "
            "mientras que controles negativos (vecindad de compuestos no-Mersenne / aleatorios) "
            "no exhiben la misma tasa de H≈0."
        ),
        metrics={
            "H": {
                "description": "Rigidez de Hodge reportada por tu kernel",
                "target_value": 0.0,
                "tolerance": 1e-12,
                "decision": "H_is_zero = |H - 0| <= tolerance",
            },
            "lsb_corr": {
                "description": "Proporción de bits iguales en LSB (nbits)",
                "nbits": 256,
                "decision": "flag if corr >= 0.60 (tunable)",
            },
            "wall_time": {
                "description": "Tiempo de cómputo del residuo (si disponible)",
                "decision": "analyze variance vs controls",
            },
        },
        pass_fail={
            "primary": {
                "name": "Diferencial de tasa H_zero (anclaje vs control)",
                "anchor_H_zero_rate_min": 0.80,
                "control_H_zero_rate_max": 0.30,
                "min_total_samples_per_group": 50,
                "verdict": "PASS if anchor_rate>=min and control_rate<=max else FAIL",
            },
            "secondary": {
                "name": "Invarianza bajo permutaciones",
                "require_drop_under_permutation": True,
                "meaning": (
                    "Si H permanece ~0 incluso tras permutar/rotar bits, "
                    "podría indicar que tu métrica H es insensible a representación, "
                    "o que se está midiendo otra cosa. Esto NO invalida, pero fuerza re-interpretación."
                ),
            },
        },
        controls={
            "negative_controls": [
                "Vecindad alrededor de un primo grande NO-Mersenne (misma escala)",
                "Vecindad alrededor de un compuesto grande NO-Mersenne (misma escala)",
                "Compuestos aleatorios de longitud comparable (muestreo)",
            ],
            "radius_sweep": [5, 10, 20, 50],
            "kernel_swap": "Opcional: correr con implementación LL alternativa si disponible",
        },
        invariances={
            "representation_tests": [
                "rotate_bits",
                "swap_lsb_msb",
                "permute_blocks",
            ],
            "hardware": "Registrar CPU/GPU/OS/flags; repetir en hardware distinto si posible",
        },
        abort_conditions={
            "stop_if": [
                "control_H_zero_rate >= 0.80 (efecto no específico, probable artefacto)",
                "H siempre 0.0 para todo (métrica degenerada)",
            ]
        },
        notes=(
            "Prohibido lenguaje ontológico (zona/herencia/fantasma) en reportes externos. "
            "Hablar solo de insensibilidad local / continuidad estructural."
        ),
    )

# ----------------------------
# LAB ADAPTER (Enchufe)
# ----------------------------

class LabAdapter:
    """
    Reemplaza estas funciones por tu implementación real.
    Puedes cargar un adapter externo con --adapter path/to/adapter.py
    que defina:
      - compute_ll_residue(p:int) -> (int|bytes|str)
      - compute_rigidity_H(residue:(int|bytes|str), meta:dict) -> float
      - optional compute_wall_time(p:int) -> float
      - optional label_of(p:int) -> str
    """

    def compute_ll_residue(self, p: int) -> Union[int, bytes, str]:
        raise NotImplementedError("Implementa compute_ll_residue(p)")

    def compute_rigidity_H(self, residue: Union[int, bytes, str], meta: Dict[str, Any]) -> float:
        raise NotImplementedError("Implementa compute_rigidity_H(residue, meta)")

    def compute_wall_time(self, p: int) -> Optional[float]:
        return None

    def label_of(self, p: int) -> str:
        return f"p={p}"

def load_adapter(path: Optional[str]) -> LabAdapter:
    if not path:
        return LabAdapter()
    spec = importlib.util.spec_from_file_location("ghost_adapter", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No pude cargar adapter: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    adapter = LabAdapter()

    # Attach provided functions if present
    for fn_name in ("compute_ll_residue", "compute_rigidity_H", "compute_wall_time", "label_of"):
        if hasattr(mod, fn_name):
            setattr(adapter, fn_name, getattr(mod, fn_name))
    # sanity checks
    if getattr(adapter.compute_ll_residue, "__code__", None) == getattr(LabAdapter.compute_ll_residue, "__code__", None):
        raise RuntimeError("Adapter externo debe definir compute_ll_residue(p)")
    if getattr(adapter.compute_rigidity_H, "__code__", None) == getattr(LabAdapter.compute_rigidity_H, "__code__", None):
        raise RuntimeError("Adapter externo debe definir compute_rigidity_H(residue, meta)")
    return adapter

# ----------------------------
# Experiment Core
# ----------------------------

@dc.dataclass
class RunConfig:
    out_dir: str
    spec_id: str
    anchors: List[int]
    radius: int
    radii_sweep: List[int]
    seed: int
    tolerance_H: float
    lsb_nbits: int
    lsb_flag: float
    perm_block_size: int
    perm_reps: int
    include_controls: bool
    controls_n: int

def parse_int_list(s: str) -> List[int]:
    if not s:
        return []
    return [int(x.strip()) for x in s.split(",") if x.strip()]

def neighbors(p: int, r: int) -> List[int]:
    """Return exponents in [p-r, p+r] excluding p itself, sorted."""
    lo, hi = p - r, p + r
    xs = [x for x in range(lo, hi + 1) if x != p and x > 0]
    return xs

def run_one_point(adapter: LabAdapter, p: int, tag: str, cfg: RunConfig) -> Dict[str, Any]:
    meta = {
        "p": p,
        "tag": tag,
        "ts": now_iso(),
    }
    t0 = time.time()
    residue = adapter.compute_ll_residue(p)
    t1 = time.time()
    wt = adapter.compute_wall_time(p)
    if wt is None:
        wt = (t1 - t0)

    rb = to_bytes(residue)
    H = adapter.compute_rigidity_H(residue, meta)
    H_is_zero = abs(H - 0.0) <= cfg.tolerance_H

    row = {
        "ts": meta["ts"],
        "p": p,
        "tag": tag,
        "residue_sha256": sha256_bytes(rb),
        "residue_len_bytes": len(rb),
        "H": H,
        "H_is_zero": H_is_zero,
        "wall_time_s": float(wt),
    }
    return row, rb

def representation_suite(adapter: LabAdapter, p: int, tag: str, cfg: RunConfig, rb: bytes) -> List[Dict[str, Any]]:
    """
    Aplica transformaciones al residuo y re-mide H.
    Nota: compute_rigidity_H recibe el residuo transformado como bytes.
    Si tu H espera int/str, ajusta adapter o transforma de vuelta.
    """
    out = []
    base_meta = {"p": p, "tag": tag, "ts": now_iso(), "repr_test": True}
    base_H = adapter.compute_rigidity_H(rb, base_meta)
    out.append({
        "ts": base_meta["ts"],
        "p": p,
        "tag": tag,
        "repr": "raw_bytes",
        "H": base_H,
        "H_is_zero": abs(base_H) <= cfg.tolerance_H,
        "residue_sha256": sha256_bytes(rb),
    })

    # rotate_bits
    for k in (1, 13, 101):
        b2 = rotate_bits(rb, k)
        H2 = adapter.compute_rigidity_H(b2, {**base_meta, "repr": f"rotate_bits_{k}"})
        out.append({
            "ts": now_iso(),
            "p": p,
            "tag": tag,
            "repr": f"rotate_bits_{k}",
            "H": H2,
            "H_is_zero": abs(H2) <= cfg.tolerance_H,
            "residue_sha256": sha256_bytes(b2),
        })

    # swap lsb<->msb
    b3 = swap_lsb_msb(rb)
    H3 = adapter.compute_rigidity_H(b3, {**base_meta, "repr": "swap_lsb_msb"})
    out.append({
        "ts": now_iso(),
        "p": p,
        "tag": tag,
        "repr": "swap_lsb_msb",
        "H": H3,
        "H_is_zero": abs(H3) <= cfg.tolerance_H,
        "residue_sha256": sha256_bytes(b3),
    })

    # permute blocks
    for i in range(cfg.perm_reps):
        seed_i = cfg.seed + 1000 + i
        b4 = permute_blocks(rb, cfg.perm_block_size, seed_i)
        H4 = adapter.compute_rigidity_H(b4, {**base_meta, "repr": f"permute_blocks_{cfg.perm_block_size}_seed{seed_i}"})
        out.append({
            "ts": now_iso(),
            "p": p,
            "tag": tag,
            "repr": f"permute_blocks_{cfg.perm_block_size}_seed{seed_i}",
            "H": H4,
            "H_is_zero": abs(H4) <= cfg.tolerance_H,
            "residue_sha256": sha256_bytes(b4),
        })

    return out

def sample_control_exponents(rng: random.Random, n: int, around: Optional[int] = None, span: int = 100000) -> List[int]:
    """
    Control de exponentes (sin garantía de primalidad).
    - around=None: muestreo global [2, span]
    - around=k: muestreo local [k-span, k+span]
    """
    xs = []
    for _ in range(n):
        if around is None:
            x = rng.randint(2, span)
        else:
            lo = max(2, around - span)
            hi = around + span
            x = rng.randint(lo, hi)
        xs.append(x)
    return xs

def hardware_fingerprint() -> Dict[str, Any]:
    return {
        "python": sys.version,
        "platform": sys.platform,
        "executable": sys.executable,
        "argv": sys.argv,
    }

def run_experiment(adapter: LabAdapter, cfg: RunConfig) -> None:
    ensure_dir(cfg.out_dir)
    jsonl_main = os.path.join(cfg.out_dir, "results.jsonl")
    jsonl_repr = os.path.join(cfg.out_dir, "repr_tests.jsonl")

    run_meta = {
        "run_id": os.path.basename(os.path.abspath(cfg.out_dir)),
        "started_at": now_iso(),
        "spec_id": cfg.spec_id,
        "config": dc.asdict(cfg),
        "hardware": hardware_fingerprint(),
    }
    write_json(os.path.join(cfg.out_dir, "run_meta.json"), run_meta)

    rng = random.Random(cfg.seed)

    # Groups:
    # - anchors: anchor neighborhoods per radius in radii_sweep
    # - controls: random exponent neighborhoods / global random exponents
    for r in cfg.radii_sweep:
        for a in cfg.anchors:
            ps = neighbors(a, r)
            for p in ps:
                row, rb = run_one_point(adapter, p, tag=f"anchor:{a}:r{r}", cfg=cfg)
                append_jsonl(jsonl_main, row)

                # Representation tests (falsabilidad algorítmica)
                repr_rows = representation_suite(adapter, p, tag=f"anchor:{a}:r{r}", cfg=cfg, rb=rb)
                for rr in repr_rows:
                    append_jsonl(jsonl_repr, rr)

        if cfg.include_controls:
            # Control 1: random exponents globally (size-matched-ish)
            control_ps = sample_control_exponents(rng, cfg.controls_n, around=None, span=max(cfg.anchors) + 5000)
            for p in control_ps:
                row, rb = run_one_point(adapter, p, tag=f"control:global:r{r}", cfg=cfg)
                append_jsonl(jsonl_main, row)
                for rr in representation_suite(adapter, p, tag=f"control:global:r{r}", cfg=cfg, rb=rb):
                    append_jsonl(jsonl_repr, rr)

            # Control 2: local around each anchor but NOT the neighborhood window (wider span)
            for a in cfg.anchors:
                local_ps = sample_control_exponents(rng, cfg.controls_n // max(1, len(cfg.anchors)), around=a, span=2000)
                for p in local_ps:
                    if abs(p - a) <= r:
                        continue
                    row, rb = run_one_point(adapter, p, tag=f"control:around:{a}:r{r}", cfg=cfg)
                    append_jsonl(jsonl_main, row)
                    for rr in representation_suite(adapter, p, tag=f"control:around:{a}:r{r}", cfg=cfg, rb=rb):
                        append_jsonl(jsonl_repr, rr)

    write_json(os.path.join(cfg.out_dir, "completed.json"), {"completed_at": now_iso(), "ok": True})

# ----------------------------
# Summarizer (quick-and-dirty, but useful)
# ----------------------------

def read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out

def rate_H_zero(rows: List[Dict[str, Any]]) -> float:
    if not rows:
        return float("nan")
    return sum(1 for r in rows if r.get("H_is_zero")) / len(rows)

def summarize(out_dir: str, tolerance_H: float) -> None:
    results_path = os.path.join(out_dir, "results.jsonl")
    rows = read_jsonl(results_path)
    if not rows:
        print("No hay resultados para resumir.")
        return

    # group by tag
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        groups.setdefault(r["tag"], []).append(r)

    summary = {
        "generated_at": now_iso(),
        "tolerance_H": tolerance_H,
        "n_rows": len(rows),
        "groups": {},
        "flags": [],
    }

    for tag, rs in sorted(groups.items(), key=lambda kv: kv[0]):
        Hs = [float(x["H"]) for x in rs if "H" in x]
        wts = [float(x["wall_time_s"]) for x in rs if "wall_time_s" in x]
        entry = {
            "n": len(rs),
            "H_zero_rate": rate_H_zero(rs),
            "H_mean": stats.fmean(Hs) if Hs else float("nan"),
            "H_stdev": stats.pstdev(Hs) if len(Hs) > 1 else 0.0,
            "wall_time_mean_s": stats.fmean(wts) if wts else float("nan"),
            "wall_time_stdev_s": stats.pstdev(wts) if len(wts) > 1 else 0.0,
        }
        summary["groups"][tag] = entry

        # Degeneracy flags
        if entry["H_zero_rate"] >= 0.98:
            summary["flags"].append({"tag": tag, "issue": "H_zero_rate≈1.0 (posible métrica degenerada o efecto muy fuerte)"})


    write_json(os.path.join(out_dir, "summary.json"), summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

# ----------------------------
# CLI
# ----------------------------

def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="GHOST-HUNTER LAB PLUG v1")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp0 = sub.add_parser("prereg", help="Genera preregistro JSON (congelar hipótesis y criterios)")
    sp0.add_argument("--out", required=True, help="Directorio de salida (run_xxx)")

    sp1 = sub.add_parser("run", help="Ejecuta experimento con controles y falsabilidad algorítmica")
    sp1.add_argument("--out", required=True, help="Directorio de salida (debe existir o se crea)")
    sp1.add_argument("--adapter", default=None, help="Ruta a adapter.py con compute_ll_residue/compute_rigidity_H")
    sp1.add_argument("--spec-id", default="GHOST_HUNTER_PREREG_0001", help="ID del preregistro")
    sp1.add_argument("--anchors", default="1279,2203,2281,3217,4253", help="Lista CSV de anclajes p")
    sp1.add_argument("--radius", type=int, default=20, help="Radio por defecto (si no se da radii)")
    sp1.add_argument("--radii", default="5,10,20,50", help="Sweep de radios CSV")
    sp1.add_argument("--seed", type=int, default=1337, help="Semilla RNG (reproducible)")
    sp1.add_argument("--tolH", type=float, default=1e-12, help="Tolerancia para H≈0")
    sp1.add_argument("--lsb-nbits", type=int, default=256, help="nbits para análisis LSB (si lo usas luego)")
    sp1.add_argument("--lsb-flag", type=float, default=0.60, help="Umbral para flag de corr LSB (si lo usas luego)")
    sp1.add_argument("--perm-block", type=int, default=32, help="Tamaño de bloque (bytes) para permutación")
    sp1.add_argument("--perm-reps", type=int, default=3, help="# repeticiones de permutación")
    sp1.add_argument("--no-controls", action="store_true", help="Desactiva controles negativos")
    sp1.add_argument("--controls-n", type=int, default=50, help="Muestras por control global (aprox)")

    sp2 = sub.add_parser("summarize", help="Resume resultados por grupo/tag")
    sp2.add_argument("--out", required=True, help="Directorio de salida (run_xxx)")
    sp2.add_argument("--tolH", type=float, default=1e-12, help="Tolerancia para H≈0 (solo reporte)")

    return p

def agent_run(args: argparse.Namespace) -> None:
    """Ejecución atómica para pipelines de orquestación con contrato estricto de salida."""
    ensure_dir(args.out_dir)
    
    # 1. Setup Watchdog
    def timeout_handler(signum, frame):
        print(json.dumps({"error_type": "timeout", "details": f"Watchdog killed after {args.timeout}s"}), file=sys.stdout)
        sys.exit(3)

    if sys.platform != "win32":
        import signal
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(max(1, args.timeout - 5))

    try:
        # 2. Preregistration
        prereg_path = os.path.join(args.out_dir, "prereg.json")
        if not os.path.exists(prereg_path):
            print(f"[DEBUG] Generando prereg default en {prereg_path}", file=sys.stderr)
            spec = default_prereg("GHOST_HUNTER_AGENT_001")
            write_json(prereg_path, dc.asdict(spec))
        
        # 3. Hash del prereg
        with open(prereg_path, 'r', encoding='utf-8') as f:
            prereg_content = json.load(f)
        canonical = json.dumps(prereg_content, sort_keys=True)
        prereg_hash = hashlib.sha256(canonical.encode()).hexdigest()[:16]

        # 4. Cargar Adapter
        try:
            adapter = load_adapter(args.adapter)
        except Exception as e:
            print(json.dumps({"error_type": "infra", "details": f"Adapter error: {str(e)}"}), file=sys.stdout)
            sys.exit(1)

        # 5. Ejecutar Candidato
        p = args.candidate
        cfg = RunConfig(
            out_dir=args.out_dir,
            spec_id="AGENT_RUN",
            anchors=[p],
            radius=0,
            radii_sweep=[],
            seed=1337,
            tolerance_H=1e-12,
            lsb_nbits=256,
            lsb_flag=0.60,
            perm_block_size=32,
            perm_reps=3,
            include_controls=False,
            controls_n=0,
        )

        print(f"[DEBUG] Corriendo candidato p={p}", file=sys.stderr)
        try:
            row, rb = run_one_point(adapter, p, tag="agent_anchor", cfg=cfg)
            repr_rows = representation_suite(adapter, p, tag="agent_anchor", cfg=cfg, rb=rb)
        except Exception as e:
            print(json.dumps({"error_type": "math", "details": f"Execution error: {str(e)}"}), file=sys.stdout)
            sys.exit(2)

        # 6. Parseo a Schema Estricto (MersenneAuditOutput)
        def eval_status(r_rows, marker: str) -> str:
            matches = [r for r in r_rows if marker in r["repr"]]
            if not matches:
                return "Fail"
            return "Pass" if all(r["H_is_zero"] for r in matches) else "Collapse"

        output = {
            "hypothesis_id": f"M_{p}",
            "rotation_status": eval_status(repr_rows, "rotate_bits"),
            "swap_status": eval_status(repr_rows, "swap_lsb_msb"),
            "permutation_status": eval_status(repr_rows, "permute_blocks"),
            "delegation_stdout": json.dumps({"anchor_H": row["H"]}),
            "timestamp": now_iso(),
            "prereg_hash": prereg_hash
        }

        # 7. Payload Único en STDOUT
        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        # Fallback de seguridad no capturado
        print(json.dumps({"error_type": "infra", "details": f"Unhandled error: {str(e)}"}), file=sys.stdout)
        sys.exit(1)
    finally:
        if sys.platform != "win32":
            signal.alarm(0)

def main() -> None:
    ap = build_argparser()
    
    # Inyectar CLI explícito del Agent_run al Parser (esto es post-build)
    sp_agent = ap._subparsers._group_actions[0].add_parser("agent_run", help="Ejecución atómica con contrato estricto de salida JSON.")
    sp_agent.add_argument("--candidate", type=int, required=True, help="El exponente p a probar")
    sp_agent.add_argument("--adapter", required=True, help="Ruta a adapter.py")
    sp_agent.add_argument("--out-dir", required=True, help="Directorio de salida temporal")
    sp_agent.add_argument("--timeout", type=int, default=300, help="Watchdog timeout en segundos para forzar exit code 3")

    args = ap.parse_args()

    if args.cmd == "agent_run":
        agent_run(args)
        return

    if args.cmd == "prereg":
        ensure_dir(args.out)
        spec = default_prereg("GHOST_HUNTER_PREREG_0001")
        write_json(os.path.join(args.out, "prereg.json"), dc.asdict(spec))
        print(f"[OK] prereg.json escrito en: {args.out}")
        return

    if args.cmd == "run":
        ensure_dir(args.out)
        # Load prereg if exists, else create default
        prereg_path = os.path.join(args.out, "prereg.json")
        if not os.path.exists(prereg_path):
            spec = default_prereg(args.spec_id)
            write_json(prereg_path, dc.asdict(spec))

        adapter = load_adapter(args.adapter)

        anchors = parse_int_list(args.anchors)
        radii = parse_int_list(args.radii) if args.radii else [args.radius]
        if not radii:
            radii = [args.radius]

        cfg = RunConfig(
            out_dir=args.out,
            spec_id=args.spec_id,
            anchors=anchors,
            radius=args.radius,
            radii_sweep=radii,
            seed=args.seed,
            tolerance_H=args.tolH,
            lsb_nbits=args.lsb_nbits,
            lsb_flag=args.lsb_flag,
            perm_block_size=args.perm_block,
            perm_reps=args.perm_reps,
            include_controls=(not args.no_controls),
            controls_n=args.controls_n,
        )
        run_experiment(adapter, cfg)
        print(f"[OK] Run completado. Outputs en: {args.out}")
        return

    if args.cmd == "summarize":
        summarize(args.out, tolerance_H=args.tolH)
        return

if __name__ == "__main__":
    main()
