# -*- coding: utf-8 -*-
"""
P1 — Perfil de células e precisão (descritivo/metodológico).
NÃO gera ranking. NÃO escolhe vencedores. Define bases empíricas para limites
que serão fixados na METODOLOGIA FINAL CONGELADA.

Produz: analise/saida/p1_*.txt e analise/saida/p1_*.png
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common_p1p2 import (load_all, build_airbnb_table, build_viv_real_table,
                         cell_key, cells_ai, cells_vi, boot_ratio, OUT)

det, hosts, mesh, price, viv = load_all()
ai = build_airbnb_table(det, mesh, price)
vi = build_viv_real_table(viv)

L = []
def out(s=""): L.append(str(s))

out("=" * 100)
out("P1 — PERFIL DE CÉLULAS E PRECISÃO (descritivo/metodológico)")
out("=" * 100)
out(f"airbnb anúncios={len(ai)}  com preço={ai['has_price'].sum()}  ({100*ai['has_price'].mean():.1f}%)")
out(f"vivareal anúncios (dedup)={len(vi)}  lançamentos/frente-mar marcados={int(vi['is_lanc'].sum())}")
out("")

LEVELS = {"bairro_tipo_q": "bairro×tipo×quartos",
          "bairro_tipo": "bairro×tipo",
          "bairro": "bairro"}

# ---------- 1) e 2) Distribuição de n_ai e de n_vi_total / n_vi_com_sale_price por granularidade ----------
out("### D1. Distribuição de n_ai (Airbnb) por granularidade ###")
out("(n_total_ai = anúncios Airbnb na célula; n_com_price = com preço) ")
for lv, lab in LEVELS.items():
    c = cells_ai(ai, lv).copy()
    c["cov%"] = (100 * c["n_com_price"] / c["n_total_ai"].replace(0, np.nan)).round(1)
    out(f"\n-- {lab} --")
    out(f"n células={len(c)}")
    out(" n_total_ai: " + c["n_total_ai"].describe().round(1).to_string().replace("\n", " | "))
    out(" n_com_price:" + c["n_com_price"].describe().round(1).to_string().replace("\n", " | "))
    out(" células com n_com_price>=5: " + str(int((c["n_com_price"] >= 5).sum())) +
        f"  ({(100*(c['n_com_price']>=5)).mean():.0f}%)")
    out(" células com n_com_price>=10: " + str(int((c["n_com_price"] >= 10).sum())))
    out(" distribuição de n_com_price (top10 contagens): " +
        str(c["n_com_price"].value_counts().head(10).to_dict()))
out("")

out("### D2. Distribuição de n_vi_total e n_vi_com_sale_price (VivaReal) por granularidade ###")
out("(n_vi_total = anúncios VivaReal elegíveis após dedup, com ou sem preço; ")
out(" n_vi_com_sale_price = anúncios com sale_price válido, efetivamente usados na estimativa)")
for lv, lab in LEVELS.items():
    cn = cells_vi(vi, lv, excl_lanc=False)
    ce = cells_vi(vi, lv, excl_lanc=True)
    out(f"\n-- {lab} --")
    out(" n células=" + str(len(cn)))
    out(" n_vi_total (sem excluir lançamento): " + cn["n_vi_total"].describe().round(1).to_string().replace("\n", " | "))
    out(" n_vi_com_sale_price (sem excluir lançamento): " + cn["n_vi_com_sale_price"].describe().round(1).to_string().replace("\n", " | "))
    out(" n_vi_total (excluindo lançamentos): " + ce["n_vi_total"].describe().round(1).to_string().replace("\n", " | "))
    out(" n_vi_com_sale_price (excluindo lançamentos): " + ce["n_vi_com_sale_price"].describe().round(1).to_string().replace("\n", " | "))
    out(" células com n_vi_com_sale_price>=5 (sem lanç): " + str(int((ce["n_vi_com_sale_price"] >= 5).sum())))
    out(" células com n_vi_com_sale_price>=10 (sem lanç): " + str(int((ce["n_vi_com_sale_price"] >= 10).sum())))
    out(" fração média n_vi_com_sale_price/n_vi_total (sem lanç): " +
        f"{ce['n_vi_com_sale_price'].divide(ce['n_vi_total'].replace(0, np.nan)).mean():.3f}")
out("")

# ---------- 3) Cobertura Price por célula ----------
out("### D3. Cobertura Price (has_price%) por célula ###")
cov_rows = []
for lv in LEVELS:
    c = cells_ai(ai, lv).copy()
    c["cov%"] = 100 * c["n_com_price"] / c["n_total_ai"].replace(0, np.nan)
    cov_rows.append((lv, c))
for lv, c in cov_rows:
    good = c[c["n_total_ai"] >= 5]
    out(f"-- {LEVELS[lv]} (células com n_total_ai>=5): n={len(good)}")
    out(good["cov%"].describe().round(1).to_string().replace("\n", " | "))
    out(" P25 da cobertura: " + f"{good['cov%'].quantile(0.25):.1f}% | mediana: "
        + f"{good['cov%'].quantile(0.5):.1f}%" )
out("")

# ---------- 4) Largura do IC95 da razão vs n (bootstrap por cluster) ----------
out("### D4. IC95 da razão R — largura vs n_ai / n_vi_com_sale_price ###")
print("computando bootstraps (B=1000/célula)...")
lv = "bairro_tipo_q"
ca = cells_ai(ai, lv).set_index(cell_key(ai, lv))
cv = cells_vi(vi, lv, excl_lanc=True).set_index(cell_key(vi, lv))

rows = []
for key, r in ca.iterrows():
    k0, k1, k2 = key[0], key[1], key[2]
    d = ai[(ai["bairro"] == k0) & (ai["tipo"] == k1) & (ai["q"] == k2)]
    d = d[(d["has_price"] == 1) & d["d_a"].notna()]
    if len(d) == 0:
        continue
    if key not in cv.index:
        continue
    n_ai_c = int(len(d))
    n_vi_c_total = int(cv.loc[key, "n_vi_total"])
    n_vi_c = int(cv.loc[key, "n_vi_com_sale_price"])
    V = vi[(vi["bairro"] == k0) & (vi["tipo"] == k1) & (vi["q"] == k2) & ~vi["is_lanc"]]
    Vpos = V.loc[V["sale_price"].gt(0), "sale_price"]
    if len(Vpos) == 0:
        continue
    dvals = d["d_a"].values
    Robs, half, ic = boot_ratio(dvals, Vpos.values, B=1000)
    rows.append({"n_ai": n_ai_c, "n_vi_com_sale_price": n_vi_c, "n_vi_total": n_vi_c_total,
                 "R": Robs, "half": half, "ic_lo": ic[0], "ic_hi": ic[1]})
ci = pd.DataFrame(rows)
out(f"células com dados p/ bootstrap: {len(ci)}")
if len(ci):
    out("meia-largura relativa do IC95(R): " +
        ci["half"].describe().round(3).to_string().replace("\n", " | "))
    out("  mediana half=" + f"{ci['half'].median():.3f}")
    out("  fração células com half<=0.60: " + f"{(ci['half']<=0.60).mean():.0%}")
    out("")
    out("half por faixa de n_ai:")
    ci["n_ai_b"] = pd.cut(ci["n_ai"], [0, 4, 9, 19, 49, 10**6], labels=["1-4", "5-9", "10-19", "20-49", "50+"])
    g = ci.groupby("n_ai_b", observed=False)["half"].agg(["count", "median", "mean", "max"])
    out(g.round(3).to_string())
    out(" (half <=0.60 é 'adequado'; <=0.35 é 'bom')")
out("")

# Subsampling study: how half-width decreases with n (descritivo, LOCAL)
out("### D4b. Estudo de subsampling na maior célula (meia praia × apartamento × 3) ###")
out("AVISO: resultado LOCAL à maior célula; com amostragem com reposição antes do bootstrap;")
out("não é demonstração de tamanho amostral universal.")
big = ai[(ai["bairro"] == "meia praia") & (ai["tipo"] == "apartamento") & (ai["q"] == "3")]
big_p = big[big["has_price"] == 1]
big_v = vi[(vi["bairro"] == "meia praia") & (vi["tipo"] == "apartamento") & (vi["q"] == "3") & ~vi["is_lanc"]]
out(f"n_ai={len(big_p)}, n_vi_total={len(big_v)}, n_vi_com_sale_price={int(pd.to_numeric(big_v['sale_price'], errors='coerce').gt(0).sum())}")
if len(big_p) >= 20 and len(big_v):
    dvals = big_p["d_a"].dropna().values
    Vpos = big_v.loc[big_v["sale_price"].gt(0), "sale_price"].values
    ss = []
    for m in [3, 5, 8, 12, 20, 30, 50]:
        hs = []
        for rep in range(15):
            rng = np.random.default_rng(rep)
            i1 = rng.integers(0, len(dvals), size=min(m, len(dvals)))
            i2 = rng.integers(0, len(Vpos), size=min(m, len(Vpos)))
            Robs, half, ic = boot_ratio(dvals[i1], Vpos[i2], B=400)
            hs.append(half)
        ss.append({"n": m, "half_med": np.median(hs), "half_p75": np.quantile(hs, 0.75)})
    ssd = pd.DataFrame(ss)
    out(ssd.round(3).to_string())
    out("=> evidência local de que a precisão (half) melhora com n nesta célula;")
    out("   o GATE de precisão da metodologia continua sendo half IC95(R) ≤ 0,60 medido por célula,")
    out("   não um n fixo (ex.: 8) universal.")
    plt.figure(figsize=(7, 4))
    plt.plot(ssd["n"], ssd["half_med"], marker="o")
    plt.axhline(0.60, color="r", ls="--", label="gate 60% (por célula)")
    plt.axhline(0.35, color="g", ls="--", label="bom 35% (referência)")
    plt.xlabel("n (amostrado por cluster)"); plt.ylabel("meia-largura relativa IC95(R)")
    plt.title("Meia-largura IC95(R) × n — subsampling (maior célula) — evidência local")
    plt.legend(); plt.grid(alpha=.3)
    plt.savefig(os.path.join(OUT, "p1_subsampling.png"), dpi=110)
    plt.close()
out("")

# ---------- 5) n_datas e estabilidade da diária individual ----------
out("### D5. n_datas dos anúncios com preço e estabilidade da mediana individual ###")
dp = ai[ai["has_price"] == 1].copy()
out(dp["n_datas"].describe().round(1).to_string().replace("\n", " | "))
out("distribuição n_datas (contagem de anúncios): " + str(dp["n_datas"].value_counts().sort_index().head(15).to_dict()))
out("")

# per-anúncio: relative SE of median across nights (bootstrap das noites)
print("computando SE da mediana por noite por anúncio...")
pp = price[["airbnb_listing_id", "date", "price"]].copy()
pp["price"] = pp["price"].astype(float)
pn = pp.groupby(["airbnb_listing_id", "date"])["price"].median().reset_index()
se_results = []
rng2 = np.random.default_rng(11)
for lid, grp in pn.groupby("airbnb_listing_id"):
    n = len(grp)
    if n < 3:
        continue
    vals = grp["price"].values
    med = np.median(vals)
    if med == 0:
        continue
    K = 200
    idx = rng2.integers(0, n, size=(K, n))
    meds = np.median(vals[idx], axis=1)
    relSE = meds.std() / med
    se_results.append({"n_datas": n, "relSE": relSE})
sed = pd.DataFrame(se_results)
out(f"anúncios com n>=3: {len(sed)}")
sed["nb"] = pd.cut(sed["n_datas"], [2, 4, 6, 10, 15, 20, 30, 40, 60, 110],
                   labels=["3-4", "5-6", "7-10", "11-15", "16-20", "21-30", "31-40", "41-60", "61+"])
g = sed.groupby("nb", observed=False)["relSE"].agg(
    count="count",
    med="median",
    mean="mean",
    p90=lambda s: s.quantile(0.90)).round(3)
out("relSE da mediana individual por faixa de n_datas (bootstrap das noites sob iid):")
out(g.round(3).to_string())
out("=> ATENÇÃO: bootstrap iid das noites NÃO captura sazonalidade/dia da semana/feriados/dependência")
out("   temporal do preço. Serve apenas como análise exploratória de estabilidade; NÃO é tamanho")
out("   amostral estatisticamente comprovado. O limiar operacional n_datas (S2) é critério de")
out("   negócio conservador, apoiado nessa exploração.")
out("")
plt.figure(figsize=(8, 4))
gp = sed.copy()
gp["nb"] = pd.cut(gp["n_datas"], [2, 4, 6, 10, 15, 20, 30, 40, 60, 110])
gm = gp.groupby("nb", observed=False)["relSE"].median()
gm.plot(marker="o")
plt.axhline(0.10, color="r", ls="--", label="10%")
plt.axhline(0.15, color="orange", ls="--", label="15%")
plt.title("Mediana do relSE da diária individual × n_datas")
plt.ylabel("relSE (desvio padrão/mediana)"); plt.legend(); plt.grid(alpha=.3)
plt.savefig(os.path.join(OUT, "p1_ndatas_estabilidade.png"), dpi=110)
plt.close()

# ---------- 6) Granularidade de quartos ----------
out("### D6. Granularidade de quartos 1|2|3|4+ ###")
out("distribuição de número_de_bedrooms (todos / com preço):")
det["sb"] = det["number_of_bedrooms"].apply(lambda x: "0" if x == 0 else ("1" if x <= 1 else ("2" if x == 2 else ("3" if x == 3 else "4+"))))
det["hp"] = det["airbnb_listing_id"].isin(set(price["airbnb_listing_id"])).astype(int)
t = det.groupby("sb").agg(n=("airbnb_listing_id", "size"),
                          n_price=("hp", "sum")).reset_index()
out(t.to_string())
out("")
out("0 (zero quartos): " + str(int(t[t['sb'] == '0']['n'].sum())) +
    " anúncios — tratar como 'sem informação'? (n com preço: "
    + str(int(t[t['sb'] == '0']['n_price'].sum())) + ")")
out("")

# avaliar piso n>=5: quantas células finas têm n_ai>=5 é razoável dado a perda
out("### D7. Avaliação do piso n>=5 (quantas células perde) ###")
ca2 = cells_ai(ai, "bairro_tipo_q")
total_cells = len(ca2)
with_price_cells = int((ca2["n_com_price"] > 0).sum())
out(f"células finas totais={total_cells} | com >=1 preço={with_price_cells}")
for k in [1, 3, 5, 8, 10, 15, 20]:
    out(f"  células com n_com_price>={k}: {int((ca2['n_com_price']>=k).sum())}")
out("")

# espaçamento de piso vs precisao: reportar cross n_ai x n_vi_com_sale_price
if len(ci):
    out("### D8. Meia-largura × n_ai × n_vi_com_sale_price (mediana) ###")
    ci["n_vi_b"] = pd.cut(ci["n_vi_com_sale_price"], [0, 4, 9, 19, 10**6], labels=["1-4", "5-9", "10-19", "20+"])
    pvt = ci.pivot_table(index="n_ai_b", columns="n_vi_b", values="half",
                         aggfunc="median").round(3)
    out(pvt.to_string())
    out("")

out("FIM_P1")

with open(os.path.join(OUT, "p1_resultados.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("\n".join(L))