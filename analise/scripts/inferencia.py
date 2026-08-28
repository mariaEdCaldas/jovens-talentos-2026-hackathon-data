# -*- coding: utf-8 -*-
"""
inferencia.py — Bootstrap por cluster (anúncio), duas amostras independentes.
Calcula R, IC95(R), half, e a distribuição da diferença Δ=ln(Ri/Rj) para pares.
Correção de múltiplas comparações via Benjamini-Hochberg (FDR).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from scipy.stats import false_discovery_control

from common_p1p2 import boot_ratio
from config import B_BOOTSTRAP, SEED


def ic_ratio_log(d_vals, Vpos, B=B_BOOTSTRAP, seed=SEED):
    """IC95 da razão (escala log) re-exponenciado; retorna R, half, (lo, hi)."""
    return boot_ratio(d_vals, Vpos, B=B, seed=seed)


def delta_boot(d_i, V_i, d_j, V_j, B=B_BOOTSTRAP, seed=SEED):
    """Distribuição bootstrap de Δ = ln(Ri) − ln(Rj), reamostrando clusters de cada
    amostra de forma independente. Retorna médianas e p-valor unilateral."""
    rng = np.random.default_rng(seed)
    n1, m1 = len(d_i), len(V_i)
    n2, m2 = len(d_j), len(V_j)
    if n1 == 0 or m1 == 0 or n2 == 0 or m2 == 0:
        return None
    d_i = np.asarray(d_i, float); V_i = np.asarray(V_i, float)
    d_j = np.asarray(d_j, float); V_j = np.asarray(V_j, float)
    id1 = rng.integers(0, n1, size=(B, n1))
    iv1 = rng.integers(0, m1, size=(B, m1))
    id2 = rng.integers(0, n2, size=(B, n2))
    iv2 = rng.integers(0, m2, size=(B, m2))
    with np.errstate(divide="ignore", invalid="ignore"):
        lr_i = np.log(np.median(d_i[id1], axis=1)) - np.log(np.median(V_i[iv1], axis=1))
        lr_j = np.log(np.median(d_j[id2], axis=1)) - np.log(np.median(V_j[iv2], axis=1))
    delta = lr_i - lr_j
    med_delta = np.median(delta)
    lo, hi = np.percentile(delta, [2.5, 97.5])
    p_gt = float((delta > 0).mean())           # P(Δ>0)
    p_lt = 1 - p_gt                            # P(Δ<0)
    p_2s = 2 * min(p_gt, p_lt)                 # p bilateral aproximado
    return {"med_delta": med_delta, "lo": lo, "hi": hi,
            "p_gt": p_gt, "p_lt": p_lt, "p_2s": max(p_2s, 1e-12)}


def fdr_qs(pvals):
    """Aplica Benjamini-Hochberg; retorna q-valores na mesma ordem."""
    p = np.asarray(pvals, float)
    return false_discovery_control(p, method="bh")