# -*- coding: utf-8 -*-
"""
Módulo comum (Fase P1/P2) — funções reproduzíveis de preparação e estimação.
Não gera ranking. Apenas dados de trabalho + funções metodológicas.
"""
import pandas as pd
import numpy as np
import unicodedata
import os

DATA = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\data"
OUT = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\analise\saida"
os.makedirs(OUT, exist_ok=True)


def strip_accents(s):
    if not isinstance(s, str):
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower().strip()


CANON = {
    "meia praia": "meia praia",
    "centro": "centro",
    "morretes": "morretes",
    "tabuleiro dos oliveiras": "tabuleiro dos oliveiras",
    "tabuleiro": "tabuleiro dos oliveiras",
    "taboleiro": "tabuleiro dos oliveiras",
    "canto da praia": "canto da praia",
    "casa branca": "casa branca",
    "alto sao bento": "alto sao bento",
    "ilhota": "ilhota",
    "varzea": "varzea",
    "andorinha": "andorinha",
    "castelo branco": "castelo branco",
    "sertao do trombudo": "sertao do trombudo",
    "jardim praiamar": "jardim praiamar",
    "jardim praia mar": "jardim praiamar",
    "sertaozinho": "sertaozinho",
    "leopoldo zarling": "leopoldo zarling",
    "areal": "areal",
    "lameiro": "lameiro",
    "estreito": "estreito",
}

LANC_KEYWORDS = ["lançamento", "lancamento", "pré-venda", "pre-venda", "frente mar",
                 "frente-mar", "à venda na planta", "em construção", "incorpora"]


def canon_bairro(s):
    k = strip_accents(s)
    if k in ("", "none") or k is pd.NA or k is None:
        return "sem_bairro"
    if k == "meia praia - frente mar":
        return "meia_praia_frente_mar"
    return CANON.get(k, "outro(" + k + ")")


def q_grp(x):
    if pd.isna(x):
        return "sem"
    x = int(x)
    if x == 0:
        return "0"
    if x <= 1:
        return "1"
    if x == 2:
        return "2"
    if x == 3:
        return "3"
    return "4+"


def tipo_grp(t):
    t = str(t).strip().lower()
    if t in ("apartamento", "casa"):
        return t
    return "outros"


def is_lancamento(s):
    s = str(s).lower()
    return any(k in s for k in LANC_KEYWORDS)


def load_all():
    det = pd.read_csv(os.path.join(DATA, "Details_Itapema.csv"), encoding="utf-8")
    hosts = pd.read_csv(os.path.join(DATA, "Hosts_ids_Itapema.csv"), encoding="utf-8")
    mesh = pd.read_csv(os.path.join(DATA, "Mesh_Ids_Data_Itapema.csv"), encoding="utf-8")
    price = pd.read_csv(os.path.join(DATA, "Price_AV_Itapema.csv"), encoding="utf-8")
    viv = pd.read_csv(os.path.join(DATA, "VivaReal_Itapema.csv"), encoding="utf-8")
    return det, hosts, mesh, price, viv


def build_airbnb_table(det, mesh, price):
    """Table por anúncio Airbnb: bairro, tipo, quartos, n_datas (com preço),
    diária mediana d_a (mediana por noite, união das capturas por dia-calendário)."""
    df = det[["airbnb_listing_id", "listing_type", "number_of_bedrooms",
              "number_of_beds", "number_of_guests", "cleaning_fee"]].copy()
    df = df.merge(mesh[["airbnb_listing_id", "suburb"]], on="airbnb_listing_id", how="left")
    df["bairro"] = df["suburb"].apply(canon_bairro)
    df["tipo"] = df["listing_type"].apply(tipo_grp)
    df["q"] = df["number_of_bedrooms"].apply(q_grp)

    # preço por anúncio: mediana das noites (mediana p/ noite; se varias capturas, mediana)
    if len(price):
        pp = price[["airbnb_listing_id", "date", "price"]].copy()
        pp["price"] = pp["price"].astype(float)
        # mediana por (anúncio, noite) sobre capturas
        pn = pp.groupby(["airbnb_listing_id", "date"])["price"].median().reset_index()
        per = pn.groupby("airbnb_listing_id")["price"].agg(
            d_a="median", n_datas="count").reset_index()
        df = df.merge(per, on="airbnb_listing_id", how="left")
    else:
        df["d_a"] = np.nan
        df["n_datas"] = 0
    df["has_price"] = df["d_a"].notna().astype(int)
    return df


