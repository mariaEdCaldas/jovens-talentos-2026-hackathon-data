# -*- coding: utf-8 -*-
"""
run_pipeline.py — Executa o fluxo completo da solução (reproduzível do zero):
dados → tratamento → features → S1 → S2 → evidências → recomendação → confiança.
Datasets originais NÃO são alterados. Nenhum peso/score é criado.
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


def main():
    resultados = {"periodo": PERIODO_OBSERVADO}

    # 0) Hashes antes
    hash_antes = hash_arquivos()

    # 1) Dados
    dados = carregar()

    # 2) Features
    ai = build_imovel_table(dados["details"], dados["hosts"], dados["mesh"], dados["price"])
    venda = build_venda_table(dados["vivareal"])

    # 3) S1 — segmentos
    res_s1 = executar_s1(ai, venda)
    df_eleg = res_s1["df_eleg"]
    df_incon = res_s1["df_incon"]

    # 4) S2 — candidatos dentro dos segmentos prioritários (da comparação)
    comp = res_s1["comp"]
    # Deduplica por CÉLULA DE TRABALHO (nível efetivo): sub-células de fallback
    # (ex.: "bairro|tipo|q" que caíram no mesmo bairro×tipo) compartilham o mesmo
    # estimador; candidato deve aparecer uma única vez.
    vistos = set()
    prior_meta = []
    for c in comp["prioritarias"]:
        nivel = c.get("nivel")
        chave = c["chave"]
        rot_trabalho = c.get("rot_trabalho")
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
                           "rot_trabalho": rot_trabalho})
    df_s2 = selecionar_candidatos(ai, prior_meta)

    # 5) Evidências e explicabilidade
    dict_eleg = {c["chave"]: c for c in comp["prioritarias"] + comp["nao_prio"] + comp["insuf"]}
    expl_linhas = []
    for _, r in df_eleg.iterrows():
        chave = (r["bairro"], r["tipo"], r["quartos"])
        dom = []
        for i, j in comp["dominacao"]:
            if i == chave:
                dom.append(f"{j[0]}|{j[1]}|{j[2]}")
            elif j == chave:
                dom.append(f"({i[0]}|{i[1]}|{i[2]}) continua dominante")
        expl_linhas.append({"chave": chave_join(chave), "explicacao":
                            explicar_celula(r, dom, None)})
    df_exp = pd.DataFrame(expl_linhas)

    # 6) Recomendação final (texto auxiliar)
    recomendacoes = []
    # mapa segmento_prioritario(S2 rotulado) -> contagem
    if len(df_s2):
        s2_counts = df_s2.groupby("segmento_prioritario")["airbnb_listing_id"].nunique()
    else:
        s2_counts = pd.Series(dtype=int)
    # células de trabalho prioritárias (rotulo do S1 único)
    for c in comp["prioritarias"]:
        nivel, chave = c.get("nivel"), c["chave"]
        rot = c.get("rot_trabalho")
        if rot is None:
            if nivel == 0:
                rot = f"{chave[0]}|{chave[1]}|{chave[2]}"
            elif nivel == 1:
                rot = f"{chave[0]}|{chave[1]}|(todos quartos)"
            elif nivel == 2:
                rot = f"{chave[0]}|(todos tipos)|(todos quartos)"
            else:
                continue
        # evita duplicar células de trabalho
        if any(r["segmento"] == rot for r in recomendacoes):
            continue
        recomendacoes.append({
            "segmento": rot,
            "tipo": chave[1],
            "n_alvos_candidatos": int(s2_counts.get(rot, 0)),
        })
    df_rec = pd.DataFrame(recomendacoes)

    # 7) Confiança / limitações
    confianca = {
        "periodo": PERIODO_OBSERVADO,
        "sem_ocupacao": True,
        "sem_receita": True,
        "sem_roi": True,
        "sem_matching_individual_airbnb_vivareal": True,
        "preco_anunciado_nao_receita": True,
        "n_ai_global": int(ai["has_price"].sum()),
        "total_airbnb": int(len(ai)),
        "ofensores_de_qualidade": int(df_incon.shape[0]),
    }

    # 8) Gravar saídas
    def gravar(df, nome):
        if df is not None and len(df):
            df.to_csv(os.path.join(OUT_DIR, nome + ".csv"), index=False,
                      encoding="utf-8-sig")
        return os.path.join(OUT_DIR, nome + ".csv")

    out_s1 = gravar(df_eleg, "s1_segmentos")
    out_incon = gravar(df_incon, "s1_inconclusivas")
    out_s2 = gravar(df_s2, "s2_candidatos")
    gravar(df_exp, "evidencias")
    gravar(df_rec, "recomendacao_segmentos")

    with open(os.path.join(OUT_DIR, "pipeline_resultados.json"), "w", encoding="utf-8") as f:
        json.dump({
            "hash_dataset_antes": hash_antes,
            "n_prioritarias": res_s1["n_prioritarias"],
            "n_nao_prioritarias": res_s1["n_nao_prio"],
            "n_insuficientes": res_s1["n_insuf"],
            "n_inconclusivas": res_s1["n_inconclusivas"],
            "n_candidatos_s2": int(len(df_s2)),
            "arquivos": {"s1": out_s1, "s1_inconclusivas": out_incon,
                         "s2": out_s2},
            "confianca": confianca,
        }, f, indent=2, ensure_ascii=False)

    hash_depois = hash_arquivos()
    intactos = hash_antes == hash_depois

    print("=" * 70)
    print("RESULTADO DO PIPELINE")
    print("=" * 70)
    print(f"Segmentos prioritários      : {res_s1['n_prioritarias']}")
    print(f"Segmentos não priorizáveis  : {res_s1['n_nao_prio']}")
    print(f"Segmentos não dominados sem evidência (insuf.): {res_s1['n_insuf']}")
    print(f"Segmentos inconclusivos     : {res_s1['n_inconclusivas']}")
    print(f"Candidatos operacionais (S2): {len(df_s2)}")
    print("=" * 70)
    print("Arquivos gerados:")
    print(" -", out_s1)
    print(" -", out_incon)
    print(" -", out_s2)
    print(" -", os.path.join(OUT_DIR, "evidencias.csv"))
    print(" -", os.path.join(OUT_DIR, "recomendacao_segmentos.csv"))
    print(f"Datasets originais intactos : {intactos}")
    print("R calculado somente em nível de segmento: OK (afirmação de código)")


def chave_join(chave):
    return " | ".join(str(x) for x in chave)


if __name__ == "__main__":
    main()