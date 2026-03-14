import sys
import os
import json
import time

# Ensure we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from research.mersenne.MERSENNE_PROBE_V1 import MersenneEngine

def test_single_candidate(p):
    engine = MersenneEngine()
    print(f"\n[ORACLE] Commencing TRUE Lucas-Lehmer Test for M_{p}...")
    start_time = time.time()
    
    is_prime, residue, dt, _ = engine.lucas_lehmer(p, checkpoint_cadence=5000)
    
    print(f"  -> Result: {'PRIME' if is_prime else 'COMPOSITE'} (dt={dt:.2f}s, Res: {str(residue)[:20]}...)")
    return is_prime, residue, dt

if __name__ == "__main__":
    print("==================================================")
    print(" GAHENAX REAL MERSENNE SEARCH (TARGET 100M+)")
    print(" WARNING: COMPUTATIONAL EXPENSE IS MASSIVE")
    print("==================================================")
    
    # We will test the very start of the 100M frontier. 
    # Testing a full block of 10 million exponents at M_100,000,000 running TRUE 
    # Lucas-Lehmer would take thousands of years on a single CPU.
    # We will test 3 hand-picked candidates at the 100M edge to prove the real calculation.
    
    candidates = [100000007, 100000037, 100000039]
    found_primes = []
    
    for p in candidates:
        is_p, res, dt = test_single_candidate(p)
        if is_p:
            found_primes.append(p)
    
    print("\n==================================================")
    print(" SEARCH COMPLETED")
    print(f" Primes Found: {found_primes}")
    print("==================================================")
