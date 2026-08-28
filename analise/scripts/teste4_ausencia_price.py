# -*- coding: utf-8 -*-
"""
Teste 4 - Significado da ausencia de observacao em Price.
Verifica: cobertura de datas por listing, padrão de ausencias, e se listings
com poucas observacoes compartilham caracteristicas.
"""
import pandas as pd
import numpy as np
import os

DATA = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\data"
OUT = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\analise\saida"

p = pd.read_csv(os.path.join(DATA, "Price_AV_Itapema.csv"), encoding="utf-8")
det = pd.read_csv(os.path.join(DATA, "Details_Itapema.csv"), encoding="utf-8")

p["date"] = pd.to_datetime(p["date"])
all_dates = pd.date_range("2025-01-06", "2025-04-20")
print("datas possiveis no periodo:", len(all_dates))

L = []
def out(s=""): L.append(str(s))

out("TESTE 4 — Ausencia em Price e cobertura de datas")
out(f"periodo possivel: {all_dates.min().date()} a {all_dates.max().date()} = {len(all_dates)} dias")
out("")

# cobertura por listing (union de datas, sem considerar capturas)
cov = p.drop_duplicates(["airbnb_listing_id", "date"]).groupby("airbnb_listing_id")["date"].agg(
    ["min", "max", "count"])
cov["cobertura_max"] = (cov["max"] - cov["min"]).dt.days + 1
cov["contiguo%"] = 100 * cov["count"] / cov["cobertura_max"]
out("### Cobertura de datas por listing (union) — 1005 listings ###")
out(cov["count"].describe().round(1).to_string())
out("")
out("distribuicao de count (n datas cobertas):")
out(cov["count"].value_counts().sort_index().repeat(1).head(40).to_string())
out("")
out("### Listings por faixa de datas cobertas ###")
bins = [0, 10, 30, 60, 90, 106]
cov["faixa"] = pd.cut(cov["count"], bins, labels=["1-9", "10-29", "30-59", "60-89", "90-105"])
out(cov["faixa"].value_counts().sort_index().to_string())
out("")
out("### Minimo de datas (inicio do calendario coberto) ###")
out(cov["min"].dt.date.value_counts().sort_index().head(10).to_string())
out("### Maximo de datas (fim do calendario coberto) ###")
out(cov["max"].dt.date.value_counts().sort_index().tail(15).to_string())
out("")
out("### continuação do calendario (gaps internos?) ###")
# para cada listing: verificar contiguidade do union das datas
gaps = []
for lid, grp in p.drop_duplicates(["airbnb_listing_id", "date"]).groupby("airbnb_listing_id"):
    ds = grp["date"].sort_values()
    present = set(ds)
    tot_backlog = 0
    min_d, max_d = ds.min(), ds.max()
    span = all_dates[(all_dates >= min_d) & (all_dates <= max_d)]
    n_missing = len(span) - len(present & set(span))
    gaps.append((lid, len(present), n_missing, (max_d - min_d).days + 1))
gdf = pd.DataFrame(gaps, columns=["lid", "n_dates", "n_missing_in_span", "span_days"])
gdf["missing%"] = 100 * gdf["n_missing_in_span"] / gdf["span_days"]
out(f"listings com 0 faltas internas no intervalo (contíguos): {(gdf['missing%']==0).sum()} de {len(gdf)}")
out(f"listings com faltas internas >5% do intervalo: {(gdf['missing%']>5).sum()}")
out(gdf["missing%"].describe().round(2).to_string())
out("")

# caracteristicas dos listings 'magros' (<30 datas) vs 'cheios' (>=60)
detx = det.set_index("airbnb_listing_id")
cov2 = cov.join(detx[["listing_type", "number_of_bedrooms", "number_of_reviews",
                      "star_rating", "picture_count", "cleaning_fee", "is_guest_favorite",
                      "is_professional"]], how="left")
cov2["grupo"] = np.where(cov2["count"] < 30, "magro(<30d)", 
                np.where(cov2["count"] >= 60, "cheio(>=60d)", "medio"))
out("### Caracteristicas por grupo de cobertura ###")
out("n por grupo: " + str(cov2["grupo"].value_counts().to_dict()))
out(cov2.groupby("grupo").agg(n=("count", "size"),
                               med_datas=("count", "median"),
                               med_reviews=("number_of_reviews", "median"),
                               med_star=("star_rating", "median"),
                               med_pic=("picture_count", "median"),
                               med_clean=("cleaning_fee", "median"),
                               pct_fav=("is_guest_favorite", "mean"),
                               pct_prof=("is_professional", "mean")).round(2).to_string())
out("")
out("fracao apartmentos por grupo:")
out(pd.crosstab(cov2["grupo"], cov2["listing_type"], normalize="index").round(3).to_string())
out("")

# n_capturas x cobertura
nc = p.groupby("airbnb_listing_id")["aquisition_date"].nunique().rename("n_cap")
c3 = cov2.join(nc)
out("### correlacao cobertura(datas) vs n_capturas ###")
out(c3[["count", "n_cap"]].corr().round(3).to_string())
out("")

out("### Conclusao estrutural ###")
out("Sem coluna de calendario/disponibilidade, ausencia = NAO COLETADO ou BLOQUEADO,")
out("indistinguivel nos dados.")

with open(os.path.join(OUT, "teste4_ausencia_price.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("\n".join(L))