# -*- coding: utf-8 -*-
"""
config.py — Parâmetros metodológicos centralizados (único local de configuração).
Metodologia congelada (fase 3 revisada + P1/P2). NÃO alterar valores na implementação.
Cada parâmetro traz seu STATUS: 'dados' (sustentado por dados), 'operacional'
(critério operacional), 'hipotese' (hipótese metodológica provisória).
"""
import numpy as np

# ---------------------------------------------------------------------------
# Datasets / rotas
DATA_DIR = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\data"
OUT_DIR = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\analise\saida"
SCRIPTS_DIR = r"C:\Users\maria\OneDrive\Área de Trabalho\hackathon\jovens-talentos-2026-hackathon-data\analise\scripts"

PERIODO_OBSERVADO = "2025-01-06 a 2025-04-20"

# ---------------------------------------------------------------------------
# Parâmetros metodológicos congelados
# ---------------------------------------------------------------------------
GATE_N_AI = 5                     # status: dados — piso anúncios Airbnb com preço por célula
GATE_N_VI_SALE = 5                # status: dados — piso anúncios VivaReal com sale_price válido
GATE_HALF_IC95 = 0.60             # status: operacional — meia-largura relativa do IC95(R) máxima
N_DATAS_MIN_S2 = 20               # status: operacional — critério conservador de calendário observado (S2)
DELTA_MIN_LOG = np.log(1.25)      # status: hipotese — Δ_min = ln(1,25) ≈ 0.223 (materialidade, provisório)

# Inferência (metodologia §4.3)
B_BOOTSTRAP = 2000                # réplicas bootstrap por cluster (anúncio)
ALPHA_IC = 0.05                   # nível do IC95
P_UMBIAR_DOM = 0.975              # P(Δ>0) p/ dominância
QUI_FDR = 0.05                    # q-Benjamini–Hochberg sobre pares
SEED = 7

# Granularidades (do mais fino ao mais grosso)
LEVELS = [
    ("bairro_tipo_q", ["bairro", "tipo", "q"]),
    ("bairro_tipo", ["bairro", "tipo"]),
    ("bairro", ["bairro"]),
]
Q_GRUPOS = ["1", "2", "3", "4+"]   # 0 quartos excluído ("sem informação")

# Rótulo/status por parâmetro (p/ documentação automática)
PARAM_STATUS = {
    "GATE_N_AI": "dados",
    "GATE_N_VI_SALE": "dados",
    "GATE_HALF_IC95": "operacional",
    "N_DATAS_MIN_S2": "operacional",
    "DELTA_MIN_LOG": "hipotese",
    "QUI_FDR": "metodologia §4.3",
    "P_UMBIAR_DOM": "metodologia §4.3",
    "B_BOOTSTRAP": "metodologia §4.3",
}

def parametros():
    """Devolve dict com valores + status (p/ relatório)."""
    return {k: {"valor": getattr(__import__(__name__), k),
                "status": PARAM_STATUS.get(k, "—")}
            for k in PARAM_STATUS}