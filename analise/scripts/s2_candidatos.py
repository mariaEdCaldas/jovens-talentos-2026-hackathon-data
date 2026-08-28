# -*- coding: utf-8 -*-
"""
s2_candidatos.py — Saída 2: candidatos operacionais dentro de segmentos prioritários.
Reforce: NÃO é recomendação de compra; has_price é só condição de disponibilidade
de informação; sinais são descritivos, nunca upside/demanda/retorno.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

from config import N_DATAS_MIN_S2


def selecionar_candidatos(ai, celulas_prioritarias_meta):
    """celulas_prioritarias_meta: lista de dicts (chave, nivel, rot_trabalho).
    Retorna DataFrame com anúncios elegíveis a candidato (descritivos).
    Deduplica por anúncio (célula de trabalho única)."""
    registros = []
    for meta in celulas_prioritarias_meta:
        chave, nivel, rot_trabalho = meta["chave"], meta["nivel"], meta["rot_trabalho"]
        bairro, tipo, q = chave
        m = (ai["bairro"] == bairro)
        if nivel == 0:
            m &= (ai["tipo"] == tipo) & (ai["q"] == q)
        elif nivel == 1:
            m &= (ai["tipo"] == tipo)
        sub = ai[m].copy()
        sub = sub[sub["has_price"] == 1]
        sub = sub[sub["n_datas"] >= N_DATAS_MIN_S2]
        new_mask = sub["is_new_listing"].fillna(True) != True
        sub = sub[new_mask]
        for _, r in sub.iterrows():
            registros.append({
                "airbnb_listing_id": r["airbnb_listing_id"],
                "segmento_prioritario": rot_trabalho,
                "bairro": bairro, "tipo": r["tipo"], "quartos": r["q"],
                "diaria_mediana": r["d_a"],
                "n_datas": r["n_datas"],
                "numero_reviews": r["number_of_reviews"],
                "reviews_ano": r.get("reviews_ano", np.nan),
                "star_rating": r["star_rating"] if r["star_rating"] > 0 else np.nan,
                "is_guest_favorite": bool(r["is_guest_favorite"]) if not pd.isna(r["is_guest_favorite"]) else None,
                "is_superhost": bool(r["is_superhost"]) if not pd.isna(r["is_superhost"]) else None,
                "is_professional": bool(r["is_professional"]) if not pd.isna(r["is_professional"]) else None,
                "can_instant_book": bool(r["can_instant_book"]) if not pd.isna(r["can_instant_book"]) else None,
                "cleaning_fee": r["cleaning_fee"],
                "n_guests": r["number_of_guests"], "n_beds": r["number_of_beds"],
                "maturidade_anos": r.get("idade_ano", np.nan),
            })
    df = pd.DataFrame(registros)
    if len(df):
        df = df.drop_duplicates(subset="airbnb_listing_id", keep="first")
    return df