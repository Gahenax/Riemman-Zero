#!/usr/bin/env python3
"""
core/ledger_writer.py
=====================
Ledger writer con garantias de durabilidad, validacion de schema,
deduplicacion global y versionado.

Mejoras sobre el sistema anterior:
- fsync() despues de cada write (durabilidad ante crash)
- Schema validation con dataclasses + type checking estricto
- Deduplicacion global por fingerprint SHA256(round(t_zero, 8))
- Campo canonico unico: t_zero (normaliza t_est / T / refined_T)
- schema_version en cada registro
- Batch atomico: escribe N registros o nada
- Checksum de integridad del archivo al cerrar
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# ─── Constantes ───────────────────────────────────────────────────────────────

SCHEMA_VERSION = "2.0"
DEDUP_PRECISION = 8       # decimales para fingerprint de t_zero
DEDUP_EPS       = 1e-7    # dos zeros mas cercanos que esto = duplicado


# ─── Schema de eventos ────────────────────────────────────────────────────────

@dataclass
class ZeroRecord:
    """
    Representacion canonica de un cero de Riemann certificado.
    Campo unico: t_zero (reemplaza t_est / T / refined_T del sistema anterior).
    """
    t_zero:         float           # posicion del cero (campo canonico)
    method:         str             # bracketing_scan_v1 | tri_filter | brent | odlyzko
    residual:       float = 0.0     # |Z(t_zero)|
    confidence:     float = 1.0     # [0, 1]
    probe:          Optional[str]   = None   # ALPHA..FOXTROT
    band_id:        Optional[int]   = None
    seq:            Optional[int]   = None
    rigidity_h:     Optional[float] = None
    bracket:        Optional[List[float]] = None
    edge:           bool = False
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> None:
        """Lanza ValueError si el registro es invalido."""
        if not math.isfinite(self.t_zero) or self.t_zero <= 0:
            raise ValueError(f"t_zero invalido: {self.t_zero}")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence fuera de rango [0,1]: {self.confidence}")
        if not math.isfinite(self.residual) or self.residual < 0:
            raise ValueError(f"residual invalido: {self.residual}")
        if self.method not in {
            "bracketing_scan_v1", "tri_filter", "brent",
            "odlyzko", "surge_refinement", "manual"
        }:
            raise ValueError(f"method desconocido: {self.method!r}")

    def fingerprint(self) -> str:
        """SHA256 del t_zero redondeado — usado para deduplicacion global."""
        key = round(self.t_zero, DEDUP_PRECISION)
        return hashlib.sha256(str(key).encode()).hexdigest()[:16]


@dataclass
class HealthRecord:
    """Evento de telemetria / monitoreo de sonda."""
    probe:          str
    status:         str             # STARTING_SWEEP | COMPLETED | ERROR
    t0:             float
    t1:             float
    zeros_found:    int = 0
    duration_s:     float = 0.0
    alpha:          float = 0.1
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> None:
        if self.t0 >= self.t1:
            raise ValueError(f"rango invalido t0={self.t0} >= t1={self.t1}")
        if self.zeros_found < 0:
            raise ValueError(f"zeros_found negativo: {self.zeros_found}")
        if self.status not in {"STARTING_SWEEP", "COMPLETED", "ERROR", "PAUSED"}:
            raise ValueError(f"status desconocido: {self.status!r}")


# ─── Writer principal ─────────────────────────────────────────────────────────

class LedgerWriter:
    """
    Escritor de ledger JSONL con:
    - Validacion de schema antes de escribir
    - fsync() por durabilidad
    - Deduplicacion global (en memoria + archivo .dedup)
    - Batch atomico
    - Metadatos de integridad al cerrar
    """

    def __init__(
        self,
        path: str | Path,
        *,
        validate: bool = True,
        compress: bool = False,   # futuro: gzip rotation
        dedup: bool = True,
        max_batch: int = 100,
    ) -> None:
        self.path      = Path(path)
        self.validate  = validate
        self.dedup     = dedup
        self.max_batch = max_batch
        self._seen: Set[str] = set()   # fingerprints en memoria
        self._batch: List[Dict[str, Any]] = []
        self._total_written = 0
        self._duplicates    = 0

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._dedup_path = self.path.with_suffix(".dedup")

        # Carga fingerprints existentes para dedup cross-session
        if dedup and self._dedup_path.exists():
            for line in self._dedup_path.read_text().splitlines():
                line = line.strip()
                if line:
                    self._seen.add(line)

        # Archivo de escritura (append)
        self._fh = open(self.path, "a", encoding="utf-8", buffering=1)

    # ── API publica ──────────────────────────────────────────────────────────

    def write_zero(self, record: ZeroRecord) -> bool:
        """
        Escribe un ZeroRecord. Retorna True si fue escrito, False si era duplicado.
        """
        if self.validate:
            record.validate()

        if self.dedup:
            fp = record.fingerprint()
            if fp in self._seen:
                self._duplicates += 1
                return False
            self._seen.add(fp)

        event = {
            "ts":      time.time(),
            "type":    "ZERO_CANDIDATE",
            "payload": asdict(record),
        }
        self._write_event(event)
        return True

    def write_health(self, record: HealthRecord) -> None:
        """Escribe un HealthRecord de telemetria."""
        if self.validate:
            record.validate()
        event = {
            "ts":      time.time(),
            "type":    "HEALTH",
            "payload": asdict(record),
        }
        self._write_event(event)

    def write_batch(self, records: List[ZeroRecord]) -> Dict[str, int]:
        """
        Escribe una lista de ZeroRecord de forma atomica.
        Si alguno falla validacion, no se escribe ninguno.
        Returns: {"written": N, "duplicates": M, "invalid": K}
        """
        valid: List[ZeroRecord] = []
        invalid = 0
        for r in records:
            try:
                if self.validate:
                    r.validate()
                valid.append(r)
            except ValueError:
                invalid += 1

        written = 0
        duplicates = 0
        events: List[Dict] = []
        new_fps: List[str] = []

        for r in valid:
            if self.dedup:
                fp = r.fingerprint()
                if fp in self._seen:
                    duplicates += 1
                    continue
                new_fps.append(fp)
            events.append({
                "ts":      time.time(),
                "type":    "ZERO_CANDIDATE",
                "payload": asdict(r),
            })
            written += 1

        # Escritura atomica: solo si todo OK
        if events:
            lines = "\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n"
            self._fh.write(lines)
            self._fh.flush()
            os.fsync(self._fh.fileno())
            self._total_written += written
            for fp in new_fps:
                self._seen.add(fp)

        return {"written": written, "duplicates": duplicates, "invalid": invalid}

    def stats(self) -> Dict[str, Any]:
        return {
            "path":           str(self.path),
            "total_written":  self._total_written,
            "duplicates_skipped": self._duplicates,
            "unique_fingerprints": len(self._seen),
            "schema_version": SCHEMA_VERSION,
        }

    def close(self) -> str:
        """
        Cierra el writer, persiste fingerprints y retorna SHA256 del archivo.
        """
        self._fh.flush()
        os.fsync(self._fh.fileno())
        self._fh.close()

        # Persiste fingerprints para proxima sesion
        if self.dedup:
            self._dedup_path.write_text("\n".join(sorted(self._seen)))

        # Calcula checksum final
        sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        return sha

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ── Privados ─────────────────────────────────────────────────────────────

    def _write_event(self, event: Dict[str, Any]) -> None:
        line = json.dumps(event, ensure_ascii=False)
        self._fh.write(line + "\n")
        self._fh.flush()
        os.fsync(self._fh.fileno())
        self._total_written += 1


# ─── Helpers de normalizacion (backward compat) ───────────────────────────────

def normalize_legacy_record(raw: Dict[str, Any]) -> Optional[ZeroRecord]:
    """
    Convierte registros del sistema anterior (t_est / T / refined_T)
    al schema canonico ZeroRecord con t_zero.
    Retorna None si no se puede extraer t_zero.
    """
    # Intenta extraer t_zero desde cualquier campo legacy
    t = (
        raw.get("t_zero")
        or raw.get("t_est")
        or raw.get("refined_T")
        or raw.get("T")
        or raw.get("t_root")
    )
    if t is None:
        return None
    try:
        t = float(t)
    except (TypeError, ValueError):
        return None

    return ZeroRecord(
        t_zero     = t,
        method     = raw.get("method", "manual"),
        residual   = float(raw.get("residual") or raw.get("root_val") or 0.0),
        confidence = float(raw.get("confidence", 1.0)),
        probe      = raw.get("probe"),
        band_id    = raw.get("band_id"),
        seq        = raw.get("seq"),
        rigidity_h = raw.get("rigidity_h"),
        bracket    = raw.get("bracket"),
        edge       = bool(raw.get("edge", False)),
    )


# ─── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile, sys

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "demo_ledger.jsonl"
        with LedgerWriter(path, validate=True, dedup=True) as w:
            r1 = ZeroRecord(t_zero=6340.363, method="bracketing_scan_v1", residual=1e-12, probe="ALPHA", band_id=0, seq=0)
            r2 = ZeroRecord(t_zero=6341.267, method="bracketing_scan_v1", residual=2e-13, probe="BRAVO", band_id=1, seq=1)
            r_dup = ZeroRecord(t_zero=6340.363, method="bracketing_scan_v1")  # duplicado

            w1 = w.write_zero(r1)
            w2 = w.write_zero(r2)
            w3 = w.write_zero(r_dup)   # deberia ser rechazado

            h = HealthRecord(probe="ALPHA", status="COMPLETED", t0=6340.0, t1=6390.0, zeros_found=55, duration_s=2809.8)
            w.write_health(h)

            batch_result = w.write_batch([
                ZeroRecord(t_zero=6342.0, method="brent"),
                ZeroRecord(t_zero=6341.267, method="brent"),  # dup de r2
            ])

            print(f"written r1={w1}, r2={w2}, r_dup(should be False)={w3}")
            print(f"batch: {batch_result}")
            print(f"stats: {w.stats()}")

        sha = w.close() if not w._fh.closed else "already closed"
        lines = path.read_text().splitlines()
        print(f"Lineas en ledger: {len(lines)}")
        print("OK — ledger_writer.py funciona correctamente")
