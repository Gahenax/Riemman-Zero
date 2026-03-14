"""
Search Memory Persistence (ReMe File-Based Pattern).
Tracks scanned p-ranges, ghost loci, and candidates across Mersenne mining sessions.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Set, Tuple, Optional


class SearchMemory:
    """
    Persistent memory for Mersenne prime search campaigns.
    Uses Markdown files for human-readable memory (ReMe CoPaw pattern).
    """
    def __init__(self, working_dir: str = "."):
        self.working_dir = Path(working_dir)
        self.memory_file = self.working_dir / "MEMORY.md"
        self.memory_dir = self.working_dir / "memory"
        self.memory_dir.mkdir(exist_ok=True)

    def load_scanned_ranges(self) -> List[Tuple[int, int]]:
        """Load already-scanned p-ranges from MEMORY.md."""
        ranges = []
        if not self.memory_file.exists():
            return ranges
        content = self.memory_file.read_text(encoding="utf-8")
        in_ranges = False
        for line in content.splitlines():
            if line.strip().startswith("## Scanned Ranges"):
                in_ranges = True
                continue
            if in_ranges and line.startswith("## "):
                break
            if in_ranges and line.startswith("- `p=["):
                try:
                    bracket = line.split("[")[1].split("]")[0]
                    parts = bracket.split(",")
                    p0 = int(parts[0].strip())
                    p1 = int(parts[1].strip())
                    ranges.append((p0, p1))
                except (IndexError, ValueError):
                    continue
        return ranges

    def is_range_covered(self, p_start: int, p_end: int,
                          scanned: List[Tuple[int, int]]) -> bool:
        """Check if [p_start, p_end] is fully covered."""
        for s0, s1 in scanned:
            if s0 <= p_start and s1 >= p_end:
                return True
        return False

    def load_ghost_loci(self) -> List[int]:
        """Load ghost loci from MEMORY.md."""
        loci = []
        if not self.memory_file.exists():
            return loci
        content = self.memory_file.read_text(encoding="utf-8")
        in_loci = False
        for line in content.splitlines():
            if line.strip().startswith("## Ghost Loci"):
                in_loci = True
                continue
            if in_loci and line.startswith("## "):
                break
            if in_loci and line.startswith("- `p="):
                try:
                    p = int(line.split("=")[1].split("`")[0])
                    loci.append(p)
                except (IndexError, ValueError):
                    continue
        return loci

    def save_session(self, p_start: int, p_end: int,
                      candidates: List[int], ghost_loci: List[int],
                      blocks_processed: int,
                      existing_ranges: Optional[List[Tuple[int, int]]] = None,
                      existing_loci: Optional[List[int]] = None) -> None:
        """Save session results to daily log and update MEMORY.md."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        daily_log = self.memory_dir / f"{today}.md"

        entry = f"\n### Session: p=[{p_start}, {p_end}]\n"
        entry += f"- **Timestamp**: {datetime.utcnow().isoformat()}Z\n"
        entry += f"- **Blocks processed**: {blocks_processed}\n"
        entry += f"- **Candidates found**: {len(candidates)}\n"
        if candidates:
            entry += f"- **Candidate list**: {candidates}\n"
        if ghost_loci:
            entry += f"- **Ghost loci**: {ghost_loci}\n"

        with open(daily_log, "a", encoding="utf-8") as f:
            if daily_log.stat().st_size == 0:
                f.write(f"# Mersenne Search Memory Log -- {today}\n")
            f.write(entry)

        # Merge ranges
        all_ranges = list(existing_ranges or [])
        all_ranges.append((p_start, p_end))
        all_ranges = self._merge_ranges(all_ranges)

        # Merge loci
        all_loci = sorted(set((existing_loci or []) + ghost_loci))

        self._update_memory_file(all_ranges, all_loci, candidates)

    def _merge_ranges(self, ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        if not ranges:
            return []
        sorted_r = sorted(ranges, key=lambda x: x[0])
        merged = [sorted_r[0]]
        for p0, p1 in sorted_r[1:]:
            if p0 <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], p1))
            else:
                merged.append((p0, p1))
        return merged

    def _update_memory_file(self, ranges: List[Tuple[int, int]],
                             ghost_loci: List[int],
                             recent_candidates: List[int]) -> None:
        total_coverage = sum(p1 - p0 for p0, p1 in ranges)
        lines = []
        lines.append("# Mersenne Search Memory\n\n")
        lines.append(f"> Last updated: {datetime.utcnow().isoformat()}Z\n\n")

        lines.append("## Summary\n\n")
        lines.append(f"- **Total p-coverage**: {total_coverage:,} exponents\n")
        lines.append(f"- **Ghost loci detected**: {len(ghost_loci)}\n")
        lines.append(f"- **Recent candidates**: {recent_candidates}\n\n")

        lines.append("## Scanned Ranges\n\n")
        for p0, p1 in ranges:
            lines.append(f"- `p=[{p0}, {p1}]`\n")
        lines.append("\n")

        lines.append("## Ghost Loci\n\n")
        for p in ghost_loci:
            lines.append(f"- `p={p}`\n")

        with open(self.memory_file, "w", encoding="utf-8") as f:
            f.writelines(lines)
