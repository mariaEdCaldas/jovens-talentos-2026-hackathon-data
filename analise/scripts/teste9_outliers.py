# -*- coding: utf-8 -*-
"""
Teste 9 - Outliers de VivaReal: sale_price, usable_area, monthly_condo_fee, yearly_iptu.
Junta com listing_type e classifica valores como plausivel / suspeito / provavel erro,
somente com evidencia. NAO remove registros.
"""
import pandas as pd
import numpy as np
import os

DATA = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\data"
OUT = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\analise\saida"

viv = pd.read_csv(os.path.join(DATA, "VivaReal_Itapema.csv"), encoding="utf-8")

L = []
def out(s=""): L.append(str(s))

out("TESTE 9 — Outliers VivaReal por listing_type")
out("n por tipo: " + str(viv["listing_type"].value_counts().to_dict()))
out("")

dv = viv.drop_duplicates("listing_id").copy()
dv["preco_m2"] = dv["sale_price"] / dv["usable_area"].replace(0, np.nan)
dv["condo_m2"] = dv["monthly_condo_fee"] / dv["usable_area"].replace(0, np.nan)

for lt in ["apartamento", "casa", "terreno", "comercial", "outros"]:
    s = dv[dv["listing_type"] == lt]
    out("=" * 80)
    out(f"### {lt} (n={len(s)}) ###")
    for col in ["sale_price", "usable_area", "monthly_condo_fee", "yearly_iptu"]:
        d = s[col].dropna()
        if len(d) == 0:
            out(f"{col}: sem dados"); continue
        q1, q3 = d.quantile([0.25, 0.75])
        iqr = q3 - q1
        out(f"{col:<18} n={len(d):>5} mediana={d.median():>12.0f} P90={d.quantile(0.9):>12.0f} "
            f"P99={d.quantile(0.99):>12.0f} max={d.max():>12.0f} nulos={int(s[col].isna().sum())}")
    d = s["preco_m2"].dropna()
    if len(d) > 0:
        q1, q3 = d.quantile([0.25, 0.75]); iqr = q3 - q1
        out(f"preço/m2       n={len(d):>5} mediana={d.median():>10.0f} P90={d.quantile(0.9):>10.0f} "
            f"max={d.max():>12.0f} | IQR x3 upper={q3 + 3 * iqr:>12.0f}")
    # top suspects
    out(f"  -- maiores preco_m2 (top6): ")
    out(d.sort_values(ascending=False).head(6).round(0).to_string())
out("")

out("### maiores areas por tipo (top4) ###")
for lt in ["apartamento", "casa", "terreno", "comercial"]:
    s = dv[dv["listing_type"] == lt]
    out(f"-- {lt}:")
    out(s.nlargest(4, "usable_area")[["listing_id", "sale_price", "usable_area",
                                      "bedrooms", "bathrooms", "suburb"]].to_string())
out("")
out("### maiores sale_price por tipo (top4) ###")
for lt in ["apartamento", "casa", "terreno", "comercial"]:
    s = dv[dv["listing_type"] == lt]
    out(f"-- {lt}:")
    out(s.nlargest(4, "sale_price")[["listing_id", "sale_price", "usable_area",
                                     "bedrooms", "suburb", "listing_title"]].to_string())
out("")
out("### condominio gigante (top5 por R$/m2) ###")
d = dv[dv["listing_type"] == "apartamento"]
out(d.nlargest(5, "condo_m2")[["listing_id", "sale_price", "usable_area",
                               "monthly_condo_fee", "yearly_iptu"]].to_string())
out("")

# regras de plausibilidade
out("### CLASSIFICACAO esquematica (evidencia interna) ###")
apt = dv[dv["listing_type"] == "apartamento"]
out(f"Aptos com area < 20 m2: {(apt['usable_area'] < 20).sum()}  | area > 500 m2: {(apt['usable_area'] > 500).sum()}")
out(f"Aptos com preco/m2 < 1000: {(apt['preco_m2'] < 1000).sum()}  | > 20000: {(apt['preco_m2'] > 20000).sum()}")
out(f"Apartamento com 0 banheiros: {(apt['bathrooms'] == 0).sum()}  | 0 quartos: {(apt['bedrooms'] == 0).sum()}")
ter = dv[dv["listing_type"] == "terreno"]
out(f"Terrenos area 0: {(ter['usable_area'] == 0).sum()}  | area<20: {(ter['usable_area'] < 20).sum()}  | area>20000: {(ter['usable_area'] > 20000).sum()}")
com = dv[dv["listing_type"] == "comercial"]
out(f"Comerciais area 0: {(com['usable_area'] == 0).sum()}")
out("")

with open(os.path.join(OUT, "teste9_outliers.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("\n".join(L))