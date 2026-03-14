#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OUROBOROS_RUNNER.py
===================
Auto-calibrador para experimentos numéricos (BSD / Ironclad).
Barre parámetros, mide error vs costo, decide PASS/WARN/FAIL y emite JSON.
"""

import time
import json
import subprocess
import sys
import re
from itertools import product

# ---- CONFIGURACIÓN DE BARRIDO ----
PARAM_GRID = {
    "dps":   [60, 80, 120],
    "terms": [2000, 5000, 12000],
}
TOL_PASS = 1e-12
TOL_WARN = 1e-9

# ---- PARSERS (ajusta regex a tu output real) ----
RE_QGEO = re.compile(r"Q_geo.*=\s*([0-9\.Ee+-]+)")
RE_LP   = re.compile(r"L'\(1\).*=\s*([0-9\.Ee+-]+)")
RE_ERR  = re.compile(r"rel_err\s*=\s*([0-9\.Ee+-]+)")

def run_case(cmd):
    t0 = time.time()
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    dt = time.time() - t0
    out = p.stdout + "\n" + p.stderr

    qgeo = float(RE_QGEO.search(out).group(1)) if RE_QGEO.search(out) else None
    lp   = float(RE_LP.search(out).group(1))   if RE_LP.search(out)   else None
    rel  = float(RE_ERR.search(out).group(1))  if RE_ERR.search(out)  else None

    status = "FAIL"
    if rel is not None:
        if rel < TOL_PASS: status = "PASS"
        elif rel < TOL_WARN: status = "WARN"

    return {
        "cmd": cmd,
        "time_s": dt,
        "Q_geo": qgeo,
        "Lprime1": lp,
        "rel_err": rel,
        "status": status,
        "stdout": out[:2000],  # truncado
    }

def main():
    results = []
    for dps, terms in product(PARAM_GRID["dps"], PARAM_GRID["terms"]):
        cmd = [
            sys.executable, "OUROBOROS_BSD_37A1_EXPERIMENT.py",
            "--dps", str(dps),
            "--terms", str(terms),
            "--tol", "1e-18"
        ]
        res = run_case(cmd)
        res.update({"dps": dps, "terms": terms})
        results.append(res)

        # Stop temprano si PASS
        if res["status"] == "PASS":
            break

    report = {
        "policy": {"PASS": TOL_PASS, "WARN": TOL_WARN},
        "grid": PARAM_GRID,
        "results": results,
        "best": next((r for r in results if r["status"]=="PASS"), None)
    }

    with open("ouroboros_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
