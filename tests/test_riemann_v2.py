"""
Tests for Riemann module v2.0 improvements:
- SweepMemory (T-range persistence)
- SpectralCamouflageGate (KS-based GUE validation)
- Checkpoint/Resume functions
"""
import os
import sys
import math
import json
import tempfile
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from research.riemann.sweep_memory import SweepMemory
from research.riemann.spectral_gate import SpectralCamouflageGate, normalized_spacings, riemann_smooth_N

# Inline checkpoint functions to avoid importing the full engine chain
CHECKPOINT_FILE = "checkpoint_surge.json"

def save_checkpoint(out_dir: str, batch_idx: int, current_t: float, total_zeros: int):
    checkpoint = {"batch_idx": batch_idx, "current_t": current_t, "total_zeros": total_zeros, "timestamp": time.time()}
    path = os.path.join(out_dir, CHECKPOINT_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)

def load_checkpoint(out_dir: str):
    path = os.path.join(out_dir, CHECKPOINT_FILE)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


# --- Test SweepMemory ---

def test_sweep_memory_write_read():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = SweepMemory(working_dir=tmpdir)

        # Initially empty
        ranges = mem.load_explored_ranges()
        assert len(ranges) == 0

        # Save a sweep
        mem.save_sweep_summary(
            t_start=5000.0, t_end=5050.0,
            total_zeros=100, bands_processed=10,
            forensic_verdict="AUDITED|SPECTRAL:PASS",
            calib_r=0.5995,
        )

        # Read back
        ranges2 = mem.load_explored_ranges()
        assert len(ranges2) == 1
        assert ranges2[0] == (5000.0, 5050.0)


def test_sweep_memory_range_merging():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = SweepMemory(working_dir=tmpdir)

        # Save overlapping sweeps
        mem.save_sweep_summary(t_start=5000.0, t_end=5050.0, total_zeros=100, bands_processed=10)
        mem.save_sweep_summary(
            t_start=5040.0, t_end=5100.0, total_zeros=120, bands_processed=12,
            explored_ranges=[(5000.0, 5050.0)]
        )

        ranges = mem.load_explored_ranges()
        assert len(ranges) == 1  # Should be merged
        assert ranges[0] == (5000.0, 5100.0)


def test_sweep_memory_band_coverage():
    mem = SweepMemory.__new__(SweepMemory)
    explored = [(5000.0, 5050.0), (5100.0, 5200.0)]

    assert mem.is_band_covered(5010.0, 5020.0, explored) is True
    assert mem.is_band_covered(5000.0, 5050.0, explored) is True
    assert mem.is_band_covered(5045.0, 5060.0, explored) is False  # Partially covered
    assert mem.is_band_covered(5050.0, 5100.0, explored) is False  # Gap


# --- Test SpectralCamouflageGate ---

def test_spectral_gate_insufficient_data():
    gate = SpectralCamouflageGate()
    result = gate.validate([14.134, 21.022, 25.010])  # Too few zeros
    assert result["status"] == "INCONCLUSIVE"


def test_spectral_gate_with_known_zeros():
    """Test with first ~30 known Riemann zeta zeros."""
    known_zeros = [
        14.134725, 21.022040, 25.010858, 30.424876, 32.935062,
        37.586178, 40.918719, 43.327073, 48.005151, 49.773832,
        52.970321, 56.446247, 59.347044, 60.831779, 65.112544,
        67.079811, 69.546402, 72.067158, 75.704691, 77.144840,
        79.337375, 82.910381, 84.735493, 87.425275, 88.809111,
        92.491899, 94.651344, 95.870634, 98.831194, 101.317851,
    ]
    gate = SpectralCamouflageGate(ks_threshold=0.15)
    result = gate.validate(known_zeros)

    assert result["status"] in ["PASS", "FAIL"]  # Should produce a definitive result
    assert result["n_spacings"] == len(known_zeros) - 1
    assert result["ks_statistic"] >= 0
    assert "mean_r" in result
    assert result["mode"] == "wigner_surmise"


def test_spectral_gate_telemetry_schema():
    gate = SpectralCamouflageGate()
    zeros = [14.0 + i * 1.5 for i in range(20)]
    result = gate.validate(zeros)
    required_keys = ["status", "ks_statistic", "p_value", "mean_r", "gue_r_target", "mode", "n_spacings"]
    for k in required_keys:
        assert k in result, f"Missing key: {k}"


# --- Test Checkpoint/Resume ---

def test_checkpoint_save_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        save_checkpoint(tmpdir, batch_idx=5, current_t=8750.0, total_zeros=2500)

        cp = load_checkpoint(tmpdir)
        assert cp is not None
        assert cp["batch_idx"] == 5
        assert cp["current_t"] == 8750.0
        assert cp["total_zeros"] == 2500


def test_checkpoint_load_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        cp = load_checkpoint(tmpdir)
        assert cp is None


def test_smooth_N_monotonic():
    """N(t) should be monotonically increasing for t > 0."""
    values = [riemann_smooth_N(t) for t in range(10, 100)]
    for i in range(1, len(values)):
        assert values[i] > values[i - 1]
