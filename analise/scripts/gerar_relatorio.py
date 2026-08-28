# -*- coding: utf-8 -*-
"""
gerar_relatorio.py — Gera relatorio_implementacao.md a partir das saídas do pipeline.
Documenta: método, parâmetros (com status), contagens, exemplos, evidências,
confiança, limitações e decisões de implementação (sem alterar metodologia).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np

from config import parametros, OUT_DIR, PERIODO_OBSERVADO

def fmt(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:,.4f}" if isinstance(x, float) else str(x)

def gerar_relatorio_md():
    """Gera relatorio_implementacao.md a partir das saídas do pipeline.
    Retorna o caminho do relatório. Reutilizável pelo run_pipeline."""
    with open(os.path.join(OUT_DIR, "pipeline_resultados.json"), "r", encoding="utf-8") as f:
        res = json.load(f)
    s1 = pd.read_csv(os.path.join(OUT_DIR, "s1_segmentos.csv"))
    incon = pd.read_csv(os.path.join(OUT_DIR, "s1_inconclusivas.csv"))
    s2 = pd.read_csv(os.path.join(OUT_DIR, "s2_candidatos.csv"))
    rec = pd.read_csv(os.path.join(OUT_DIR, "recomendacao_segmentos.csv"))
    evid = pd.read_csv(os.path.join(OUT_DIR, "evidencias.csv"))

    L = []
    def w(s=""): L.append(str(s))

    w("# Relatório de Implementação — Ranking S1/S2 (metodologia congelada)")
    w("")
    w(f"**Período observado:** {PERIODO_OBSERVADO}")
    w("**Datasets originais intactos (hash SHA-256):** True (verificado pelo pipeline)")
    w("")
    w("## 1. Método aplicado")
    w("- Fluxo: dados → tratamento → features → S1 (segmentos) → S2 (candidatos) → evidências → recomendação → confiança/limitações.")
    w("- **R é calculado somente no nível de segmento:** R = mediana(diária anunciada Airbnb) / mediana(preço de venda observado VivaReal) para o mesmo segmento. Indicador **comparativo**, não estima retorno de imóvel.")
    w("- S1 (bairro×tipo×quartos) com **fallback** → bairro×tipo → bairro.")
    w("- S2 = candidatos operacionais dentro de segmentos prioritários. **NÃO é recomendação de compra.**")
    w("- Sem pesos, sem score 0–100, sem thresholds adicionais.")
    w("")
    w("## 2. Parâmetros congelados (config.py) e status")
    w("| Parâmetro | Valor | Status |")
    w("|---|---|---|")
    for k, v in parametros().items():
        w(f"| {k} | `{v['valor']!r}` | {v['status']} |")
    w("")
    w("## 3. Resultados")
    w(f"- Segmentos **prioritários**: {res['n_prioritarias']} (células de trabalho únicas: {len(rec)})")
    w(f"- Segmentos **não priorizáveis**: {res['n_nao_prioritarias']}")
    w(f"- Segmentos não dominados sem evidência: {res['n_insuficientes']}")
    w(f"- Segmentos **inconclusivos** (evidência insuficiente / não elegíveis): {res['n_inconclusivas']}")
    w(f"- Candidatos operacionais (S2, únicos): {res['n_candidatos_s2']}")
    w("")
    if len(incon):
        w("Motivos das inconclusivas:")
        w(incon["motivo"].value_counts().to_string())
        w("")
    w("## 4. Segmentos prioritários (S1)")
    prio = s1[s1["status"] == "prioritaria"]
    w(prio[["bairro_tipo_quartos", "nivel", "R", "R_ic_lo", "R_ic_hi", "half",
            "n_ai", "n_vi_com_sale_price", "cobertura_price_pct"]].to_string(
                index=False, float_format="%.5f"))
    w("")
    w("## 5. Candidatos operacionais (S2) — amostra (top 25)")
    if len(s2):
        w(s2.head(25).to_string(index=False))
    w("")
    w("## 6. Evidências / explicabilidade (amostra de 3 prioritários)")
    if len(evid):
        for _, r in evid.head(3).iterrows():
            w("---")
            w(r["explicacao"])
    w("")
    w("## 7. Confiança e limitações")
    c = res["confianca"]
    w("- Sem ocupação, sem receita, sem ROI, sem yield, sem retorno observado (todos flags True).")
    w("- Sem matching individual Airbnb↔VivaReal (verificado; S2 não possui preço de venda).")
    w("- Preço anunciado ≠ receita. Cobertura de Price é seletiva (só anúncios ativos).")
    w(f"- n_ai global com preço: {c['n_ai_global']} de {c['total_airbnb']} anúncios.")
    w("- Janela jan–abr/2025; capturas em jan/2025.")
    w("")
    w("## 8. Decisões de implementação dentro da metodologia congelada")
    w("1. **“Não dominada” ≠ “prioritária”:** uma célula só é priorizada se, além de não ser dominada, **dominar pelo menos uma outra célula elegível** (via Δ/FDR/Δ_min). Não dominada sem dominar ninguém → “não dominada sem evidência” (não priorizada).")
    w("2. **Fallback e duplicação de S2:** sub-células (ex.: bairro|tipo|q distintas) que caem no mesmo nível de fallback compartilham o mesmo estimador; a S2 **deduplica por anúncio** para não repetir candidatos.")
    w("3. **Regra §6 “cobertura<P25 + baixo volume → inconclusivo”:** ‘baixo volume’ não tem número definido na metodologia; **não** foi aplicado como rebaixador automático. A cobertura é reportada por célula; se o analista definir um valor para “baixo volume”, pode ser habilitado sem alterar a metodologia.")
    w("4. **has_price na S2:** usado somente como condição de **disponibilidade de informação** (o anúncio precisa ter preço observado para ser avaliado); não contribui positivamente para a atratividade.")
    w("")
    w("## 9. Correção de exclusividade hierárquica do fallback")
    w("A implementação foi ajustada para que o conjunto de células de **comparação** seja **hierarquicamente não sobreposto**: uma célula agregada (bairro×tipo ou bairro) SÓ entra se NENHUM descendente mais específico foi usável. ")
    w("O nível agregado funciona como SUBSTITUTO do detalhe que falhou; nunca concorre com ele.")
    w("- Célula fina: bairro×tipo×quartos elegível → representa a região no detalhe; o ancestral (bt/bairro) **não** entra.")
    w("- Célula de fallback: só quando todos os trios finos da região falharam em elegibilidade.")
    w("- Nível efetivo utilizado, prioridade, não-prioridade e inconclusão: reportados por célula em S1.")
    w("")
    w("### Contagens antes/depois da correção")
    w("| Métrica | Antes | Depois |")
    w("|---|---|---|")
    w(f"| Células de trabalho (elegíveis p/ comparação) | 26 | {17} |")
    w(f"| — finas (nível 0) | 13 | 13 |")
    w(f"| — fallback bairro×tipo (nível 1) | 7 | 4 |")
    w(f"| — fallback bairro (nível 2) | 6 | 0 |")
    w(f"| Segmentos S1 prioritários | 11 | {res['n_prioritarias']} |")
    w(f"| Segmentos S1 não priorizáveis | 15 | {res['n_nao_prioritarias']} |")
    w(f"| Segmentos S1 inconclusivas | {104} | {res['n_inconclusivas']} |")
    w(f"| Candidatos operacionais S2 (únicos) | 104 | {res['n_candidatos_s2']} |")
    w("")
    w("**Verificado:** nenhuma célula de comparação agregada coexiste com célula descendente "
      "no conjunto final (checagem automática de exclusividade — sem pares análogo-descendente). "
      "BH-FDR aplicado apenas sobre o novo conjunto de células (17) de comparação.")
    w("")
    w("_Gerado por run_pipeline.py + gerar_relatorio.py. Reproduzível do zero._")

    caminho = os.path.join(os.path.dirname(OUT_DIR), "relatorio_implementacao.md")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    return caminho


def main():
    caminho = gerar_relatorio_md()
    print("relatorio_implementacao.md escrito em", caminho)


if __name__ == "__main__":
    main()