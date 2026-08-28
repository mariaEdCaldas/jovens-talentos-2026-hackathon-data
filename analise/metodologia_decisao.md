# Metodologia de Decisão — Fase 3 (revisada) — Segmentos prioritários + Candidatos operacionais

**Projeto:** Hackathon Seazone — Itapema (SC)
**Objetivo:** definir metodologia com as correções estruturais da revisão técnica: (1) inferência estatística correta da razão diária/preço; (2) separação entre "informação sobre o anúncio" e "representatividade de mercado"; (3) reforço da definição da Saída 2; (4) decisões pendentes fechadas de forma defensável.
**Não produzido nesta fase:** ranking final, código, pesos, ou uso de referência interna da Seazone para calibrar.
**Linguagem:** os termos "ROI / yield / cap rate / retorno / rentabilidade / payback / receita esperada" **não** descrevem indicadores; surgem apenas como rótulos de um **cenário teórico de sensibilidade** (ocupação plena) explicitamente sem valor econômico-real.

---

## 1. Definição revisada do problema

A Seazone precisa de *screening* de oportunidades potenciais de operação de curta temporada em Itapema. Os dados observam apenas:
- **diária anunciada** por noite (Price) — preço de oferta, não transação;
- **preço de venda anunciado**, **condomínio/IPTU anunciado**, **área anunciada** (VivaReal) — referências de mercado de aquisição, não negociação;
- características do anúncio/host (Details/Hosts) e localização (Mesh).

Não observado: ocupação, reservas, receita realizada, custos operacionais completos, correspondência individual Airbnb↔VivaReal.

**Problema resolvível:** produzir um conjunto ordenado de **candidaturas potenciais** — segmentos cuja relação diária-anunciada/capital-de-aquisição-anunciado é mais intensa (Decisão A), e anúncios dentro deles com sinais operacionais compatíveis (Decisão B). Saída = candidaturas com evidências, não aposta de lucro.

---

## 2. As duas decisões (definitivas)

### Decisão A — Segmento de mercado
> "Quais segmentos (bairro×tipo×quartos) apresentam características economicamente mais promissoras para operação de curta temporada, dada a relação entre **diária anunciada observada** (Airbnb) e **capital de aquisição anunciado** (VivaReal agregado)?"

**Unidade:** bairro×tipo×quartos, com fallback (bairro×tipo → bairro).
**Natureza:** econômica/agregada. O preço do VivaReal é **referência agregada de mercado** para imóveis semelhantes; **não é** o preço de nenhum anúncio Airbnb individual.

### Decisão B — Candidato operacional (Saída 2)
> "Dentro dos segmentos prioritários, quais **anúncios Airbnb** apresentam características operacionais compatíveis com eventual estratégia de captação/operação pela Seazone?"

**Unidade:** anúncio individual (`airbnb_listing_id`).
**Natureza:** exclusivamente operacional.

**Regras de não-conversão (obrigatórias):**
- A S2 **não é** um ranking de oportunidade de investimento individual; **não** afirma que o anúncio será "o imóvel comprado"; **não** conhece preço de aquisição individual.
- Sinais de boa operação atual — `is_superhost`, `is_guest_favorite`, `star_rating`, `is_professional`, `can_instant_book`, `reviews` — indicam **maturidade/qualidade operacional**, **NÃO upside, oportunidade de aquisição, potencial de investimento nem demanda**.
- Um anúncio com excelente operação atual pode representar **maturidade** (e baixa disponibilidade para captação), não oportunidade.
- Decisão A decide **onde**; Decisão B **quais anúncios são operacionalmente interessantes** nesses segmentos — sem score de investimento.

---

## 3. Arquitetura final

```
DADOS → TRATAMENTO → SEGMENTAÇÃO → ELEGIBILIDADE → INDICADORES →
INCERTEZA (procedimento estatístico correto, §4/§8) → COMPARAÇÃO (dominância com efeito mínimo, §11-12) →
SHORTLIST (S1 segmentos; S2 candidatos) → EVIDÊNCIAS
```

