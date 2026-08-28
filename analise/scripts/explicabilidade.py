# -*- coding: utf-8 -*-
"""
explicabilidade.py — Gera blocos de texto explicável por célula/candidato,
deixando claro: o que foi avaliado, quais dados, R, comparação, n, precisão,
cobertura, elegibilidade, evidência, confiança e limitações.
"""
import numpy as np


def explicar_celula(row, pares_dominados, def_rot):
    """row: dict da linha (segmento, status, R, etc.). Retorna texto."""
    linhas = []
    linhas.append(f"Segmento: {row['bairro_tipo_quartos']} "
                  f"(nível avaliado: {row['nivel']})")
    linhas.append(f"Status: {row['status']}")
    linhas.append(f"R = {row['R']:.5f} — razão entre a mediana da diária anunciada no "
                  f"Airbnb e a mediana dos preços de venda observados no VivaReal "
                  f"para o mesmo segmento (indicador COMPARATIVO de segmento; "
                  f"não estima retorno de imóvel individual).")
    linhas.append(f"IC95(R) = [{row['R_ic_lo']:.5f}, {row['R_ic_hi']:.5f}] | "
                  f"half = {row['half']:.3f}")
    linhas.append(f"Observações utilizadas: n_ai (Airbnb com preço) = {row['n_ai']}, "
                  f"n_vi_total = {row['n_vi_total']}, "
                  f"n_vi_com_sale_price = {row['n_vi_com_sale_price']} "
                  f"(usados na estimativa).")
    cov = row.get("cobertura_price_pct")
    if cov is not None and not np.isnan(cov):
        linhas.append(f"Cobertura do Price no segmento: {cov:.1f}% "
                      f"(métrica de representatividade; seleção de Price é limitação).")
    if pares_dominados:
        linhas.append("Dominância contra outros segmentos (Δ com FDR controlado, "
                      f"Δ_min = 25%): domina {len(pares_dominados)} segmento(s) — "
                      + "; ".join(pdef for pdef in pares_dominados[:5]))
    else:
        linhas.append("Dominância: sem comparação estatisticamente relevante com outros "
                      "segmentos (ou segmento único/evidência insuficiente).")
    linhas.append("Limitações: preço anunciado (não receita/ocupação); janela jan–abr/2025; "
                  "junção Airbnb×VivaReal agregada; sem correspondência individual.")
    return "\n".join(linhas)


def explicar_candidato(row):
    linhas = []
    linhas.append(f"Candidato operacional (não compra recomendada): "
                  f"listing {row['airbnb_listing_id']} no segmento prioritário "
                  f"{row['segmento_prioritario']}")
    linhas.append(f"Diária mediana observada: R$ {row['diaria_mediana']:.2f} "
                  f"(anunciada, não receita) | n_datas: {row['n_datas']}")
    linhas.append(f"Operação (descritivo): reviews={row['numero_reviews']}, "
                  f"rating={'%.2f' % row['star_rating'] if not pd_isnan(row['star_rating']) else 'sem avaliação'}, "
                  f"favorite={row['is_guest_favorite']}, superhost={row['is_superhost']}, "
                  f"professional={row['is_professional']}, instant_book={row['can_instant_book']}")
    linhas.append("Sinais de boa operação atual NÃO implicam oportunidade de aquisição; "
                  "reviews ≠ demanda; diária alta ≠ retorno; sem custo de aquisição individual.")
    return "\n".join(linhas)


def pd_isnan(x):
    try:
        return np.isnan(x)
    except Exception:
        return False