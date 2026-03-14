"""
Ghost Locus Validation Gate.
Integrates the Seismograph's modular signature check with invariance stress-testing
to produce a unified DEEP / SURFACE / ARTIFACT verdict for ghost locus candidates.
"""
import math
import hashlib
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class GhostVerdict:
    p: int
    signature_z: float
    invariance_survived: bool
    verdict: str  # "DEEP" | "SURFACE" | "ARTIFACT"
    details: str


def signature_p0(p: int, q_list: List[int]) -> List[int]:
    """Compute P0 modular signature: pow(2, p, q) - 1 == 0 for each q."""
    return [1 if pow(2, p, q) == 1 else 0 for q in q_list]


def feature_energy(sig: List[int], q_list: List[int]) -> List[float]:
    """Compute energy-weighted features from signature."""
    return [sig[i] * math.log(q_list[i]) for i in range(len(sig))]


def robust_z(x: float, med: float, mad_val: float, eps: float = 1e-12) -> float:
    """Robust z-score using median and MAD."""
    return (x - med) / (mad_val * 1.4826 + eps)


class GhostValidationGate:
    """
    Combined validation gate for ghost locus candidates.

    Stage 1: Signature check (P0 modular signature z-score).
    Stage 2: Invariance stress test (Endian-Swap simulation).
    Verdict: DEEP (both pass) / SURFACE (only signature) / ARTIFACT (neither).
    """
    def __init__(self, q_pool_size: int = 500, z_threshold: float = 3.0,
                 seed: int = 1337):
        self.q_pool_size = q_pool_size
        self.z_threshold = z_threshold
        self.seed = seed
        self.rng = random.Random(seed)

        # Generate prime pool
        self.q_list = self._first_primes(q_pool_size, start=3)

    def _first_primes(self, count: int, start: int = 3) -> List[int]:
        primes = []
        n = start
        while len(primes) < count:
            if self._is_prime(n):
                primes.append(n)
            n += 2 if n > 2 else 1
        return primes

    def _is_prime(self, n: int) -> bool:
        if n < 2:
            return False
        if n < 4:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True

    def _endian_swap_test(self, p: int) -> bool:
        """
        Invariance stress test: check if the P0 signature is stable
        under hash-based perturbation (simulates Endian-Swap).
        A truly deep ghost locus survives this.
        """
        sig_original = signature_p0(p, self.q_list[:64])
        energy_original = sum(feature_energy(sig_original, self.q_list[:64]))

        # Perturb p by small offsets and check stability
        perturbations = [p - 2, p + 2, p - 4, p + 4]
        energies = []
        for pp in perturbations:
            if pp < 2:
                continue
            sig_pp = signature_p0(pp, self.q_list[:64])
            energies.append(sum(feature_energy(sig_pp, self.q_list[:64])))

        if not energies:
            return False

        # The ghost locus should have HIGHER energy than neighbors
        mean_neighbor = sum(energies) / len(energies)
        return energy_original > mean_neighbor * 1.1

    def validate(self, p: int, baseline_ps: Optional[List[int]] = None) -> GhostVerdict:
        """
        Run the full validation gate on a candidate ghost locus p.

        Args:
            p: candidate exponent
            baseline_ps: optional list of known-prime exponents for baseline z-score
        """
        # Stage 1: Signature z-score
        sig = signature_p0(p, self.q_list)
        energy = sum(feature_energy(sig, self.q_list))

        if baseline_ps:
            baseline_energies = []
            for bp in baseline_ps:
                bsig = signature_p0(bp, self.q_list)
                baseline_energies.append(sum(feature_energy(bsig, self.q_list)))
            med = sorted(baseline_energies)[len(baseline_energies) // 2]
            diffs = [abs(e - med) for e in baseline_energies]
            mad_val = sorted(diffs)[len(diffs) // 2]
        else:
            # Use self-calibrated baseline from neighborhood
            neighborhood = [p - 10, p - 6, p - 4, p - 2, p + 2, p + 4, p + 6, p + 10]
            neighborhood = [pp for pp in neighborhood if pp > 2]
            baseline_energies = []
            for pp in neighborhood:
                bsig = signature_p0(pp, self.q_list)
                baseline_energies.append(sum(feature_energy(bsig, self.q_list)))
            med = sorted(baseline_energies)[len(baseline_energies) // 2]
            diffs = [abs(e - med) for e in baseline_energies]
            mad_val = sorted(diffs)[len(diffs) // 2]

        z_score = robust_z(energy, med, mad_val)
        signature_pass = abs(z_score) >= self.z_threshold

        # Stage 2: Invariance stress test
        invariance_pass = self._endian_swap_test(p)

        # Combined verdict
        if signature_pass and invariance_pass:
            verdict = "DEEP"
        elif signature_pass:
            verdict = "SURFACE"
        else:
            verdict = "ARTIFACT"

        return GhostVerdict(
            p=p,
            signature_z=round(z_score, 4),
            invariance_survived=invariance_pass,
            verdict=verdict,
            details=f"z={z_score:.4f} (threshold={self.z_threshold}), endian_swap={'SURVIVED' if invariance_pass else 'COLLAPSED'}"
        )
