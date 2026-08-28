# P1/P2 — Análises pré-decisão (perfil de células, precisão e efeito mínimo)

**Projeto:** Hackathon Seazone — Itapema (SC)
**Fase:** P1 (perfil de células e precisão) e P2 (efeito mínimo Δ_min). **Sem ranking, sem shortlist, sem pesos.**
**Scripts reproduzíveis:** `analise/scripts/p1_perfil_celulas.py`, `analise/scripts/p2_delta_min.py` (+ `common_p1p2.py`).
**Saídas:** `analise/saida/p1_resultados.txt`, `p2_delta_min.txt`, `p1_subsampling.png`, `p1_ndatas_estabilidade.png`, `p2_delta_min.png`.

**Nota de revisão (2026-08-28):** este relatório foi corrigido para separar explicitamente
`n_vi_total` de `n_vi_com_sale_price`, reformular a interpretação do subsampling como **evidência
local** (e não tamanho amostral universal), tratar `n_datas ≥ 20` como **limiar operacional
conservador** (e não comprovação estatística), e tratar `Δ_min` como **hipótese metodológica de
materialidade** (e não descoberta empírica). Números intactos; apenas interpretações e
nomenclaturas corrigidas.

---

## 1. Resultados do P1 — Perfil de células e precisão

### Definições de contagem usadas (correção da revisão)

- **`n_ai`** = nº de anúncios Airbnb **com preço** (`has_price=1`) na célula — são os efetivamente usados no bootstrap.
- **`n_vi_total`** = nº de anúncios VivaReal **estruturalmente elegíveis** na célula após dedup e exclusão de lançamentos/frente-mar (com ou sem `sale_price` válido).
- **`n_vi_com_sale_price`** = nº de anúncios VivaReal com **`sale_price` válido** (não-nulo e >0) na célula — é o **efetivamente usado na estimativa** (o bootstrap usa `sale_price.dropna()`).
- O critério de elegibilidade e o bootstrap usam **`n_vi_com_sale_price`**; `n_vi_total` é reportado como contexto de cobertura do lado de venda.
- **Nos dados atuais** `n_vi_com_sale_price == n_vi_total` (fração média 1,000 em todas as granularidades), pois `sale_price` não tem nulos no VivaReal. A distinção é mantida para robustez da definição e para fluxos futuros.

### 1.1 Distribuição de n_ai (anúncios Airbnb com preço) por granularidade

| Granularidade | n células | mediana n_total_ai | mediana n_com_price | células com n_ai≥5 | células com n_ai≥10 |
|---|---|---|---|---|---|
| bairro×tipo×quartos | 130 | 5 | 0,5 | **16 (12%)** | 12 |
| bairro×tipo | 41 | 14 | 2 | **14 (34%)** | 8 |
| bairro | 16 | 35,5 | 5,5 | **10 (62%)** | 6 |

- A **granularidade fina sofre de escassez**: apenas 12% das células atingem n_ai≥5 com preço. Isso impõe o **fallback hierárquico** como regra central (bairro×tipo×quartos → bairro×tipo → bairro).
- Metade das células finas tem **0 anúncios com preço** (65 células) → sem possibilidade de estimativa; ficam fora ou caem no fallback.

### 1.2 Distribuição de n_vi (VivaReal) por granularidade
*(n_vi abreviado abaixo refere-se a `n_vi_com_sale_price` quando usado na estimativa; `n_vi_total` reportado como contexto.)*

| Granularidade | n células | n_vi_total mediana (sem lanç.) | n_vi_com_sale mediana (sem lanç.) | células com n_vi_com_sale≥5 | células com n_vi_com_sale≥10 |
|---|---|---|---|---|---|
| bairro×tipo×quartos | 120 | 5 | 5 | **61** | 46 |
| bairro×tipo | 46 | 17 | 17 | **36** | 27 |
| bairro | 19 | 94 | 94 | **14** | 14 |

- O lado de venda é **muito menos limitante**: ~2× mais células com n_vi_com_sale_price≥5 que n_ai≥5. O **estrangulamento de dados está no Airbnb (preço)**.
- Lançamentos/frente-mar: 472 anúncios marcados; a exclusão preserva a maioria das células (120→115 células com amostra; medianas próximas).
- `n_vi_com_sale_price == n_vi_total` no dataset atual (ver definições acima).

