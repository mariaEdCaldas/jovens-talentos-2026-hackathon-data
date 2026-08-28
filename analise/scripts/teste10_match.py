# -*- coding: utf-8 -*-
"""
Teste 10 - Possibilidade de relacionamento indireto Airbnb x VivaReal.
Avalia estrategias progressivas de agregacao. NAO transforma agregacao em match individual.
"""
import pandas as pd
import numpy as np
import unicodedata
import os

DATA = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\data"
OUT = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\analise\saida"

det = pd.read_csv(os.path.join(DATA, "Details_Itapema.csv"), encoding="utf-8")
mesh = pd.read_csv(os.path.join(DATA, "Mesh_Ids_Data_Itapema.csv"), encoding="utf-8")
price = pd.read_csv(os.path.join(DATA, "Price_AV_Itapema.csv"), encoding="utf-8")
viv = pd.read_csv(os.path.join(DATA, "VivaReal_Itapema.csv"), encoding="utf-8")

def strip(s):
    if not isinstance(s, str):
        return pd.NA
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower().strip()

CANON = {
    "meia praia": "meia praia",
    "meia praia _frentemar": "meia praia _frentemar",
    "centro": "centro",
    "morretes": "morretes",
    "tabuleiro dos oliveiras": "tabuleiro dos oliveiras",
    "tabuleiro": "tabuleiro dos oliveiras",
    "taboleiro": "tabuleiro dos oliveiras",
    "canto da praia": "canto da praia",
    "casa branca": "casa branca",
    "alto sao bento": "alto sao bento",
    "ilhota": "ilhota",
    "varzea": "varzea",
    "andorinha": "andorinha",
    "castelo branco": "castelo branco",
    "sertao do trombudo": "sertao do trombudo",
    "jardim praiamar": "jardim praiamar",
    "jardim praia mar": "jardim praiamar",
    "sertaozinho": "sertaozinho",
    "leopoldo zarling": "leopoldo zarling",
    "areal": "areal",
    "lameiro": "lameiro",
    "estreito": "estreito",
    "itapema": "itapema",
    "ocean tower": "ocean tower",
    None: "sem_bairro",
}
def canon(s):
    k = strip(s)
    if k is pd.NA or k == "none":
        return "sem_bairro"
    if k == "meia praia - frente mar":
        return "meia_praia_frente_mar"
    return CANON.get(k, "outro(" + str(k) + ")")

price_ids = set(price["airbnb_listing_id"])
det["has_price"] = det["airbnb_listing_id"].isin(price_ids).astype(int)
det = det.merge(mesh[["airbnb_listing_id", "suburb"]], on="airbnb_listing_id", how="left")
det["bairro"] = det["suburb"].apply(canon)
viv["bairro"] = viv["suburb"].apply(canon)

L = []
def out(s=""): L.append(str(s))

out("TESTE 10 — Relacionamento Airbnb x VivaReal")
out(f"airbnb listings={len(det)} (com price: {det['has_price'].sum()})  | vivareal={len(viv)}")
out("")

out("### Estrategia A: bairro canonico somente ###")
t = det.groupby("bairro")["airbnb_listing_id"].count().rename("airbnb_all")
tp = det[det["has_price"] == 1].groupby("bairro")["airbnb_listing_id"].count().rename("airbnb_com_preco")
tv = viv.groupby("bairro")["listing_id"].count().rename("vivareal")
tab = pd.concat([t, tp, tv], axis=1).fillna(0).astype(int)
tab["viv_a_m2?"] = ""
out(tab.to_string())
out("")
out("bairros 100% cobertos nos dois universos: " +
    str(sorted(set(det['bairro']) & set(viv['bairro']))))
out("bairros so airbnb: " + str(sorted(set(det['bairro']) - set(viv['bairro']))))
out("bairros so vivareal: " + str(sorted(set(viv['bairro']) - set(det['bairro']))))
out("")
cov_abn = len(set(det['bairro']) & set(viv['bairro'])) / len(set(det['bairro']))
out(f"cobertura de bairros: {100*cov_abn:.1f}% dos bairros airbnb possuem oferta vivareal")
out("")

