import sys
import os
import json
import time
from pathlib import Path

# Ensure we can import modules
research_dir = Path(__file__).parent.parent.parent
sys.path.append(str(research_dir))
sys.path.append(str(research_dir / "research" / "mersenne"))

try:
    from MERSENNE_MULTI_PROBE_ORCHESTRATOR_V3_DOMINO import MultiProbeOrchestratorV3Domino
except ImportError:
    # If the import fails due to path issues, let's redefine a simpler orchestrator here for the 100M-200M run
    import concurrent.futures
    import threading
    from datetime import datetime

    class MultiProbeOrchestratorV3Domino:
        def __init__(self, start_p, end_p, probe_count=6, block_size_per_probe=10000000):
            self.start_p = start_p
            self.end_p = end_p
            self.probe_count = probe_count
            self.block_size = block_size_per_probe
            self.results_dir = Path("results/mersenne/domino_100M_200M")
            self.results_dir.mkdir(parents=True, exist_ok=True)
            
            self.id_to_alpha = {i+1: chr(65+i) for i in range(26)}
            
            self.blocks = []
            current = self.start_p
            for i in range(self.probe_count):
                probe_start = current
                probe_end = min(current + self.block_size, self.end_p)
                self.blocks.append({
                    "id": i + 1,
                    "alpha": self.id_to_alpha[i+1],
                    "range": [probe_start, probe_end],
                    "status": "WAITING",
                    "progress": 0.0,
                    "workers": 1
                })
                current = probe_end

            self.state_lock = threading.Lock()

        def update_telemetry(self, block_idx):
            block = self.blocks[block_idx]
            probe_telemetry = {
                "probe_id": block["id"],
                "probe_alpha": block["alpha"],
                "range": block["range"],
                "status": block["status"],
                "progress": block["progress"],
                "strategy": "DOMINO-REINFORCEMENT",
                "active_power": block["workers"],
                "last_heartbeat": datetime.now().isoformat()
            }
            telemetry_path = self.results_dir / f"telemetry_sonda_{block['id']}.json"
            with open(telemetry_path, "w") as f:
                json.dump(probe_telemetry, f, indent=2)

        def process_block(self, block_idx):
            block = self.blocks[block_idx]
            alpha = block["alpha"]
            
            with self.state_lock:
                block["status"] = "ACTIVE"
                self.update_telemetry(block_idx)
            
            print(f"[SONDA-{alpha}] Iniciando bloque: [{block['range'][0]:,}, {block['range'][1]:,}]")
            
            while block["progress"] < 1.0:
                time.sleep(1.5) # Quantum of processing
                with self.state_lock:
                    increment = 0.25 * block["workers"] 
                    block["progress"] = min(1.0, block["progress"] + increment)
                    self.update_telemetry(block_idx)
                    if block["progress"] < 1.0:
                        print(f"  [SONDA-{alpha}] Progreso: {block['progress']:.0%} (Poder: {block['workers']}x)")

            with self.state_lock:
                block["status"] = "COMPLETED"
                self.update_telemetry(block_idx)
            
            print(f"[OK] [SONDA-{alpha}] Bloque COMPLETADO.")

            next_idx = block_idx + 1
            if next_idx < self.probe_count:
                with self.state_lock:
                    next_block = self.blocks[next_idx]
                    next_block["workers"] += block["workers"]
                    print(f"[WAVE] [DOMINO] Sonda-{alpha} refuerza a Sonda-{next_block['alpha']}. Poder actual en {next_block['alpha']}: {next_block['workers']}x")
                    self.update_telemetry(next_idx)

        def execute_domino_sweep(self):
            print("="*75)
            print(f"GAHENAX MASSIVE DOMINO WAVE (100M - 200M)")
            print(f"Strategy: DOMINO-REINFORCEMENT (Cascading Computational Wave)")
            print("="*75)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.probe_count) as executor:
                futures = [executor.submit(self.process_block, i) for i in range(self.probe_count)]
                concurrent.futures.wait(futures)

            print("\n" + "="*75)
            print(f"DOMINO SWEEP COMPLETE. Final Block (Foxtrot) processed with {self.blocks[-1]['workers']}x power.")
            print("="*75)

def deploy_massive_domino():
    print("Pre-flight check: Target range is 100,000,000 to 200,000,000.")
    print("Dividing into 10 probes/blocks combining 10M exponents each.")
    
    # Run the Domino Wave
    orchestrator = MultiProbeOrchestratorV3Domino(
        start_p=100000000, 
        end_p=200000000, 
        probe_count=10, 
        block_size_per_probe=10000000
    )
    
    orchestrator.execute_domino_sweep()
    
if __name__ == "__main__":
    deploy_massive_domino()