### 1.3 Cobertura Price por célula

| Granularidade (células com n_total_ai≥5) | n | P25 | mediana | P75 |
|---|---|---|---|---|
| bairro×tipo×quartos | 66 | 0% | **14,6%** | 24,9% |
| bairro×tipo | 32 | 5,8% | **13,7%** | 21,5% |
| bairro | 15 | 14,6% | **18,8%** | 25,3% |

- A cobertura é **baixa e variável** (mediana ~15%). Reforça: a cobertura é métrica de **evidência/representatividade**, não regra dura de elegibilidade (metodologia §6 mantida).

### 1.4 Largura do IC95 da razão R (bootstrap por cluster) × n

- Células com dados para bootstrap: **44** (bairro×tipo×quartos). Meia-largura relativa do IC95(R): mediana **0,221**; fração com half ≤ 0,60: **86%**.

| Faixa de n_ai | células | mediana half | média half | máx |
|---|---|---|---|---|
| 1–4 | 29 | 0,210 | 0,291 | 1,51 |
| 5–9 | 3 | 0,572 | 0,541 | 0,66 |
| 10–19 | 4 | 0,375 | 0,750 | 2,05 |
| 20–49 | 2 | 0,151 | 0,151 | 0,17 |
| 50+ | 6 | 0,194 | 0,179 | 0,29 |

- Há **forte variabilidade de precisão por célula** mesmo em faixas de n_ai comparáveis (ex.: n_ai 10–19 tem half de 0,205 a 2,046). Isso reforça que o critério de qualidade deve ser o **gate de precisão medido por célula (half IC95(R) ≤ 0,60)**, e **não um n fixo**.
- n_ai 1–4 tem half até 1,51 — inviável como base de ordenação na prática (mas mesmo células pequenas pontuais podem passar no gate se forem dispersas o suficiente).

**Subsampling (evidência LOCAL, não tamanho amostral universal):**
- Estudo realizado **somente na maior célula (Meia Praia × apartamento × 3 quartos)** (n_ai=327; n_vi_total=1638, dos quais n_vi_com_sale_price=1638), com **amostragem com reposição antes do bootstrap** (e bootstraps com B=400, 15 réplicas).

| n amostrado | 3 | 5 | 8 | 12 | 20 | 30 | 50 |
|---|---|---|---|---|---|---|---|
| half_med | 0,76 | 0,80 | 0,42 | 0,33 | 0,26 | 0,21 | 0,17 |
| half_p75 | 0,91 | 0,95 | 0,53 | 0,37 | 0,30 | 0,26 | 0,19 |

- **Interpretação correta:** o estudo indica que, **nesta célula**, a precisão melhora conforme aumenta o nº de anúncios. É uma **evidência local** sobre essa célula e **não deve ser interpretado como demonstração de um tamanho amostral universal** (ex.: "8 anúncios é suficiente para qualquer célula"). O gate real continua sendo baseado na **precisão observada pelo IC95(R)** de cada célula, e **não em um n=8 universal**.

### 1.5 n_datas e estabilidade da diária individual

- Distribuição de n_datas (anúncios com preço): mediana **62**, Q25 42, Q75 77, mín 2, máx 105.
- relSE da mediana individual (bootstrap das noites sob hipótese **i.i.d.**):

| Faixa de n_datas | células | med relSE | p90 |
|---|---|---|---|
| 3–4 | 1 | 0,000 | 0,000 |
| 7–10 | 9 | 0,000 | 0,031 |
| 11–15 | 31 | 0,018 | 0,204 |
| 16–20 | 21 | 0,006 | 0,093 |
| 21–30 | 77 | 0,036 | 0,184 |
| 31–40 | 99 | 0,023 | 0,137 |
| 41–60 | 242 | 0,025 | 0,134 |
| 61+ | 518 | 0,028 | 0,127 |

