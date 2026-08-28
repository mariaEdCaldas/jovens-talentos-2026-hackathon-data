# -*- coding: utf-8 -*-
"""
Teste 3 - Estabilidade e direcao das variacoes de preco entre capturas.
Para cada (listing, date): n capturas, min/max/mediana/media/std, amplitude relativa,
variacao prim->ult (abs e %), direcao. Segmenta por intervalo entre dias de captura.
"""
import pandas as pd
import numpy as np
import os

DATA = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\data"
OUT = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\analise\saida"

p = pd.read_csv(os.path.join(DATA, "Price_AV_Itapema.csv"), encoding="utf-8")
p["ad"] = pd.to_datetime(p["aquisition_date"])
p["ts"] = p["ad"].dt.strftime("%Y-%m-%d %H:%M:%S")
p["cal"] = p["ad"].dt.strftime("%Y-%m-%d")

g = p.sort_values("ts").groupby(["airbnb_listing_id", "date"])["price"]
df = pd.DataFrame({
    "n_cap": g.size(),
    "price_min": g.min(),
    "price_max": g.max(),
    "price_med": g.median(),
    "price_mean": g.mean(),
    "price_std": g.std(),
})

df["ampl_rel"] = (df["price_max"] - df["price_min"]) / df["price_med"]
df["pct_var_max_min"] = 100 * (df["price_max"] - df["price_min"]) / df["price_min"]

# variacao prim->ult por (listing,date)
f = p.sort_values("ts").groupby(["airbnb_listing_id", "date"], as_index=False)
prim = f.first().rename(columns={"price": "p_prim", "ts": "ts_prim"})[["airbnb_listing_id", "date", "p_prim", "ts_prim"]]
ult = f.last().rename(columns={"price": "p_ult", "ts": "ts_ult"})[["airbnb_listing_id", "date", "p_ult", "ts_ult"]]
comb = prim.merge(ult, on=["airbnb_listing_id", "date"])
comb["cal_prim"] = comb["ts_prim"].str[:10]
comb["cal_ult"] = comb["ts_ult"].str[:10]
nc = df.reset_index()[["airbnb_listing_id", "date", "n_cap"]]
comb = comb.merge(nc, on=["airbnb_listing_id", "date"], how="left")

L = []; 
def out(s=""): L.append(str(s))

out("TESTE 3 — Estabilidade/direcao de preco entre capturas")
out(f"grupos (listing,date): {len(df)}")
out("distribuicao de n_capturas: ")
out(df["n_cap"].value_counts().sort_index().to_string())
out("")
out("### amplitude relativa (max-min)/mediana por n_capturas ###")
df["ncap_b"] = np.minimum(df["n_cap"], 8)
out(df.groupby("ncap_b")["ampl_rel"].describe().round(4).to_string())
out("")
out("### variacao % entre min e max (percentis) ###")
out(df.groupby("ncap_b")["pct_var_max_min"].quantile([0.5, 0.75, 0.9, 0.99]).round(2).to_string())
out("")
out("### fração de pares com variacao nula / pequena ###")
out(f"ampl_rel==0 (preco constante): {100*(df['ampl_rel']==0).mean():.2f}%")
out(f"ampl_rel < 0.10 (variacao <10% da mediana): {100*(df['ampl_rel']<0.10).mean():.2f}%")
out(f"ampl_rel > 0.25: {100*(df['ampl_rel']>0.25).mean():.2f}%")
out(f"ampl_rel > 0.50: {100*(df['ampl_rel']>0.50).mean():.2f}%")
out("")

out("### variacao prim->ult (abs e %) ###")
comb["vd_abs"] = comb["p_ult"] - comb["p_prim"]
comb["vd_pct"] = 100 * comb["vd_abs"] / comb["p_prim"]
comb["dir"] = np.sign(comb["vd_abs"])
m = comb[comb["n_cap"] > 1]
out(f"pares com >1 captura: {len(m)}")
out("direcao da variacao prim->ult:")
out(m["dir"].value_counts().to_string())
out(f"% sem mudanca: {100*(m['dir']==0).mean():.1f}%  subiu: {100*(m['dir']>0).mean():.1f}%  caiu: {100*(m['dir']<0).mean():.1f}%")
out("")
out("vd_pct percentis (pares que mudaram): ")
m2 = m[m["dir"] != 0]
out(m2["vd_pct"].quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(2).to_string())
out("")

out("### segmentacao por intervalo de dias entre capturas (prim->ult) ###")
def seg(r):
    d = (pd.to_datetime(r["cal_ult"]) - pd.to_datetime(r["cal_prim"])).days
    if d == 1: return "06/01_para_07/01 (1 dia)"
    if d == 13: return "07/01_para_20/01 (13 dias)"
    if d == 14: return "06/01_para_20/01 (14 dias)"
    if d == 0: return "mesmo_dia"
    return f"outro(d={d})"
m["seg"] = m.apply(seg, axis=1)
out(m.groupby("seg")["dir"].apply(lambda s: s.value_counts().to_dict()).to_string())
out(m.groupby("seg")["vd_pct"].describe().round(2).to_string())
out("")

out("### verificar se 'mesmo_dia' tem mudanca (capturas no mesmo dia p/ mesma noite) ###")
md = m[m["seg"] == "mesmo_dia"]
out(f"pares mesmo_dia: {len(md)} | dos quais mudaram prim->ult: {0 if len(md)==0 else 100*(md['dir']!=0).mean():.1f}%")
out("(no mesmo dia, uma determinada noite nao costuma ser capturada 2x - ver Teste 1: fatias disjuntas)")
out("")

# por lista: fracao de datas com mudanca (pode indicar lista mais volátil)
out("### volatilidade por listing ###")
per_listing = m.groupby("airbnb_listing_id").agg(
    n_pares=("vd_pct", "size"),
    frac_mudou=("dir", lambda s: (s != 0).mean()),
    med_ampl=("vd_pct", lambda s: np.median(np.abs(s))))
out(per_listing.describe().round(3).to_string())
out(f"fracao de listings com >=50% das datas mudando: {100*(per_listing['frac_mudou']>=0.5).mean():.1f}%")
out("")

with open(os.path.join(OUT, "teste3_preco_estabilidade.txt"), "w", encoding="utf-8") as fp:
    fp.write("\n".join(L))
print("\n".join(L))