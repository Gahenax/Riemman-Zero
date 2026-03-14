import subprocess
import json
import os

def sweep():
    alphas = [0.5, 1.0, 1.5]
    gammas = [0.2, 0.5, 1.0, 2.0]
    betas = [0.1, 0.5, 1.0]
    deltas = [0.05, 0.1, 0.2]
    
    for a in alphas:
        for g in gammas:
            for b in betas:
                for d in deltas:
                    outdir = f"results/sweep/a{a}_g{g}_b{b}_d{d}"
                    cmd = [
                        "python", "experiments/ouroboros_lab/OUROBOROS_LAB.py",
                        "--alpha", str(a),
                        "--gamma", str(g),
                        "--beta", str(b),
                        "--delta", str(d),
                        "--steps", "2000",
                        "--outdir", outdir
                    ]
                    subprocess.run(cmd, capture_output=True)
                    
                    v_path = os.path.join(outdir, "verdict.json")
                    if os.path.exists(v_path):
                        with open(v_path) as f:
                            res = json.load(f)
                            if res["verdict"] in ["GREEN", "AMBER"]:
                                print(f"FOUND {res['verdict']}: alpha={a}, gamma={g}, beta={b}, delta={d} score={res['cycle_detection_score']}")
                                return
    print("No cycle found in sweep")

if __name__ == "__main__":
    sweep()