Tratamento (não altera originais): dedup VivaReal; marcar 6 órfãos; `min_nights=0` descartado; lat/lon do Mesh; rating=0→"sem avaliação"; suburb canônico; outliers por tipo marcados; Price unificado por dia-calendário (06/07/20) → grid imóvel×noite; `has_price` = flag de cobertura (não sinal).

---

## 4. Indicadores de segmento (revisados)

### 4.1 Estimadores
Para cada célula C elegível:
- **Diária do anúncio** `d_a` = mediana dos preços das noites do anúncio *a* (união das capturas). 
- **Diária da célula** `D_C` = mediana de `d_a` sobre os anúncios (*igual peso por anúncio*). ← correção: evita que anúncio com 90 noites domine a célula; e separa "informação sobre o anúncio" (cobertura) de "nível de mercado".
- **Preço de venda da célula** `V_C` = mediana de `sale_price` na célula (VivaReal, dedup), com exclusão sinalizada de lançamentos/frente-mar (§"lançamentos").
- **Razão (indicador comparativo)** `R_C = D_C / V_C` — "**intensidade de diária sobre capital de aquisição anunciado**" (nome neutro; ver §4.2).

### 4.2 Premissas explícitas do indicador R (obrigatórias em qualquer saída)
1. diária = **preço anunciado por noite** (não receita);
2. preço de venda = **preço anunciado no VivaReal** (referência agregada);
3. **não existe ocupação observada**;
4. **não existe receita observada**;
5. **não inclui custos operacionais completos** (`cleaning_fee` = precificação do anúncio; condomínio/IPTU = custos recorrentes anunciados do mercado de venda, com missingness sinalizada);
6. **não existe correspondência individual** Airbnb↔VivaReal.

`R` é **exclusivamente comparativo** entre células. **Termos proibidos** para descrevê-lo: ROI, yield, cap rate, retorno, rentabilidade, payback, receita esperada.

### 4.3 Procedimento estatístico para a incerteza e comparação da razão (CORREÇÃO 1)

**Por que não vale "IC das duas medianas sem sobreposição":** as duas medianas vêm de **amostras independentes sem correspondência individual**; "ICs que não se sobrepõem" é um **teste indireto** (falho: subestima/interpreta mal a significância) e não quantifica a incerteza da *razão* em si.

**Procedimento adotado — bootstrap por cluster de duas amostras independentes, com inferência sobre a razão e diferença de razões:**

1. **Unidade de reamostragem:** o **anúncio** (cluster), não a linha (noite). 
   - Lado Airbnb: reamostrar com reposição os `n_ai` anúncios da célula; para cada anúncio sorteado, tomar sua `d_a` (mediana das noites). Recalcular `D*` (mediana das `d_a*`).
   - Lado VivaReal: reamostrar com reposição os `n_vi_com_sale_price` anúncios (com `sale_price` válido); recalcular `V*` (mediana).
   - As duas reamostragens são **independentes** (respeitando a estrutura de amostras separadas).
2. **Razão por iteração:** `R* = D* / V*`. Repetir B=2000 (padrão; revisar se n for muito baixo). 
3. **IC da razão:** percentis 2,5% e 97,5% de `R*`. Em células com n pequeno, trabalhar na escala log (`log R*`) e re-exponenciar, para estabilidade.
4. **Comparação de pares de células (i,j):** distribuição bootstrap de `Δ = log R_i − log R_j` (diferença das razões, duas amostras independentes). IC95 de Δ = [q2,5%, q97,5%].
5. **Critério de dominância informacional** (substitui a sobreposição de IC): declarar `C_i ` mais intensa que `C_j` **somente se TODOS**:
   - IC95(Δ) **exclui 0**;
   - proporção bootstrap `P(Δ>0) ≥ 0,975` (ou `≤0,025` no sentido inverso);
   - **efeito mínimo de materialidade** `|mediana de Δ| ≥ Δ_min` pré-declarado (ver §16/§17): diferença de razão considerada suficiente para distinguir segmentos (decisão de negócio de materialidade). Hipótese provisória: `Δ_min = log(1,25) ≈ 0,223` (diferença relativa de 25%); sensibilidade obrigatória em 15/25/30%.
   - Correção **Benjamini–Hochberg (FDR)** sobre o conjunto de pares comparados; dominância só em pares com `q ≤ 0,05`.
