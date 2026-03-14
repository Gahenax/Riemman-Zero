#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OUROBOROS_LAB_AUTOPILOT.py
=========================
Laboratorio Ouroboros: runner adaptativo (cola vs precisión) + reporte forense.

Qué integra (habilidades -> código):
1) Autopilot cola vs precisión:
   - corre (dps, terms=T) y (dps, terms=2T) para decidir si subir terms o dps.
2) Semáforo contextual:
   - PASS_STRICT < 1e-12
   - PASS_GUERRILLA < 1e-9
   - WARN < 1e-7
   - FAIL >= 1e-7
3) Detector de estancamiento:
   - si 3 mejoras seguidas < 10%, cambia de palanca o detiene.
4) Reporte forense JSON:
   - guarda parámetros, métricas, tiempos, entorno y salida truncada.
5) Selección “mínimo costo”:
   - elige el PASS más barato según proxy de costo.

Integración Antigravity:
- Úsalo como comando:  python3 OUROBOROS_LAB_AUTOPILOT.py --cmd "python3 OUROBOROS_BSD_37A1_EXPERIMENT.py"
- O como módulo: from OUROBOROS_LAB_AUTOPILOT import OuroborosLab; lab.run()

NOTA:
- Este runner no asume un problema particular. Sólo requiere que tu experimento imprima:
  - rel_err = <float>
  - Q_geo = <float> (opcional)
  - L'(1) = <float> (opcional)
Si tus etiquetas difieren, ajusta los regex.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from hashlib import sha256
from typing import Dict, List, Optional, Tuple

# -------------------------
# Parsing (ajusta si cambia tu output)
# -------------------------
RE_RELERR = re.compile(r"rel_err\s*=\s*([0-9\.Ee+\-]+)")
RE_ABSERR = re.compile(r"abs_err\s*=\s*([0-9\.Ee+\-]+)")
RE_QGEO   = re.compile(r"Q_geo.*=\s*([0-9\.Ee+\-]+)")
RE_LP     = re.compile(r"L'\(1\).*=\s*([0-9\.Ee+\-]+)")
RE_OMEGA  = re.compile(r"Omega_total.*=\s*([0-9\.Ee+\-]+)")
RE_REG    = re.compile(r"Regulator R.*=\s*([0-9\.Ee+\-]+)")

# -------------------------
# Semáforo
# -------------------------
PASS_STRICT = 1e-12
PASS_GUERR  = 1e-9
WARN_TOL    = 1e-7


def classify(rel_err: Optional[float]) -> Tuple[str, str]:
    """Return (status, meaning)."""
    if rel_err is None:
        return "FAIL", "No se pudo parsear rel_err: posible cambio de formato o crash."
    if rel_err < PASS_STRICT:
        return "PASS_STRICT", "Cierre de expediente: convergencia fuerte."
    if rel_err < PASS_GUERR:
        return "PASS_GUERRILLA", "Puente operativo: pipeline sano, falta francotirador."
    if rel_err < WARN_TOL:
        return "WARN", "Subcalibrado: suele requerir más dps/terms o suma más estable."
    return "FAIL", "Error alto: o falta calibración extrema o hay bug/modelo incorrecto."


def cost_proxy(time_s: float, dps: int, terms: int) -> float:
    """
    Proxy simple de costo (UA-ish):
    - sube con tiempo real
    - penaliza dps y terms suavemente
    """
    return time_s * (1.0 + dps / 80.0) * (1.0 + terms / 20000.0)


def file_sha256(path: str) -> Optional[str]:
    if not path or not os.path.exists(path):
        return None
    h = sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class RunConfig:
    dps: int
    terms: int
    extra_args: List[str]


@dataclass
class RunResult:
    config: RunConfig
    time_s: float
    rel_err: Optional[float]
    abs_err: Optional[float]
    status: str
    meaning: str
    Q_geo: Optional[float]
    Lprime1: Optional[float]
    Omega_total: Optional[float]
    Regulator_R: Optional[float]
    cost: float
    stdout_trunc: str
    returncode: int


@dataclass
class LabReport:
    policy: Dict[str, float]
    env: Dict[str, str]
    experiment_cmd: str
    experiment_script_hash: Optional[str]
    runs: List[Dict]
    best: Optional[Dict]
    best_guerrilla: Optional[Dict]


