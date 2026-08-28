"""
Teste T4 - Validacao empirica dos problemas de integracao e qualidade
identificados no diagnostico.

Verifica:
  (a) VivaReal: duplicatas de listing_id - sao linhas identicas? quantas?
  (b) Hosts: fan-out por owner_id (quantos owners tem N linhas).
  (c) Integracao Airbnb x VivaReal via bairro: normalizacao cobre quanto;
      quantos bairros continuam sem correspondencia de um lado.
  (d) Price: 6 listings orfaos (sem Details/Mesh) - tamanho/cobertura.
  (e) Details: lat/lon zeradas (confirmacao), min_nights zeros.
  (f) role: coordenadas unicas de mesh 3349 x 3142 -> possiveis duplicatas de
      localizacao (mesmo predio) entre listings Airbnb.
"""
import pandas as pd
import numpy as np
import os
import io

import sys
sys.path.insert(0, os.path.dirname(__file__))
from prep import prepare

OUT = os.path.join(os.path.dirname(__file__), "..", "output")
buf = io.StringIO()

def line(*a):
    buf.write(" ".join(str(x) for x in a) + "\n")

def main():
    d = prepare()
    det, hosts, mesh, price, viv = d["det"], d["hosts"], d["mesh"], d["price"], d["viv"]

    line("=" * 100)
    line("T4 - VALIDACAO DE INTEGRACAO E QUALIDADE")
    line("=" * 100)

    # ---- (a) VivaReal duplicatas ----
    line("-- (a) VivaReal - duplicatas de listing_id --")
    dup_mask = viv.duplicated(subset=["listing_id"], keep=False)
    line("linhas envolvidas em duplicata:", int(dup_mask.sum()))
    dup_rows = viv[dup_mask].sort_values("listing_id")
    n_dup_ids = dup_rows["listing_id"].nunique()
    line("listing_ids duplicados distintos:", n_dup_ids)
    line("-> dessas, grupos onde todas as colunas sao identicas (dup EXATA) e onde divergem:")
    check = []
    for lid, grp in dup_rows.groupby("listing_id"):
        mx = grp.drop(columns=["listing_id"]).nunique(dropna=False).max()
        identical = (mx == 1)
        check.append((lid, len(grp), identical, mx))
    ck = pd.DataFrame(check, columns=["listing_id", "n", "todos_identicos", "max_colunas_distintas"])
    line("distribuicao (n linhas, linhas identicas):")
    line(ck.groupby(["n", "todos_identicos"]).size().to_string())
    line(f"listing_ids com duplicata EXATA (todas colunas iguais): "
         f"{int(ck['todos_identicos'].sum())}")
    line(f"listing_ids com divergencia entre as linhas: "
         f"{int((~ck['todos_identicos']).sum())}")
    line("-> Os 35 duplicados 'exatos' provavelmente = mesmo anuncio presente 2x")
    line("   no arquivo (arte fatual); manter 1. Ha 1 caso (2655470871) com")
    line("   divergencia (pode ser mesmo imovel ofertado por 2 anuncios).")
    line()

    # ---- (b) Hosts fan-out ----
    line("-- (b) Hosts - fan-out por owner_id --")
    cnt = hosts.groupby("owner_id").size()
    line("owners distintos:", len(cnt))
    line("distribuicao do numero de linhas por owner:")
    line(cnt.value_counts().sort_index().head(12).to_string())
    line("linhas que precisariam de dedup p/ owner-unico:", int((cnt > 1).sum()), "owners")
    line()

    # ---- (c) integracao por bairro ----
    line("-- (c) Normalizacao de bairro (Airbnb mesh vs VivaReal) --")
    mesa = set(mesh["suburb_norm"].dropna())
    viva = set(viv["suburb_norm"].dropna())
    line("bairros mesh (norm):", len(mesa), sorted(mesa))
    line("bairros viv (norm):", len(viva), sorted(viva))
    line("bairros com correspondencia:", len(mesa & viva), sorted(mesa & viva))
    line("bairros SOMENTE mesh (sem venda VivaReal):", sorted(mesa - viva))
    line("bairros SOMENTE viv (sem oferta Airbnb/mesh):", sorted(viva - mesa))
    line()
    # linhas VivaReal que ficam sem par de bairro no mesh
    viv_nopair = viv[~viv["suburb_norm"].isin(mesa)]
    line("linhas VivaReal em bairros sem oferta Airbnb (sem par p/ integracao):",
         len(viv_nopair), f"= {len(viv_nopair)/len(viv):.1%}")
    line(viv_nopair["suburb_norm"].value_counts().to_string())
    mesh_nopair = mesh[~mesh["suburb_norm"].isin(viva)]
    line("linhas Airbnb (mesh) em bairros sem oferta VivaReal:", len(mesh_nopair),
         f"= {len(mesh_nopair)/len(mesh):.1%}")
    line(mesh_nopair["suburb_norm"].value_counts().to_string())
    line()

    # ---- (d) price orfaos ----
    line("-- (d) Price - listing_ids sem Details/Mesh (orfaos) --")
    orphans = set(price["airbnb_listing_id"]) - set(det["airbnb_listing_id"])
    line("total orfaos:", len(orphans))
    line("linhas de price orfas:", price["airbnb_listing_id"].isin(orphans).sum(),
         f"= {price['airbnb_listing_id'].isin(orphans).mean():.2%} do price")
    line("> esses nao podem ser agregados a caracteristicas/loc do listing.")
    line()

    # ---- (e) Details coords/min_nights ----
    line("-- (e) Details: coordenadas e min_nights --")
    line("latitude==0 e longitude==0:", int(((det['latitude']==0) & (det['longitude']==0)).sum()), "de", len(det))
    line("min_nights == 0 em todas:", int((det['min_nights']==0).all()))
    line()

    # ---- (f) duplicatas de localizacao no mesh ----
    line("-- (f) mesma coordenada (predio) compartilhada por varios listings --")
    coord = mesh.groupby(["latitude", "longitude"]).size()
    line("coords unicas:", len(coord))
    line("coords compartilhadas por 2+ listings:", int((coord > 1).sum()))
    line("max listings numa mesma coord:", int(coord.max()))
    line(coord.value_counts().sort_index().head(10).to_string())
    line("> indica unidades distintas no mesmo edificio (permite analise intra-predio).")
    line()

    out = buf.getvalue()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "t4_integracao_qualidade.txt"), "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote t4_integracao_qualidade.txt", len(out))


if __name__ == "__main__":
    main()