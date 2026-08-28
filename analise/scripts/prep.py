"""
Preparacao de dados (somente-leitura) para os testes empiricos do hackathon.

Este script NAO modifica os datasets originais. Ele apenas le os CSVs e
monta estruturas derivadas (tabelas de presenca, flags, normalizacao de bairro)
usadas pelos testes. Toda saida vai para analise/output/.
"""
import pandas as pd
import os

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "data")
OUT = os.path.join(os.path.dirname(__file__), "..", "output")


def load(name):
    return pd.read_csv(os.path.join(DATA, name), encoding="utf-8")


def prepare():
    det = load("Details_Itapema.csv")
    hosts = load("Hosts_ids_Itapema.csv")
    mesh = load("Mesh_Ids_Data_Itapema.csv")
    price = load("Price_AV_Itapema.csv")
    viv = load("VivaReal_Itapema.csv")

    # --- flags de presenca ao nivel de listing (Airbnb) ---
    price_ids = set(price["airbnb_listing_id"].unique())
    det["has_price"] = det["airbnb_listing_id"].isin(price_ids)

    # marca se o listing existe no mesh (todos existem, mas mantemos p/ robustez)
    mesh_ids = set(mesh["airbnb_listing_id"].unique())
    det["has_mesh"] = det["airbnb_listing_id"].isin(mesh_ids)

    # estimativa de idade: usamos a data de aquisicao do mesh como proxy
    # de quando o anuncio comecou a ser rastreado (nao confundir com criacao)
    m = mesh[["airbnb_listing_id", "aquisition_date"]].rename(
        columns={"aquisition_date": "mesh_first_seen"})
    det = det.merge(m, on="airbnb_listing_id", how="left")
    det["mesh_first_seen_dt"] = pd.to_datetime(det["mesh_first_seen"], errors="coerce")

    # normalizacao de bairro (canonica) para integracao Airbnb x VivaReal
    def norm_suburb(s):
        if pd.isna(s):
            return None
        x = str(s).strip().lower()
        # remove acentos e substitui variacoes conhecidas
        x = (x.replace("sao", "são").replace("taboleiro", "tabuleiro")
              .replace("sertao", "sertão").replace("mar", "mar")
              .replace("meia praia - frente mar", "meia praia")
              .replace("jardim praia mar", "jardim praiamar")
              .replace("varzea", "várzea"))
        canon = {
            "centro": "Centro",
            "meia praia": "Meia Praia",
            "morretes": "Morretes",
            "tabuleiro dos oliveiras": "Tabuleiro dos Oliveiras",
            "tabuleiro": "Tabuleiro dos Oliveiras",
            "casa branca": "Casa Branca",
            "alto são bento": "Alto São Bento",
            "ilhota": "Ilhota",
            "canto da praia": "Canto da Praia",
            "várzea": "Várzea",
            "sertão do trombudo": "Sertão do Trombudo",
            "sertãozinho": "Sertãozinho",
            "andorinha": "Andorinha",
            "castelo branco": "Castelo Branco",
            "estreito": "Estreito",
            "ocean tower": "Ocean Tower",
            "jardim praiamar": "Jardim Praiamar",
            "areal": "Areal",
            "lameiro": "Lameiro",
            "leopoldo zarling": "Leopoldo Zarling",
            "itapema": "Itapema",
        }
        return canon.get(x, x if x not in ("none", "nan", "") else None)

    mesh["suburb_norm"] = mesh["suburb"].apply(norm_suburb)
    viv["suburb_norm"] = viv["suburb"].apply(norm_suburb)
    det = det.merge(mesh[["airbnb_listing_id", "suburb", "suburb_norm"]],
                    on="airbnb_listing_id", how="left", suffixes=("", "_mesh"))

    # presenca de reviews (rating>0 == tem avaliacao)
    det["has_reviews"] = det["number_of_reviews"] > 0

    out = {
        "det": det, "hosts": hosts, "mesh": mesh, "price": price, "viv": viv,
    }
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    d = prepare()
    for k, df in d.items():
        print(k, df.shape)
    # salvar prepared para reuso opcional
    # (nao salvamos para nao poluir; testes recarregam via prepare())