6. **Células não dominantes entre si:** ficam na **mesma faixa de ordenação** (empate informado) — nunca ranking numérico estrito.

**Premissas do procedimento:** (i) amostras independentes entre Airbnb e VivaReal; (ii) independência **entre anúncios** dentro de cada universo (não independente dentro do anúncio — tratada pela clusterização); (iii) os anúncios observados são a unidade repetível (seleção é ameaça, não resolvida aqui); (iv) n_clusters suficientes (ver elegibilidade); (v) log-razão aproximadamente simétrica p/ IC.

**O que o procedimento permite afirmar (e não afirma):**
- Permite: "a intensidade diária/capital observada na célula i é consistentemente maior que na célula j, com erro de múltiplas comparações controlado e considerando o efeito mínimo pré-declarado — **no período observado (jan–abr/2025)**."
- Não permite: estimar qualquer fluxo de caixa, probabilidade de retorno, ou valor individual de imóvel. É um ordenamento de **potencial comparativo**, não uma previsão.

**Limitações:** seleção da cobertura Price (a inferência vale para o universo dos anúncios observados com preço); células pequenas (elegibilidade trata); viés por anúncio dentro custodiado; janela temporal curta; preços são anunciados.

---

## 5. Indicadores de candidato (Saída 2) — reforçado

Papéis (inalterados em relação à Fase 3, reforçado o §2):
- **Operacionais/descritivos (NUNCA de upside):** `reviews`/`reviews_ano`, `star_rating(>0)`, `is_guest_favorite`, `is_superhost`, `is_professional`, `can_instant_book`, `picture_count`, `cleaning_fee` (precificação do anúncio).
- **Caracterização de candidato:** `tipo`, `n_quartos`, `n_guests`, `n_beds`, `diaria_mediana` (nível), maturidade (`first_seen`, `is_new_listing`).
- **Apenas confiança:** `n_datas`, `n_capturas`, flags de qualidade.
- **Descartadas:** `min_nights` (0), `response_rate/time` (100% nulos), `rental_price` (2 não-nulos).

**CORREÇÃO 2 — n_datas/n_capturas:**
- `n_datas`/`n_capturas` = **informação sobre o anúncio** (quanto do calendário daquele anúncio foi observado → confiança da `d_a`). Mais observações → melhor estimativa daquela diária.
- **NÃO** significam maior representatividade *de mercado*: a cobertura de Price permanece **seletiva** (para ativos/profissionais). Em nenhum lugar `n_datas`/`n_capturas` entra como "representatividade de mercado". A cobertura da célula (`has_price%`) é métrica separada e sinalizada por seu viés.
- A **diária de célula** usa igual-peso por anúncio (§4.1), de modo que mais noites de um anúncio não inflam a célula.

**S2 (definitiva):** "anúncios Airbnb operacionalmente interessantes **dentro dos segmentos prioritários**". Não é ranking de investimento individual; não converte operação boa em upside.

---

## 6. Regras de elegibilidade (fechamento §16 → §16bis fechadas)

Distingue **Elegibilidade ≠ Atratividade ≠ Evidência** (reforçado).

**Definições fechadas:**
- **Granularidade de quartos:** `1 | 2 | 3 | 4+` (colapsa 4+ por baixa frequência de quartos grandes e para preservar n de células; ver justificativa em "Decisões fechadas").
- **Fallback:** bairro×tipo×quartos → (se falhar) bairro×tipo → bairro. Regra de fallback: uma célula falha quando não atinge elegibilidade em volume/cobertura/précisão no nível mais fino.

