"""
Generic Orchestrator Checkpoint/Resume.
Reusable across all Mersenne scale-specific orchestrators (100M, 200M, 500M, 1B, 10B, 100B).
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional


class OrchestratorCheckpoint:
    """
    Saves and loads checkpoint state for any Mersenne orchestrator.
    Enables crash-resistant resume without losing progress.
    """
    def __init__(self, checkpoint_dir: str = ".", name: str = "mersenne"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / f"checkpoint_{name}.json"

    def save(self, block_idx: int, current_p: int,
             candidates_found: List[int] = None,
             extra: Dict[str, Any] = None) -> None:
        """Save checkpoint after a successful block."""
        checkpoint = {
            "block_idx": block_idx,
            "current_p": current_p,
            "candidates_found": candidates_found or [],
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if extra:
            checkpoint.update(extra)
        with open(self.checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, indent=2)

    def load(self) -> Optional[Dict[str, Any]]:
        """Load checkpoint if it exists."""
        if not self.checkpoint_file.exists():
            return None
        try:
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def clear(self) -> None:
        """Remove checkpoint file (e.g., after successful completion)."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()

    def resume_or_start(self, default_start_p: int) -> Dict[str, Any]:
        """
        Convenience method: returns checkpoint data if available,
        otherwise returns fresh start state.
        """
        cp = self.load()
        if cp:
            print(f"[CHECKPOINT] Resuming from block #{cp['block_idx']}, p={cp['current_p']:,}")
            return cp
        return {
            "block_idx": 0,
            "current_p": default_start_p,
            "candidates_found": [],
            "resumed": False,
        }
