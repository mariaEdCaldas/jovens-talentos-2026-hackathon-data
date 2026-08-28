"""
Teste Q4 - Reviews sao um proxy defensavel de demanda?
Teste Q5 - Podemos inferir ocupacao/receita ou so potencial de mercado?

Q4 (fat / hipotese / inferencia):
  Fato: number_of_reviews eh um CONTADOR ACUMULADO (stock), nao fluxo de demanda
        corrente.
  Testa:
    a) distribuicao de reviews (share de 0 reviews = anuncios sem avaliacao).
    b) reviews correlacionam com idade do host/listing (acumulo ao longo do tempo)
       -> se sim, reviews é confundido com tempo, NAO eh demanda corrente.
    c) reviews correlacionam com preco (associacao, sem causalidade).
    d) reviews refletem apenas hospedagens que resultaram em review escrito
       (rate de review < 100%) -> numero de reviews < numero de hospedagens.

Q5:
  Testa se existe QUALQUER campo que registre ocupacao/reservas realizadas.
  Testa se a ausencia de preco para uma data pode indicar indisponibilidade
  (sinal fraco/ambiguo de ocupacao).
  Testa a disponibilidade de benchmark de aluguel no VivaReal (rental_price).
  Conclusao: sem ocupacao observada, receita nao pode ser inferida sem assumir
  taxa de ocupacao; entao resta "potencial de mercado".
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

def line(*a):
    buf.write(" ".join(str(x) for x in a) + "\n")

def main():
    d = prepare()
    det = d["det"]
    hosts = d["hosts"].drop_duplicates("owner_id")
    price = d["price"].copy()
    viv = d["viv"]

    det = det.merge(hosts[["owner_id", "years_host", "months_host"]],
                    on="owner_id", how="left")

    line("=" * 100)
    line("Q4 - REVIEWS COMO PROXY DE DEMANDA")
    line("=" * 100)
    line("Fato: variable number_of_reviews = contador ACUMULADO (stock).")
    line()

    # a) distribuicao
    line("-- a) share de anuncios SEM reviews --")
    line(f"anuncios com 0 reviews: {(det['number_of_reviews']==0).sum()} de {len(det)} "
         f"= {(det['number_of_reviews']==0).mean():.1%}")
    line("distribuicao de reviews:")
    line(det["number_of_reviews"].describe().to_string())
    line("quantis 90/99/max:", det["number_of_reviews"].quantile([0.5, 0.9, 0.99, 1.0]).to_dict())
    line()

    # b) reviews vs idade
    line("-- b) reviews correlacionam com idade (acumulo ao longo do tempo) --")
    line("mediana de reviews por anos_host:")
    bins = [0, 1, 2, 3, 4, 5, 8, 20]
    det["years_bin"] = pd.cut(det["years_host"], bins=bins, right=True)
    line(det.groupby("years_bin", observed=True)["number_of_reviews"]
         .agg(["count", "median", "mean"]).to_string())
    tau, p = stats.kendalltau(det["years_host"], det["number_of_reviews"])
    line(f"Kendall tau(reviews, years_host) = {tau:.3f} (p={p:.2e})")
    line("> Se reviews sobem com a idade, sao proxy de ACUMULO historico,")
    line("> nao de demanda corrente/nivel de ocupacao atual.")
    line()

    # c) reviews vs preco (apenas listings com preco)
    line("-- c) associacao reviews x preco (apenas 999 listings com preco) --")
    hasp = det[det["has_price"]].copy()
    pr = (price.assign(cap_dt=pd.to_datetime(price["aquisition_date"]))
          .sort_values("cap_dt")
          .groupby("airbnb_listing_id")["price"].median().rename("price_mdn"))
    pp = hasp.merge(pr, left_on="airbnb_listing_id", right_index=True, how="left")
    tau, p = stats.kendalltau(pp["number_of_reviews"], pp["price_mdn"])
    line(f"Kendall tau(reviews, preco_mdn/noite) = {tau:.3f} (p={p:.2e})")
    line("preco_mdn mediano por faixa de reviews:")
    pp["rbin"] = np.select(
        [pp["number_of_reviews"] == 0, pp["number_of_reviews"] <= 5,
         pp["number_of_reviews"] <= 15, pp["number_of_reviews"] <= 40],
        ["0", "1-5", "6-15", "16-40"], default="40+")
    line(pp.groupby("rbin", observed=True)["price_mdn"]
         .agg(["count", "median", "mean"]).reindex(["0", "1-5", "6-15", "16-40", "40+"]).to_string())
    line("> Assoc. e so correlacional; preco alto pode reduzir reservas (endogeneidade).")
    line()

    # d) reviews < hospedagens
    line("-- d) reviews < hospedagens (taxa de review <100%) --")
    line("Fato estrutural: revisoes sao escritas por apenas parte dos hospedes;")
    line("logo number_of_reviews SUBESTIMA o numero de hospedagens realizadas.")
    line("Nao ha no dataset o numero real de reservas; nao podemos quantificar a taxa.")
    line()

    line("=" * 100)
    line("Q5 - OBSERVACAO DE OCUPACAO/RECEITA vs POTENCIAL DE MERCADO")
    line("=" * 100)
    line("Fato: NENHUMA coluna no dataset registra reservas realizadas, dias")
    line("ocupados ou ocupacao. Campos de preco = valor ANUNCIADO por noite.")
    line()

    line("-- a) campos relacionados a receita/disponibilidade existentes --")
    cols_occ = [c for c in price.columns if 'aquis' in c or 'date' in c]
    line("Price cols:", cols_occ)
    line("Details cols de reviews/avaliacao (proxy historico, nao ocupacao):",
         [c for c in det.columns if 'review' in c or 'rating' in c])
    line()

    # Sinal fraco de indisponibilidade: datas de estadia sem preco
    line("-- b) sinal fraco/ambiguo: cobertura do calendario de estadia por imovel --")
    line("Janela de estadia observavel: 2025-01-06 a 2025-04-20 (105 datas).")
    cov = (price.drop_duplicates(["airbnb_listing_id", "date"])
           .groupby("airbnb_listing_id")["date"].count())
    line(cov.describe().to_string())
    line("Imoveis cobrindo 105 datas (calendario completo):",
         int((cov == 105).sum()), f"= {(cov==105).mean():.1%}")
    line("Imoveis cobrindo < 50 datas:", int((cov < 50).sum()),
         f"= {(cov<50).mean():.1%}")
    line("> Datas ausentes podem indicar (i) nao disponivel/bloqueado, (ii) calendario")
    line("> nao preenchido, ou (iii) imovel sem preco naquela captura -> AMBIGUO.")
    line("> Portanto NAO da para tratar 'data sem preco' como 'data ocupada'.")
    line()

    # Consistencia: o mesmo (listing, stay_date) aparece com preco em capturas
    # diferentes -> calendario estava anunciado; ausencia parcial nao = ocupado.
    line("-- c) VivaReal: aluguel como benchmark de mercado --")
    line("rental_price preenchido em:", int(viv['rental_price'].notna().sum()),
         "de", len(viv), f"= {viv['rental_price'].notna().mean():.1%}")
    line("rental_price is null:", int(viv['rental_price'].isna().sum()),
         "de", len(viv), f"= {viv['rental_price'].isna().mean():.1%}")
    line("> Sem serie de aluguel no VivaReal, nao ha como fazer benchmark de")
    line("> rendimento de locacao tradicional com os dados fornecidos.")
    line()

    line("-- d) conclusao Q5 (fatos vs inferencia) --")
    line("FATO: nao observamos noches ocupadas. Assim, receita realizada = ")
    line("      preco_noite x noches_ocupadas, e noches_ocupadas NAO esta nos dados.")
    line("INFERENCIA metodologica defensavel: usar POTENCIAL de mercado java que")
    line("      receita só seria calculada sob hipotese explicita de ocupacao.")
    line("Hipoteses que exigiriam dados ausentes (ocupacao real, taxa de revisao,")
    line("      sazonalidade anual) e nao podem ser validadas aqui.")
    line()

    out = buf.getvalue()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "t3_q4_q5_reviews_ocupacao.txt"), "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote t3_q4_q5_reviews_ocupacao.txt", len(out))


if __name__ == "__main__":
    main()