- **Interpretação correta (correção da revisão):**
  - O bootstrap **i.i.d. das noites** NÃO captura **sazonalidade, dia da semana, feriados, blocos temporais nem a dependência temporal do preço**. Portanto, serve apenas como **análise exploratória de estabilidade da mediana**.
  - **`n_datas ≥ 20` é adotado como limiar operacional conservador** para exigir uma quantidade mínima de calendário observado no anúncio (S2), apoiado por essa exploração — **não** como um tamanho amostral estatisticamente comprovado.
  - **Não** é afirmado que "o grupo ≥20 tem p90 < 19%" — a tabela agrupa faixas **16–20** e **21–30** separadamente; não há um número único calculado exatamente para o grupo "≥20".

### 1.6 Granularidade de quartos 1|2|3|4+

Distribuição de `number_of_bedrooms` (todos / com preço):

| Grp | n total | n com preço |
|---|---|---|
| 0 | 56 | 8 |
| 1 | 549 | 144 |
| 2 | 1482 | 351 |
| 3 | 1922 | 404 |
| 4+ | 432 | 92 |

- Frequências declinantes para 4+ (432 anúncios, 92 com preço) **justificam agregar 4+** para não pulverizar células.
- **0 quartos (56; 8 com preço):** representam cadastro sem dormitório declarado (estúdios/ambíguos). **Decisão:** excluir da segmentação de células (relator "sem informação de quartos"), sem imputar.

---

## 2. Resultados do P2 — Efeito mínimo Δ_min

### 2.1 Significado operacional de cada diferença relativa de R

Base: mediana D≈460 R$/noite, mediana V≈990 mil R$, R≈0,000465.

| Δ (rel.) | múltiplo de R | Δ=ln(1+p) | Exemplo (D fixo, V varia) | Exemplo (V fixo, D varia) |
|---|---|---|---|---|
| 10% | x1,10 | +0,095 | D 460 / V 900 mil | V 990 mil / D 506 |
| 15% | x1,15 | +0,140 | D 460 / V 861 mil | V 990 mil / D 529 |
| 20% | x1,20 | +0,182 | D 460 / V 825 mil | V 990 mil / D 552 |
| 25% | x1,25 | +0,223 | D 460 / V 792 mil | V 990 mil / D 575 |
| 30% | x1,30 | +0,262 | D 460 / V 762 mil | V 990 mil / D 598 |
| 40% | x1,40 | +0,337 | D 460 / V 707 mil | V 990 mil / D 644 |

- Ex.: R 25% maior ⇔ diária fixa com capital ~20% menor, ou capital fixo com diária 25% maior.

### 2.2 Distribuição das diferenças pareadas observadas (14 células elegíveis; 91 pares)

| | | 
|---|---|
| média |Md| | 0,416 |
| P25 / P50 / P75 | 0,169 / 0,371 / 0,561 |
| mínimo | 0,004 | máximo | 1,294 |

- Esta distribuição é **apenas descritiva** da amostra observada de células; **não** demonstra qual Δ_min é "correto".

### 2.3 Impacto do Δ_min sobre os pares comparáveis

| Δ_min | pares abaixo do limiar de materialidade | pares acima do limiar |
|---|---|---|
| 10% | 14,3% | 85,7% |
| 15% | 22,0% | 78,0% |
| 20% | 27,5% | 72,5% |
| **25%** | **31,9%** | **68,1%** |
| 30% | 36,3% | 63,7% |
| 40% | 45,1% | 54,9% |

- **Interpretação correta (correção da revisão):** os valores indicam a fração de pares cuja **diferença observada** ficaria **abaixo do limiar de materialidade** escolhido (e, portanto, considerada **insuficiente para distinguir os segmentos dentro da metodologia adotada**).
- **Não** é afirmado que essas diferenças sejam "ruído". Uma diferença pequena pode ser apenas **uma diferença observada abaixo do limiar** — sua natureza (ruído, diferença real, efeito de seleção, diferença estrutural ou incerteza de estimativa) **não é identificada pelo P2**.
- Tampouco se afirma que 25% seja um "ponto de equilíbrio" ou o "melhor valor": isso é uma **decisão de materialidade**, não um resultado empírico (ver 2.4).

### 2.4 Recomendação Δ_min (hipótese metodológica provisória)