class OuroborosLab:
    def __init__(
        self,
        experiment_cmd: str,
        script_path_for_hash: Optional[str] = None,
        out_json: str = "ouroboros_report.json",
        max_stdout_chars: int = 4000,
        stagnation_window: int = 3,
        stagnation_improve_min: float = 0.10,  # 10%
        cola_ratio_threshold: float = 1.8,
        precision_bump: int = 40,
        terms_growth: int = 2,
    ):
        """
        experiment_cmd: comando base, sin dps/terms (se agregan aquí).
          Ej: "python3 OUROBOROS_BSD_37A1_EXPERIMENT.py"
        """
        self.experiment_cmd = experiment_cmd.strip()
        self.script_hash = file_sha256(script_path_for_hash) if script_path_for_hash else None
        self.out_json = out_json
        self.max_stdout_chars = max_stdout_chars
        self.stagnation_window = stagnation_window
        self.stagnation_improve_min = stagnation_improve_min
        self.cola_ratio_threshold = cola_ratio_threshold
        self.precision_bump = precision_bump
        self.terms_growth = terms_growth
        self._runs: List[RunResult] = []

    def _build_cmd(self, cfg: RunConfig) -> List[str]:
        # Split naive: allow passing as a single string; use shell=False.
        base = cfg.extra_args[:]  # not used here; we append later
        # We'll tokenize experiment_cmd by spaces; if you need complex quoting, pass --cmd as list in Antigravity wrapper.
        cmd = self.experiment_cmd.split()
        # Convention: experiment supports --dps and --terms and --tol; if not, adjust here.
        cmd += ["--dps", str(cfg.dps), "--terms", str(cfg.terms)]
        cmd += base
        return cmd

    @staticmethod
    def _parse_float(regex: re.Pattern, text: str) -> Optional[float]:
        m = regex.search(text)
        if not m:
            return None
        try:
            return float(m.group(1))
        except Exception:
            return None

    def _run_once(self, cfg: RunConfig) -> RunResult:
        cmd = self._build_cmd(cfg)
        t0 = time.time()
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        dt = time.time() - t0

        out = (p.stdout or "") + "\n" + (p.stderr or "")
        out_trunc = out[: self.max_stdout_chars]

        rel = self._parse_float(RE_RELERR, out)
        ab  = self._parse_float(RE_ABSERR, out)
        qg  = self._parse_float(RE_QGEO, out)
        lp  = self._parse_float(RE_LP, out)
        om  = self._parse_float(RE_OMEGA, out)
        rg  = self._parse_float(RE_REG, out)

        status, meaning = classify(rel)
        cost = cost_proxy(dt, cfg.dps, cfg.terms)

        rr = RunResult(
            config=cfg,
            time_s=dt,
            rel_err=rel,
            abs_err=ab,
            status=status,
            meaning=meaning,
            Q_geo=qg,
            Lprime1=lp,
            Omega_total=om,
            Regulator_R=rg,
            cost=cost,
            stdout_trunc=out_trunc,
            returncode=p.returncode,
        )
        self._runs.append(rr)
        return rr

    def _best_by(self, predicate) -> Optional[RunResult]:
        cands = [r for r in self._runs if predicate(r)]
        if not cands:
            return None
        return min(cands, key=lambda r: r.cost)

    def _improvement_ratio(self, old: Optional[float], new: Optional[float]) -> Optional[float]:
        if old is None or new is None or new <= 0:
            return None
        return old / new

    def _stagnating(self) -> bool:
        # Look at last N improvements in rel_err among successful parses.
        parsed = [r for r in self._runs if r.rel_err is not None]
        if len(parsed) < self.stagnation_window + 1:
            return False
        last = parsed[-(self.stagnation_window + 1):]
        # improvements: rel_err decreases => ratio > 1
        ratios = []
        for i in range(1, len(last)):
            prev = last[i - 1].rel_err
            curr = last[i].rel_err
            if prev is None or curr is None or curr <= 0:
                return False
            ratios.append(prev / curr)
        # If all ratios < 1 + min_improve, it's stagnation
        return all(r < (1.0 + self.stagnation_improve_min) for r in ratios)

    def run(
        self,
        start_dps: int = 80,
        start_terms: int = 5000,
        max_dps: int = 220,
        max_terms: int = 100000,
        tol_label: str = "1e-18",
        stop_on: str = "PASS_STRICT",
        max_steps: int = 30,
        extra_args: Optional[List[str]] = None,
    ) -> LabReport:
        """
        stop_on: "PASS_STRICT" or "PASS_GUERRILLA"
        extra_args: extra args forwarded to experiment (e.g. ["--tol","1e-18","--sanity"])
        """
        extra_args = extra_args or ["--tol", tol_label]

        dps = start_dps
        terms = start_terms

        # --- Main loop ---
        for step in range(max_steps):
            # Run at T and 2T to diagnose cola vs precision
            r1 = self._run_once(RunConfig(dps=dps, terms=terms, extra_args=extra_args))
            # Stop check
            if (stop_on == "PASS_STRICT" and r1.status == "PASS_STRICT") or (
                stop_on == "PASS_GUERRILLA" and (r1.status in ("PASS_STRICT", "PASS_GUERRILLA"))
            ):
                break

            # If parsing failed or crashed, don't do fancy; bump dps a bit and retry.
            if r1.rel_err is None or r1.returncode != 0:
                dps = min(max_dps, dps + self.precision_bump)
                continue

            # Second probe: 2T same dps
            t2 = min(max_terms, terms * self.terms_growth)
            if t2 == terms:
                # can't grow terms further; must grow precision
                dps = min(max_dps, dps + self.precision_bump)
                continue

            r2 = self._run_once(RunConfig(dps=dps, terms=t2, extra_args=extra_args))

            # Stop check
            if (stop_on == "PASS_STRICT" and r2.status == "PASS_STRICT") or (
                stop_on == "PASS_GUERRILLA" and (r2.status in ("PASS_STRICT", "PASS_GUERRILLA"))
            ):
                break

            # Decide next action: cola vs precision
            ratio = self._improvement_ratio(r1.rel_err, r2.rel_err)  # how much better when doubling terms
            if ratio is not None and ratio >= self.cola_ratio_threshold:
                # cola domina -> seguir subiendo terms
                terms = t2
            else:
                # precisión domina -> subir dps; y bajar terms a un nivel medio para no quemar tiempo
                if dps < max_dps:
                    dps = min(max_dps, dps + self.precision_bump)
                # Mantén terms en el mayor de los dos (porque ya pagaste el costo) pero sin exceder max_terms.
                terms = t2

            # Estancamiento: si no mejora, cambia de palanca o corta.
            if self._stagnating():
                # Si está estancado subiendo terms, sube dps; si está estancado subiendo dps, sube terms.
                if dps < max_dps:
                    dps = min(max_dps, dps + self.precision_bump)
                elif terms < max_terms:
                    terms = min(max_terms, terms * self.terms_growth)
                else:
                    break

        best_strict = self._best_by(lambda r: r.status == "PASS_STRICT")
        best_guerr  = self._best_by(lambda r: r.status in ("PASS_STRICT", "PASS_GUERRILLA"))

        report = LabReport(
            policy={
                "PASS_STRICT": PASS_STRICT,
                "PASS_GUERRILLA": PASS_GUERR,
                "WARN": WARN_TOL,
            },
            env={
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "cwd": os.getcwd(),
            },
            experiment_cmd=self.experiment_cmd,
            experiment_script_hash=self.script_hash,
            runs=[asdict(r) for r in self._runs],
            best=asdict(best_strict) if best_strict else None,
            best_guerrilla=asdict(best_guerr) if best_guerr else None,
        )

        with open(self.out_json, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)

        return report


