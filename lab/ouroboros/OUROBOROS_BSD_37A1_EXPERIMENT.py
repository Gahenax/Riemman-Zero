#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OUROBOROS_BSD_37A1_EXPERIMENT.py
================================
End-to-end BSD bridge test for Cremona 37a1:
    y^2 + y = x^3 - x

Goal:
  Compute geometric target Q_geo = Omega * R * (Sha * prod c_p / tors^2)
  and analytic value L'(1) via a_n and a smoothed series.

Outputs:
  - Omega^+ (identity component), Omega_total = 2*Omega^+ (two real components)
  - R = canonical (Néron-Tate) height of generator P
  - Q_geo using Omega_total (default)
  - L'(1)
  - abs / rel error
  - optional PSLQ certificate for L'(1) / Q_geo

This is a "guerrilla" experiment: no Sage/Magma.
"""

import argparse
from dataclasses import dataclass
from fractions import Fraction
from math import log
import mpmath as mp

# ----------------------------
# Curve: 37a1
# Original: y^2 + y = x^3 - x
# Short model via y' = y + 1/2:
#   (y')^2 = x^3 - x + 1/4
# ----------------------------

A = Fraction(-1, 1)
B = Fraction(1, 4)
N_CONDUCTOR = 37

@dataclass(frozen=True)
class RPoint:
    x: Fraction
    y: Fraction
    inf: bool = False

O = RPoint(Fraction(0), Fraction(0), True)

def on_curve(P: RPoint) -> bool:
    if P.inf:
        return True
    return P.y * P.y == P.x * P.x * P.x + A * P.x + B

def add(P: RPoint, Q: RPoint) -> RPoint:
    """Exact group law on y^2 = x^3 + A x + B over Q."""
    if P.inf: return Q
    if Q.inf: return P

    if P.x == Q.x:
        if P.y == -Q.y:
            return O
        lam = (3 * P.x * P.x + A) / (2 * P.y)
    else:
        lam = (Q.y - P.y) / (Q.x - P.x)

    x3 = lam * lam - P.x - Q.x
    y3 = lam * (P.x - x3) - P.y
    return RPoint(x3, y3, False)

def mul(P: RPoint, k: int) -> RPoint:
    """Double-and-add."""
    R = O
    Bp = P
    kk = k
    while kk > 0:
        if kk & 1:
            R = add(R, Bp)
        Bp = add(Bp, Bp)
        kk >>= 1
    return R

def log_height_x(x: Fraction) -> float:
    """Logarithmic naive height of rational x."""
    if x == 0:
        return 0.0
    return log(max(abs(x.numerator), abs(x.denominator)))

def canonical_height(P: RPoint, nmax: int = 10) -> float:
    """
    Canonical height:
      hhat(P) = lim_{n} h(x(2^n P)) / 4^n
    Exact group arithmetic; float only at final log.
    """
    Q = P
    val = 0.0
    for n in range(1, nmax + 1):
        Q = add(Q, Q)  # 2^n P
        val = log_height_x(Q.x) / (4**n)
    return val

def real_period_Omega_plus() -> mp.mpf:
    """
    Omega^+ = 2 * ∫_{e1..∞} dx / sqrt(4x^3 - 4x + 1)
    """
    roots = mp.polyroots([4, 0, -4, 1])  # 4x^3 - 4x + 1
    reals = sorted([mp.re(r) for r in roots])
    e1 = reals[2]  # largest real root
    f = lambda x: 1 / mp.sqrt(4*x**3 - 4*x + 1)
    return 2 * mp.quad(f, [e1, mp.inf])

# ----------------------------
# Analytic side: a_n and L'(1)
# ----------------------------

def count_points_bruteforce(p: int) -> int:
    """Affine count for y^2 + y = x^3 - x mod p (safe for p=2)."""
    cnt = 0
    for x in range(p):
        rhs = (x*x*x - x) % p
        for y in range(p):
            if (y*y + y - rhs) % p == 0:
                cnt += 1
    return cnt

def count_points_legendre(p: int) -> int:
    """
    For odd p, use:
      (2y+1)^2 = 4x^3 - 4x + 1
    For each x: #solutions in y is 1 + (rhs|p).
    """
    cnt = 0
    for x in range(p):
        rhs = (4 * pow(x, 3, p) - 4 * x + 1) % p
        leg = pow(rhs, (p - 1)//2, p)  # 0,1,p-1
        if leg == p - 1:
            leg = -1
        cnt += 1 + leg
    return cnt

def ap_for_prime(p: int) -> int:
    """
    a_p = p + 1 - #E(F_p) = p - N_aff
    For 37a1:
      - p=2 needs brute force (Legendre invalid)
      - p=37 is bad multiplicative; take a_37 = -1
    """
    if p == 2:
        N_aff = count_points_bruteforce(2)
        return p - N_aff  # should be -2
    if p == N_CONDUCTOR:
        return -1
    N_aff = count_points_legendre(p)
    return p - N_aff

def primes_up_to(n: int):
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            sieve[i*i:n+1:i] = [False] * (((n - i*i) // i) + 1)
    return [i for i, v in enumerate(sieve) if v]

def spf_sieve(n: int):
    """Smallest prime factor sieve."""
    spf = list(range(n + 1))
    for i in range(2, int(n**0.5) + 1):
        if spf[i] == i:
            for j in range(i*i, n + 1, i):
                if spf[j] == j:
                    spf[j] = i
    return spf

def generate_an(limit_n: int):
    """
    Build a_n for n<=limit_n using SPF decomposition and Hecke recursion.

    If n = p*m with p = spf[n]:
      - if p∤m: a_n = a_p * a_m
      - else:
          good p: a_n = a_p a_m - p a_{m/p}
          bad p=37: a_n = a_p a_m
    """
    spf = spf_sieve(limit_n)
    ap = {p: ap_for_prime(p) for p in primes_up_to(limit_n)}

    an = [0] * (limit_n + 1)
    an[1] = 1
    for n in range(2, limit_n + 1):
        p = spf[n]
        m = n // p
        if m % p != 0:
            an[n] = an[m] * ap[p]
        else:
            if p == N_CONDUCTOR:
                an[n] = ap[p] * an[m]
            else:
                an[n] = ap[p] * an[m] - p * an[m // p]
    return an

def compute_Lprime_1(an, conductor: int) -> mp.mpf:
    """
    L'(1) = 2 * Σ (a_n/n) * E1(2π n / √N)
    with E1(x)=expint(1,x).
    """
    sqrtN = mp.sqrt(conductor)
    factor = 2 * mp.pi / sqrtN
    s = mp.mpf("0")
    for n in range(1, len(an)):
        a = an[n]
        if a == 0:
            continue
        x = factor * n
        s += mp.mpf(a) / n * mp.expint(1, x)
    return 2 * s

# ----------------------------
# Orchestration (Ouroboros)
# ----------------------------

def run(args):
    mp.mp.dps = args.dps

    print("=== OUROBOROS EXPERIMENT: ELLIPTIC BRIDGE (37a1) ===")
    print(f"[cfg] dps={args.dps}  terms={args.terms}  height_iters={args.height_iters}")
    print()

    # --- GEOMETRY ---
    print("[GEOM] Computing Omega^+ ...")
    Omega_plus = real_period_Omega_plus()
    Omega_total = 2 * Omega_plus  # discriminant > 0 => two real components

    # Generator: original (0,0) -> short model (0, 1/2)
    P = RPoint(Fraction(0), Fraction(1, 2))
    if not on_curve(P):
        raise RuntimeError("Generator not on short model curve (should never happen).")

    print("[GEOM] Computing regulator R = hhat(P) ...")
    R = canonical_height(P, nmax=args.height_iters)

    # Finite invariants (known for 37a1; keep exposed for experiments)
    sha = mp.mpf(args.sha)
    tamagawa = mp.mpf(args.tamagawa)
    tors = mp.mpf(args.torsion)

    Q_geo = (Omega_total * mp.mpf(R) * sha * tamagawa) / (tors**2)

    print(f"Omega^+        = {Omega_plus}")
    print(f"Omega_total    = {Omega_total}")
    print(f"Regulator R    = {mp.mpf(R)}")
    print(f"Q_geo (target) = {Q_geo}")
    print()

    # --- ANALYTIC ---
    print("[AN] Generating a_n (Hecke) ...")
    an = generate_an(args.terms)

    if args.sanity:
        print("[AN] sanity a_n[1..12] =", an[:13])
        print("[AN] expected: a2=-2, a3=-3, a4=2, a5=-2, a6=6, a7=-1 (for 37a1)")
        print()

    print("[AN] Summing smoothed series for L'(1) ...")
    Lp = compute_Lprime_1(an, N_CONDUCTOR)
    print(f"L'(1)          = {Lp}")
    print()

    # --- BRIDGE VERDICT ---
    abs_err = mp.fabs(Lp - Q_geo)
    rel_err = abs_err / mp.fabs(Q_geo) if Q_geo != 0 else mp.inf

    print("=== BRIDGE CHECK ===")
    print(f"abs_err = {abs_err}")
    print(f"rel_err = {rel_err}")

    ok = abs_err < mp.mpf(args.tol)
    print(f"veredict = {'MISSION PASSED [OK]' if ok else 'MISSION FAILED [ERR]'}  (tol={args.tol})")
    print()

    # --- OPTIONAL PSLQ CERTIFICATE ---
    if args.pslq:
        print("[CERT] PSLQ attempt for ratio L'(1)/Q_geo ...")
        ratio = Lp / Q_geo
        # search a small rational relation: ratio ~ p/q
        # PSLQ expects list [ratio, 1] so that a*ratio + b = 0 => ratio = -b/a
        rel = mp.pslq([ratio, mp.mpf(1)], maxcoeff=args.maxcoeff)
        if rel is None:
            print("[CERT] PSLQ: no relation found within maxcoeff.")
        else:
            a, b = rel
            if a != 0:
                rat = -mp.mpf(b) / mp.mpf(a)
                print(f"[CERT] relation: {a}*ratio + {b} = 0  => ratio ≈ {rat}")
            else:
                print("[CERT] PSLQ returned degenerate relation (a=0).")
        print()

    # compact return for orchestration
    return {
        "Omega_plus": Omega_plus,
        "Omega_total": Omega_total,
        "R": mp.mpf(R),
        "Q_geo": Q_geo,
        "Lprime1": Lp,
        "abs_err": abs_err,
        "rel_err": rel_err,
        "passed": bool(ok),
    }

def build_parser():
    p = argparse.ArgumentParser(description="Ouroboros BSD experiment for 37a1 (no CAS).")
    p.add_argument("--dps", type=int, default=80, help="mpmath decimal precision")
    p.add_argument("--terms", type=int, default=5000, help="max n for a_n and series sum")
    p.add_argument("--height-iters", dest="height_iters", type=int, default=10, help="iterations for canonical height limit (2^n)")
    p.add_argument("--sha", type=str, default="1", help="assumed |Sha|")
    p.add_argument("--tamagawa", type=str, default="1", help="assumed product of Tamagawa numbers")
    p.add_argument("--torsion", type=str, default="1", help="torsion order |E_tors|")
    p.add_argument("--tol", type=str, default="1e-18", help="absolute tolerance for bridge check")
    p.add_argument("--sanity", action="store_true", help="print a_n sanity block")
    p.add_argument("--pslq", action="store_true", help="attempt PSLQ rationality certificate for ratio")
    p.add_argument("--maxcoeff", type=int, default=50, help="PSLQ max coefficient")
    return p

if __name__ == "__main__":
    args = build_parser().parse_args()
    run(args)
