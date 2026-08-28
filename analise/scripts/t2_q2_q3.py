"""
Teste Q2 e Q3 - aquisition_date e granularidade das capturas de preco; e
como representar multiplas observacoes.

Q2 - O que e aquisition_date no Price?
  * e um timestamp por linha (data+minuto+segundo) = momento da raspagem daquele
    listing/foto de calendario.
  * Testamos: quantos dias-calendario distintos de captura existem; quantas
    "rodadas" por listing; se cada listing foi capturado em 1, 2 ou 3 dias.
  * Tambem testamos se o preco muda ENTRE dias de captura para o mesmo
    (listing, data de estadia) -> evidencia de capturas longitudinais reais.

Q3 - Como representar multiplas observacoes de preco?
  * Compara 'ultima captura' vs 'mediana entre capturas' vs 'primeira' para cada
    (listing, data de estadia).
  * Quantifica quantos pares mudam de preco entre capturas e a magnitude.
"""
import pandas as pd
import numpy as np
import os
import io

import sys
sys.path.insert(0, os.path.dirname(__file__))
from prep import prepare

OUT = os.path.join(os.path.dirname(__file__), "..", "output")
buf = io.StringIO()

def line(*a):
    buf.write(" ".join(str(x) for x in a) + "\n")

def main():
    d = prepare()
    price = d["price"].copy()

    line("=" * 100)
    line("Q2 - O QUE E AQUISITION_DATE? TRUE GRANULARITY DAS CAPTURAS")
    line("=" * 100)
    price["cap_dt"] = pd.to_datetime(price["aquisition_date"], errors="coerce")
    price["cap_day"] = price["cap_dt"].dt.date
    price["stay_dt"] = pd.to_datetime(price["date"], errors="coerce")

    line("total de linhas:", len(price))
    line("distinct listing:", price["airbnb_listing_id"].nunique())
    line("distinct timestamps de captura (aquisition_date):", price["aquisition_date"].nunique())
    line("distinct DIAS-calendario de captura:",
         price["cap_day"].nunique())
    line()
    line("linhas por dia de captura:")
    line(price["cap_day"].value_counts().sort_index().to_string())
    line()

    # qtd de dias distintos de captura POR listing
    line("-- dias de captura por listing (1, 2 ou 3 dias) --")
    days_per = price.groupby("airbnb_listing_id")["cap_day"].nunique()
    line(days_per.value_counts().sort_index().to_string())
    line(f"share com 3 dias de captura: {(days_per==3).mean():.1%}")
    line()
    line("-- capturas (linhas) por listing: descritiva --")
    line(price.groupby("airbnb_listing_id")["cap_dt"].nunique().describe().to_string())
    line()

    # Existe variacao de preco entre dias de captura para o mesmo par?
    # Precisamos do preco NA MESMA data de estadia do mesmo listing em capturas diferentes
    line("=" * 100)
    line("Q3 - REPRESENTACAO DE MULTIPLAS OBSERVACOES DE PRECO")
    line("=" * 100)
    # pivo: para cada par (listing, stay_date), pegue preco por dia de captura
    keys = ["airbnb_listing_id", "stay_dt"]
    g = price.groupby(keys + ["cap_day"])["price"].first().unstack("cap_day")
    line("pares (listing, stay_date) totais (com qualquer captura):", len(g))
    line("pares com captura em 1 dia:", int((g.notna().sum(axis=1) == 1).sum()))
    line("pares com captura em 2 dias:", int((g.notna().sum(axis=1) == 2).sum()))
    line("pares com captura em 3 dias:", int((g.notna().sum(axis=1) == 3).sum()))
    line()

    # para pares com >=2 dias: quanto variou o preco entre o 1o e o ultimo dia de captura?
    multi = g[g.notna().sum(axis=1) >= 2]
    first_day = g.columns.min()
    last_day = g.columns.max()
    line(f"-- pares com >=2 capturas: {len(multi)} --")
    line(f"(usando 1a captura day={first_day} vs ultima captura day={last_day})")
    row = multi.dropna(subset=[first_day, last_day])
    p1 = row[first_day]
    p2 = row[last_day]
    line("pares com preco tanto na 1a quanto na ultima captura:", len(row))
    line("pares onde o preco MUDOU entre 1a e ultima captura:",
         int((p1 != p2).sum()), f"({(p1!=p2).mean():.1%})")
    line("pares onde o preco NAO mudou:", int((p1 == p2).sum()))
    rel = (p2 - p1) / p1
    line("variacao relativa (ultima/1a - 1):")
    line(rel.describe().to_string())
    line("quantis da variacao absoluta (R$):")
    line((p2 - p1).abs().quantile([0.5, 0.75, 0.9, 0.95, 0.99]).to_string())
    line()

    # Representacoes candidatas - comparacao para o par (listing, stay_date)
    # 1) ultima captura (max cap_dt)
    # 2) mediana entre capturas
    # 3) primeira captura
    line("-- Comparacao 3 representacoes por (listing, stay_date) --")
    price["stay_or_cap"] = price["cap_dt"]
    last = (price.sort_values("cap_dt")
            .groupby(keys)["price"].last().rename("last"))
    first = (price.sort_values("cap_dt")
             .groupby(keys)["price"].first().rename("first"))
    med = (price.groupby(keys)["price"].median().rename("median"))
    comp = pd.concat([first, med, last], axis=1)
    comp["last_vs_first_abs"] = (comp["last"] - comp["first"]).abs()
    comp["last_vs_median_abs"] = (comp["last"] - comp["median"]).abs()
    line("total pares:", len(comp))
    line("pares onde last != first:", int((comp["last"] != comp["first"]).sum()),
         f"({(comp['last']!=comp['first']).mean():.1%})")
    line("pares onde last != median:", int((comp["last"] != comp["median"]).sum()),
         f"({(comp['last']!=comp['median']).mean():.1%})")
    line("|last-first| em R$  :", comp["last_vs_first_abs"].describe().to_dict())
    line("|last-median| em R$ :", comp["last_vs_median_abs"].describe().to_dict())
    line()
    line("MEDIANA do preco por (listing, stay_date) — stat final:")
    line("(esta eh a base sugerida para 'preco por noite' em analise futura)")
    line("  ultima=(max cap) representaria o preco 'atual' ao fim do rastreio;")
    line("  mediana entre capturas reduziria ruido de captura sequencial.")
    line()

    # Magnitude do ruido: se representarmos por ultima captura vs por mediana,
    # qual a discrepancia media por IMOVEL (agregado ao nivel de listing)?
    line("-- Agregado ao nivel de IMOVEL: preco medio por noite (ultima vs mediana) --")
    last_agg = comp["last"].groupby(level=0).mean().rename("mean_last")
    med_agg = comp["median"].groupby(level=0).mean().rename("mean_median")
    agg = pd.concat([last_agg, med_agg], axis=1)
    agg["diff"] = (agg["mean_last"] - agg["mean_median"]).abs()
    line(agg["diff"].describe().to_string())
    line("fracao de imoveis com |diff|>R$50:", f"{(agg['diff']>50).mean():.1%}")
    line()

    out = buf.getvalue()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "t2_q2_q3_granularidade.txt"), "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote t2_q2_q3_granularidade.txt", len(out))


if __name__ == "__main__":
    main()