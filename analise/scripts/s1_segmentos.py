# -*- coding: utf-8 -*-
"""
s1_segmentos.py — Saída 1: priorização de segmentos.
Calcula R por célula elegível, comparação pareada com FDR, e classifica cada
célula como: prioritária / não priorizada / inconclusiva / não elegível.
R é calculado SOMENTE no nível agregado do segmento.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

from elegibilidade import montar_celulas
from comparacao import comparar_pares
from config import LEVELS


def rotulo_nivel(nivel):
    if nivel == 0:
        return "bairro×tipo×quartos"
    if nivel == 1:
        return "bairro×tipo"
    if nivel == 2:
        return "bairro"
    return "n/a"


def chave_rotulo(chave):
    return " | ".join(str(x) for x in chave)


def executar_s1(ai, vi):
    celulas = montar_celulas(ai, vi)
    elegiveis = [c for c in celulas if c.get("elegivel")]
    comp = comparar_pares(elegiveis)

    linhas = []
    # Mapa chave->status da comparação
    status_comp = {}
    for c in comp["prioritarias"]:
        status_comp[c["chave"]] = "prioritaria"
    for c in comp["nao_prio"]:
        status_comp[c["chave"]] = "nao_prioritaria"
    for c in comp["insuf"]:
        status_comp[c["chave"]] = "nao_dominada_insuf"

    for c in comp["prioritarias"] + comp["nao_prio"] + comp["insuf"]:
        k = c["chave"]
        nivel = c.get("nivel")
        rot = c.get("rot_trabalho", chave_rotulo(k))
        linhas.append({
            "bairro_tipo_quartos": rot,
            "bairro": k[0], "tipo": k[1], "quartos": k[2],
            "nivel": rotulo_nivel(nivel),
            "status": status_comp[k],
            "R": c["R"], "R_ic_lo": c["ic_lo"], "R_ic_hi": c["ic_hi"],
            "half": c["half"], "n_ai": c["n_ai"],
            "n_vi_total": c["n_vi_total"],
            "n_vi_com_sale_price": c["n_vi_com_sale_price"],
            "cobertura_price_pct": (c["n_ai"] / c["n_total_ai"] * 100) if c["n_total_ai"] else np.nan,
            "origin": c.get("orig", "fino"),
        })
    df_eleg = pd.DataFrame(linhas)

    # células não elegíveis / inconclusivas
    incon = []
    for c in celulas:
        if not c.get("elegivel"):
            k = c["chave"]
            rot = c.get("rot_trabalho", chave_rotulo(k))
            incon.append({
                "bairro_tipo_quartos": rot,
                "bairro": k[0], "tipo": k[1], "quartos": k[2],
                "nivel": rotulo_nivel(c.get("nivel")),
                "status": "inconclusiva",
                "motivo": c.get("motivo", "no_dados"),
                "R": np.nan, "R_ic_lo": np.nan, "R_ic_hi": np.nan,
                "half": np.nan, "n_ai": c.get("n_ai", 0),
                "n_vi_total": c.get("n_vi_total", 0),
                "n_vi_com_sale_price": c.get("n_vi_com_sale_price", 0),
                "cobertura_price_pct": (c.get("n_ai", 0) / c.get("n_total_ai", 1) * 100)
                if c.get("n_total_ai") else np.nan,
                "origin": c.get("orig", "fino"),
            })
    df_incon = pd.DataFrame(incon)

    return {"df_eleg": df_eleg, "df_incon": df_incon,
            "comp": comp, "n_prioritarias": len(comp["prioritarias"]),
            "n_nao_prio": len(comp["nao_prio"]),
            "n_insuf": len(comp["insuf"]),
            "n_inconclusivas": len(incon)}