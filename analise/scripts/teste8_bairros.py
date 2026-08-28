# -*- coding: utf-8 -*-
"""
Teste 8 - Normalizacao de bairros (suburb) entre Mesh (Airbnb) e VivaReal.
Separa diferencas puramente textuais de diferencas semanticas.
NAO une categorias semanticamente diferentes automaticamente.
"""
import pandas as pd
import unicodedata
import os

DATA = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\data"
OUT = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\analise\saida"

mesh = pd.read_csv(os.path.join(DATA, "Mesh_Ids_Data_Itapema.csv"), encoding="utf-8")
viv = pd.read_csv(os.path.join(DATA, "VivaReal_Itapema.csv"), encoding="utf-8")

def strip_accents(s):
    if not isinstance(s, str):
        return s
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")

def norm(s):
    if not isinstance(s, str):
        return None
    s = strip_accents(s).lower().strip()
    s = s.replace(" - frente mar", " _frentemar").replace("- frente mar", " _frentemar")
    return s

mesh_tags = mesh["suburb"].dropna()
viv_tags = viv["suburb"].dropna().replace("", pd.NA).dropna()

ms = mesh_tags.value_counts()
vs = viv_tags.value_counts()
all_tags = sorted(set(ms.index) | set(vs.index))

L = []
def out(s=""): L.append(str(s))

out("TESTE 8 — Bairros: normalizacao")
out(f"{'ORIGINAL':<30} {'AIRBNB':>7} {'VIVAREAL':>9} {'norm':<22} proposta")
for t in all_tags:
    a = int(ms.get(t, 0)); v = int(vs.get(t, 0))
    n = norm(t) or "NA"
    out(f"{t:<30} {a:>7} {v:>9} {n:<22}")
out("")

# agrupar por normalizado
from collections import defaultdict
groups = defaultdict(list)
for t in all_tags:
    n = norm(t)
    groups[n if n else "<NA>"].append(t)

out("### Grupos candidatos a UNIAO (textualmente identicos apos acentos/caixa) ###")
for n, ts in sorted(groups.items()):
    if len(ts) > 1:
        out(f"{n}: {ts}")

out("")
out("### Analise semantica dos grupos com mais de uma versao ###")
semantic_cases = {
    "Meia Praia": ["Meia Praia", "MEIA PRAIA", "Meia praia", "meia praia"],
    "Meia Praia (frente mar)": ["Meia Praia - Frente Mar"],
    "Centro": ["Centro", "CENTRO"],
    "Tabuleiro dos Oliveiras": ["Tabuleiro dos Oliveiras", "Tabuleiro", "Taboleiro"],
    "Sertao do Trombudo": ["Sertao do Trombudo", "Sertao Do Trombudo"],
    "Alto Sao Bento": ["Alto Sao Bento", "Alto São Bento"],
    "Sertaozinho": ["Sertaozinho", "Sertãozinho"],
    "Jardim Praiamar": ["Jardim Praiamar", "Jardim Praia Mar"],
}
for canon, versoes in semantic_cases.items():
    out(f"CANON proposto: {canon} <- {versoes}")

out("")
out("### Bairros apenas em um universo ###")
g_all = defaultdict(int)
for t in all_tags:
    g_all[norm(t)] += (ms.get(t, 0) > 0) + (vs.get(t, 0) > 0)
only_airbnb = [t for t in all_tags if ms.get(t, 0) > 0 and vs.get(t, 0) == 0]
only_viva = [t for t in all_tags if vs.get(t, 0) > 0 and ms.get(t, 0) == 0]
out("so AIRBNB: " + str(only_airbnb))
out("so VIVAREAL: " + str(only_viva))
out("")
out("### casos especiais ###")
out("'none' (airbnb): nao-coleta de bairro")
out("'Ocean Tower', 'Itapema', 'Estreito': sidras/empreendimento ou cidade em vez de bairro")
out("")

with open(os.path.join(OUT, "teste8_bairros.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("\n".join(L))