# -*- coding: utf-8 -*-
"""
Teste 11 - Capacidade analítica (fatos de apoio apenas).
Coleta numeros que sustentam as respostas sobre ocupacao/receita/ROI/potencial.
"""
import pandas as pd
import numpy as np
import os

DATA = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\data"
OUT = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\analise\saida"

det = pd.read_csv(os.path.join(DATA, "Details_Itapema.csv"), encoding="utf-8")
price = pd.read_csv(os.path.join(DATA, "Price_AV_Itapema.csv"), encoding="utf-8")
viv = pd.read_csv(os.path.join(DATA, "VivaReal_Itapema.csv"), encoding="utf-8")

L = []
def out(s=""): L.append(str(s))

out("TESTE 11 — Capacidade analitica (fatos de apoio)")
out("")
out("### Ocupacao/receita: existe coluna? ###")
report_cols = [c for c in det.columns if any(k in c.lower() for k in
              ["occup", "book", "reserv", "calendar", "avail", "revenue", "revpar", "sold"])]
out("Details colunas de ocupacao/reserva/receita: " + str(report_cols if report_cols else "NENHUMA"))
out("Price colunas: " + str(list(price.columns)))
out(f"VivaReal posui preco de ALUGUEL (rental_price)? n nao-nulo: {int(viv['rental_price'].notna().sum())} de {len(viv)}")
out(f"details min_nights valores unicos: {det['min_nights'].unique().tolist()} (impossivel usar para politica de estadia)")
out("")
out("### O que temos = preco anunciado por noite ###")
p = price.copy()
p["date"] = pd.to_datetime(p["date"])
p["mes"] = p["date"].dt.to_period("M")
por_mes = p.groupby("mes")["price"].agg(["count", "median", "mean"]).round(1)
out("Distribuicao do preco por noite por mes de estadia (jan-abr/2025):")
out(por_mes.to_string())
out("")
daily_cap = p["price"].quantile([0.25, 0.5, 0.75])
out("preco/noite percentis (toda a amostra):")
out(daily_cap.to_string())
out("")
out("### Duracao do periodo coberto ###")
out(f"primeira data de estadia: {p['date'].min().date()} | ultima: {p['date'].max().date()} (~3,5 meses de calendario)")
out("")

with open(os.path.join(OUT, "teste11_capacidade.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("\n".join(L))