- **Não há referência interna da Seazone** disponível para definir objetivamente a materialidade.
- **`Δ_min = ln(1,25) ≈ 0,223` (diferença relativa de 25% em R)** é adotado **provisoriamente como hipótese de materialidade**.
- **Esse valor não foi descoberto empiricamente pelos dados e não representa um valor econômico objetivo.** O P2 apenas descreve a distribuição das diferenças entre as 14 células analisadas.
- **Sensibilidade obrigatória** nas vizinhanças **15%, 25% e 30%**.
- Se a Seazone definir outro valor de relevância econômica, ele substitui o provisório sem revisitar a metodologia (o pipeline re-executa).

---

## 3. Parâmetros recomendados (P1+P2)

| Parâmetro | Valor | Status | Base |
|---|---|---|---|
| Granularidade de quartos | 1 \| 2 \| 3 \| 4+ (0 → excluído/"sem informação") | **Sustentado por dados** | Frequências com preço 144/351/404/92; 0→56 (8 com preço) |
| Piso n_ai (mín. anúncios com preço/célula) | **5** | **Sustentado por dados** (gate de estabilidade do cluster-bootstrap) | n_ai 1–4 com half até 1,5; 5+ habilita 16/14/10 células |
| Piso n_vi (mín. anúncios de venda/célula) | **5** (`n_vi_com_sale_price`) | **Sustentado por dados** | 61 células finas satisfazem; lado não limitante |
| Suficiência de precisão | **half IC95(R) ≤ 0,60** (por célula) | **Critério operacional** | 86% das células com dados (mediana half 0,22); gate medido, não n fixo |
| Cobertura mínima (price%) | **sem gate rígido** — rebaixador de evidência | **Critério operacional** | cobertura mediana ~15% por célula; gate eliminaria quase tudo |
| n_datas mínimo (S2) | **≥ 20** | **Critério operacional conservador** | estabilidade exploratória da mediana (i.i.d.); NÃO comprovação estatística |
| Δ_min (efeito mínimo) | **ln(1,25)=0,223 (25%)** | **Hipótese metodológica provisória** | P2 descreve distribuição; valor é decisão de materialidade; sensibilidade 15/25/30% |
| Fallback | bairro×tipo×quartos → bairro×tipo → bairro | **Sustentado por dados** | 12%→34%→62% de células com n_ai≥5 |

**Classificação por natureza (correção da revisão):**
- **Sustentados diretamente pelos dados:** granularidade de quartos; piso n_ai≥5; piso n_vi≥5; fallback.
- **Critérios operacionais (decisão metodológica, não "verdade estatística"):** gate de precisão half≤0,60; cobertura como rebaixador; n_datas≥20.
- **Hipóteses metodológicas:** Δ_min=25% (materialidade), sensibilidade 15/25/30%.

---

## 4. Justificativa de cada parâmetro

1. **Quartos 1|2|3|4+:** distribuição empírica declinante; 4+ agrega 432/92 p/ preservar n de células; 0 = "sem informação" (sem dormitório declarado) fica fora.
2. **Piso n_ai=5 / n_vi=5:** mantém custo de bootstrap por cluster viável (5 clusters é o menor tamanho defensável); P1 mostra n_ai 1–4 com half até 1,5 (inviável em geral). O piso é um **pré-filtro**; a precisão final é garantida pelo gate de half.
3. **Suficiência ≤ 0,60:** garante que só entram células com precisão observada suficiente; com ele, 86% das células com dados passam. É **complementar ao piso**, porque piso sozinho não controla dispersão (ex.: n_ai 10–19 pode ter half 2,0).
4. **Cobertura sem gate:** cobertura ~15% reflete seleção estrutural de Price; torná-la gate eliminaria quase tudo e enviesaria a amostra final; mantém-se como **rebaixador de evidência** e reporte obrigatório.
5. **n_datas ≥ 20:** critério operacional conservador (mínimo de calendário observado), apoiado por exploração de estabilidade; **não** comprovação estatística (i.i.d. não captura sazonalidade etc.).
6. **Δ_min=25%:** hipótese de materialidade; **não** derivada empiricamente como valor "ótimo"; sensibilidade obrigatória 15/25/30%.

---

## 5. Análise de sensibilidade (resumo, a aprofundar na implementação)