**Minimos de observação (critério estatístico, não número mágico):**
- **Definição de contagem (aplicada a todo este documento):** `n_ai` = anúncios Airbnb com preço na célula; **`n_vi_total`** = anúncios VivaReal estruturalmente elegíveis na célula (após dedup e exclusão de lançamentos), independente de ter `sale_price` válido; **`n_vi_com_sale_price`** = anúncios com `sale_price` válido (não-nulo e >0), **efetivamente usados na estimativa**. Nos dados atuais ambos coincidem (sale_price sem nulos), mas a distinção é mantida por definição.
- **Piso absoluto de clusters** (inegociável): `n_ai ≥ 5` anúncios com preço e **`n_vi_com_sale_price ≥ 5`** (justificativa: bootstrap por cluster com <5 clusters é instável — o IC raramente se estabiliza; também protege contra dominância de 1–2 anúncios). `n_vi_total` é reportado como contexto de cobertura do lado de venda.
- **Regra de suficiência de precisão:** célula é elegível se a **meia-largura relativa** do IC95 da razão for **≤ 60%** do valor de R (i.e., IC de R não exceder ±60%; justificativa: acima disso, célula não separa nada; patamar calibrado na análise pré-implementação P1; sujeito a sensibilidade). Como o piso de clusters já protege basalmente, o limite de ±60% entra como *segunda barreira de precisão*.
- **Cobertura mínima:** definida como **rebaixador de evidência, não elegibilidade dura** — células com `has_price%` abaixo do percentil de referência da cobertura observada (P25 das células) são marcadas "evidência fraca → inconclusivo" **se, e somente se, também** tiverem baixo volume. Nunca usada para favorecer o "resultado do topo".

**Células pequenas:** sem pooling arbitrário — aplica-se fallback hierárquico; se ainda falhar → **inconclusivo** (não entra no ranking).

**Lançamentos / frente-mar (VivaReal):** detectar por heurística textual declarada (título contendo "lançamento", "pré-venda", "frente mar", "lanç…") e **excluir da mediana** da célula, reportando quantos foram excluídos. Células cuja exclusão mude materialmente a mediana (>limiar de relevância) → flag/limitação textual. Lançamentos não entram como "capital de aquisição" porque seu preço é de pré-venda.

**Definição de "inconclusivo":** célula que **falha** elegibilidade em qualquer eixo (piso de clusters, precisão, cobertura+volume) OU cujo IC95 da razão seja demasiado largo (§limite acima). Célula inconclusiva sai do ranking e reporta **motivo** codificado (volume / precisão / cobertura). Candidatos em células inconclusivas podem ser listados como *contexto* descritivo, mas a S1 não os ordena.

**Comparação entre segmentos:** procedimento §4.3 (Δ das razões, FDR, efeito mínimo).

---

## 7. Métricas de evidência / confiança

Grelha por célula: `n_ai`, `n_vi_total`, `n_vi_com_sale_price`, `n_owners`, `cobertura_price%`, `missing_cond/iptu%`, `%outliers_suspeitos`, `n_lancamentos_excluidos`, dispersão (CV das `d_a`), e classificação final: **robusta / moderada / fraca→inconclusiva / não-elegível**. Evidência fraca nunca vira "peso menor"; vira "inconclusivo".

---

## 8. Tratamento da incerteza (revisado)

- Medianas + bootstrap por cluster (anúncio) conforme §4.3.
- Comparações só por Δ (log-razão) com FDR e efeito mínimo.
- Células não separáveis → **faixas/empate informado**, nunca ranking estrito.
- Toda saída indica o **nível de evidência** e o **período observado (jan–abr/2025)**.
- Para cada resultado, análise de sensibilidade (limiares ±20%, janela de noites, winsorização leve, com/sem lançamentos) reportada — §14.

---

## 9–10. Dados ausentes e outliers

- Nada imputado quando não observado. `cleaning_fee` = precificação do anúncio; `condomínio/IPTU` = custos recorrentes anunciados do mercado de venda, reportados com missingness; nunca viram custo individual do Airbnb. `rating=0` = categoria "sem avaliação". `suburb none`/bairros só-de-um-lado → fora da segmentação (reportados).
- Outliers: classificar por tipo (área <20/>500, condomínio≈preço, terreno área 0, R$/m² extremo) → marcar **suspeito/provável erro**; medianas são robustas; winsorização leve só como análise de sensibilidade; células com excesso de suspeitos → rebaixar evidência. Nunca excluir sem registro.

