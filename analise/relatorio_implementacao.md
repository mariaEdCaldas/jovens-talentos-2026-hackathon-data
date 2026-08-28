# Relatório de Implementação — Ranking S1/S2 (metodologia congelada)

**Período observado:** 2025-01-06 a 2025-04-20
**Datasets originais intactos (hash SHA-256):** True (verificado pelo pipeline)

## 1. Método aplicado
- Fluxo: dados → tratamento → features → S1 (segmentos) → S2 (candidatos) → evidências → recomendação → confiança/limitações.
- **R é calculado somente no nível de segmento:** R = mediana(diária anunciada Airbnb) / mediana(preço de venda observado VivaReal) para o mesmo segmento. Indicador **comparativo**, não estima retorno de imóvel.
- S1 (bairro×tipo×quartos) com **fallback** → bairro×tipo → bairro.
- S2 = candidatos operacionais dentro de segmentos prioritários. **NÃO é recomendação de compra.**
- Sem pesos, sem score 0–100, sem thresholds adicionais.

## 2. Parâmetros congelados (config.py) e status
| Parâmetro | Valor | Status |
|---|---|---|
| GATE_N_AI | `5` | dados |
| GATE_N_VI_SALE | `5` | dados |
| GATE_HALF_IC95 | `0.6` | operacional |
| N_DATAS_MIN_S2 | `20` | operacional |
| DELTA_MIN_LOG | `np.float64(0.22314355131420976)` | hipotese |
| QUI_FDR | `0.05` | metodologia §4.3 |
| P_UMBIAR_DOM | `0.975` | metodologia §4.3 |
| B_BOOTSTRAP | `2000` | metodologia §4.3 |

## 3. Resultados
- Segmentos **prioritários**: 7 (células de trabalho únicas: 7)
- Segmentos **não priorizáveis**: 10
- Segmentos não dominados sem evidência: 0
- Segmentos **inconclusivos** (evidência insuficiente / não elegíveis): 167
- Candidatos operacionais (S2, únicos): 98

Motivos das inconclusivas:
motivo
volume_ai+volume_vi    138
volume_ai               27
volume_vi                1
precisao                 1

## 4. Segmentos prioritários (S1)
                  bairro_tipo_quartos               nivel       R  R_ic_lo  R_ic_hi    half  n_ai  n_vi_com_sale_price  cobertura_price_pct
            casa branca|apartamento|2 bairro×tipo×quartos 0.00054  0.00042  0.00063 0.19536    11                   19             20.75472
                 centro|apartamento|1 bairro×tipo×quartos 0.00050  0.00044  0.00072 0.28133    78                   21             67.24138
                 centro|apartamento|2 bairro×tipo×quartos 0.00053  0.00039  0.00064 0.23832    65                   86             35.51913
               morretes|apartamento|2 bairro×tipo×quartos 0.00060  0.00051  0.00070 0.15937    51                  999             22.27074
               morretes|apartamento|3 bairro×tipo×quartos 0.00077  0.00057  0.00118 0.39657    10                  141             16.94915
tabuleiro dos oliveiras|apartamento|2 bairro×tipo×quartos 0.00058  0.00044  0.00087 0.37028    12                  108             16.21622
        morretes|casa|(todos quartos)         bairro×tipo 0.00057  0.00048  0.00099 0.44621    14                  358             14.14141

## 5. Candidatos operacionais (S2) — amostra (top 25)
  airbnb_listing_id      segmento_prioritario      bairro        tipo quartos  diaria_mediana  n_datas  numero_reviews  reviews_ano  star_rating  is_guest_favorite  is_superhost is_professional can_instant_book  cleaning_fee  n_guests  n_beds  maturidade_anos
           29341170 casa branca|apartamento|2 casa branca apartamento       2       349.00000     46.0              81   305.002577         4.88              False         False            True            False         180.0         5       2         0.265572
 795757968903961791 casa branca|apartamento|2 casa branca apartamento       2       350.00000     73.0              12     6.053867         4.67              False         False           False             True           0.0         3       3         1.982204
1083196219974177016 casa branca|apartamento|2 casa branca apartamento       2       315.00000     57.0               1     1.137850         5.00              False         False           False            False         200.0         4       3         0.878850
 784836681288428817 casa branca|apartamento|2 casa branca apartamento       2       370.00000     65.0              13    48.951031         4.77              False         False           False             True         200.0         5       4         0.265572
           29302246 casa branca|apartamento|2 casa branca apartamento       2       400.00000     58.0              56   210.865979         4.91              False         False            True            False         180.0         5       4         0.265572
