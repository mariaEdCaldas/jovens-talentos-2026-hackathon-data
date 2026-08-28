# -*- coding: utf-8 -*-
"""
Teste 1 (VERSÃO AUDITADA) - Estrutura temporal de Price.
Corrige bug anterior ([ad.dt.date] nao era coluna) e investiga profundamente
o significado de aquisition_date x date x capturas.

Perguntas desta audicao:
- quantos timestamps existem por dia-calendario
- quantos listings aparecem em cada timestamp
- quais intervalos de date cada timestamp cobre
- se os intervalos sao sistematicamente particionados
- se existe padrao temporal explicando ausencia de sobreposicao
- se o conjunto de listings muda entre timestamps
- se cada captura representa janela parcial do calendario
- evidencias de que aquisition_date = momento da coleta e date = data de estadia
"""
import pandas as pd
import numpy as np
import os
from scipy.stats import spearmanr

DATA = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\data"
OUT = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\analise\saida"

p = pd.read_csv(os.path.join(DATA, "Price_AV_Itapema.csv"), encoding="utf-8")
p["ad"] = pd.to_datetime(p["aquisition_date"], errors="coerce")
p["date"] = pd.to_datetime(p["date"], errors="coerce")
p["cal"] = p["ad"].dt.strftime("%Y-%m-%d")
p["ts"] = p["ad"].dt.strftime("%Y-%m-%d %H:%M:%S")

L = []
def out(s=""): L.append(str(s))

out("=" * 100)
out("TESTE 1 (AUDITADO) - Granularidade temporal de Price")
out("=" * 100)
out(f"linhas={len(p)} listings={p['airbnb_listing_id'].nunique()} datas_estadia={p['date'].nunique()}")
out(f"aquisition_date sem hora? {not p['aquisition_date'].str.contains(r'\\d{2}:\\d{2}:\\d{2}').any()} | exemplo: {p['aquisition_date'].iloc[0]}")
out("")

# ---------- B: dias-calendario e timestamps ----------
out("### B.1 - Dias-calendario e timestamps por dia ###")
out(p["cal"].value_counts().sort_index().to_string())
ts_per_day = p.groupby("cal")["ts"].nunique()
out("timestamps distintos por dia:")
out(ts_per_day.to_string())
out("faixa horaria por dia:")
rng = p.groupby("cal")["ad"].agg(["min", "max"])
rng["dur_h"] = (rng["max"] - rng["min"]).dt.total_seconds() / 3600
out(rng.assign(dur_h=rng["dur_h"].round(3)).to_string())
out("")

# ---------- C: listings por timestamp ----------
out("### C.1 - Listings unicos por timestamp ###")
c_list = p.groupby("ts")["airbnb_listing_id"].nunique()
out(c_list.describe().round(2).to_string())
out("linhas por timestamp:")
c_lin = p.groupby("ts").size()
out(c_lin.describe().round(2).to_string())
out(f"n timestamps={len(c_list)} (media de pares listing,date por ts: {p.shape[0]/len(c_list):.1f})")
out("")

# ---------- D: janelas de date por timestamp ----------
out("### D.1 - Janela de datas de estadia coberta por cada timestamp ###")
win = p.groupby(["airbnb_listing_id", "cal", "ts"])["date"].agg(
    min_date="min", max_date="max", n_dates="count")
win["tam"] = (win["max_date"] - win["min_date"]).dt.days + 1
out("tamanho da janela (dias) por captura:")
out(win["tam"].describe().round(2).to_string())
out("histograma (top20):")
out(win["tam"].value_counts().sort_index().head(20).to_string())
out("")

# ---------- D.2: particionamento sistemático ----------
out("### D.2 - Particionamento: janelas consecutivas do mesmo (listing, dia) ###")
# prepara janelas por (listing, cal, ts)
win2 = p.groupby(["airbnb_listing_id", "cal", "ts"])["date"].agg(
    min_date="min", max_date="max").reset_index()
cnt_ts = p.groupby(["airbnb_listing_id", "cal"])["ts"].nunique().rename("num_ts")
win2 = win2.merge(cnt_ts, on=["airbnb_listing_id", "cal"])
multi2 = win2[win2["num_ts"] > 1]
results = {"contiguo": 0, "gap": 0, "overlap": 0, "pares": 0}
ordem_total_ok = 0
uni_contigue = 0
# grupos (listing,cal) com multiplos ts
grouped = multi2.groupby(["airbnb_listing_id", "cal"])
n_grupos_multi = len(grouped)
for key, grp in grouped:
    g = grp.sort_values("ts")
    starts = g["min_date"].values
    ends = g["max_date"].values
    ok_ordem = True
    contiguo_bloco = True
    for a in range(len(g) - 1):
        results["pares"] += 1
        if ends[a] < starts[a + 1]:
            gap_d = (starts[a + 1] - ends[a]).astype("timedelta64[D]").astype(int) - 1
            if gap_d == 0:
                results["contiguo"] += 1
            else:
                results["gap"] += 1
                contiguo_bloco = False
        else:
            results["overlap"] += 1
            contiguo_bloco = False
        if not (starts[a] <= ends[a] < starts[a + 1]):
            ok_ordem = False
    if ok_ordem:
        ordem_total_ok += 1
    if contiguo_bloco:
        uni_contigue += 1

