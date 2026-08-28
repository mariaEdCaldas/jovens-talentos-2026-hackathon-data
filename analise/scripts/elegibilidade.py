# -*- coding: utf-8 -*-
"""
elegibilidade.py — Aplica os gates (n_ai, n_vi_com_sale_price, half≤0,60) por célula,
com fallback hierárquico bairro×tipo×quartos → bairro×tipo → bairro.
Gera o status de ELEGIBILIDADE (volume/precisão) e retorna as células elegíveis
no nível de trabalho mais fino que atendem todos os gates.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np

from common_p1p2 import cell_key, boot_ratio
from config import (GATE_N_AI, GATE_N_VI_SALE, GATE_HALF_IC95, B_BOOTSTRAP,
                    LEVELS, SEED)


def _dados_celula(ai, vi, nivel, chave):
    """Retorna (d_vals, Vpos, n_ai, n_vi_total, n_vi_com_sale, n_total_ai)."""
    keys = LEVELS[nivel][1]
    mask = pd.Series(True, index=ai.index)
    for k, v in zip(keys, chave):
        mask &= (ai[k] == v)
    sub = ai[mask]
    d_vals = sub.loc[sub["d_a"].notna() & sub["has_price"] == 1, "d_a"].values
    n_ai = len(d_vals)
    n_total_ai = len(sub)

    vmask = pd.Series(True, index=vi.index)
    for k, v in zip(keys, chave):
        vmask &= (vi[k] == v)
    vsub = vi[vmask & ~vi["is_lanc"]]  # exclui lançamentos da mediana
    Vpos = vsub.loc[vsub["sale_price"].gt(0), "sale_price"].values
    n_vi_com_sale = len(Vpos)
    n_vi_total = int(vsub["listing_id"].nunique()) if len(vsub) else 0
    return d_vals, Vpos, n_ai, n_vi_total, n_vi_com_sale, n_total_ai


def _boot_celula(d_vals, Vpos):
    if len(d_vals) == 0 or len(Vpos) == 0:
        return None
    R, half, (lo, hi) = boot_ratio(d_vals, Vpos, B=B_BOOTSTRAP, seed=SEED)
    return {"R": R, "half": half, "ic_lo": lo, "ic_hi": hi}


def avaliar_celula(ai, vi, nivel, chave):
    """Aplica gates. Retorna dict com status de elegibilidade + motivos,
    ou None se sem dados. half só é calculado se volume passa; se half>gate, falha precisão."""
    d_vals, Vpos, n_ai, n_vi_total, n_vi_com_sale, n_total_ai = _dados_celula(
        ai, vi, nivel, chave)
    motivo = []
    if n_ai < GATE_N_AI:
        motivo.append("volume_ai")
    if n_vi_com_sale < GATE_N_VI_SALE:
        motivo.append("volume_vi")
    base = {"n_ai": n_ai, "n_vi_total": n_vi_total,
            "n_vi_com_sale_price": n_vi_com_sale, "n_total_ai": n_total_ai,
            "d_vals": d_vals, "Vpos": Vpos}
    if motivo:
        return {"elegivel": False, "motivo": "+".join(motivo) if motivo else "sem_dados",
                **base, "R": np.nan, "half": np.nan, "ic_lo": np.nan, "ic_hi": np.nan}
    boot = _boot_celula(d_vals, Vpos)
    if boot is None:
        return {"elegivel": False, "motivo": "sem_dados",
                **base, "R": np.nan, "half": np.nan, "ic_lo": np.nan, "ic_hi": np.nan}
    if not np.isfinite(boot["half"]) or boot["half"] > GATE_HALF_IC95:
        return {"elegivel": False, "motivo": "precisao",
                **base, "R": boot["R"], "half": boot["half"],
                "ic_lo": boot["ic_lo"], "ic_hi": boot["ic_hi"]}
    return {"elegivel": True, "motivo": "",
            **base, "R": boot["R"], "half": boot["half"],
            "ic_lo": boot["ic_lo"], "ic_hi": boot["ic_hi"]}


def _eval_trio(ai, vi, bairro, tipo, q):
    chave = (bairro, tipo, q)
    res = avaliar_celula(ai, vi, 0, chave)
    return chave, res


def _celula_dict(chave, res, nivel, orig, rot):
    """Constrói dict de célula a partir do resultado de avaliar_celula."""
    base = {"chave": chave, "nivel": nivel, "orig": orig,
            "rot_trabalho": rot}
    if res is None:
        return {"elegivel": False, "motivo": "sem_dados",
                "n_ai": 0, "n_vi_total": 0, "n_vi_com_sale_price": 0,
                "n_total_ai": 0, "d_vals": [], "Vpos": [],
                "R": np.nan, "half": np.nan, "ic_lo": np.nan, "ic_hi": np.nan,
                **base}
    return {**base, **res}


def montar_celulas(ai, vi):
    """Constrói o conjunto de CÉLULAS DE COMPARAÇÃO hierarquicamente NÃO SOBREPOSTO.

    Regra (semantica do fallback na metodologia):
      - Uma célula agregada (bairro×tipo ou bairro) SÓ entra nas comparações se
        NENHUMA célula descendente (mais especifica) foi utilizável.
      - Se algum trio fino (bairro,tipo,q) é elegível, ele representa a região no
        detalhe e a célula agregada bt correspondente NÃO entra (ficaria contida).
      - Se nenhum trio fino da região bt é elegível, então a bt pode entrar
        (substituto). Idem para bairro: só entra se nenhum bt nem trio fino do
        bairro foi usado.

    Células não elegíveis são reportadas como inconclusivas (não participam da
    comparação). Nenhuma célula agregada coexiste com descendente no comparativo.
    """
    bairros = sorted([b for b in ai["bairro"].dropna().unique()
                      if b != "sem_bairro" and not str(b).startswith("outro")])
    tipos = ["apartamento", "casa", "outros"]
    qs = ["1", "2", "3", "4+"]

    celulas = []
    celulas_finas_por_regiao = {}   # (bairro,tipo) -> lista de celulas finas elegiveis
    inconclusivos = []               # trios que não foram representados em qq nível
    bt_usados = set()               # (bairro,tipo) com célula bt elegível

    # Passo 1: avaliar trios finos, por região bt
    regiao_fina_eleita = {}   # (bairro,tipo) -> lista de trios elegíveis
    for bairro in bairros:
        for tipo in tipos:
            finos_eleg = []
            for q in qs:
                chave, res = _eval_trio(ai, vi, bairro, tipo, q)
                if res is not None and res["elegivel"]:
                    finos_eleg.append(chave)
            regiao_fina_eleita[(bairro, tipo)] = finos_eleg
            for chave in finos_eleg:
                res = avaliar_celula(ai, vi, 0, chave)
                celulas.append(_celula_dict(chave, res, 0, "fino",
                                            f"{bairro}|{tipo}|{chave[2]}"))

    # Passo 2: regiões sem trio fino elegível → tentam bt
    bt_a_avaliar = set()
    for bairro in bairros:
        for tipo in tipos:
            if regiao_fina_eleita[(bairro, tipo)]:
                continue   # já representada no fino
            bt_a_avaliar.add((bairro, tipo))
    for (bairro, tipo) in bt_a_avaliar:
        res = avaliar_celula(ai, vi, 1, (bairro, tipo))
        if res is not None and res["elegivel"]:
            chave = (bairro, tipo, qs[0])
            celulas.append(_celula_dict(chave, res, 1, "fallback_bt",
                                        f"{bairro}|{tipo}|(todos quartos)"))
            bt_usados.add((bairro, tipo))

    # Passo 3: bairros sem nenhum representante fino/bt → tentam bairro
    for bairro in bairros:
        algum_tipo_representado = any(
            regiao_fina_eleita[(bairro, tipo)] or (bairro, tipo) in bt_usados
            for tipo in tipos)
        if algum_tipo_representado:
            continue
        res = avaliar_celula(ai, vi, 2, (bairro,))
        if res is not None and res["elegivel"]:
            chave = (bairro, tipos[0], qs[0])
            celulas.append(_celula_dict(chave, res, 2, "fallback_b",
                                        f"{bairro}|(todos tipos)|(todos quartos)"))

    # Passo 4: trios não representados em nenhum nível → inconclusivos
    representados = set()
    for c in celulas:
        if c["elegivel"]:
            if c["nivel"] == 0:
                representados.add(c["chave"])
            elif c["nivel"] == 1:
                representados.update((bairro, tipo, q) for q in qs
                                     if (bairro, tipo) == (c["chave"][0], c["chave"][1]))
            elif c["nivel"] == 2:
                b = c["chave"][0]
                representados.update((b, t, q) for t in tipos for q in qs)
    for (bairro, tipo, q) in [(b, t, q) for b in bairros for t in tipos for q in qs]:
        if (bairro, tipo, q) in representados:
            continue
        chave, res = _eval_trio(ai, vi, bairro, tipo, q)
        # usa o melhor res (fino) para o motivo
        inconclusivos.append(_celula_dict(chave, res, None, "nao_elegivel",
                                          f"{bairro}|{tipo}|{q}"))

    celulas.extend(inconclusivos)
    return celulas