1184152596221501552      centro|apartamento|1      centro apartamento       1       601.00000     81.0              11    27.518836         4.82              False         False            True             True         190.0         4       2         0.399726
1242713378625026725      centro|apartamento|1      centro apartamento       1       660.00000     83.0               8    28.096154         4.75              False         False            True             True         190.0         4       2         0.284736
1183418487997408853      centro|apartamento|1      centro apartamento       1       586.66670     63.0              20    50.034247         4.75              False         False            True             True         190.0         4       2         0.399726
1208757710030861160      centro|apartamento|1      centro apartamento       1       372.00000     87.0               4    14.048077         5.00              False         False            True             True         150.0         2       1         0.284736
1207992119242235910      centro|apartamento|1      centro apartamento       1       372.00000     89.0               3    60.000000         5.00              False         False            True             True         150.0         2       1         0.000000
1216602433904805187      centro|apartamento|1      centro apartamento       1       607.00000     85.0              10    35.120192         4.60              False         False            True             True         190.0         4       2         0.284736
1197195878719681680      centro|apartamento|1      centro apartamento       1       384.00000     76.0              16   320.000000         4.56              False         False            True             True         160.0         3       1         0.000000
1197121947398131654      centro|apartamento|1      centro apartamento       1       384.00000     73.0              21   420.000000         4.67              False         False            True             True         170.0         2       1         0.000000
1249385754807434824      centro|apartamento|1      centro apartamento       1       607.00000     78.0               7    24.584135         4.57              False         False            True             True         190.0         4       2         0.284736
1207335703563012811      centro|apartamento|1      centro apartamento       1       427.00000     82.0               1    20.000000         5.00              False         False            True             True         150.0         2       1         0.000000
1236367599770739400      centro|apartamento|1      centro apartamento       1       600.00000     59.0              15    52.680288         4.73              False          True           False            False         200.0         4       2         0.284736
1207383031689344642      centro|apartamento|1      centro apartamento       1       800.00000     76.0               8    20.013699         4.88              False         False           False            False         150.0         4       1         0.399726
           40371384      centro|apartamento|1      centro apartamento       1       601.00000     91.0             343   106.621915         4.83              False          True            True             True          60.0         6       3         3.216975
1181944920258781413      centro|apartamento|1      centro apartamento       1       374.50000     87.0              17    42.529110         4.71              False         False            True             True         150.0         2       1         0.399726
1181723518413479765      centro|apartamento|1      centro apartamento       1       450.00000     86.0              12    30.020548         4.67              False         False           False            False         150.0         4       1         0.399726
1207940918769840398      centro|apartamento|1      centro apartamento       1       374.50000     77.0               2     7.024038         5.00              False         False            True             True         150.0         2       1         0.284736
1234084273027568746      centro|apartamento|1      centro apartamento       1       374.41667     60.0              13    45.656250         4.77              False         False            True             True         180.0         3       2         0.284736
           40039627      centro|apartamento|1      centro apartamento       1       319.00000     84.0             504   156.668936         4.84              False          True            True             True          35.0         3       2         3.216975
1208718899534488031      centro|apartamento|1      centro apartamento       1       427.00000     90.0               5   100.000000         4.80              False         False            True             True         150.0         2       1         0.000000
1181933658424522281      centro|apartamento|1      centro apartamento       1       373.00000     77.0              19    47.532534         4.79              False         False            True             True         150.0         2       1         0.399726

## 6. Evidências / explicabilidade (amostra de 3 prioritários)
---
Segmento: casa branca|apartamento|2 (nível avaliado: bairro×tipo×quartos)
Status: prioritaria
R = 0.00054 — razão entre a mediana da diária anunciada no Airbnb e a mediana dos preços de venda observados no VivaReal para o mesmo segmento (indicador COMPARATIVO de segmento; não estima retorno de imóvel individual).
IC95(R) = [0.00042, 0.00063] | half = 0.195
Observações utilizadas: n_ai (Airbnb com preço) = 11, n_vi_total = 19, n_vi_com_sale_price = 19 (usados na estimativa).
Cobertura do Price no segmento: 20.8% (métrica de representatividade; seleção de Price é limitação).
Dominância contra outros segmentos (Δ com FDR controlado, Δ_min = 25%): domina 8 segmento(s) — centro|apartamento|3; centro|apartamento|4+; meia praia|apartamento|3; meia praia|apartamento|4+; meia praia|casa|3
Limitações: preço anunciado (não receita/ocupação); janela jan–abr/2025; junção Airbnb×VivaReal agregada; sem correspondência individual.
---
Segmento: centro|apartamento|1 (nível avaliado: bairro×tipo×quartos)
Status: prioritaria
R = 0.00050 — razão entre a mediana da diária anunciada no Airbnb e a mediana dos preços de venda observados no VivaReal para o mesmo segmento (indicador COMPARATIVO de segmento; não estima retorno de imóvel individual).
IC95(R) = [0.00044, 0.00072] | half = 0.281
Observações utilizadas: n_ai (Airbnb com preço) = 78, n_vi_total = 21, n_vi_com_sale_price = 21 (usados na estimativa).
Cobertura do Price no segmento: 67.2% (métrica de representatividade; seleção de Price é limitação).
Dominância contra outros segmentos (Δ com FDR controlado, Δ_min = 25%): domina 8 segmento(s) — centro|apartamento|3; centro|apartamento|4+; meia praia|apartamento|3; meia praia|apartamento|4+; meia praia|casa|3
Limitações: preço anunciado (não receita/ocupação); janela jan–abr/2025; junção Airbnb×VivaReal agregada; sem correspondência individual.
---
Segmento: centro|apartamento|2 (nível avaliado: bairro×tipo×quartos)
Status: prioritaria
R = 0.00053 — razão entre a mediana da diária anunciada no Airbnb e a mediana dos preços de venda observados no VivaReal para o mesmo segmento (indicador COMPARATIVO de segmento; não estima retorno de imóvel individual).
IC95(R) = [0.00039, 0.00064] | half = 0.238
Observações utilizadas: n_ai (Airbnb com preço) = 65, n_vi_total = 86, n_vi_com_sale_price = 86 (usados na estimativa).
Cobertura do Price no segmento: 35.5% (métrica de representatividade; seleção de Price é limitação).
Dominância contra outros segmentos (Δ com FDR controlado, Δ_min = 25%): domina 7 segmento(s) — centro|apartamento|3; centro|apartamento|4+; meia praia|apartamento|3; meia praia|apartamento|4+; meia praia|outros|1
Limitações: preço anunciado (não receita/ocupação); janela jan–abr/2025; junção Airbnb×VivaReal agregada; sem correspondência individual.

