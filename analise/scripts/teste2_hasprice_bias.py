# -*- coding: utf-8 -*-
"""
Teste 2 - Vies de selecao: has_price (listing presente em Price) vs NAO-price.
Compara os dois grupos usando Details, Mesh e Hosts.
"""
import pandas as pd
import numpy as np
import os
from scipy import stats

DATA = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\data"
OUT = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\analise\saida"

det = pd.read_csv(os.path.join(DATA, "Details_Itapema.csv"), encoding="utf-8")
mesh = pd.read_csv(os.path.join(DATA, "Mesh_Ids_Data_Itapema.csv"), encoding="utf-8")
hosts = pd.read_csv(os.path.join(DATA, "Hosts_ids_Itapema.csv"), encoding="utf-8")
price = pd.read_csv(os.path.join(DATA, "Price_AV_Itapema.csv"), encoding="utf-8")

price_ids = set(price["airbnb_listing_id"])

# has_price join listas
df = det.copy()
df["has_price"] = df["airbnb_listing_id"].isin(price_ids).astype(int)
df = df.merge(mesh[["airbnb_listing_id", "suburb", "latitude", "longitude"]],
              on="airbnb_listing_id", how="left")

# hosts: deduplicar por owner (atributos do host constantes? usaremos primeira ocorrencia por owner)
hosts_dedup = hosts.drop_duplicates("owner_id", keep="first")
df = df.merge(hosts_dedup[["owner_id", "is_superhost", "star_rating_host", "is_verified",
                           "years_host", "months_host", "number_of_reviews_host"]],
              on="owner_id", how="left")

g0 = df[df["has_price"] == 0]
g1 = df[df["has_price"] == 1]
print("n has_price=1:", len(g1), f"({100*len(g1)/len(df):.2f}%)  has_price=0:", len(g0),
      f"({100*len(g0)/len(df):.2f}%)")

lines = []
def L(s=""):
    lines.append(str(s))
L("TESTE 2 — Vies de selecao has_price")
L(f"total listings={len(df)}  has_price=1: {len(g1)} ({100*len(g1)/len(df):.2f}%)  has_price=0: {len(g0)} ({100*len(g0)/len(df):.2f}%)")
L("")

L("### Cobertura por suburb (bairro) ###")
t = pd.crosstab(df["suburb"], df["has_price"], margins=True)
t["cov%"] = (100 * t[1] / t["All"]).round(1)
L(t.to_string())
L("")

L("### listing_type ###")
t = pd.crosstab(df["listing_type"], df["has_price"], margins=True)
t["cov%"] = (100 * t[1] / t["All"]).round(1)
L(t.to_string())
L("")

def cont_cat(col):
    t = pd.crosstab(df[col], df["has_price"], margins=True)
    t["cov%"] = (100 * t[1] / t["All"]).round(1)
    return t

for col in ["bedroomsGrp", "bathGrp", "guestsGrp", "bedsGrp", "cleaningGrp", "reviewsGrp",
            "starGrp", "is_guest_favorite", "is_superhost", "is_professional",
            "can_instant_book", "is_new_listing", "is_verified"]:
    pass

# construir faixas
df["bedroomsGrp"] = pd.cut(df["number_of_bedrooms"], [0,1,2,3,4,50], labels=["1","2","3","4","5+"])
df["guestsGrp"] = pd.cut(df["number_of_guests"], [0,4,6,8,20], labels=["1-4","5-6","7-8","9+"])
df["bedsGrp"] = pd.cut(df["number_of_beds"], [0,2,4,6,60], labels=["1-2","3-4","5-6","7+"])
df["cleaningGrp"] = pd.cut(df["cleaning_fee"], [0,0.1,150,250,500,10000], labels=["0","1-149","150-249","250-499","500+"])
df["reviewsGrp"] = pd.cut(df["number_of_reviews"], [0,0.1,5,20,100,1000], labels=["0","1-4","5-19","20-99","100+"])
df["starGrp"] = df["star_rating"].apply(lambda x: "0 (sem rev)" if x == 0 else ("<4.5" if x < 4.5 else ">=4.5"))
df["bathGrp"] = pd.cut(df["number_of_bathrooms"], [0,1,2,3,30], labels=["0-1","2","3","4+"])

for col in ["suburb", "listing_type", "bedroomsGrp", "bathGrp", "guestsGrp", "bedsGrp",
            "cleaningGrp", "reviewsGrp", "starGrp", "is_guest_favorite", "is_superhost",
            "is_professional", "can_instant_book", "is_new_listing", "is_verified"]:
    L(f"### {col} ###")
    L(cont_cat(col).to_string())
    L("")
    # teste chi2
    ct = pd.crosstab(df[col], df["has_price"])
    if ct.shape[0] > 1 and (ct.sum(axis=1) > 0).all():
        chi2, pv, dof, _ = stats.chi2_contingency(ct)
        L(f"  chi2 p-valor={pv:.4f} (df={dof})")
    L("")

# variaveis continuas
print("Calcular continuas...")
cont_vars = ["number_of_bedrooms", "number_of_bathrooms", "number_of_beds", "number_of_guests",
             "cleaning_fee", "number_of_reviews", "star_rating", "picture_count",
             "min_nights", "years_host", "months_host", "star_rating_host", "number_of_reviews_host"]
L("### Variaveis continuas: mediana/mean has_price 0 vs 1 ###")
for v in cont_vars:
    if v not in df.columns:
        continue
    a = g0[v].dropna(); b = g1[v].dropna()
    if len(a) == 0 or len(b) == 0:
        continue
    try:
        stat, pv = stats.mannwhitneyu(b, a, alternative="two-sided")
    except Exception:
        pv = float("nan")
    L(f"{v:<24} med0={np.median(a):>10.3f} med1={np.median(b):>10.3f} | mean0={np.mean(a):>12.3f} mean1={np.mean(b):>12.3f} | MWU p={pv:.4f}")
L("")

# owner concentracao: listings com price pertencem a owners grandes?
L("### Owners: concentracao de listings no price por owner ###")
owner_n = df.groupby("owner_id").size().rename("n_listings")
owner_p = df.groupby("owner_id")["has_price"].sum().rename("n_price")
oi = pd.concat([owner_n, owner_p], axis=1)
oi["pct_price"] = oi["n_price"] / oi["n_listings"]
bins = [0,1,2,5,10,20,1000]
oi["tam"] = pd.cut(oi["n_listings"], bins, labels=["1","2","4","5-9","10-19","20+"])
L("distribuicao cobertura por tamanho de owner (media de pct_price):")
L(oi.groupby("tam", observed=False)["pct_price"].agg(["count", "mean"]).round(3).to_string())
L("")
L("owners com TODAS listas no price vs NENHUMA:")
L(f"todas price: {(oi['pct_price'] == 1).sum()}  nenhuma price: {(oi['pct_price'] == 0).sum()}")

with open(os.path.join(OUT, "teste2_hasprice_bias.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\n".join(lines))