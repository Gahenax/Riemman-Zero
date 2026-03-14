"""
Campaign Dashboard Generator.
Consolidates telemetry from all Mersenne probes, heartbeats, and evidence files
into a single DASHBOARD.md for real-time campaign visibility.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class CampaignDashboard:
    """
    Reads telemetry sources and produces a unified DASHBOARD.md.
    """
    def __init__(self, results_dir: str = "results/mersenne",
                 output_path: str = "DASHBOARD.md"):
        self.results_dir = Path(results_dir)
        self.output_path = Path(output_path)

    def _load_heartbeat(self) -> Optional[Dict[str, Any]]:
        hb = Path("heartbeat.json")
        if hb.exists():
            try:
                with open(hb, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return None

    def _load_probe_telemetry(self) -> List[Dict[str, Any]]:
        probes = []
        probe_dir = self.results_dir / "multi_probe"
        if not probe_dir.exists():
            return probes
        for f in sorted(probe_dir.glob("telemetry_sonda_*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    probes.append(json.load(fh))
            except (json.JSONDecodeError, OSError):
                continue
        return probes

    def _load_evidence_files(self) -> List[Dict[str, Any]]:
        evidence = []
        for f in sorted(Path(".").glob("evidence_p*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    evidence.append(json.load(fh))
            except (json.JSONDecodeError, OSError):
                continue
        return evidence

    def _load_memory(self) -> Optional[str]:
        mem = Path("research/mersenne/MEMORY.md")
        if mem.exists():
            return mem.read_text(encoding="utf-8")
        return None

    def generate(self) -> str:
        """Generate DASHBOARD.md and return its content."""
        heartbeat = self._load_heartbeat()
        probes = self._load_probe_telemetry()
        evidence = self._load_evidence_files()

        lines = []
        lines.append("# Mersenne Campaign Dashboard\n\n")
        lines.append(f"> Generated: {datetime.utcnow().isoformat()}Z\n\n")

        # System Status
        lines.append("## System Status\n\n")
        if heartbeat:
            lines.append(f"- **Status**: {heartbeat.get('status', 'UNKNOWN')}\n")
            lines.append(f"- **Active Workers**: {heartbeat.get('active_workers', 'N/A')}\n")
            lines.append(f"- **Last p Processed**: {heartbeat.get('last_p_processed', 'N/A')}\n")
            lines.append(f"- **Heartbeat**: {heartbeat.get('timestamp', 'N/A')}\n")
        else:
            lines.append("- **Status**: NO HEARTBEAT DETECTED\n")
        lines.append("\n")

        # Probe Status
        if probes:
            lines.append("## Probe Status\n\n")
            lines.append("| Probe | Range | Status | Progress | Power |\n")
            lines.append("|---|---|---|---|---|\n")
            for p in probes:
                alpha = p.get("probe_alpha", "?")
                r = p.get("range", [0, 0])
                status = p.get("status", "?")
                progress = p.get("progress", 0)
                power = p.get("active_power", 1)
                lines.append(f"| {alpha} | {r[0]:,}-{r[1]:,} | {status} | {progress:.0%} | {power}x |\n")
            lines.append("\n")

        # Evidence / Candidates
        if evidence:
            lines.append("## Verified Candidates\n\n")
            lines.append("| p | Status | Roundoff | Wall Time |\n")
            lines.append("|---|---|---|---|\n")
            for e in evidence:
                p = e.get("p", "?")
                status = e.get("status", "?")
                ro = e.get("roundoff_max", 0)
                wt = e.get("wall_time", 0)
                lines.append(f"| {p} | {status} | {ro:.3f} | {wt:.2f}s |\n")
            lines.append("\n")

        # Summary
        lines.append("## Summary\n\n")
        lines.append(f"- **Total probes**: {len(probes)}\n")
        lines.append(f"- **Total evidence files**: {len(evidence)}\n")
        active = sum(1 for p in probes if p.get("status") == "ACTIVE")
        completed = sum(1 for p in probes if p.get("status") == "COMPLETED")
        lines.append(f"- **Active probes**: {active}\n")
        lines.append(f"- **Completed probes**: {completed}\n")

        content = "".join(lines)
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return content


if __name__ == "__main__":
    dash = CampaignDashboard()
    content = dash.generate()
    print(content)