---

## 11. Comparação das metodologias (resumo — ver Fase 3)

**Preferência consolidada (sem pesos arbitrários):** elegibilidade (regras) + medição com incerteza + **dominância/ordenação pareada** (§4.3). Score ponderado (E) e multiobjetivo (D) apenas como sensibilidade. Regras/percentis (A/B) apenas como camada de apresentação, nunca regra de decisão isolada.

---

## 12. Metodologia recomendada (cascata, sem pesos)

**E1 Elegibilidade** (regras §6) → **E2 Indicadores + incerteza** (§4) → **E3 Comparação** (Δ com FDR + efeito mínimo) → **E4 Shortlist** (S1 células/faixas prioritárias; S2 anúncios dos segmentos prioritários) → **E5 Evidências** (features, n, cobertura, IC, flags, limitações textuais por linha).

### Saída 1 — Segmentos prioritários
Células/faixas de maior intensidade comparativa, cada uma com: n(ai), n(vi_total), n(vi_com_sale_price), owners, cobertura, `d` (p25/p50/p75 por anúncio), `V` (p50), condomínio/IPTU medianos (com missing), R + IC95, Δ dos pares dominados (com FDR), flags de outliers/lançamentos, nível de evidência, limitação textual.

### Saída 2 — Candidatos operacionais
Anúncios em células prioritárias que passam função operacional: `has_price=1`; `n_datas ≥ 20` (critério operacional conservador de mínimo de calendário observado — apoiado por exploração de estabilidade, **não** comprovação estatística); `is_new_listing=0`; não-órfão; capacidade/tipo coerentes com o segmento. Colunas **somente descritivas** de operação (tração, rating>0, favorito/superhost/profissional/instant, cleaning_fee, maturidade). **Nenhum** custo/aquisição individual; **nenhuma** classificação de "melhor investimento".

---

## 13. Justificativa da metodologia

1. Inferência estatística correta da razão (bootstrap por cluster, duas amostras independentes, Δ+FDR+efeito mínimo) — evita o viés do "ICs não sobrepostos".
2. Igual-peso por anúncio e clusterização separam confiança do anúncio × nível de mercado.
3. Elegibilidade preserva da flutuação; inconclusivo explícito.
4. S2 operacional, sem conversão em oportunidade de compra.
5. Sem pesos; sensibilidade sistemática.

---

## 14. Estratégia de validação (contra gabaritos internos)

Internalidade: sensibilidade de limiares, robustez a outliers, sanidade de células, consistência com os fatos auditados (seleção de Price, janela, junção agregada). Cenário teórico de ocupação (100% e 50%) só como seção de sensibilidade (§4.2 item 6) com rótulo explícito — nunca como ganho esperado. **Não usar referência interna da Seazone para calibrar.**

---

## 15. Limitações explícitas

(como Fase 3 — janela jan–abr/2025; sem ocupação/receita/custos; junção agregada; seleção de Price; rating/min_nights/response nulos; bairros sem contraparte; preços anunciados; missing cond/iptu 30–33%.)

---

## 16: DECISÕES FECHADAS — "METODOLOGIA CONGELADA — PRONTA PARA IMPLEMENTAÇÃO"

As decisões abaixo **não serão mais alteradas durante esta primeira implementação**. Foram definidas por propriedades dos dados, precisão estatística ou regra de negócio explícita — não olhando para resultado de ranking.

