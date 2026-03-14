"""
Spectral Camouflage Gate (ported from P-ATLAS-NP Gate 6).
Validates that discovered Riemann zeros match the expected GUE spacing distribution
using the Kolmogorov-Smirnov test against a reference dataset or GUE theoretical CDF.
"""
import math
import numpy as np
from typing import List, Dict, Any, Optional


def riemann_smooth_N(t: float) -> float:
    """Smooth counting function N(t) for the Riemann zeta zeros."""
    if t <= 0:
        return 0.0
    return (t / (2 * math.pi)) * math.log(t / (2 * math.pi)) - (t / (2 * math.pi)) + 7 / 8


def unfold_zeros(zeros: List[float]) -> np.ndarray:
    """Unfold zeros using the smooth counting function N(t)."""
    return np.array([riemann_smooth_N(t) for t in sorted(zeros)])


def normalized_spacings(zeros: List[float]) -> np.ndarray:
    """Compute normalized spacings from a list of zeros."""
    if len(zeros) < 3:
        return np.array([])
    unfolded = unfold_zeros(zeros)
    gaps = np.diff(unfolded)
    mean_gap = np.mean(gaps)
    if mean_gap < 1e-12:
        return np.array([])
    return gaps / mean_gap


def wigner_surmise_cdf(s: np.ndarray) -> np.ndarray:
    """GUE Wigner surmise CDF: P(S < s) = 1 - exp(-4s^2/pi)."""
    return 1.0 - np.exp(-4.0 * s ** 2 / math.pi)


class SpectralCamouflageGate:
    """
    Validates discovered zeros against the expected GUE spacing distribution.

    Two modes:
    1. Compare against Wigner surmise CDF (default, no reference data needed).
    2. Compare against a reference dataset of known zeros (if provided).
    """

    def __init__(self, ks_threshold: float = 0.1):
        self.ks_threshold = ks_threshold

    def validate(self, discovered_zeros: List[float],
                 reference_zeros: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Run the spectral camouflage gate.

        Returns:
            Dict with keys: status (PASS/FAIL/INCONCLUSIVE), ks_statistic, p_value, details
        """
        spacings = normalized_spacings(discovered_zeros)

        if len(spacings) < 10:
            return {
                "status": "INCONCLUSIVE",
                "ks_statistic": 0.0,
                "p_value": 1.0,
                "details": f"Insufficient data: only {len(spacings)} spacings (need >= 10)"
            }

        if reference_zeros is not None and len(reference_zeros) >= 10:
            # Mode 2: Compare against reference zeros
            ref_spacings = normalized_spacings(reference_zeros)
            from scipy.stats import ks_2samp
            ks_stat, p_value = ks_2samp(spacings, ref_spacings)
            mode = "reference_comparison"
        else:
            # Mode 1: Compare against Wigner surmise CDF
            sorted_s = np.sort(spacings)
            empirical_cdf = np.arange(1, len(sorted_s) + 1) / len(sorted_s)
            theoretical_cdf = wigner_surmise_cdf(sorted_s)
            ks_stat = float(np.max(np.abs(empirical_cdf - theoretical_cdf)))

            # Approximate p-value using Kolmogorov distribution
            n = len(sorted_s)
            lambda_ks = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * ks_stat
            # Kolmogorov asymptotic formula
            p_value = max(0.0, 2.0 * sum(
                (-1) ** (k - 1) * math.exp(-2 * k ** 2 * lambda_ks ** 2)
                for k in range(1, 101)
            ))
            mode = "wigner_surmise"

        # GUE alignment: compute <r> statistic
        r_stats = []
        for i in range(len(spacings) - 1):
            s_i, s_next = spacings[i], spacings[i + 1]
            if max(s_i, s_next) > 1e-12:
                r_stats.append(min(s_i, s_next) / max(s_i, s_next))
        mean_r = float(np.mean(r_stats)) if r_stats else 0.0

        status = "PASS" if ks_stat <= self.ks_threshold else "FAIL"

        return {
            "status": status,
            "ks_statistic": round(ks_stat, 6),
            "p_value": round(p_value, 6),
            "mean_r": round(mean_r, 5),
            "gue_r_target": 0.5996,
            "r_deviation": round(abs(mean_r - 0.5996), 5),
            "mode": mode,
            "n_spacings": len(spacings),
            "details": f"KS={ks_stat:.4f} (threshold={self.ks_threshold}), <r>={mean_r:.5f} (GUE=0.5996), mode={mode}"
        }
