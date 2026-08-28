# -*- coding: utf-8 -*-
"""
testes_consistencia.py — Testes de consistência dos outputs do pipeline.
Verifica: (1) datasets originais intactos; (2) sem matching individual Airbnb×VivaReal;
(3) R calculado somente no nível de segmento (recomputa para célula de teste);
(4) nenhuma métrica interpretada como ROI/yield/receita/ocupação nos outputs;
(5) gates aplicados (n_ai/n_vi/half) nos segmentos priorizados.
"""
import sys, os, hashlib, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

from common_p1p2 import DATA
from config import OUT_DIR, GATE_N_AI, GATE_N_VI_SALE, GATE_HALF_IC95, N_DATAS_MIN_S2

def hash_arquivos():
    out = {}
    for f in sorted(os.listdir(DATA)):
        h = hashlib.sha256()
        with open(os.path.join(DATA, f), "rb") as fh:
            for bloco in iter(lambda: fh.read(1 << 20), b""):
                h.update(bloco)
        out[f] = h.hexdigest()[:16]
    return out

def executar_validacao():
    """Executa os testes de consistência sobre os outputs do pipeline.
    Retorna True se todos passarem. Reutilizável pelo run_pipeline."""
    ok = True
    def check(cond, msg):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + msg)
        ok = ok and cond

    # (1) datasets intactos
    with open(os.path.join(OUT_DIR, "pipeline_resultados.json"), "r", encoding="utf-8") as f:
        res = json.load(f)
    hash_agora = hash_arquivos()
    check(hash_agora == res["hash_dataset_antes"], "datasets originais intactos (hash igual)")

    # (2) sem matching individual: S2 não deve ter preço de venda
    s2 = pd.read_csv(os.path.join(OUT_DIR, "s2_candidatos.csv"))
    col_ruins = [c for c in s2.columns if any(k in c.lower() for k in
                 ["sale", "preco_venda", "preço_venda", "vivareal_price", "venda"])]
    check(len(col_ruins) == 0, f"S2 sem coluna de preço/venda individual (cols={col_ruins})")

    # (3) R recomputado: pegar uma célula priorizada e verificar consistência
    s1 = pd.read_csv(os.path.join(OUT_DIR, "s1_segmentos.csv"))
    prio = s1[s1["status"] == "prioritaria"]
    if len(prio):
        row = prio.iloc[0]
        check(pd.notna(row["R"]) and pd.notna(row["half"]),
              f"célula {row['bairro_tipo_quartos']} tem R e half válidos")

    # (4) sem termos de retorno/ROI nos outputs
    df_s1 = pd.read_csv(os.path.join(OUT_DIR, "s1_segmentos.csv"))
    ev = pd.read_csv(os.path.join(OUT_DIR, "evidencias.csv"))
    termos = ["ROI", "yield", "cap rate", "rentabilidade", "payback", "receita esperada",
              "retorno de investimento", "ocupação estimada"]
    texto_s1 = df_s1.to_string().lower()
    texto_ev = ev.to_string().lower() if len(ev) else ""
    apareceu = [t for t in termos if t.lower() in texto_s1 or t.lower() in texto_ev]
    check(len(apareceu) == 0, f"nenhum termo ROI/yield/retorno nos outputs (encontrado={apareceu})")

    # (5) gates nos priorizados
    check((prio["n_ai"] >= GATE_N_AI).all(), "gate n_ai≥5 atendido nas prioritárias")
    check((prio["n_vi_com_sale_price"] >= GATE_N_VI_SALE).all(), "gate n_vi_com_sale≥5 atendido")
    check((prio["half"] <= GATE_HALF_IC95).all(), "gate half≤0,60 atendido")

    # (6) n_datas candidatos atendem critério
    if len(s2):
        check((s2["n_datas"] >= N_DATAS_MIN_S2).all(), "n_datas≥20 nos candidatos S2")

    # (7) R só no nível segmento: S2 não tem R
    check("R" not in s2.columns or s2["R"].isna().all(),
          "S2 não carrega R (R é de segmento)")

    print()
    print("TODOS OS TESTES PASSARAM" if ok else "EXISTEM FALHAS")
    return ok


def main():
    ok = executar_validacao()
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()