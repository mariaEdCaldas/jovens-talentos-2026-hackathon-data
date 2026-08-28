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
        morretes|casa|(todos quartos)         bairro×tipo 0.00057  0.00048  0.00099 0.44621    14                  358             14.14141
tabuleiro dos oliveiras|apartamento|2 bairro×tipo×quartos 0.00058  0.00044  0.00087 0.37028    12                  108             16.21622

## 5. Candidatos operacionais (S2) — amostra (top 25)
 airbnb_listing_id          segmento_prioritario      bairro        tipo quartos  diaria_mediana  n_datas  numero_reviews  reviews_ano  star_rating  is_guest_favorite  is_superhost is_professional can_instant_book  cleaning_fee  n_guests  n_beds  maturidade_anos
           8838629        morretes|apartamento|3    morretes apartamento       3           650.0     66.0              88    27.354894         4.70              False          True            True             True         200.0        15      11         3.216975
          11044577          centro|apartamento|1      centro apartamento       1           378.0     55.0              26    97.902062         4.38              False         False           False             True         306.0         4       1         0.265572
          21545686          centro|apartamento|2      centro apartamento       2           269.0     72.0              92   346.422680         4.76              False          True           False             True         120.0         5       3         0.265572
          22421421 morretes|casa|(todos quartos)    morretes        casa       2           347.0     56.0               4     1.243404         4.50              False         False           False            False         100.0        11       5         3.216975
          22421606 morretes|casa|(todos quartos)    morretes        casa       2           361.0     47.0              27   101.667526         4.85              False         False           False            False         100.0        11       8         0.265572
          22514231          centro|apartamento|2      centro apartamento       2           300.0     36.0              34   128.025773         4.82              False         False           False             True         250.0         6       2         0.265572
          22648075          centro|apartamento|2      centro apartamento       2           348.0     65.0              16     4.973617         5.00              False         False           False            False         150.0         6       5         3.216975
          28410850          centro|apartamento|1      centro apartamento       1           499.0     76.0              62   233.458763         4.85              False         False           False             True           0.0         2       1         0.265572
          29302246     casa branca|apartamento|2 casa branca apartamento       2           400.0     58.0              56   210.865979         4.91              False         False            True            False         180.0         5       4         0.265572
          29341170     casa branca|apartamento|2 casa branca apartamento       2           349.0     46.0              81   305.002577         4.88              False         False            True            False         180.0         5       2         0.265572
          30332330          centro|apartamento|2      centro apartamento       2           350.0     56.0              57    17.718511         4.67              False         False           False            False         150.0         6       4         3.216975
          31682871          centro|apartamento|2      centro apartamento       2           290.0     41.0              59   222.162371         4.68              False          True           False            False         180.0         5       3         0.265572
          32766950          centro|apartamento|2      centro apartamento       2           300.0     48.0              11     3.662489         4.82              False         False           False            False         250.0         6       4         3.003422
          38899673        morretes|apartamento|2    morretes apartamento       2           710.0     78.0               7     2.175957         5.00              False         False           False            False         245.0         4       2         3.216975
          40023421        morretes|apartamento|2    morretes apartamento       2           500.0     99.0              11    41.420103         4.73              False         False           False            False         280.0         6       3         0.265572
          40039627          centro|apartamento|1      centro apartamento       1           319.0     84.0             504   156.668936         4.84              False          True            True             True          35.0         3       2         3.216975
          40209404          centro|apartamento|1      centro apartamento       1           311.0     73.0             373   115.947447         4.86              False          True            True             True          35.0         4       3         3.216975
          40371384          centro|apartamento|1      centro apartamento       1           601.0     91.0             343   106.621915         4.83              False          True            True             True          60.0         6       3         3.216975
          46530405        morretes|apartamento|3    morretes apartamento       3          1043.0     83.0              41    21.301920         4.85              False         False           False            False         520.0         8       3         1.924709
          47402735          centro|apartamento|2      centro apartamento       2           399.0     66.0               6    22.592784         5.00              False         False           False             True         610.0         6       5         0.265572
          47421617          centro|apartamento|2      centro apartamento       2           370.0     36.0               7    26.358247         4.71              False         False           False            False         260.0         5       4         0.265572
          48526011 morretes|casa|(todos quartos)    morretes        casa       3           500.0     65.0              17    64.012887         4.88              False         False           False            False         300.0        10       3         0.265572
          48941838          centro|apartamento|2      centro apartamento       2           370.0     46.0              25     7.771277         4.48              False         False           False            False         180.0         6       3         3.216975
          52059007          centro|apartamento|2      centro apartamento       2          1000.0    105.0               1     3.765464         5.00              False         False           False            False          50.0         6       2         0.265572
          52266549        morretes|apartamento|3    morretes apartamento       3           700.0     77.0              14     4.661349         4.79              False         False           False            False         300.0         8       7         3.003422

## 6. Evidências / explicabilidade (amostra de 3 prioritários)
---
Segmento: canto da praia|apartamento|(todos quartos) (nível avaliado: bairro×tipo)
Status: nao_prioritaria
R = 0.00030 — razão entre a mediana da diária anunciada no Airbnb e a mediana dos preços de venda observados no VivaReal para o mesmo segmento (indicador COMPARATIVO de segmento; não estima retorno de imóvel individual).
IC95(R) = [0.00018, 0.00042] | half = 0.399
Observações utilizadas: n_ai (Airbnb com preço) = 5, n_vi_total = 93, n_vi_com_sale_price = 93 (usados na estimativa).
Cobertura do Price no segmento: 55.6% (métrica de representatividade; seleção de Price é limitação).
Dominância contra outros segmentos (Δ com FDR controlado, Δ_min = 25%): domina 9 segmento(s) — (casa branca|apartamento|2) continua dominante; (centro|apartamento|1) continua dominante; (centro|apartamento|2) continua dominante; (meia praia|apartamento|1) continua dominante; (morretes|apartamento|2) continua dominante
Limitações: preço anunciado (não receita/ocupação); janela jan–abr/2025; junção Airbnb×VivaReal agregada; sem correspondência individual.
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

## 7. Confiança e limitações
- Sem ocupação, sem receita, sem ROI, sem yield, sem retorno observado (todos flags True).
- Sem matching individual Airbnb↔VivaReal (verificado; S2 não possui preço de venda).
- Preço anunciado ≠ receita. Cobertura de Price é seletiva (só anúncios ativos).
- n_ai global com preço: 999 de 4441 anúncios.
- Janela jan–abr/2025; capturas em jan/2025.

## 8. Decisões de implementação dentro da metodologia congelada
1. **“Não dominada” ≠ “prioritária”:** uma célula só é priorizada se, além de não ser dominada, **dominar pelo menos uma outra célula elegível** (via Δ/FDR/Δ_min). Não dominada sem dominar ninguém → “não dominada sem evidência” (não priorizada).
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