## 7. Confiança e limitações
- Sem ocupação, sem receita, sem ROI, sem yield, sem retorno observado (todos flags True).
- Sem matching individual Airbnb↔VivaReal (verificado; S2 não possui preço de venda).
- Preço anunciado ≠ receita. Cobertura de Price é seletiva (só anúncios ativos).
- n_ai global com preço: 999 de 4441 anúncios.
- Janela jan–abr/2025; capturas em jan/2025.

## 8. Decisões de implementação dentro da metodologia congelada
1. **“Não dominada” ≠ “prioritária”:** uma célula só é priorizada se, além de não ser dominada, **dominar pelo menos uma outra célula elegível** (via Δ/FDR/Δ_min). Não dominada sem dominar ninguém → “não dominada sem evidência” (não priorizada). Emitido semípara quando aplicável.
2. **Fallback e duplicação de S2:** sub-células (ex.: bairro|tipo|q distintas) que caem no mesmo nível de fallback compartilham o mesmo estimador; a S2 **deduplica por anúncio** para não repetir candidatos.
3. **Regra §6 “cobertura<P25 + baixo volume → inconclusivo”:** ‘baixo volume’ não tem número definido na metodologia; **não** foi aplicado como rebaixador automático. A cobertura é reportada por célula; se o analista definir um valor para “baixo volume”, pode ser habilitado sem alterar a metodologia.
4. **has_price na S2:** usado somente como condição de **disponibilidade de informação** (o anúncio precisa ter preço observado para ser avaliado); não contribui positivamente para a atratividade.

## 9. Correção de exclusividade hierárquica do fallback
A implementação foi ajustada para que o conjunto de células de **comparação** seja **hierarquicamente não sobreposto**: uma célula agregada (bairro×tipo ou bairro) SÓ entra se NENHUM descendente mais específico foi usável. 
O nível agregado funciona como SUBSTITUTO do detalhe que falhou; nunca concorre com ele.
- Célula fina: bairro×tipo×quartos elegível → representa a região no detalhe; o ancestral (bt/bairro) **não** entra.
- Célula de fallback: só quando todos os trios finos da região falharam em elegibilidade.
- Nível efetivo utilizado, prioridade, não-prioridade e inconclusão: reportados por célula em S1.

### Contagens antes/depois da correção
| Métrica | Antes | Depois |
|---|---|---|
| Células de trabalho (elegíveis p/ comparação) | 26 | 17 |
| — finas (nível 0) | 13 | 13 |
| — fallback bairro×tipo (nível 1) | 7 | 4 |
| — fallback bairro (nível 2) | 6 | 0 |
| Segmentos S1 prioritários | 11 | 7 |
| Segmentos S1 não priorizáveis | 15 | 10 |
| Segmentos S1 inconclusivas | 104 | 167 |
| Candidatos operacionais S2 (únicos) | 104 | 98 |

**Verificado:** nenhuma célula de comparação agregada coexiste com célula descendente no conjunto final (checagem automática de exclusividade — sem pares análogo-descendente). BH-FDR aplicado apenas sobre o novo conjunto de células (17) de comparação.

_Gerado por run_pipeline.py + gerar_relatorio.py. Reproduzível do zero._