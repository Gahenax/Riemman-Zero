#!/usr/bin/env python3
"""
scripts/data_quality_monitor.py
================================
Monitor de calidad de datos en tiempo real para datasets de Riemann y Mersenne.

Funciones:
1. Densidad observada vs teorica von Mangoldt (detecta gaps o exceso)
2. Deteccion de outliers en espaciado (> 3 sigma → flag)
3. Alerta si confidence < umbral configurable
4. Reporte de duplicados y registros invalidos
5. Verificacion de checksums de archivos
6. Resumen ejecutivo por sonda / shard

Uso:
    python scripts/data_quality_monitor.py [--base-dir .] [--threshold-sigma 3.0] [--min-confidence 0.5]
    python scripts/data_quality_monitor.py --watch   # modo continuo (60s refresh)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── Importar modulos del proyecto ────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from core.ledger_reader import LedgerReader, ShardMerger, read_phase1_shards
    from core.ledger_writer import SCHEMA_VERSION
    _LEDGER_AVAILABLE = True
except ImportError:
    _LEDGER_AVAILABLE = False


# ─── Teoria: von Mangoldt ─────────────────────────────────────────────────────

def n_von_mangoldt(t: float) -> float:
    """Numero teorico acumulado de zeros hasta T."""
    if t < 10:
        return 0.0
    return (t / (2 * math.pi)) * (math.log(t / (2 * math.pi)) - 1) + 7.0 / 8.0


def expected_zeros_in_range(t0: float, t1: float) -> float:
    """Zeros esperados en [t0, t1] segun von Mangoldt."""
    return max(0.0, n_von_mangoldt(t1) - n_von_mangoldt(t0))


def mean_spacing_at(t: float) -> float:
    """Espaciado medio teorico en T."""
    if t < 2 * math.pi:
        return 1.0
    return (2 * math.pi) / math.log(t / (2 * math.pi))


# ─── Dataclasses de reporte ───────────────────────────────────────────────────

@dataclass
class SpacingAlert:
    t_zero:   float
    spacing:  float
    sigma:    float
    kind:     str   # "OUTLIER_HIGH" | "OUTLIER_LOW" | "DUPLICATE"


@dataclass
class ShardReport:
    path:              str
    count:             int
    t_min:             float
    t_max:             float
    expected:          float
    deficit:           float          # expected - count (negativo = exceso)
    deficit_pct:       float
    spacing_mean:      float
    spacing_std:       float
    spacing_theoretical: float
    spacing_ratio:     float          # observed / theoretical
    outlier_count:     int
    low_confidence:    int
    edge_count:        int
    duplicate_count:   int
    corrupt_lines:     int
    checksum:          str
    alerts:            List[SpacingAlert] = field(default_factory=list)
    verdict:           str = "OK"     # OK | WARN | FAIL


@dataclass
class GlobalReport:
    timestamp:       str
    base_dir:        str
    shards_analyzed: int
    total_zeros:     int
    total_duplicates: int
    total_corrupt:   int
    global_t_min:    float
    global_t_max:    float
    global_expected: float
    global_deficit:  float
    global_deficit_pct: float
    overall_verdict: str
    shard_reports:   List[ShardReport] = field(default_factory=list)


# ─── Analisis de un shard ─────────────────────────────────────────────────────

def analyze_shard(
    path: Path,
    *,
    sigma_threshold: float = 3.0,
    min_confidence:  float = 0.5,
    max_alerts:      int   = 20,
) -> ShardReport:
    """Analiza un archivo JSONL y retorna ShardReport."""

    # Lectura de datos
    t_vals:      List[float] = []
    confidences: List[float] = []
    edge_count   = 0
    corrupt      = 0
    seen_fps:    Dict[str, int] = {}   # fingerprint → count

    # Detecta encoding (UTF-16 BOM o UTF-8)
    encoding = _detect_encoding(path)
    with open(path, encoding=encoding, errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                corrupt += 1
                continue

            payload = event.get("payload", event)
            t = _extract_t(payload)
            if t is None or not math.isfinite(t) or t <= 0:
                continue

            fp = _fingerprint(t)
            seen_fps[fp] = seen_fps.get(fp, 0) + 1
            t_vals.append(t)

            conf = payload.get("confidence")
            if conf is not None:
                try:
                    confidences.append(float(conf))
                except (TypeError, ValueError):
                    pass

            if payload.get("edge", False):
                edge_count += 1

    # --- Estadisticas basicas ---
    n = len(t_vals)
    duplicates = sum(c - 1 for c in seen_fps.values() if c > 1)

    if n == 0:
        return ShardReport(
            path=str(path), count=0, t_min=0, t_max=0,
            expected=0, deficit=0, deficit_pct=0,
            spacing_mean=0, spacing_std=0, spacing_theoretical=0, spacing_ratio=0,
            outlier_count=0, low_confidence=0, edge_count=0, duplicate_count=0,
            corrupt_lines=corrupt, checksum=_sha256(path), verdict="FAIL",
        )

    t_sorted = sorted(t_vals)
    t_min, t_max = t_sorted[0], t_sorted[-1]
    spacings = [t_sorted[i+1] - t_sorted[i] for i in range(n - 1)]

    sp_mean = _mean(spacings) if spacings else 0.0
    sp_std  = _std(spacings)  if spacings else 0.0
    sp_theo = mean_spacing_at((t_min + t_max) / 2)
    sp_ratio = sp_mean / sp_theo if sp_theo > 0 else 1.0

    expected    = expected_zeros_in_range(t_min, t_max)
    deficit     = expected - n
    deficit_pct = (deficit / expected * 100) if expected > 0 else 0.0

    # --- Deteccion de outliers en espaciado ---
    alerts: List[SpacingAlert] = []
    if spacings and sp_std > 0:
        for i, s in enumerate(spacings):
            sigma = (s - sp_mean) / sp_std
            if abs(sigma) >= sigma_threshold:
                kind = "OUTLIER_HIGH" if sigma > 0 else "OUTLIER_LOW"
                if s < 1e-6:
                    kind = "DUPLICATE"
                alerts.append(SpacingAlert(
                    t_zero  = t_sorted[i + 1],
                    spacing = s,
                    sigma   = round(sigma, 2),
                    kind    = kind,
                ))
                if len(alerts) >= max_alerts:
                    break

    low_conf = sum(1 for c in confidences if c < min_confidence)

    # --- Veredicto ---
    verdict = "OK"
    if corrupt > 0 or abs(deficit_pct) > 15:
        verdict = "FAIL"
    elif low_conf > n * 0.1 or len(alerts) > 5 or abs(deficit_pct) > 5:
        verdict = "WARN"

    return ShardReport(
        path              = str(path),
        count             = n,
        t_min             = round(t_min, 6),
        t_max             = round(t_max, 6),
        expected          = round(expected, 2),
        deficit           = round(deficit, 2),
        deficit_pct       = round(deficit_pct, 2),
        spacing_mean      = round(sp_mean, 6),
        spacing_std       = round(sp_std, 6),
        spacing_theoretical = round(sp_theo, 6),
        spacing_ratio     = round(sp_ratio, 4),
        outlier_count     = len(alerts),
        low_confidence    = low_conf,
        edge_count        = edge_count,
        duplicate_count   = duplicates,
        corrupt_lines     = corrupt,
        checksum          = _sha256(path),
        alerts            = alerts[:5],   # solo los primeros 5 en el reporte
        verdict           = verdict,
    )


# ─── Reporte global ───────────────────────────────────────────────────────────

def run_global_report(
    base_dir: Path,
    *,
    sigma_threshold: float = 3.0,
    min_confidence:  float = 0.5,
    patterns: Optional[List[str]] = None,
) -> GlobalReport:
    """Analiza todos los shards encontrados y genera reporte global."""

    if patterns is None:
        patterns = [
            "ledger_riemann_phase1/shard_*.jsonl",
            "results/riemann/*.jsonl",
            "results/mersenne/cert_ledger_seismic.jsonl",
            "run_mersenne/Block-A/ledger.jsonl",
        ]

    paths: List[Path] = []
    for pat in patterns:
        paths.extend(sorted(base_dir.glob(pat)))

    # Deduplica rutas
    seen_paths: set = set()
    unique_paths: List[Path] = []
    for p in paths:
        if p not in seen_paths:
            seen_paths.add(p)
            unique_paths.append(p)

    shard_reports: List[ShardReport] = []
    for p in unique_paths:
        try:
            sr = analyze_shard(p, sigma_threshold=sigma_threshold, min_confidence=min_confidence)
            shard_reports.append(sr)
        except Exception as e:
            print(f"  [!] Error analizando {p.name}: {e}", file=sys.stderr)

    total_zeros     = sum(r.count for r in shard_reports)
    total_duplicates = sum(r.duplicate_count for r in shard_reports)
    total_corrupt   = sum(r.corrupt_lines for r in shard_reports)

    t_mins = [r.t_min for r in shard_reports if r.count > 0]
    t_maxs = [r.t_max for r in shard_reports if r.count > 0]
    g_min  = min(t_mins) if t_mins else 0.0
    g_max  = max(t_maxs) if t_maxs else 0.0

    g_expected   = expected_zeros_in_range(g_min, g_max)
    g_deficit    = g_expected - total_zeros
    g_deficit_pct = (g_deficit / g_expected * 100) if g_expected > 0 else 0.0

    fail_count = sum(1 for r in shard_reports if r.verdict == "FAIL")
    warn_count = sum(1 for r in shard_reports if r.verdict == "WARN")
    if fail_count > 0:
        overall = "FAIL"
    elif warn_count > 0 or total_corrupt > 0:
        overall = "WARN"
    else:
        overall = "OK"

    return GlobalReport(
        timestamp        = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        base_dir         = str(base_dir),
        shards_analyzed  = len(shard_reports),
        total_zeros      = total_zeros,
        total_duplicates = total_duplicates,
        total_corrupt    = total_corrupt,
        global_t_min     = round(g_min, 4),
        global_t_max     = round(g_max, 4),
        global_expected  = round(g_expected, 2),
        global_deficit   = round(g_deficit, 2),
        global_deficit_pct = round(g_deficit_pct, 2),
        overall_verdict  = overall,
        shard_reports    = shard_reports,
    )


# ─── Display ──────────────────────────────────────────────────────────────────

VERDICT_ICON = {"OK": "✓", "WARN": "⚠", "FAIL": "✗"}

def print_report(report: GlobalReport, verbose: bool = False) -> None:
    icon = VERDICT_ICON.get(report.overall_verdict, "?")
    print(f"\n{'='*70}")
    print(f"  GAHENAX DATA QUALITY MONITOR — {report.timestamp}")
    print(f"  Veredicto global: {icon} {report.overall_verdict}")
    print(f"{'='*70}")
    print(f"  Base dir:        {report.base_dir}")
    print(f"  Shards analizados: {report.shards_analyzed}")
    print(f"  Zeros totales:   {report.total_zeros:,}")
    print(f"  Duplicados:      {report.total_duplicates:,}")
    print(f"  Lineas corruptas:{report.total_corrupt:,}")
    print(f"  T range:         [{report.global_t_min:.2f}, {report.global_t_max:.2f}]")
    print(f"  Von Mangoldt:    esperado={report.global_expected:.1f} | deficit={report.global_deficit:.1f} ({report.global_deficit_pct:+.1f}%)")
    print()

    for sr in report.shard_reports:
        icon_s = VERDICT_ICON.get(sr.verdict, "?")
        name   = Path(sr.path).name
        deficit_str = f"{sr.deficit_pct:+.1f}%"
        print(f"  {icon_s} {name:<45} N={sr.count:<5} deficit={deficit_str:<8} "
              f"spacing={sr.spacing_mean:.4f}±{sr.spacing_std:.4f} "
              f"(ratio={sr.spacing_ratio:.3f})")

        if verbose and sr.verdict != "OK":
            if sr.outlier_count:
                print(f"      Outliers de espaciado: {sr.outlier_count}")
                for a in sr.alerts[:3]:
                    print(f"        t={a.t_zero:.4f} s={a.spacing:.6f} ({a.sigma:+.1f}σ) [{a.kind}]")
            if sr.low_confidence:
                print(f"      Confidence baja: {sr.low_confidence} registros")
            if sr.duplicate_count:
                print(f"      Duplicados: {sr.duplicate_count}")
            if sr.corrupt_lines:
                print(f"      Lineas corruptas: {sr.corrupt_lines}")

    print(f"{'='*70}\n")


def save_report(report: GlobalReport, output: Path) -> None:
    """Guarda el reporte como JSON."""
    import dataclasses
    def _serialize(obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return str(obj)
    output.write_text(json.dumps(dataclasses.asdict(report), indent=2, default=_serialize))


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _detect_encoding(path: Path) -> str:
    """Detecta UTF-16 por BOM, de lo contrario asume UTF-8."""
    with open(path, "rb") as f:
        header = f.read(4)
    if header[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return "utf-16"
    if header[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    return "utf-8"


def _extract_t(payload: Dict[str, Any]) -> Optional[float]:
    for key in ("t_zero", "t_est", "refined_T", "T", "t_root"):
        v = payload.get(key)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return None


def _fingerprint(t: float) -> str:
    return str(round(t, 8))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:12]  # short hash para display


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs: List[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monitor de calidad de datos Gahenax",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--base-dir",         default=".", help="Directorio raiz del repo")
    parser.add_argument("--sigma",            type=float, default=3.0, help="Umbral sigma para outliers de espaciado")
    parser.add_argument("--min-confidence",   type=float, default=0.5, help="Confidence minima aceptable")
    parser.add_argument("--output",           default=None, help="Guardar reporte JSON en este archivo")
    parser.add_argument("--verbose", "-v",    action="store_true", help="Mostrar detalles de alertas")
    parser.add_argument("--watch",            action="store_true", help="Modo continuo (refresh cada 60s)")
    parser.add_argument("--interval",         type=int, default=60, help="Intervalo en segundos para --watch")
    args = parser.parse_args()

    base = Path(args.base_dir).resolve()

    def run_once():
        report = run_global_report(base, sigma_threshold=args.sigma, min_confidence=args.min_confidence)
        print_report(report, verbose=args.verbose)
        if args.output:
            out = Path(args.output)
            save_report(report, out)
            print(f"  Reporte guardado en: {out}")
        return report.overall_verdict

    if args.watch:
        print(f"Modo watch activado — refresh cada {args.interval}s. Ctrl+C para detener.")
        while True:
            verdict = run_once()
            time.sleep(args.interval)
    else:
        verdict = run_once()
        sys.exit(0 if verdict == "OK" else 1)


if __name__ == "__main__":
    main()