### Congeladas (não podem mudar na implementação)
1. **Duas decisões separadas:** A=segmentos (bairro×tipo×quartos), B=candidatos operacionais (anúncios). S2 **exclusivamente** operacional; nenhuma conversão a "imóvel a comprar"; nenhum custo individual atribuído ao anúncio.
2. **Indicador comparativo de segmento:** `R = D_C / V_C` com nome "**intensidade de diária sobre capital de aquisição anunciado**"; premissas obrigatórias (diária anunciada; preço de venda anunciado VivaReal; sem ocupação/receita; sem custos completos; sem correspondência individual). Termos ROI/yield/cap rate/retorno/rentabilidade/payback/receita proibidos para descrevê-lo. `diária×365/preço` só como cenário teórico de ocupação plena rotulado, fora dos indicadores.
3. **Estimador de célula:** `D_C` = mediana das diárias medianas por anúncio (**igual peso por anúncio**); `V_C` = mediana dos `sale_price` (dedup, excluindo lançamentos/frente-mar detectados por heurística textual declarada e registrados).
4. **Inferência da razão:** bootstrap **por cluster (anúncio)**, duas amostras independentes; IC da razão por percentis (escala log p/ n pequeno); comparação por `Δ=logR_i−logR_j` com **IC95 excluindo 0 + P(Δ>0)≥0,975 + efeito mínimo Δ_min** (diferença mínima pré-declarada p/ relevância econômica, revisada em P1 com justificativa de negócio) + **FDR (Benjamini–Hochberg, q≤0,05)**. **Proibido:** "IC sem sobreposição = significativo".
5. **Granularidade de quartos:** `1 | 2 | 3 | 4+` (justificativa: distribuição concentra-se em 1–3; 4+ agregado para preservar n de células; verificação empírica da distribuição é permitida, não o ajuste ao ranking).
6. **Elegibilidade:** piso `n_ai≥5` e `n_vi_com_sale_price≥5` (estabilidade do cluster-bootstrap — regra de precisão; `n_vi_total` reportado como contexto); + regra de suficiência: meia-largura relativa do IC95(R) ≤ 60% (calibrar em P1, sem olhar ranking); cobertura como rebaixador de evidência (evidência fraca → **inconclusivo**). Fallback hierárquico fixo.
7. **Inconclusivo:** falha em qualquer eixo de elegibilidade OU IC largo; reporta motivo codificado; não ordena.
8. **Lançamentos/frente-mar:** excluídos da mediana de venda (registro do excluído); não servem de capital de aquisição.
9. **Outliers:** classificação por tipo; medianas robustas; nunca excluir sem registro; winsorização leve só em sensibilidade.
10. **Missing:** nada imputado; cleaning_fee = precificação; cond/iptu = recurso de mercado com missing; rating 0 = categoria.
11. **n_datas/n_capturas:** confiança da diária daquele anúncio; **nunca** representatividade de mercado. Cobertura price é métrica separada de viés.
12. **S2 critérios:** excludentes = `has_price=1`, `n_datas≥ mínimo` (definido em P1 por quanto de janela torna a mediana estável), `is_new_listing=0`, não-órfão, célula prioritária; descritivos = tração/rating/favorito/superhost/profissional/instant/cleaning_fee/maturidade. Sem pesos operacionais.
13. **Sem peso arbitrário:** metodologia por elegibilidade+Δ+FDR+efeito mínimo; score/multiobjetivo apenas sensibilidade.
14. **Validação:** sensibilidade de limiares, robustez a outliers, sanidade, consistência com fatos auditados; cenário teórico de ocupação rotulado; **sem usar referência interna da Seazone**.

### Análises P1/P2 executadas (2026-08-28 — ver `p1_p2_relatorio.md`)
- **P1 — Perfil de células e precisão:** executado; definiu piso 5/5, gate half ≤ 0,60 (por célula), cobertura como rebaixador, n_datas≥20 como critério operacional, e validou granularidade 1|2|3|4+ (0 excluído).
- **P2 — Efeito mínimo:** executado; **sem referência interna da Seazone não há valor objetivo**; `Δ_min = log(1,25)` (25%) adotado como **hipótese metodológica provisória** de materialidade (não descoberta empírica), com sensibilidade obrigatória 15/25/30%.

### Decisões que permanecem em aberto APÓS a congelada (a resolver na implementação, não na metodologia)
- Se as células de faixas (empates) serão apresentadas em ordem lexicográfica interna de apresentação (não estatística).
- Mecanismo de apresentação da sensibilidade (Δ_min, half, n_datas) junto ao ranking.

---

## 17: METODOLOGIA FINAL CONGELADA — parâmetros definidos via P1/P2 (prontos para implementação)

