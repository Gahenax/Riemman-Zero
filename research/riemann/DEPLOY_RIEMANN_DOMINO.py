import sys
import os

# Ensure we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from research.riemann.riemann_domino_wave import RiemannDominoOrchestrator

def deploy_riemann_wave():
    print("==================================================")
    print(" GAHEANX RIEMANN DOMINO WAVE DEPLOYMENT")
    print("==================================================")
    print("Target Range: T = [5000.0, 5050.0]")
    
    orch = RiemannDominoOrchestrator(
        t_start=5000.0,
        t_end=5050.0,
        probe_names=["ALPHA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT"],
        band_width=5.0, # 10 bands of width 5
        out_dir="./ledger_domino_riemann_extended",
        cfg={"alpha": 0.5}
    )
    
    summary = orch.run_sweep()
    print("==================================================")
    print(f" DOMINO SWEEP COMPLETE")
    print(f" Status: {summary['status']}")
    print(f" Bands Processed: {summary['bands_processed']}")
    print(f" Total Zeros Bracketed: {summary['total_zeros']}")
    print("==================================================")

if __name__ == "__main__":
    deploy_riemann_wave()
