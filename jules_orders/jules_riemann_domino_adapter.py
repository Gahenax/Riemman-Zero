import sys
import os
# Setup relative src config loading for subdirectories
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import src.config


import os
import sys
from pathlib import Path

# Jules Environment Configuration
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
JULES_PLAYGROUND = Path(str(src.config.ENGINE_ROOT))
sys.path.append(str(JULES_PLAYGROUND))
sys.path.append(str(JULES_PLAYGROUND / "core"))

# Import our local orchestrator
from riemann_domino_wave import RiemannDominoOrchestrator

def run_jules_domino_cascade(t0, t1, probes=6):
    print("="*60)
    print("JULES DOMINO-WAVE: CASCADING RIEMANN MINER")
    print(f"Goal: T=[{t0}, {t1}] | Strategy: Reinforced Cascade")
    print("="*60)
    
    # We use the names from our nomenclature
    probe_names = ["ALPHA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT"][:probes]
    
    orch = RiemannDominoOrchestrator(
        t_start=t0,
        t_end=t1,
        probe_names=probe_names,
        band_width=100.0,
        out_dir="./ledger_domino_10k",
        cfg={"alpha": 0.05} # High precision for Jules
    )
    
    summary = orch.run_sweep()
    
    print("\n" + "="*60)
    print(f"DONE. JULES CASCADE COMPLETE. Total Zeros Certified: {summary['total_zeros']}")
    print("="*60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--t0", type=float, required=True)
    parser.add_argument("--t1", type=float, required=True)
    args = parser.parse_args()
    
    run_jules_domino_cascade(args.t0, args.t1)