- **Piso 5 → 8:** células finas com n_ai≥8 = 14 (vs 16 com ≥5); redução pequena → parâmetro estável. Reduzir para 3 é inviável (half alto). **Mantido 5.**
- **Suficiência 0,60 → 0,50/0,35:** aumenta percentual de "inconclusivos" (evidência mais estrita); 0,60 é o filtro mais permissivo ainda seguro (elimina só as piores células por precisão). A reportar no ranking.
- **n_datas 10 vs 20 vs 30:** efeito marginal na cobertura (maioria dos anúncios tem 62 datas). Mantido 20 como critério operacional.
- **Δ_min 15%–30%:** a sensibilidade deve ser reportada em **15%, 25% e 30%**; o ranking de *topo* (segmentos com diferenças grandes) tende a ser robusto; a separação de células de meio pode variar. Reportar explicitamente.
- **Fallback:** decisivo (indispensável dado P1); sensibilidade = verificar se células do topo no nível fino se mantêm no nível agregado (consistência hierárquica).

---

## 6. Alterações em relação à metodologia congelada (resultados de P1/P2)

1. **n_datas mínimo de S2 = 20** — agora com status explícito de **critério operacional conservador** (não comprovação estatística).
2. **Δ_min = 25% (0,223)** — status **hipótese metodológica provisória**; sensibilidade 15/25/30%.
3. **0 quartos excluído** da segmentação de células ("sem informação de quartos").
4. **Definição explícita de `n_vi`:** toda menção passa a usar `n_vi_com_sale_price` (usado na estimativa) com reporte de `n_vi_total` como contexto.
5. **Requisito de reporte em toda saída:** n_ai, n_vi_total, n_vi_com_sale_price, cobertura price%, half ou "inconclusivo".

---

## 7. METODOLOGIA FINAL CONGELADA — parâmetros definidos (status explícito)

As decisões abaixo **não mais variarão na primeira implementação** do ranking (alterações posteriores exigem re-análise P1/P2):

### Parâmetros (com status)
| Parâmetro | Valor | Status |
|---|---|---|
| Granularidade de quartos | 1 \| 2 \| 3 \| 4+ (0 excluído) | Sustentado por dados |
| Piso n_ai | ≥ 5 | Sustentado por dados |
| Piso n_vi | ≥ 5 (`n_vi_com_sale_price`) | Sustentado por dados |
| Suficiência de precisão | half IC95(R) ≤ 0,60 (por célula) | Critério operacional |
| Cobertura price% | sem gate; rebaixador de evidência | Critério operacional |
| n_datas mínimo (S2) | ≥ 20 | Critério operacional conservador |
| Δ_min | ln(1,25) = 0,223 (25%) | Hipótese metodológica provisória (sensibilidade 15/25/30%) |
| Fallback | bairro×tipo×quartos → bairro×tipo → bairro | Sustentado por dados |

### Regras que permanecem inalteradas
- Duas decisões separadas (S1 segmentos / S2 candidatos); S2 nunca = "imóvel a comprar".
- `R` = "intensidade de diária sobre capital de aquisição anunciado", com as 6 premissas; termos ROI/yield/cap rate/retorno/rentabilidade/payback/receita proibidos.
- Bootstrap por cluster (anúncio), amostras independentes; comparação por Δ com **IC95 excluindo 0 + P(Δ>0)≥0,975 + Δ_min + FDR (BH q≤0,05)**; "ICs que não se sobrepõem" proibido.
- Elegibilidade (piso 5/5 + half≤0,60) + fallback hierárquico + "inconclusivo" com motivo codificado.
- `min_nights=0` descartado; rating=0 → "sem avaliação"; lançamentos/frente-mar excluídos das medianas; outliers só com registro.
- Atratividade ≠ evidência ≠ elegibilidade; evidência fraca → inconclusivo, nunca "peso menor".

*P1 e P2 concluídos sem gerar ranking, shortlist ou pesos. Pronto para a etapa de implementação, que deverá incluir as análises de sensibilidade (piso ±, half 0,35–0,60, Δ_min 15/25/30%, n_datas 10–30) e verificação de consistência hierárquica do fallback.*