def build_viv_real_table(viv):
    """Table por anúncio VivaReal: bairro, tipo, quartos, preço de venda,
    área, condomínio, iptu; marca lançamentos/frente-mar."""
    v = viv.copy()
    v = v.drop_duplicates("listing_id", keep="first")
    v["bairro"] = v["suburb"].apply(canon_bairro)
    v["tipo"] = v["listing_type"].apply(tipo_grp)
    v["q"] = v["bedrooms"].apply(q_grp)
    v["is_lanc"] = v["listing_title"].apply(is_lancamento) | v["link_url"].apply(is_lancamento)
    # preço positivo
    v["sale_price"] = pd.to_numeric(v["sale_price"], errors="coerce")
    return v


def cell_key(df, level):
    """level: 'bairro_tipo_q' | 'bairro_tipo' | 'bairro'."""
    if level == "bairro_tipo_q":
        return ["bairro", "tipo", "q"]
    if level == "bairro_tipo":
        return ["bairro", "tipo"]
    return ["bairro"]


def cells_ai(df, level):
    g = df.groupby(cell_key(df, level), dropna=False)
    # n_total_ai   = anúncios Airbnb na célula (all, com ou sem preço)
    # n_com_price  = anúncios Airbnb com preço (has_price=1) — efetivamente usados
    t = g.agg(n_total_ai=("airbnb_listing_id", "size"),
              n_com_price=("has_price", "sum")).reset_index()
    return t


def cells_vi(v, level, excl_lanc=True):
    if excl_lanc:
        vv = v[~v["is_lanc"]]
    else:
        vv = v
    g = vv.groupby(cell_key(vv, level), dropna=False)
    # n_vi_total            = anúncios VivaReal estruturalmente elegíveis na célula (após dedup,
    #                         com ou sem preço de venda válido)
    # n_vi_com_sale_price   = anúncios com sale_price válido (não-nulo e >0),
    #                         efetivamente usados na estimativa da mediana/precisão
    t = g.apply(lambda s: pd.Series({
        "n_vi_total": int(s["listing_id"].nunique()),
        "n_vi_com_sale_price": int(pd.to_numeric(s["sale_price"], errors="coerce")
                                   .gt(0).sum()),
        "n_lanc": int((s["is_lanc"]).sum()),
    })).reset_index()
    return t


def boot_ratio(d_list, v_list, B=1000, seed=7):
    """Bootstrap por cluster (anúncio), duas amostras independentes.
    Retorna Robs, meia-largura relativa do IC95 (na escala da razão),
    e intervalo (ratio_lo, ratio_hi)."""
    d = np.asarray(d_list, dtype=float)
    v = np.asarray(v_list, dtype=float)
    n1, n2 = len(d), len(v)
    if n1 == 0 or n2 == 0:
        return np.nan, np.nan, (np.nan, np.nan)
    Robs = np.median(d) / np.median(v)
    rng = np.random.default_rng(seed)
    idx1 = rng.integers(0, n1, size=(B, n1))
    idx2 = rng.integers(0, n2, size=(B, n2))
    Ds = np.median(d[idx1], axis=1)
    Vs = np.median(v[idx2], axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        logR = np.log(Ds) - np.log(Vs)
    lo, hi = np.percentile(logR, [2.5, 97.5])
    ratio_lo, ratio_hi = np.exp(lo), np.exp(hi)
    half = (ratio_hi - ratio_lo) / (2 * Robs)
    return Robs, half, (ratio_lo, ratio_hi)