As análises P1 (perfil de células e precisão) e P2 (efeito mínimo Δ_min) foram executadas
(`analise/p1_p2_relatorio.md`, scripts `p1_perfil_celulas.py`, `p2_delta_min.py`). Nenhuma
delas gerou ranking: apenas calibrou parâmetros por propriedades dos dados.

### Parâmetros congelados (não mudar na implementação sem nova P1/P2)

| Parâmetro | Valor final | Status | Base empírica (P1/P2) |
|---|---|---|---|
| Granularidade de quartos | 1 \| 2 \| 3 \| 4+ | Sustentado por dados | Frequências com preço: 144/351/404/92; 0 quartos → excluído ("sem informação") |
| Piso n_ai | ≥ 5 | Sustentado por dados | n_ai 1–4 → half IC95 até 1,5 (inviável); n≥5 habilita 16/14/10 células |
| Piso n_vi | ≥ 5 (`n_vi_com_sale_price`) | Sustentado por dados | Lado não limitante (61 células finas satisfazem) |
| Suficiência de precisão | half IC95(R) ≤ 0,60 | Critério operacional | 86% das células com dados (mediana half 0,22); gate medido por célula, **não** n fixo universal |
| Cobertura price% | sem gate; rebaixador de evidência | Critério operacional | 96 células: mediana ~15%; cobertura baixa → "inconclusivo" se + baixo volume |
| n_datas mínimo (S2) | ≥ 20 | Critério operacional conservador | Exploração de estabilidade da mediana (i.i.d.); NÃO comprovação estatística |
| Δ_min (efeito mínimo) | ln(1,25) = **0,223** (25%) | Hipótese metodológica provisória | P2: descreve distribuição; valor é decisão de materialidade; sensibilidade obrigatória 15/25/30% |
| Pacote de comparação | Δ=logRi−logRj; IC95 exclui 0; P(Δ>0)≥0,975; FDR BH q≤0,05 | Metodologia §4.3 | — |

### Alterações registradas (justificadas por P1/P2)
1. **n_datas mínimo da S2 = 20** — status: **critério operacional conservador** (apoio exploratório de estabilidade; não comprovação estatística).
2. **Δ_min = 0,223 (25%) como hipótese metodológica provisória** — sem referência interna da Seazone; valor é decisão de materialidade, **não** descoberta empírica; sensibilidade obrigatória 15/25/30%.
3. **0 quartos excluído** da segmentação (antes categoria "0") — 56 anúncios (8 com preço) sem dormitório declarado.
4. **Definição explícita de n_vi:** critério de elegibilidade e estimativa usam `n_vi_com_sale_price`; `n_vi_total` reportado como contexto (nos dados atuais coincidem).
5. **Requisito de reporte em toda saída:** n_ai, n_vi_total, n_vi_com_sale_price, cobertura price%, half ou "inconclusivo".

### Regras que permanecem inalteradas (revisão confirma)
- Duas decisões separadas (S1 segmentos / S2 candidatos); S2 nunca = "imóvel a comprar".
- `R` = "intensidade de diária sobre capital de aquisição anunciado", com as 6 premissas; termos ROI/yield/cap rate/retorno/rentabilidade/payback/receita proibidos.
- Bootstrap por cluster (anúncio), amostras independentes; "ICs que não se sobrepõem" proibido.
- Elegibilidade (piso 5/5 + half≤0,60) + fallback hierárquico + "inconclusivo" com motivo codificado.
- `min_nights=0` descartado; rating=0 → "sem avaliação"; lançamentos/frente-mar excluídos das medianas; outliers só com registro.
- distintos: atratividade ≠ evidência ≠ elegibilidade; evidência fraca → inconclusivo, nunca "peso menor".

**Pronto para a etapa de implementação (ranking S1/S2), que deverá incluir as análises de sensibilidade
(piso ±, half 0,35–0,60, Δ_min 15/25/30%, n_datas 10–30) e verificação de consistência hierárquica do fallback.**

*Nenhum ranking foi gerado até aqui.*