out(f"(listing, dia) com multiplos ts (grupos analisados): {n_grupos_multi}")
out(f"pares de janelas consecutivas analisados: {results['pares']}")
out(f"  contiguas (end_i + 1 == start_j):  {results['contiguo']} ({100*results['contiguo']/max(results['pares'],1):.1f}%)")
out(f"  com GAP entre janelas:             {results['gap']} ({100*results['gap']/max(results['pares'],1):.1f}%)")
out(f"  com OVERLAP:                       {results['overlap']} ({100*results['overlap']/max(results['pares'],1):.1f}%)")
out(f"(listing, dia) onde NENHUM par viola ordenacao (janelas crescem): {ordem_total_ok}/{n_grupos_multi}")
out(f"(listing, dia) cuja uniao das janelas forma bloco contiguo: {uni_contigue}/{n_grupos_multi}")
out("")

# ---------- E: espaçamento temporal entre ts distintos consecutivos ----------
out("### E.1 - Espacamento temporal entre timestamps DISTINTOS consecutivos do mesmo (listing,dia) ###")
seq_gaps = []
for key, grp in grouped:
    ts_ord = sorted(pd.to_datetime(grp["ts"].unique()))
    for a in range(len(ts_ord) - 1):
        seq_gaps.append((ts_ord[a + 1] - ts_ord[a]).total_seconds() / 60)
seq = pd.Series(seq_gaps)
out(f"n gaps (ts distintos consecutivos do mesmo listing+dia): {len(seq)}")
out("gap em minutos:")
out(seq.describe().round(1).to_string())
out(f"gaps <=1s (aparente re-agrupamento): {100*((seq*60)<=1).mean():.1f}% | "
    f"gaps entre 5 e 25 min: {100*((seq>=5)&(seq<=25)).mean():.1f}%")
out("")

# ---------- F: correlação temporal ts -> janela ----------
out("### F.1 - A janela avanca com o tempo da captura? (correlacao por (listing,dia)) ###")
rho_list = []
for key, grp in grouped:
    g = grp.sort_values("ts")
    if len(g) >= 2:
        t = pd.to_datetime(g["ts"]).astype("int64").values
        md = g["min_date"].astype("int64").values
        r, _ = spearmanr(t, md)
        rho_list.append(r)
rho = pd.Series(rho_list)
out(f"(listing,dia) com >=2 ts: {len(rho)}")
out(f"correlacao Spearman ts->min_date : mediana {rho.median():.3f} | mean {rho.mean():.3f} | frac=1.0: {100*(rho==1.0).mean():.1f}%")
out("")

# ---------- G: janela parcial ----------
out("### G.1 - Evidencia de que cada captura e janela parcial ###")
out(f"tamanho da janela por captura: Q10={win['tam'].quantile(0.10):.0f} Q25={win['tam'].quantile(0.25):.0f} "
    f"Q50={win['tam'].quantile(0.50):.0f} Q75={win['tam'].quantile(0.75):.0f} Q90={win['tam'].quantile(0.90):.0f}")
out("(janela de 1 dia foi a mais frequente -> fatias pequenas; ver histograma em D.1)")
out("")
out("### G.2 - date é futura em relacao a captura? (data de estadia) ###")
future = (p["date"] >= p["ad"].dt.normalize()).mean()
out(f"linhas onde date >= data_da_captura (dia): {100*future:.2f}%")
out("linhas onde date <  data_da_captura: (inverso)")
out(f"  = {100*(1-future):.2f}%  | ver exemplos:")
ant = p[p["date"] < p["ad"].dt.normalize()][["airbnb_listing_id", "date", "aquisition_date"]]
out(ant.head(5).to_string() if len(ant) else "NENHUM caso (date sempre >= dia da captura)")
out("")
out("### G.3 - variacao por mes de estadia (sazonalidade de calendario) ###")
p["mes"] = p["date"].dt.to_period("M")
out(p.groupby("mes")["price"].agg(["count", "median", "mean"]).round(1).to_string())
out("")

with open(os.path.join(OUT, "teste1_auditado.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("\n".join(L))
print("FIM_TESTE1_AUDITADO_OK")