# -*- coding: utf-8 -*-
"""
Teste 5 - Reviews como proxy de tracao historica.
Verifica relacao de number_of_reviews com idade/atividade (mesh aquisition_date
como primeiro tracking, is_new_listing, tenure do host), star_rating, listing_type,
bairro e has_price. Calcula reviews por ano de atividade quando possivel.
"""
import pandas as pd
import numpy as np
import os

DATA = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\data"
OUT = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\analise\saida"

det = pd.read_csv(os.path.join(DATA, "Details_Itapema.csv"), encoding="utf-8")
mesh = pd.read_csv(os.path.join(DATA, "Mesh_Ids_Data_Itapema.csv"), encoding="utf-8")
hosts = pd.read_csv(os.path.join(DATA, "Hosts_ids_Itapema.csv"), encoding="utf-8")
price = pd.read_csv(os.path.join(DATA, "Price_AV_Itapema.csv"), encoding="utf-8")

price_ids = set(price["airbnb_listing_id"])
df = det.copy()
df["has_price"] = df["airbnb_listing_id"].isin(price_ids).astype(int)
hosts_dedup = hosts.drop_duplicates("owner_id", keep="first")
df = df.merge(hosts_dedup[["owner_id", "years_host", "months_host", "is_superhost"]],
              on="owner_id", how="left")
mesh2 = mesh[["airbnb_listing_id", "suburb", "aquisition_date"]].rename(
    columns={"aquisition_date": "first_seen"})
df = df.merge(mesh2, on="airbnb_listing_id", how="left")
df["first_seen"] = pd.to_datetime(df["first_seen"], errors="coerce")

# idade em anos ate o snapshot (2025-01-13)
SNAP = pd.Timestamp("2025-01-13")
df["age_years"] = (SNAP - df["first_seen"]).dt.days / 365.25
df["reviews_per_year"] = df["number_of_reviews"] / df["age_years"].clip(lower=0.05)

L = []
def out(s=""): L.append(str(s))

out("TESTE 5 — Reviews e tracao historica")
out(f"n listings={len(df)}  primeiro tracking (first_seen): ")
out(df["first_seen"].dt.year.value_counts().sort_index().to_string())
out("")
out("### correlacao reviews vs idade/atividade ###")
cont = ["number_of_reviews", "age_years", "years_host", "months_host", "star_rating",
        "picture_count", "cleaning_fee"]
out(df[cont + ["reviews_per_year"]].corr().round(3).to_string())
out("")

# is_new_listing x reviews
out("### number_of_reviews por is_new_listing ###")
out(df.groupby("is_new_listing")["number_of_reviews"].agg(["count", "median", "mean", "max"]).round(1).to_string())
out("")
out("### reviews por ano de primeiro tracking (faixa de idade) ###")
df["idade_grp"] = pd.cut(df["age_years"], [0, 0.5, 1, 2, 3, 5, 15],
                        labels=["0-0.5", "0.5-1", "1-2", "2-3", "3-5", "5+"])
out(df.groupby("idade_grp", observed=False).agg(
    n=("airbnb_listing_id", "size"),
    med_reviews=("number_of_reviews", "median"),
    mean_reviews=("number_of_reviews", "mean"),
    med_rev_ano=("reviews_per_year", "median"),
    mean_rev_ano=("reviews_per_year", "mean"),
    pct_new=("is_new_listing", lambda s: (s == True).mean())).round(2).to_string())
out("")

out("### reviews por listing_type ###")
out(df.groupby("listing_type")["number_of_reviews"].agg(["count", "median", "mean"]).round(1).to_string())
out("")

out("### reviews por bairro (top) ###")
out(df.groupby("suburb")["number_of_reviews"].agg(["count", "median", "mean"]).round(1)
   .sort_values("median", ascending=False).head(12).to_string())
out("")

out("### reviews x has_price ###")
out(df.groupby("has_price")["number_of_reviews"].agg(["count", "median", "mean"]).round(2).to_string())
out("")

out("### has_price x reviews_por_ano (decisivo para interpretar) ###")
df2 = df[df["age_years"] > 0]
out(df2.groupby("has_price")["reviews_per_year"].agg(["median", "mean"]).round(2).to_string())
out("")

out("### reviews normalizado por tempo dentro do grupo COM price ###")
out("corr(reviews_per_year, has_price)? (point-biserial aprox via grupos acima)")
out("")
out("### fracao de listings novos entre reviews baixos ###")
low = df[df["number_of_reviews"] <= 5]
high = df[df["number_of_reviews"] > 50]
out(f"reviews 0-5: n={len(low)}, pct has_price={100*low['has_price'].mean():.1f}%, pct is_new_listing={100*(low['is_new_listing']==True).mean():.1f}%, med idade={low['age_years'].median():.2f}")
out(f"reviews >50: n={len(high)}, pct has_price={100*high['has_price'].mean():.1f}%, pct is_new_listing={100*(high['is_new_listing']==True).mean():.1f}%, med idade={high['age_years'].median():.2f}")
out("")

with open(os.path.join(OUT, "teste5_reviews_tracao.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("\n".join(L))