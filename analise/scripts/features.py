# -*- coding: utf-8 -*-
"""
features.py — Construção das tabelas de trabalho (imóvel Airbnb + anúncios VivaReal).
Reutiliza common_p1p2.py e configuração central. Nenhum dataset original é alterado.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np

from common_p1p2 import load_all, build_airbnb_table, build_viv_real_table

SNAP = pd.Timestamp("2025-01-13")


def carregar():
    det, hosts, mesh, price, viv = load_all()
    return {"details": det, "hosts": hosts, "mesh": mesh,
            "price": price, "vivareal": viv}


def build_imovel_table(det, hosts, mesh, price):
    """Tabela por anúncio Airbnb: segmentação, diária, cobertura, tração e confiança."""
    ai = build_airbnb_table(det, mesh, price)

    extra_cols = [c for c in ["owner_id", "number_of_guests", "number_of_beds",
                              "cleaning_fee", "number_of_reviews", "star_rating",
                              "picture_count", "is_guest_favorite", "is_professional",
                              "can_instant_book", "is_new_listing"]
                  if (c in det.columns) and (c not in ai.columns)]
    ai = ai.merge(det[["airbnb_listing_id"] + extra_cols], on="airbnb_listing_id",
                  how="left")

    hosts_d = hosts.drop_duplicates("owner_id", keep="first")
    ai = ai.merge(hosts_d[["owner_id", "is_superhost"]], on="owner_id", how="left")
    ai["is_superhost"] = ai["is_superhost"].fillna(False)

    mesh_s = mesh[["airbnb_listing_id", "aquisition_date"]].rename(
        columns={"aquisition_date": "first_seen"})
    ai = ai.merge(mesh_s, on="airbnb_listing_id", how="left")
    ai["first_seen"] = pd.to_datetime(ai["first_seen"], errors="coerce")
    ai["idade_ano"] = ((SNAP - ai["first_seen"]).dt.days.clip(lower=0)) / 365.25
    ai["reviews_ano"] = ai["number_of_reviews"] / ai["idade_ano"].clip(lower=0.05)
    return ai


def build_venda_table(viv):
    v = build_viv_real_table(viv)
    v["preco_m2"] = v["sale_price"] / v["usable_area"].replace(0, np.nan)
    return v