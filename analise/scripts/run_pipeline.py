# -*- coding: utf-8 -*-
"""
run_pipeline.py — Ponto de entrada do pipeline reproduzível (execução única de ponta a ponta):
dados originais → carregamento → tratamento → features → elegibilidade/fallback →
inferência → comparação → S1 → S2 → evidências → recomendação → relatório final → validação.

- Parte sempre dos datasets originais (data/), sem depender de outputs prévios.
- Determinismo: seed fixa (config.SEED) → bootstrap determinístico.
- Não altera datasets, não cria pesos/score, não modifica a metodologia.
- Integra, reutilizando módulos existentes: gerar_relatorio (relatório) e
  testes_consistencia (validação final).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import hashlib
import json

import pandas as pd
import numpy as np

from common_p1p2 import DATA
from config import OUT_DIR, PERIODO_OBSERVADO
from features import carregar, build_imovel_table, build_venda_table
from elegibilidade import montar_celulas
from comparacao import comparar_pares
from s1_segmentos import executar_s1
from s2_candidatos import selecionar_candidatos
from explicabilidade import explicar_celula, explicar_candidato
from gerar_relatorio import gerar_relatorio_md
from testes_consistencia import executar_validacao

os.makedirs(OUT_DIR, exist_ok=True)


def hash_arquivos():
    """Hash dos datasets originais (para confirmar que não foram alterados)."""
    out = {}
    for f in sorted(os.listdir(DATA)):
        caminho = os.path.join(DATA, f)
        h = hashlib.sha256()
        with open(caminho, "rb") as fh:
            for bloco in iter(lambda: fh.read(1 << 20), b""):
                h.update(bloco)
        out[f] = h.hexdigest()[:16]
    return out


def gravar(df, nome, ordenar_por=None):
    """Grava DataFrame em analise/saida/<nome>.csv (se não vazio).
    Ordena por chave estável quando informado — garante determinismo byte-a-byte
    (iteração de set python não é determinística entre processos)."""
    if df is not None and len(df):
        if ordenar_por is not None and ordenar_por in df.columns:
            df = df.sort_values(ordenar_por, kind="mergesort").reset_index(drop=True)
        caminho = os.path.join(OUT_DIR, nome + ".csv")
        df.to_csv(caminho, index=False, encoding="utf-8-sig")
        return caminho
    return os.path.join(OUT_DIR, nome + ".csv")


def main():
    resultados = {"periodo": PERIODO_OBSERVADO}

    # --- 0) Hashes antes (integridade) ---
    hash_antes = hash_arquivos()

    # --- 1) Dados originais (somente leitura) ---
    dados = carregar()

    # --- 2) Features ---
    ai = build_imovel_table(dados["details"], dados["hosts"], dados["mesh"], dados["price"])
    venda = build_venda_table(dados["vivareal"])

    # --- 3) S1 — elegibilidade/fallback + inferência + comparação ---
    res_s1 = executar_s1(ai, venda)
    df_eleg = res_s1["df_eleg"]
    df_incon = res_s1["df_incon"]
    comp = res_s1["comp"]

    # --- 4) S2 — candidatos nos segmentos prioritários (célula de trabalho única) ---
    vistos = set()
    prior_meta = []
    for c in comp["prioritarias"]:
        nivel = c.get("nivel")
        chave = c["chave"]
        if nivel == 0:
            seg_wk = ("q", chave)
        elif nivel == 1:
            seg_wk = ("bt", (chave[0], chave[1]))
        elif nivel == 2:
            seg_wk = ("b", (chave[0],))
        else:
            continue
        if seg_wk in vistos:
            continue
        vistos.add(seg_wk)
        prior_meta.append({"chave": chave, "nivel": nivel,
                           "rot_trabalho": c.get("rot_trabalho")})
    df_s2 = selecionar_candidatos(ai, prior_meta)

    # --- 5) Evidências / explicabilidade ---
    expl_linhas = []
    for _, r in df_eleg.iterrows():
        chave = (r["bairro"], r["tipo"], r["quartos"])
        dom = []
        for i, j in comp["dominacao"]:
            if i == chave:
                dom.append(f"{j[0]}|{j[1]}|{j[2]}")
            elif j == chave:
                dom.append(f"({i[0]}|{i[1]}|{i[2]}) continua dominante")
        expl_linhas.append({"chave": chave_join(chave),
                            "explicacao": explicar_celula(r, dom, None)})
    df_exp = pd.DataFrame(expl_linhas)

    # --- 6) Recomendação (texto auxiliar, sem score) ---
    s2_counts = (df_s2.groupby("segmento_prioritario")["airbnb_listing_id"].nunique()
                 if len(df_s2) else pd.Series(dtype=int))
    recomendacoes = []
    for c in comp["prioritarias"]:
        nivel, chave = c.get("nivel"), c["chave"]
        rot = c.get("rot_trabalho")
        if rot is None:
            rot = (f"{chave[0]}|{chave[1]}|{chave[2]}" if nivel == 0
                   else f"{chave[0]}|{chave[1]}|(todos quartos)" if nivel == 1
                   else f"{chave[0]}|(todos tipos)|(todos quartos)" if nivel == 2
                   else None)
        if rot is None or any(r["segmento"] == rot for r in recomendacoes):
            continue
        recomendacoes.append({"segmento": rot, "tipo": chave[1],
                              "n_alvos_candidatos": int(s2_counts.get(rot, 0))})
    df_rec = pd.DataFrame(recomendacoes)

    # --- 7) Confiança / limitações ---
    confianca = {
        "periodo": PERIODO_OBSERVADO,
        "sem_ocupacao": True, "sem_receita": True, "sem_roi": True,
        "sem_matching_individual_airbnb_vivareal": True,
        "preco_anunciado_nao_receita": True,
        "n_ai_global": int(ai["has_price"].sum()),
        "total_airbnb": int(len(ai)),
        "ofensores_de_qualidade": int(df_incon.shape[0]),
    }

    # --- 8) Gravar outputs principais (ordenados por chave estável → determinismo) ---
    out_s1 = gravar(df_eleg, "s1_segmentos", ordenar_por="bairro_tipo_quartos")
    out_incon = gravar(df_incon, "s1_inconclusivas", ordenar_por="bairro_tipo_quartos")
    out_s2 = gravar(df_s2, "s2_candidatos", ordenar_por="airbnb_listing_id")
    gravar(df_exp, "evidencias", ordenar_por="chave")
    gravar(df_rec, "recomendacao_segmentos", ordenar_por="segmento")

    res_json = {
        "hash_dataset_antes": hash_antes,
        "n_prioritarias": res_s1["n_prioritarias"],
        "n_nao_prioritarias": res_s1["n_nao_prio"],
        "n_insuficientes": res_s1["n_insuf"],
        "n_inconclusivas": res_s1["n_inconclusivas"],
        "n_candidatos_s2": int(len(df_s2)),
        "arquivos": {"s1": out_s1, "s1_inconclusivas": out_incon, "s2": out_s2},
        "confianca": confianca,
    }
    with open(os.path.join(OUT_DIR, "pipeline_resultados.json"), "w", encoding="utf-8") as f:
        json.dump(res_json, f, indent=2, ensure_ascii=False)

    # --- 9) Hash depois + integridade ---
    hash_depois = hash_arquivos()
    intactos = (hash_antes == hash_depois)
    res_json["hash_dataset_depois"] = hash_depois
    res_json["datasets_intactos"] = intactos

    # --- 10) Relatório final (reutiliza gerar_relatorio) ---
    relatorio_path = gerar_relatorio_md()

    # --- 11) Validação (reutiliza testes_consistencia) ---
    validacao_ok = executar_validacao()

    # --- 12) Console (final) ---
    print("=" * 70)
    print("RESULTADO DO PIPELINE")
    print("=" * 70)
    print(f"Segmentos prioritários      : {res_s1['n_prioritarias']}")
    print(f"Segmentos não priorizáveis  : {res_s1['n_nao_prio']}")
    print(f"Segmentos não dominados sem evidência (insuf.): {res_s1['n_insuf']}")
    print(f"Segmentos inconclusivos     : {res_s1['n_inconclusivas']}")
    print(f"Candidatos operacionais (S2): {len(df_s2)}")
    print("-" * 70)
    print("Arquivos gerados:")
    for p in (out_s1, out_incon, out_s2,
              os.path.join(OUT_DIR, "evidencias.csv"),
              os.path.join(OUT_DIR, "recomendacao_segmentos.csv"),
              os.path.join(OUT_DIR, "pipeline_resultados.json"),
              relatorio_path):
        print("  - " + p)
    print(f"Datasets originais intactos : {intactos}")
    print(f"Validação de consistência   : {'PASSOU' if validacao_ok else 'FALHOU'}")
    print("=" * 70)

    return 0 if (intactos and validacao_ok) else 1


def chave_join(chave):
    return " | ".join(str(x) for x in chave)


if __name__ == "__main__":
    sys.exit(main())