"""
Sweep Memory Persistence (ReMe File-Based Pattern).
Tracks explored T-ranges across Riemann sweeps to enable incremental exploration.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Set, Tuple


class SweepMemory:
    """
    Persistent memory for Riemann zero-mining sweeps.
    Inspired by the ReMe CoPaw file-based memory pattern.
    """
    def __init__(self, working_dir: str = "."):
        self.working_dir = Path(working_dir)
        self.memory_file = self.working_dir / "MEMORY.md"
        self.memory_dir = self.working_dir / "memory"
        self.memory_dir.mkdir(exist_ok=True)

    def load_explored_ranges(self) -> List[Tuple[float, float]]:
        """Load list of already-swept T-ranges from MEMORY.md."""
        ranges = []
        if not self.memory_file.exists():
            return ranges

        content = self.memory_file.read_text(encoding="utf-8")
        in_ranges = False
        for line in content.splitlines():
            if line.strip().startswith("## Explored T-Ranges"):
                in_ranges = True
                continue
            if in_ranges and line.startswith("## "):
                break
            if in_ranges and line.startswith("- `T=["):
                try:
                    # Parse "- `T=[5000.0, 5050.0]`"
                    bracket = line.split("[")[1].split("]")[0]
                    parts = bracket.split(",")
                    t0 = float(parts[0].strip())
                    t1 = float(parts[1].strip())
                    ranges.append((t0, t1))
                except (IndexError, ValueError):
                    continue
        return ranges

    def is_band_covered(self, t0: float, t1: float, explored: List[Tuple[float, float]]) -> bool:
        """Check if a band [t0, t1] is fully covered by explored ranges."""
        for et0, et1 in explored:
            if et0 <= t0 and et1 >= t1:
                return True
        return False

    def save_sweep_summary(self, t_start: float, t_end: float,
                            total_zeros: int, bands_processed: int,
                            forensic_verdict: str = "NOT_RUN",
                            calib_r: float = 0.0,
                            explored_ranges: List[Tuple[float, float]] = None) -> None:
        """Append sweep to daily log and update MEMORY.md."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        daily_log = self.memory_dir / f"{today}.md"

        # Append to daily log
        entry = f"\n### Sweep: T=[{t_start}, {t_end}]\n"
        entry += f"- **Timestamp**: {datetime.utcnow().isoformat()}Z\n"
        entry += f"- **Bands Processed**: {bands_processed}\n"
        entry += f"- **Total Zeros**: {total_zeros}\n"
        entry += f"- **Forensic Verdict**: {forensic_verdict}\n"
        entry += f"- **<r> (GUE)**: {calib_r:.5f}\n"

        with open(daily_log, "a", encoding="utf-8") as f:
            if daily_log.stat().st_size == 0:
                f.write(f"# Riemann Sweep Memory Log — {today}\n")
            f.write(entry)

        # Update MEMORY.md
        all_ranges = list(explored_ranges or [])
        all_ranges.append((t_start, t_end))
        # Merge overlapping ranges
        all_ranges = self._merge_ranges(all_ranges)

        self._update_memory_file(all_ranges, total_zeros, forensic_verdict, calib_r)

    def _merge_ranges(self, ranges: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Merge overlapping or adjacent T-ranges."""
        if not ranges:
            return []
        sorted_r = sorted(ranges, key=lambda x: x[0])
        merged = [sorted_r[0]]
        for t0, t1 in sorted_r[1:]:
            if t0 <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], t1))
            else:
                merged.append((t0, t1))
        return merged

    def _update_memory_file(self, ranges: List[Tuple[float, float]],
                             total_zeros: int, forensic_verdict: str,
                             calib_r: float) -> None:
        """Rewrite MEMORY.md with accumulated knowledge."""
        total_coverage = sum(t1 - t0 for t0, t1 in ranges)
        lines = []
        lines.append("# Riemann Zero-Mining Memory\n\n")
        lines.append(f"> Last updated: {datetime.utcnow().isoformat()}Z\n\n")

        lines.append("## Summary\n\n")
        lines.append(f"- **Total T-coverage**: {total_coverage:.1f} units\n")
        lines.append(f"- **Latest zeros found**: {total_zeros}\n")
        lines.append(f"- **Latest forensic verdict**: {forensic_verdict}\n")
        lines.append(f"- **Latest <r>**: {calib_r:.5f} (GUE target: 0.5996)\n\n")

        lines.append("## Explored T-Ranges\n\n")
        for t0, t1 in ranges:
            lines.append(f"- `T=[{t0}, {t1}]`\n")

        with open(self.memory_file, "w", encoding="utf-8") as f:
            f.writelines(lines)
