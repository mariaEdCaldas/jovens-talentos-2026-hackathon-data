# -*- coding: utf-8 -*-
"""
comparacao.py — Comparação pareada entre células elegíveis.
Dominância i sobre j se: med_delta ≥ Δ_min e IC95(Δ) exclui 0 e P(Δ>0) ≥ 0.975 (ou
o simétrico) e q-FDR ≤ 0.05. Gera grafo de dominância e classifica células.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from inferencia import delta_boot, fdr_qs
from config import DELTA_MIN_LOG, P_UMBIAR_DOM, QUI_FDR, SEED


def _par(chave_i, chave_j):
    return (chave_i, chave_j) if chave_i < chave_j else (chave_j, chave_i)


def comparar_pares(celulas_elegiveis):
    """celulas_elegiveis: lista de dicts com chave, d_vals, Vpos.
    Retorna dict: mat (dict par->result), dominacao (set de pares (i,j) com i domina j)."""
    # d_vals precisa estar presente - garantir que foi adicionado na montagem
    n = len(celulas_elegiveis)
    pares = {}
    for a in range(n):
        for b in range(a + 1, n):
            ca, cb = celulas_elegiveis[a], celulas_elegiveis[b]
            r = delta_boot(ca["d_vals"], ca["Vpos"], cb["d_vals"], cb["Vpos"],
                           seed=SEED)
            if r is not None:
                pares[(ca["chave"], cb["chave"])] = r

    # FDR sobre os p bilaterais dos pares
    keys = list(pares.keys())
    pvals = [pares[k]["p_2s"] for k in keys]
    qvals = fdr_qs(pvals) if pvals else []
    for k, q in zip(keys, qvals):
        pares[k]["q"] = float(q)

    dominacao = []  # (chave_i, chave_j) => i domina j
    for k in keys:
        r = pares[k]
        i, j = k
        if r["q"] > QUI_FDR:
            continue
        if abs(r["med_delta"]) < DELTA_MIN_LOG:
            continue
        if r["lo"] > 0 and r["p_gt"] >= P_UMBIAR_DOM:
            dominacao.append((i, j))
        elif r["hi"] < 0 and r["p_lt"] >= P_UMBIAR_DOM:
            dominacao.append((j, i))

    # classes
    dominado = {x for _, x in dominacao}          # quem é dominado por alguém
    nao_dominado = {c["chave"] for c in celulas_elegiveis} - dominado
    possui_acao = {i for i, _ in dominacao}       # quem domina ao menos um

    prioritarias = [c for c in celulas_elegiveis if c["chave"] in nao_dominado
                    and c["chave"] in possui_acao]
    nao_prio = [c for c in celulas_elegiveis if c["chave"] in dominado]
    insuf = [c for c in celulas_elegiveis if c["chave"] in (nao_dominado - possui_acao)]

    return {"pares": pares, "dominacao": dominacao,
            "prioritarias": prioritarias, "nao_prio": nao_prio,
            "insuf": insuf}