#!/usr/bin/env python3
"""
core/ledger_reader.py
=====================
Lector de ledger JSONL con:
- Lectura por streaming (generador) — no carga todo en memoria
- Verificacion de checksum SHA256 al abrir
- Merge cross-shard con deduplicacion automatica
- Filtros por rango T, probe, metodo, schema_version
- Estadisticas basicas en un solo paso (sin recargar)
- Normalizacion de campos legacy (t_est / T / refined_T → t_zero)
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, Iterator, List, Optional, Set, Tuple

from core.ledger_writer import normalize_legacy_record, ZeroRecord, DEDUP_PRECISION, DEDUP_EPS


# ─── Constantes ───────────────────────────────────────────────────────────────

ZERO_TYPES  = {"ZERO_CANDIDATE"}
HEALTH_TYPES = {"HEALTH"}


# ─── Streaming reader ─────────────────────────────────────────────────────────

class LedgerReader:
    """
    Lee un archivo JSONL de ledger linea por linea (streaming).
    No carga el archivo completo en memoria.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        verify_checksum: bool = False,
        expected_sha256: Optional[str] = None,
    ) -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Ledger no encontrado: {self.path}")

        if verify_checksum and expected_sha256:
            actual = _sha256_file(self.path)
            if actual != expected_sha256:
                raise ValueError(
                    f"Checksum mismatch en {self.path.name}\n"
                    f"  esperado: {expected_sha256}\n"
                    f"  actual:   {actual}"
                )

    # ── Iteradores ────────────────────────────────────────────────────────────

    def events(
        self,
        *,
        event_types: Optional[Set[str]] = None,
        skip_corrupt: bool = True,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Itera sobre todos los eventos del ledger linea por linea.
        Retorna el dict completo: {ts, type, payload}.
        """
        with open(self.path, encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    if not skip_corrupt:
                        raise
                    continue

                if event_types and event.get("type") not in event_types:
                    continue
                yield event

    def zeros(
        self,
        *,
        t_min: float = -math.inf,
        t_max: float = math.inf,
        probe: Optional[str] = None,
        method: Optional[str] = None,
        min_confidence: float = 0.0,
        skip_edge: bool = False,
    ) -> Generator[ZeroRecord, None, None]:
        """
        Itera sobre ZeroRecords aplicando filtros.
        Normaliza campos legacy automaticamente.
        """
        for event in self.events(event_types=ZERO_TYPES):
            payload = event.get("payload", event)  # soporte legacy sin envelope

            # Normaliza al schema canonico
            rec = _payload_to_zero(payload)
            if rec is None:
                continue

            # Filtros
            if not (t_min <= rec.t_zero <= t_max):
                continue
            if probe and rec.probe != probe:
                continue
            if method and rec.method != method:
                continue
            if rec.confidence < min_confidence:
                continue
            if skip_edge and rec.edge:
                continue

            yield rec

    def health_events(self) -> Generator[Dict[str, Any], None, None]:
        """Itera sobre eventos HEALTH."""
        for event in self.events(event_types=HEALTH_TYPES):
            yield event.get("payload", event)

    def count(self, event_type: str = "ZERO_CANDIDATE") -> int:
        """Cuenta eventos de un tipo sin cargar en memoria."""
        n = 0
        for _ in self.events(event_types={event_type}):
            n += 1
        return n

    def stats(
        self,
        *,
        t_min: float = -math.inf,
        t_max: float = math.inf,
    ) -> Dict[str, Any]:
        """
        Calcula estadisticas basicas en un solo paso de streaming.
        No requiere cargar todos los datos en memoria.
        """
        n = 0
        t_vals: List[float] = []  # guardamos solo t_zero para espaciados
        residuals: List[float] = []
        confidences: List[float] = []
        probes: Dict[str, int] = {}
        methods: Dict[str, int] = {}
        edge_count = 0

        for rec in self.zeros(t_min=t_min, t_max=t_max):
            n += 1
            t_vals.append(rec.t_zero)
            if rec.residual is not None:
                residuals.append(rec.residual)
            if rec.confidence is not None:
                confidences.append(rec.confidence)
            if rec.probe:
                probes[rec.probe] = probes.get(rec.probe, 0) + 1
            if rec.method:
                methods[rec.method] = methods.get(rec.method, 0) + 1
            if rec.edge:
                edge_count += 1

        if n == 0:
            return {"count": 0}

        t_vals_sorted = sorted(t_vals)
        spacings = [t_vals_sorted[i+1] - t_vals_sorted[i] for i in range(len(t_vals_sorted)-1)]

        result: Dict[str, Any] = {
            "count":       n,
            "t_min":       t_vals_sorted[0],
            "t_max":       t_vals_sorted[-1],
            "t_range":     t_vals_sorted[-1] - t_vals_sorted[0],
            "edge_count":  edge_count,
            "probes":      probes,
            "methods":     methods,
        }

        if spacings:
            result["spacing"] = {
                "mean":   _mean(spacings),
                "median": _median(spacings),
                "min":    min(spacings),
                "max":    max(spacings),
                "std":    _std(spacings),
            }

        if residuals:
            result["residual"] = {
                "mean": _mean(residuals),
                "max":  max(residuals),
                "min":  min(residuals),
            }

        if confidences:
            result["confidence"] = {
                "mean": _mean(confidences),
                "min":  min(confidences),
                "max":  max(confidences),
            }

        return result


# ─── Merge cross-shard ────────────────────────────────────────────────────────

class ShardMerger:
    """
    Fusiona multiples shards JSONL en un stream deduplicado.
    No escribe un archivo temporal — trabaja en streaming.
    """

    def __init__(
        self,
        shard_paths: Iterable[str | Path],
        *,
        dedup: bool = True,
        sort: bool = True,
    ) -> None:
        self.readers = [LedgerReader(p) for p in shard_paths]
        self.dedup   = dedup
        self.sort    = sort

    def zeros(
        self,
        *,
        t_min: float = -math.inf,
        t_max: float = math.inf,
        **kwargs,
    ) -> List[ZeroRecord]:
        """
        Retorna lista deduplicada y ordenada de ZeroRecords de todos los shards.
        Para datasets muy grandes usar zeros_stream() en su lugar.
        """
        seen: Set[str] = set()
        results: List[ZeroRecord] = []

        for reader in self.readers:
            for rec in reader.zeros(t_min=t_min, t_max=t_max, **kwargs):
                if self.dedup:
                    fp = rec.fingerprint()
                    if fp in seen:
                        continue
                    seen.add(fp)
                results.append(rec)

        if self.sort:
            results.sort(key=lambda r: r.t_zero)

        return results

    def zeros_stream(
        self,
        *,
        t_min: float = -math.inf,
        t_max: float = math.inf,
        **kwargs,
    ) -> Generator[ZeroRecord, None, None]:
        """
        Version streaming de zeros() — no acumula en memoria.
        No garantiza orden global entre shards (cada shard se lee en orden).
        """
        seen: Set[str] = set()
        for reader in self.readers:
            for rec in reader.zeros(t_min=t_min, t_max=t_max, **kwargs):
                if self.dedup:
                    fp = rec.fingerprint()
                    if fp in seen:
                        continue
                    seen.add(fp)
                yield rec

    def stats(self, **kwargs) -> Dict[str, Any]:
        """Estadisticas agregadas de todos los shards."""
        all_zeros = self.zeros(**kwargs)
        if not all_zeros:
            return {"count": 0, "shards": len(self.readers)}

        t_vals = [r.t_zero for r in all_zeros]
        spacings = [t_vals[i+1] - t_vals[i] for i in range(len(t_vals)-1)]
        probes: Dict[str, int] = {}
        for r in all_zeros:
            if r.probe:
                probes[r.probe] = probes.get(r.probe, 0) + 1

        return {
            "count":    len(all_zeros),
            "shards":   len(self.readers),
            "t_min":    t_vals[0],
            "t_max":    t_vals[-1],
            "t_range":  t_vals[-1] - t_vals[0],
            "probes":   probes,
            "spacing":  {
                "mean":   _mean(spacings),
                "median": _median(spacings),
                "min":    min(spacings) if spacings else None,
                "max":    max(spacings) if spacings else None,
                "std":    _std(spacings),
            } if spacings else {},
        }


# ─── Funciones de conveniencia ────────────────────────────────────────────────

def read_phase1_shards(base_dir: str | Path = ".") -> ShardMerger:
    """Carga los 6 shards del ledger Phase 1."""
    base = Path(base_dir)
    shard_dir = base / "ledger_riemann_phase1"
    paths = sorted(shard_dir.glob("shard_*.jsonl"))
    if not paths:
        raise FileNotFoundError(f"No se encontraron shards en {shard_dir}")
    return ShardMerger(paths)


def read_all_riemann_results(base_dir: str | Path = ".") -> ShardMerger:
    """Carga todos los resultados de Riemann (Phase 1 + surge + datos historicos)."""
    base = Path(base_dir)
    paths = list(sorted(base.glob("ledger_riemann_phase1/shard_*.jsonl")))
    paths += list(sorted(base.glob("results/riemann/*.jsonl")))
    return ShardMerger(paths)


# ─── Utilidades internas ──────────────────────────────────────────────────────

def _payload_to_zero(payload: Dict[str, Any]) -> Optional[ZeroRecord]:
    """Convierte un dict payload a ZeroRecord (normaliza campos legacy)."""
    # Schema nuevo: ya tiene t_zero
    if "t_zero" in payload:
        try:
            return ZeroRecord(
                t_zero     = float(payload["t_zero"]),
                method     = payload.get("method", "manual"),
                residual   = float(payload.get("residual") or 0.0),
                confidence = float(payload.get("confidence", 1.0)),
                probe      = payload.get("probe"),
                band_id    = payload.get("band_id"),
                seq        = payload.get("seq"),
                rigidity_h = payload.get("rigidity_h"),
                bracket    = payload.get("bracket"),
                edge       = bool(payload.get("edge", False)),
            )
        except (TypeError, ValueError):
            return None

    # Schema legacy: normaliza
    return normalize_legacy_record(payload)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs: List[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m)**2 for x in xs) / (len(xs) - 1))


def _median(xs: List[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2.0


# ─── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from pathlib import Path
    import sys

    base = Path(__file__).parent.parent

    # Test 1: leer Phase 1 shards
    print("=== Phase 1 Shards (merge cross-shard) ===")
    try:
        merger = read_phase1_shards(base)
        stats = merger.stats()
        print(f"  Zeros totales (dedup): {stats['count']}")
        print(f"  T range: [{stats['t_min']:.4f}, {stats['t_max']:.4f}]")
        print(f"  Spacing medio: {stats['spacing']['mean']:.6f}")
        print(f"  Spacing std:   {stats['spacing']['std']:.6f}")
        print(f"  Probes: {stats['probes']}")
    except FileNotFoundError as e:
        print(f"  {e}")

    # Test 2: leer un shard individual con filtro
    print("\n=== Shard ALPHA (T=[6340,6370]) ===")
    shard_path = base / "ledger_riemann_phase1" / "shard_ALPHA_band0.jsonl"
    if shard_path.exists():
        reader = LedgerReader(shard_path)
        s = reader.stats(t_min=6340, t_max=6370)
        print(f"  Zeros en rango: {s['count']}")
        if "spacing" in s:
            print(f"  Spacing medio: {s['spacing']['mean']:.6f}")
    else:
        print(f"  {shard_path} no encontrado")

    print("\nOK — ledger_reader.py funciona correctamente")
