"""
Teste Q1 - Por que apenas 1005 dos 4441 listings possuem dados em Price?

Hipoteses testadas (todas testadas empiricamente, sem inferencia):
  H1a: a presenca de preco depende do listing_type (hotel/profissional?).
  H1b: a presenca de preco depende de ter reviews (atividade historica).
  H1c: a presenca de preco depende do volume de reviews.
  H1d: a presenca de preco depende de flags de profissionalismo (is_professional,
       is_guest_favorite, is_superhost).
  H1e: a presenca de preco depende do bairro (localizacao).
  H1f: a presenca de preco depende do "mesh_first_seen" (inicio do rastreamento)?
       (hipotese: listings mais antigos de rastreio teriam preco).

Metodo: comparacao descritiva entre o grupo com preco (n=1005) e sem preco (n=3436),
mais teste qui-quadrado para variaveis categoricas e comparacao de medias.
"""
import pandas as pd
import numpy as np
import os
import io
from scipy import stats

import sys
sys.path.insert(0, os.path.dirname(__file__))
from prep import prepare

OUT = os.path.join(os.path.dirname(__file__), "..", "output")

buf = io.StringIO()

def line(s=""):
    buf.write(str(s) + "\n")

def main():
    d = prepare()
    det = d["det"]
    hosts = d["hosts"].drop_duplicates("owner_id")

    line("=" * 100)
    line("Q1 - POR QUE APENAS 1005 DOS 4441 LISTINGS TEM PRECO?")
    line("=" * 100)
    line(f"com preco: {det['has_price'].sum()} | sem preco: {(~det['has_price']).sum()} | total: {len(det)}")
    line()

    g = det.groupby("has_price")

    # H1a listing_type
    line("-- H1a: listing_type x tem preco --")
    ct = pd.crosstab(det["listing_type"], det["has_price"], margins=True)
    line(ct.to_string())
    chi2, p, dof, _ = stats.chi2_contingency(
        pd.crosstab(det["listing_type"], det["has_price"]).values)
    line(f"chi2={chi2:.1f} p={p:.2e} (n>=5 em cada celula recomendado)")
    line()

    # H1b/H1c reviews
    line("-- H1b: tem reviews (number_of_reviews>0) x tem preco --")
    ct = pd.crosstab(det["has_reviews"], det["has_price"], margins=True)
    line(ct.to_string())
    chi2, p, dof, _ = stats.chi2_contingency(
        pd.crosstab(det["has_reviews"], det["has_price"]).values)
    line(f"chi2={chi2:.1f} p={p:.2e}")
    line()
    line("-- H1c: numero de reviews (mediana/descritiva) por grupo --")
    line(det.groupby("has_price")["number_of_reviews"].describe().to_string())
    # Mann-Whitney (n~1000 vs ~3400, distribuicoes assimetricas)
    mw = stats.mannwhitneyu(
        det.loc[det["has_price"], "number_of_reviews"],
        det.loc[~det["has_price"], "number_of_reviews"],
        alternative="two-sided")
    line(f"Mann-Whitney U={mw.statistic:.0f} p={mw.pvalue:.2e}")
    line()
    # tau de kendall entre ter preco(0/1) e reviews
    tau, tp = stats.kendalltau(det["has_price"].astype(int), det["number_of_reviews"])
    line(f"Kendall tau(reviews, has_price) = {tau:.3f} (p={tp:.2e})")
    line()

    # H1d flags
    line("-- H1d: flags profissionalismo --")
    for col in ["is_professional", "is_guest_favorite", "can_instant_book"]:
        flag = det[col].replace({True: "True", False: "False"})
        ct = pd.crosstab(flag, det["has_price"], margins=True)
        line(f"--- {col} ---")
        line(ct.to_string())
        ct2 = pd.crosstab(flag.fillna("NaN"), det["has_price"]).values
        chi2, p, dof, _ = stats.chi2_contingency(ct2)
        line(f"chi2={chi2:.1f} p={p:.2e}")
        line()
    # superhost: merge com hosts (dedup owner)
    det2 = det.merge(hosts[["owner_id", "is_superhost"]], on="owner_id", how="left")
    ct = pd.crosstab(det2["is_superhost"], det2["has_price"], margins=True)
    line("--- is_superhost (do host do listing) ---")
    line(ct.to_string())
    chi2, p, dof, _ = stats.chi2_contingency(
        pd.crosstab(det2["is_superhost"], det2["has_price"]).values)
    line(f"chi2={chi2:.1f} p={p:.2e}")
    line()

    # H1e bairro
    line("-- H1e: bairro (suburb_norm do mesh) x tem preco --")
    ct = pd.crosstab(det["suburb_norm"], det["has_price"], margins=True)
    line(ct.to_string())
    chi2, p, dof, _ = stats.chi2_contingency(
        pd.crosstab(det["suburb_norm"], det["has_price"]).values)
    line(f"chi2={chi2:.1f} p={p:.2e}")
    line(f"- share com preco por bairro (taxa de cobertura):")
    cov = det.groupby("suburb_norm")["has_price"].agg(["sum", "count"])
    cov["share"] = (cov["sum"] / cov["count"]).round(3)
    line(cov.sort_values("count", ascending=False).to_string())
    line()

    # H1f mesh_first_seen
    line("-- H1f: ano de primeiro rastreio no mesh x tem preco --")
    det["first_year"] = det["mesh_first_seen_dt"].dt.year
    ct = pd.crosstab(det["first_year"].fillna("NA").astype(str), det["has_price"], margins=True)
    line(ct.to_string())
    mw = stats.mannwhitneyu(
        det.loc[det["has_price"], "mesh_first_seen_dt"].dropna().astype("int64"),
        det.loc[~det["has_price"], "mesh_first_seen_dt"].dropna().astype("int64"))
    line(f"Mann-Whitney (mesh_first_seen) p={mw.pvalue:.2e}")
    line()

    # tempo: reviews por ano de host (rastejar qdo comecou)
    line("-- H1g (contexto): years_host/media reviews por ano --")
    det2b = det2.merge(hosts[["owner_id", "years_host", "months_host"]],
                       on="owner_id", how="left", suffixes=('', '_h2'))
    line(det2b.groupby("has_price")[["years_host", "months_host"]].median().to_string())
    line()

    line("-- Resumo fatos Q1 --")
    line("(1) Cobertura de price = 1005/4441 = {:.1%}".format(det['has_price'].mean()))
    line("(2) Diferencas de composicao entre grupos (ver tabelas crosstab acima).")
    line("(3) Importante: cobertura por bairro varia (ver tabela share).")
    line()

    out = buf.getvalue()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "t1_q1_presenca_preco.txt"), "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote t1_q1_presenca_preco.txt", len(out))


if __name__ == "__main__":
    main()