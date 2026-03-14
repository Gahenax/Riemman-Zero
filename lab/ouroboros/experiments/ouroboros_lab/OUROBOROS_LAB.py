#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OUROBOROS_LAB.py
================
Toy model of Governed Learning Systems.
Simulates the interaction between local optimization (Omega) and systemic heat (H).

Mechanics:
 dO/dt = alpha * O * (1 - O) - gamma * H
 dH/dt = beta * O - delta * H
"""

import argparse
import json
import os
import numpy as np

def simulate(alpha, beta, gamma, delta, steps, seed):
    np.random.seed(seed)
    
    # States: O (Omega - Optimization/Order), H (Heat/Entropy)
    o_val = 0.1
    h_val = 0.05
    
    o_history = []
    h_history = []
    
    # dt for numerical stability
    dt = 0.01
    inner_steps = int(steps / dt)
    
    # Recording interval to match the requested 'steps' output
    record_interval = int(1/dt)

    # Control run (no feedback: gamma = 0)
    o_ctrl = 0.1
    h_ctrl = 0.05
    o_ctrl_history = []
    
    for i in range(inner_steps):
        # Ouroboros dynamics
        do = (alpha * o_val * (1 - o_val) - gamma * h_val) * dt
        dh = (beta * o_val - delta * h_val) * dt
        
        o_val += do + np.random.normal(0, 0.001)
        h_val += dh
        
        # Clip to prevent negative/explosion in this simple toy model
        o_val = max(0, min(1.2, o_val))
        h_val = max(0, h_val)
        
        # Control dynamics (no governance)
        do_c = (alpha * o_ctrl * (1 - o_ctrl)) * dt # Normal logistic growth
        o_ctrl += do_c + np.random.normal(0, 0.001)
        o_ctrl = max(0, min(1.2, o_ctrl))

        if i % record_interval == 0:
            o_history.append(float(o_val))
            h_history.append(float(h_val))
            o_ctrl_history.append(float(o_ctrl))
            
    return np.array(o_history), np.array(h_history), np.array(o_ctrl_history)

def detect_cycle(data, threshold=0.1):
    """Simple autocorrelation-based cycle detection."""
    if len(data) < 100:
        return 0, False
    
    # Remove trend
    data_dt = data - np.mean(data)
    
    # Autocorrelation
    acf = np.correlate(data_dt, data_dt, mode='full')
    acf = acf[len(acf)//2:]
    acf /= acf[0]
    
    # Find first peak after lag 0
    peaks = []
    for i in range(1, len(acf)-1):
        if acf[i] > acf[i-1] and acf[i] > acf[i+1]:
            peaks.append((i, acf[i]))
    
    if not peaks:
        return 0, False
    
    first_peak_lag, first_peak_val = peaks[0]
    is_cycle = first_peak_val > threshold and first_peak_lag > 5
    
    return float(first_peak_val), is_cycle

def main():
    parser = argparse.ArgumentParser(description="Ouroboros Lab Experiment Runner")
    parser.add_argument("--alpha", type=float, default=0.5, help="Growth rate of optimization")
    parser.add_argument("--beta", type=float, default=0.1, help="Heat production rate")
    parser.add_argument("--gamma", type=float, default=1.2, help="Governance feedback strength")
    parser.add_argument("--delta", type=float, default=0.05, help="Heat dissipation rate")
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", type=str, required=True, help="Directory to save artifacts")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
        
    print(f"[OUROBOROS] Starting experiment with alpha={args.alpha}, gamma={args.gamma}, seed={args.seed}")
    
    omega, heat, control = simulate(args.alpha, args.beta, args.gamma, args.delta, args.steps, args.seed)
    
    # Detect Cycles
    peak_val, is_cycle = detect_cycle(omega)
    
    verdict = "RED"
    if is_cycle:
        verdict = "GREEN" if peak_val > 0.4 else "AMBER"
    
    # Save artifacts
    np.save(os.path.join(args.outdir, "omega_ouroboros.npy"), omega)
    np.save(os.path.join(args.outdir, "heat_ouroboros.npy"), heat)
    np.save(os.path.join(args.outdir, "omega_control.npy"), control)
    
    with open(os.path.join(args.outdir, "verdict.json"), "w") as f:
        json.dump({
            "verdict": verdict,
            "cycle_detection_score": float(peak_val),
            "is_cycle": bool(is_cycle),
            "summary": f"System state: {verdict}. Peak autocorrelation: {peak_val:.4f}"
        }, f, indent=2)
        
    with open(os.path.join(args.outdir, "params.json"), "w") as f:
        json.dump(vars(args), f, indent=2)
        
    print(f"[OUROBOROS] Experiment complete. Verdict: {verdict}")
    print(f"[OUROBOROS] Artifacts saved to {args.outdir}")

if __name__ == "__main__":
    main()
