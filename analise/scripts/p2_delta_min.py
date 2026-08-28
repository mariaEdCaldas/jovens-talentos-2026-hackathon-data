# -*- coding: utf-8 -*-
"""
P2 — Efeito mínimo Δ_min (análise de impacto, sem ranking).
Demonstra o significado operacional de diferentes diferenças relativas
(10%..40%) da razão R = diária_mediana / preço_venda_mediano.
NÃO escolhe ranking. Recomenda valor provisório como hipótese metodológica.
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
out("P2 — EFEITO MÍNIMO Δ_min (análise de impacto; sem ranking)")
out("=" * 100)

# Células elegíveis para a análise (bairro×tipo×quartos, piso provisório 5/5)
lv = "bairro_tipo_q"
ca = cells_ai(ai, lv).set_index(cell_key(ai, lv))
cv = cells_vi(vi, lv, excl_lanc=True).set_index(cell_key(vi, lv))

cells = []
for key, r in ca.iterrows():
    k0, k1, k2 = key[0], key[1], key[2]
    d = ai[(ai["bairro"] == k0) & (ai["tipo"] == k1) & (ai["q"] == k2)]
    d = d[(d["has_price"] == 1) & d["d_a"].notna()]
    if len(d) < 5:
        continue
    if key not in cv.index:
        continue
    n_vi_c = int(cv.loc[key, "n_vi_com_sale_price"])
    n_vi_t = int(cv.loc[key, "n_vi_total"])
    V = vi[(vi["bairro"] == k0) & (vi["tipo"] == k1) & (vi["q"] == k2) & ~vi["is_lanc"]]
    Vpos = V.loc[V["sale_price"].gt(0), "sale_price"]
    if len(Vpos) < 5:
        continue
    dvals = d["d_a"].values
    Robs, half, ic = boot_ratio(dvals, Vpos.values, B=2000)
    cells.append({"cel": f"{k0}|{k1}|{k2}", "n_ai": len(dvals),
                  "n_vi_total": n_vi_t, "n_vi_com_sale_price": n_vi_c,
                  "D": np.median(dvals), "V": np.median(Vpos), "R": Robs, "half": half,
                  "dvals": dvals, "Vpos": Vpos.values})
out(f"células elegíveis (piso provisório n>=5 em ambos): {len(cells)}")
if not cells:
    out("sem células; encerra análise")
    open(os.path.join(OUT, "p2_delta_min.txt"), "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))
    sys.exit(0)

summ = pd.DataFrame(cells)
out("R (diária_venda) por célula — descritivo (sem ordenar por ranking):")
out(summ[["cel", "n_ai", "n_vi_total", "n_vi_com_sale_price", "D", "V", "R", "half"]].round(4).to_string())
out("")

out("### Significado operacional de cada diferença relativa de R ###")
baseD = summ["D"].median(); baseV = summ["V"].median(); baseR = baseD / baseV
out(f"referência: mediana D={baseD:.0f} R$/noite | mediana V={baseV:,.0f} R$ | R(med)={baseR:.6f}")
out("")
out("cenário de diferença | múltiplo R | Δ=ln(1+pct) | exemplo (D fixo, V varia) | exemplo (V fixo, D varia)")
for pct in [0.10, 0.15, 0.20, 0.25, 0.30, 0.40]:
    mult = 1 + pct
    delta = np.log(mult)
    # D fixo: V precisa cair para levantar R
    V_d = baseV / mult
    # V fixo: D precisa subir
    D_v = baseD * mult
    out(f"  {pct*100:>5.0f}%          x{mult:.2f}     {delta:+.4f}      "
        f"D={baseD:.0f}/V={V_d:,.0f}        V={baseV:,.0f}/D={D_v:.0f}")
out("")
out("interpretação: R diferir 25% (x1.25) equivale, com diária fixa, a um capital de "
    "aquisição ~20% menor (1/1.25) ou, com capital fixo, a diária 25% maior.")
out("")

# Distribuição das diferenças pareadas observadas (apenas descritivo)
out("### Distribuição das diferenças pareadas |Δ| entre células elegíveis ###")
deltas = []
cell_names = summ["cel"].tolist()
for i in range(len(cells)):
    for j in range(i + 1, len(cells)):
        ri = cells[i]["R"]; rj = cells[j]["R"]
        if ri > 0 and rj > 0:
            deltas.append(abs(np.log(ri / rj)))
dd = pd.Series(deltas)
out(f"pares de células: {len(dd)}")
out(dd.describe().round(3).to_string())
out("percentis |Δ|: " + str({f"p{p}": round(v, 3) for p, v in dd.quantile(
    [0.10, 0.25, 0.50, 0.75, 0.90]).items()}))
out("")

# Quantos pares seriam "bloqueados" pelo efeito mínimo em cada cenário
out("### Quantos pares observados ficariam abaixo de cada Δ_min (abaixo do limiar de materialidade) ###")
out("(fração dos pares comparáveis cuja diferença observada não superaria a cláusula")
out(" de materialidade — isso NÃO é ruído mensurado; é interpretação metodológica de ")
out(" diferença considerada insuficiente para distinguir segmentos)")
for pct in [0.10, 0.15, 0.20, 0.25, 0.30, 0.40]:
    thr = np.log(1 + pct)
    below = (dd < thr).mean()
    out(f"  Δ_min={pct*100:>3.0f}% (Δ={thr:+.4f}) -> {100*below:>5.1f}% dos pares abaixo do limiar"
        f"   | acima: {100*(1-below):.1f}%")
out("")

# Gráfico: % pares que passam por um efeito-mínimo hipotético
plt.figure(figsize=(7, 4))
pcts = np.arange(0.05, 0.51, 0.05)
pass_frac = [(dd >= np.log(1 + p)).mean() for p in pcts]
plt.plot(pcts * 100, np.array(pass_frac) * 100, marker="o")
for p in [10, 15, 20, 25, 30, 40]:
    plt.axvline(p, color="gray", ls=":", alpha=0.6)
plt.xlabel("Δ_min (diferença relativa % de R)"); plt.ylabel("% dos pares de células acima do efeito mínimo")
plt.title("Pares de células acima de cada Δ_min (sensibilidade de materialidade; sem testes)")
plt.grid(alpha=.3)
plt.savefig(os.path.join(OUT, "p2_delta_min.png"), dpi=110)
plt.close()

out("### RECOMENDAÇÃO (hipótese metodológica provisória — NÃO descoberta empírica) ###")
out("Sem referência interna da Seazone (não disponível), não há base objetiva para fixar o Δ_min.")
out("O P2 apenas descreve a distribuição observada das diferenças entre as células analisadas;")
out("não demonstra qual valor de relevância é 'correto'.")
out("Proposta provisória: Δ_min = ln(1,25) ≈ 0,223 (diferença relativa de 25% em R), ")
out("declarada como HIPÓTESE METODOLÓGICA de materialidade. ")
out("Esse valor NÃO foi descoberto empiricamente pelos dados e não representa um valor ")
out("econômico objetivo. Sensibilidade obrigatória nas vizinhanças 15%, 25% e 30%.")
out("Se a Seazone definir outro valor de relevância econômica, basta re-executar o pipeline.")
out("")

with open(os.path.join(OUT, "p2_delta_min.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("\n".join(L))