def main():
    ap = argparse.ArgumentParser(description="Ouroboros Lab Autopilot: calibration + forensic JSON.")
    ap.add_argument("--cmd", required=True, help='Base command, e.g. "python3 OUROBOROS_BSD_37A1_EXPERIMENT.py"')
    ap.add_argument("--hash-script", default="", help="Path to experiment script to hash into report (optional)")
    ap.add_argument("--out", default="ouroboros_report.json", help="Output JSON report path")

    ap.add_argument("--start-dps", type=int, default=80)
    ap.add_argument("--start-terms", type=int, default=5000)
    ap.add_argument("--max-dps", type=int, default=220)
    ap.add_argument("--max-terms", type=int, default=100000)
    ap.add_argument("--steps", type=int, default=30)

    ap.add_argument("--stop-on", choices=["PASS_STRICT", "PASS_GUERRILLA"], default="PASS_STRICT")
    ap.add_argument("--tol", default="1e-18", help="Forwarded to experiment as --tol <tol>")

    ap.add_argument("--extra", nargs="*", default=[], help="Extra args forwarded to experiment after dps/terms/tol")
    args = ap.parse_args()

    extra_args = ["--tol", args.tol] + args.extra

    lab = OuroborosLab(
        experiment_cmd=args.cmd,
        script_path_for_hash=(args.hash_script or None),
        out_json=args.out,
    )

    report = lab.run(
        start_dps=args.start_dps,
        start_terms=args.start_terms,
        max_dps=args.max_dps,
        max_terms=args.max_terms,
        max_steps=args.steps,
        stop_on=args.stop_on,
        tol_label=args.tol,
        extra_args=extra_args,
    )

    # Print compact summary
    best = report.best_guerrilla or report.best
    print("=== OUROBOROS LAB AUTOPILOT: SUMMARY ===")
    if best:
        print(f"best_status: {best['status']}  dps={best['config']['dps']} terms={best['config']['terms']}")
        print(f"rel_err: {best['rel_err']}  time_s: {best['time_s']:.3f}  cost: {best['cost']:.3f}")
    else:
        print("No PASS found. Check report JSON for details.")
    print(f"report: {args.out}")


if __name__ == "__main__":
    main()
