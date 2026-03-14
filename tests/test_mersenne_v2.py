"""
Tests for Mersenne module v2.0 improvements:
- SearchMemory (p-range persistence)
- OrchestratorCheckpoint (generic save/load/resume)
- GhostValidationGate (unified DEEP/SURFACE/ARTIFACT verdict)
- CampaignDashboard (unified telemetry)
"""
import os
import sys
import json
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from research.mersenne.search_memory import SearchMemory
from research.mersenne.orchestrator_checkpoint import OrchestratorCheckpoint
from research.mersenne.ghost_validation_gate import (
    GhostValidationGate, GhostVerdict, signature_p0, feature_energy, robust_z
)
from research.mersenne.campaign_dashboard import CampaignDashboard


# --- Test SearchMemory ---

def test_search_memory_write_read():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = SearchMemory(working_dir=tmpdir)
        assert len(mem.load_scanned_ranges()) == 0

        mem.save_session(
            p_start=20000, p_end=50000,
            candidates=[21701, 23209],
            ghost_loci=[21503],
            blocks_processed=15,
        )
        ranges = mem.load_scanned_ranges()
        assert len(ranges) == 1
        assert ranges[0] == (20000, 50000)

        loci = mem.load_ghost_loci()
        assert 21503 in loci


def test_search_memory_range_merging():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = SearchMemory(working_dir=tmpdir)
        mem.save_session(p_start=20000, p_end=50000, candidates=[], ghost_loci=[], blocks_processed=5)
        mem.save_session(
            p_start=45000, p_end=80000, candidates=[], ghost_loci=[], blocks_processed=7,
            existing_ranges=[(20000, 50000)]
        )
        ranges = mem.load_scanned_ranges()
        assert len(ranges) == 1
        assert ranges[0] == (20000, 80000)


def test_search_memory_range_coverage():
    mem = SearchMemory.__new__(SearchMemory)
    scanned = [(20000, 50000), (100000, 200000)]
    assert mem.is_range_covered(25000, 40000, scanned) is True
    assert mem.is_range_covered(50000, 60000, scanned) is False
    assert mem.is_range_covered(100000, 200000, scanned) is True


# --- Test OrchestratorCheckpoint ---

def test_checkpoint_save_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        cp = OrchestratorCheckpoint(checkpoint_dir=tmpdir, name="test")
        cp.save(block_idx=3, current_p=500000, candidates_found=[499979])
        data = cp.load()
        assert data is not None
        assert data["block_idx"] == 3
        assert data["current_p"] == 500000
        assert 499979 in data["candidates_found"]


def test_checkpoint_load_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        cp = OrchestratorCheckpoint(checkpoint_dir=tmpdir, name="test")
        assert cp.load() is None


def test_checkpoint_clear():
    with tempfile.TemporaryDirectory() as tmpdir:
        cp = OrchestratorCheckpoint(checkpoint_dir=tmpdir, name="test")
        cp.save(block_idx=1, current_p=100)
        assert cp.load() is not None
        cp.clear()
        assert cp.load() is None


def test_checkpoint_resume_or_start():
    with tempfile.TemporaryDirectory() as tmpdir:
        cp = OrchestratorCheckpoint(checkpoint_dir=tmpdir, name="test")
        # No checkpoint → fresh start
        state = cp.resume_or_start(default_start_p=20000)
        assert state["current_p"] == 20000
        assert state["block_idx"] == 0

        # Save and resume
        cp.save(block_idx=5, current_p=75000)
        state = cp.resume_or_start(default_start_p=20000)
        assert state["current_p"] == 75000
        assert state["block_idx"] == 5


# --- Test GhostValidationGate ---

def test_ghost_gate_known_prime():
    """Known Mersenne primes should have distinctive signatures."""
    gate = GhostValidationGate(q_pool_size=100, z_threshold=2.0, seed=42)
    # p=127 is a known Mersenne prime (M127 = 2^127 - 1 is prime)
    result = gate.validate(127)
    assert isinstance(result, GhostVerdict)
    assert result.p == 127
    assert result.verdict in ["DEEP", "SURFACE", "ARTIFACT"]
    assert isinstance(result.signature_z, float)


def test_ghost_gate_composite():
    """A composite exponent should generally not produce DEEP."""
    gate = GhostValidationGate(q_pool_size=100, z_threshold=3.0, seed=42)
    result = gate.validate(100)  # 100 is not prime, so 2^100-1 is not Mersenne prime
    assert result.verdict in ["SURFACE", "ARTIFACT"]


def test_ghost_gate_telemetry_schema():
    gate = GhostValidationGate(q_pool_size=50, seed=42)
    result = gate.validate(61)
    assert hasattr(result, "p")
    assert hasattr(result, "signature_z")
    assert hasattr(result, "invariance_survived")
    assert hasattr(result, "verdict")
    assert hasattr(result, "details")


def test_signature_p0_determinism():
    q_list = [3, 5, 7, 11, 13]
    sig1 = signature_p0(127, q_list)
    sig2 = signature_p0(127, q_list)
    assert sig1 == sig2


def test_robust_z_basic():
    assert robust_z(10.0, 5.0, 2.0) > 0
    assert robust_z(0.0, 5.0, 2.0) < 0


# --- Test CampaignDashboard ---

def test_dashboard_generation_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "DASHBOARD.md")
        dash = CampaignDashboard(results_dir=os.path.join(tmpdir, "results"), output_path=out)
        content = dash.generate()
        assert "Mersenne Campaign Dashboard" in content
        assert "NO HEARTBEAT DETECTED" in content


def test_dashboard_with_heartbeat():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock heartbeat
        hb_path = os.path.join(tmpdir, "heartbeat.json")
        with open(hb_path, "w") as f:
            json.dump({"status": "RUNNING", "active_workers": "7/8", "last_p_processed": 50000}, f)

        # Run from tmpdir context
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            out = os.path.join(tmpdir, "DASHBOARD.md")
            dash = CampaignDashboard(results_dir=os.path.join(tmpdir, "results"), output_path=out)
            content = dash.generate()
            assert "RUNNING" in content
            assert "7/8" in content
        finally:
            os.chdir(old_cwd)
