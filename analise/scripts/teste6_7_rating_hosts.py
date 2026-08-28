# -*- coding: utf-8 -*-
"""
Teste 6 - Semantica de star_rating=0.
Teste 7 - Consistencia dos atributos de hosts por owner_id.
"""
import pandas as pd
import numpy as np
import os

DATA = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\data"
OUT = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\analise\saida"

det = pd.read_csv(os.path.join(DATA, "Details_Itapema.csv"), encoding="utf-8")
hosts = pd.read_csv(os.path.join(DATA, "Hosts_ids_Itapema.csv"), encoding="utf-8")

L = []
def out(s=""): L.append(str(s))

out("TESTE 6 — star_rating=0")
r0_r0 = ((det["star_rating"] == 0) & (det["number_of_reviews"] == 0)).sum()
r0_r1 = ((det["star_rating"] == 0) & (det["number_of_reviews"] > 0)).sum()
r1_r0 = ((det["star_rating"] > 0) & (det["number_of_reviews"] == 0)).sum()
r1_r1 = ((det["star_rating"] > 0) & (det["number_of_reviews"] > 0)).sum()
out(f"star=0 & rev=0   : {r0_r0}")
out(f"star=0 & rev>0   : {r0_r1}")
out(f"star>0 & rev=0   : {r1_r0}")
out(f"star>0 & rev>0   : {r1_r1}")
out("")
# e os demais ratings?
for c in ["accuracy_rating", "cleanliness_rating", "checkin_rating", "communication_rating",
          "location_rating", "value_rating"]:
    z = det[(det[c] == 0) & (det["number_of_reviews"] > 0)].shape[0]
    out(f"{c}==0 com reviews>0: {z}")
out("")
out("guest_satisfaction_overall x star_rating (0,0 cruzam sempre?):")
out(f"star=0 & gust_sat>0: {((det['star_rating']==0)&(det['guest_satisfaction_overall']>0)).sum()}")
out(f"star>0 & gust_sat=0: {((det['star_rating']>0)&(det['guest_satisfaction_overall']==0)).sum()}")
out("")
out("=> interpretacao defensavel: 0 = sem avaliacao (nao nota real).")
out("=> mas confirmar com documentacao do dataset continua sendo recomendado.")
out("")

out("=" * 80)
out("TESTE 7 — Consistencia de atributos de hosts por owner_id")
owner_cols = ["is_superhost", "is_verified", "star_rating_host", "number_of_reviews_host",
              "years_host", "months_host"]
g = hosts.groupby("owner_id")
for c in owner_cols:
    nun = g[c].nunique()
    out(f"{c:<26} owners com valores CONSTANTES: {(nun==1).sum()} | com VARIACAO: {(nun>1).sum()}")
out("")
out(f"n owners: {hosts['owner_id'].nunique()}  linhas: {len(hosts)}")
dup = hosts[hosts.duplicated(subset=["owner_id"], keep=False)]
out(f"owners duplicados: {dup['owner_id'].nunique()}  linhas duplicadas: {len(dup)}")
out("")
out("### amostra de conflitos (se houver) ###")
confl = {}
for c in owner_cols:
    v = g[c].nunique()
    ids = hosts.groupby("owner_id")[c].nunique()
    trouble = ids[ids > 1]
    if len(trouble) > 0:
        confl[c] = len(trouble)
        ex = hosts[hosts["owner_id"].isin(trouble.index[:2])][
            ["owner_id", c, "years_host", "number_of_reviews_host", "star_rating_host"]]
        out(f"-- coluna {c}: {len(trouble)} owners conflitantes, exemplo:")
        out(ex.to_string())
out("")
if len(confl) == 0:
    out("NENHUMA coluna com constancia violada por owner -> hosts pode ser reduzido "
        "a uma linha por owner (dimensao de proprietario).")
else:
    out("cols conflitantes: " + str(confl))
    out("=> verificar se conflitos sao entre owners diferentes com mesmo id ou valores reais.")
out("")

# host_snapshot_date constante por owner?
out("host_snapshot_date: distinct values por owner:")
out(str(g["host_snapshot_date"].nunique().value_counts().to_dict()))

with open(os.path.join(OUT, "teste6_7_rating_hosts.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("\n".join(L))