out("### Estrategia B: bairro + listing_type ###")
det["tipo_norm"] = det["listing_type"].where(det["listing_type"].isin(
    ["apartamento", "casa"]), "outros")
ts = pd.crosstab(det["bairro"], det["tipo_norm"]).rename(columns=lambda c: "ai_" + c)
tv2 = pd.crosstab(viv["bairro"], viv["listing_type"]).rename(columns=lambda c: "vi_" + c)
combo = pd.concat([ts, tv2], axis=1).fillna(0).astype(int)
out(combo.to_string())
out("")

out("### Estrategia C: bairro + tipo + quartos (ambos universos) ###")
qc = pd.crosstab([det["bairro"], det["tipo_norm"]], det["number_of_bedrooms"]).max(axis=1) * 0
det["q_grp"] = det["number_of_bedrooms"].apply(lambda b: "1" if b <= 1 else ("2" if b == 2 else ("3" if b == 3 else "4+")))
viv["q_grp"] = viv["bedrooms"].apply(lambda b: "1" if b <= 1 else ("2" if b == 2 else ("3" if b == 3 else "4+")))
c1 = pd.crosstab([det["bairro"], det["tipo_norm"], det["q_grp"]], columns=det["has_price"] > -1).rename(columns={True: "airbnb"})
c1 = c1.reset_index()[["bairro", "tipo_norm", "q_grp", "airbnb"]].rename(columns={"tipo_norm": "tipo", "q_grp": "q"})
c2 = pd.crosstab([viv["bairro"], viv["listing_type"], viv["q_grp"]], columns=viv["sale_price"] > -1).rename(columns={True: "vivareal"})
c2 = c2.reset_index()[["bairro", "listing_type", "q_grp", "vivareal"]].rename(columns={"listing_type": "tipo", "q_grp": "q"})
merged = c1.merge(c2, on=["bairro", "tipo", "q"], how="outer").fillna({"airbnb": 0, "vivareal": 0})
merged[["airbnb", "vivareal"]] = merged[["airbnb", "vivareal"]].astype(int)
merged["ambos"] = (merged["airbnb"] > 0) & (merged["vivareal"] > 0)
out(f"combinacoes bairro+tipo+quartos present nos DOIS universos: {merged['ambos'].sum()} de {len(merged)}")
out("top 12 combinacoes por n (ambos):")
out(merged[merged["ambos"]].sort_values(["airbnb", "vivareal"], ascending=False).head(12).to_string())
out("")
out("### Estrategia D: area (so vivareal tem area; airbnb NAO tem m2) ###")
out("=> INVIAVEL cruzar area: airbnb nao tem usable_area. Alternativa: comparar quartos/camas apenas.")
out("")

out("### Estrategia E: geografica ###")
out("airbnb: lat/lon no mesh | vivareal: NAO possui lat/lon => sem georreferenciamento direto.")
out("proximidade geografica so possivel nivel-bairro, nao ponto.")
out("")

out("### comparacao de perfil por bairro (mediana) ###")
prof = det[det["has_price"] == 1].groupby("bairro").agg(
    n_ai=("airbnb_listing_id", "count"), med_quartos=("number_of_bedrooms", "median"),
    med_preco=("cleaning_fee", "median")).rename(columns={"med_preco": "proxy_teste"})
pv = viv[viv["listing_type"] == "apartamento"].groupby("bairro").agg(
    n_vi=("listing_id", "count"), med_venda=("sale_price", "median"),
    med_area=("usable_area", "median"))
out(pd.concat([prof.drop(columns="proxy_teste"), pv], axis=1).round(0).to_string())
out("")

with open(os.path.join(OUT, "teste10_match.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("\n".join(L))