# Auditoria do Trabalho — Validação Empírica (revisão rigorosa)

**Projeto:** Hackathon Seazone — Itapema (SC)
**Objeto:** auditoria dos 11 testes empíricos executados
**Data:** 2026-08-28
**Escopo:** somente diagnóstico. Sem recomendação final, sem score, sem pesos, sem alteração dos datasets originais.
**Arquivos:** scripts em `analise/scripts/`; saídas em `analise/saida/`.

> Regras desta auditoria:
> - Um teste só é válido se o script executou até o fim **sem erro** (exit code 0) e a conclusão usa **apenas** a saída dessa execução.
> - Corrigir qualquer erro de implementação e **re-executar** antes de usar o resultado.
> - Diferenciar **observado** (medido) / **interpretação** (leitura defensável) / **hipótese** (suposição) / **limitação** (barreira estrutural).
> - Evitar causalidade onde há apenas associação.

---

## 1. Status de auditoria de cada teste

| Teste | Script | Exit atual | Erros encontrados nesta auditoria | Status |
|---|---|---|---|---|
| 1 — Granularidade temporal | `teste1_granularidade_price.py` | **0** | (antigo) bug `[ad.dt.date]` quebrava o script; os resultados da 1ª etapa vieram de execução **inline avulsa**, não do script. Na reescrita, encontrei 2 novos bugs corrigidos: (a) contador `n_grupos_multi` contava *listings* em vez de *grupos* (769 vs 1303) → frações inválidas; (b) métrica E media gap *entre linhas* (dominada por 0) em vez de *entre timestamps*. Ambos corrigidos e re-executado (exit 0). | ✅ válido (re-executado) |
| 2 — Viés has_price | `teste2_hasprice_bias.py` | **0** | 2 erros de formatação na função `out()` (3–4 args) na 1ª etapa; corrigidos. Re-executado. **Ressalva:** `pd.crosstab` exclui NaN → os p-valores chi² de `can_instant_book`, `is_professional`, `is_new_listing` foram calculados sobre o subconjunto sem NaN; o restante sobre 4.441. | ✅ válido |
| 3 — Estabilidade do preço | `teste3_preco_estabilidade.py` | **0** | Na 1ª etapa os **rótulos dos intervalos estavam trocados** (`d==13` rotulado como "06_para_19?", `d==14` como "07->20 (14 dias)"; o correto é 07→20=13d e 06→20=14d). Não alterou os números, mas tornava a leitura enganosa; **corrigido**. Removeu o `nan%` de "mesmo_dia". Re-executado. | ✅ válido (rótulos corrigidos) |
| 4 — Ausência em Price | `teste4_ausencia_price.py` | **0** | 1 erro de formatação em `out()` na 1ª etapa (corrigido). Re-executado. | ✅ válido |
| 5 — Reviews/tração | `teste5_reviews_tracao.py` | **0** | 1 erro na 1ª etapa: merge de hosts faltava `years_host`/`months_host` (KeyError). Corrigido, re-executado. | ✅ válido |
| 6/7 — Rating 0 / Hosts | `teste6_7_rating_hosts.py` | **0** | 3 erros de formatação em `out()` corrigidos. Re-executado. | ✅ válido |
| 8 — Bairros | `teste8_bairros.py` | **0** | 1 erro de formatação corrigido. Re-executado. | ✅ válido |
| 9 — Outliers VivaReal | `teste9_outliers.py` | **0** | 2 erros de formatação corrigidos. Re-executado. | ✅ válido |
| 10 — Match Airbnb↔Viva | `teste10_match.py` | **0** | 1 erro funcional (`crosstab` sem coluna), corrigido; e rótulo "frente mar" tratado como categoria própria. Re-executado. | ✅ válido |
| 11 — Capacidade analítica | `teste11_capacidade.py` | **0** | 3 erros de formatação corrigidos. Re-executado. | ✅ válido |

**Conclusão da auditoria:** todos os scripts executam até o fim (exit 0) e **todas** as saídas usadas nas conclusões foram regeneradas nesta auditoria. Nenhuma conclusão desta resposta se apoia em execução falha. Foram descartados os resultados do Teste 1 obtidos anteriormente por execução inline.

---

## 2. Investigação profunda do Teste 1 (múltiplos timestamps e janelas disjuntas)

### 2.1 O que foi medido (observado)

- **3 dias-calendário** de coleta (06/01, 07/01, 20/01/2025) e **4.172 timestamps** com hora (1.364 / 1.364 / 1.444 por dia). Janela horária ~13:22–15:0x (≈1,6–1,8 h/dia).
- **Listings por timestamp:** média 1,20; p25/p50/p75 = 1; máx 6 → a maioria dos timestamps pertence a **um único imóvel**.
- **Pares (listing,date) por timestamp:** média ~28,5; p50 15; p25 4; p75 49; máx 229.
- **Tamanho da janela de datas por captura (imóvel×timestamp):** Q10 1, Q50 18, Q75 57, Q90 77 dias; 607 capturas cobrem exatamente 1 dia; 426 cobrem 2.
- **Particionamento (1.303 grupos imóvel×dia com ≥2 timestamps; 2.691 pares de janelas consecutivas):**
  - janelas **contíguas** (fim_i + 1 = início_j): 88,7%;
  - janelas com **gap**: 11,3%;
  - janelas com **overlap**: 0,0% (0 de 2.691);
  - **1303/1303** grupos sem NENHUMA violação de ordenação (as janelas sempre crescem com o timestamp);
  - união das janelas forma bloco contíguo em 1017/1303 (~78%).
- **Espaçamento entre timestamps distintos consecutivos do mesmo imóvel+dia:** mediana 17,8 min; p25 10,5; p75 24,2; 67,7% entre 5 e 25 min.
- **`date` vs captura:** **100%** das linhas têm `date ≥ dia da captura` (nenhuma `date` anterior ao dia da coleta).
- **Sazonalidade por mês de estadia:** jan mediana 800 → fev 700 → mar 574 → abr 480 (tarifa cai com o afastamento da alta temporada).

### 2.2 Interpretação (o que esses números sustentam)

- Um mesmo **imóvel** coleta o calendário em **fatias** (páginas) cobrindo dezenas de noites cada; cada página recebe um **timestamp próprio**. Vários timestamps no mesmo dia-calendário = **particionamento do calendário do imóvel naquela sessão de coleta**, não "duas coletas independentes completas" nem "snapshots completos do mercado".
- **`aquisition_date` = momento da coleta** daquela fatia (evidência: janela de datas é sempre futura em relação ao timestamp; espaçamento ~18 min entre páginas consecutivas é compatível com requisições sequenciais).
- **`date` = data da noite de estadia** (evidência: 100% das `date` ≥ dia da captura; preço varia por mês de estadia — padrão de calendário, não de transação).
- A **ausência de sobreposição dentro do mesmo dia** é **consequência direta do particionamento**, e NÃO indica que diferentes timestamps são "coletas independentes".

### 2.3 Hipóteses (não demonstradas, sem evidência no dataset)

- Que as páginas sejam provenientes de paginação da interface/API do Airbnb (plausível; os dados não documentam o crawler).
- Que a ausência de uma noite específica em um dia represente "indisponível" (não há coluna de disponibilidade; a ausência pode ser só "não incluída na fatia").

### 2.4 Limitações estruturais

- Não há documentação nos arquivos sobre o processo de coleta.
- Não há coluna de disponibilidade/calendário → **ausência ≠ indisponibilidade** (ver §3, item 2).
- O **conceito de "captura completa de mercado" só existe no nível dia-calendário** (06/07/20 = união das fatias), não no nível timestamp.

---

## 3. Achados × "isso muda alguma decisão na solução?"

Para cada achado, respondo se afeta alguma decisão futura (o passo da recomendação) e qual.

**A1. Preço por noite tem até 3 observações (06/07/20), 56% idênticas; variação direcional modesta (mediana −6,25% entre quem muda).**
- **Muda a decisão? SIM.** Decisão: qual valor de preço usar por (imóvel, noite) e por imóvel — mediana das capturas vs "última (20/01)". Afeta robustez do indicador de diária por perfil/localização. Dado o resultado (modesta variação), decisão defensável: **mediana das capturas disponíveis**, reportar sensibilidade.
- **Confiança:** alta (medido em 59.040 pares).

**A2. Ausência de preço = não coletado/bloqueado, indistinguível.**
- **Muda a decisão? SIM.** Decisão: **não é possível derivar ocupação nem disponibilidade** de Price; portanto nenhum cálculo de receita/ROI pode usar datas ausentes como "não ocupado". Qualquer cenário financeiro precisa de hipótese explícita de ocupação.
- **Confiança:** alta (estrutural).

**A3. Cobertura de Price é auto-selecionada (anúncios ativos/profissionais).**
- **Muda a decisão? SIM.** Decisão: toda conclusão sobre "melhor perfil/loc" deve ser qualificada como "entre anúncios ativos/profissionais com preço"; qualquer comparação com os 3.442 sem preço exige controle dessas variáveis. Afeta diretamente o teste da tese "compactos no Centro".
- **Confiança:** alta (múltiplas dimensões, p<0,001).

**A4. Reviews = tração acumulada, não demanda atual; fortemente correlacionada com ter preço.**
- **Muda a decisão? SIM.** Decisão: reviews não entram como proxy de demanda/receita; podem entrar como **covariável de atividade** em análise descritiva. Afeta a definição de "melhor desempenho".
- **Confiança:** alta (associação medida; causalidade não demonstrada).

**A5. `star_rating`=0 ≡ sem avaliação.**
- **Muda a decisão? SIM (preventivo).** Decisão: tratar como categoria "sem avaliação", nunca como nota 0. Evita viés na comparação de perfis.
- **Confiança:** alta (1.540/1.540 casos; 0 contradições).

**A6. Hosts é dimensão de proprietário (deduplicável).**
- **Muda a decisão? SIM (pré-ready).** Decisão: detectar multi-listings de um mesmo owner na recomendação (ex.: exposição concentrada), sem fan-out.
- **Confiança:** alta.

**A7. Bairros: 13 comuns, casos textuais × semânticos; Airbnb e VivaReal unem-se apenas por agregação (até bairro+tipo+quartos).**
- **Muda a decisão? SIM.** Decisão: o relacionamento Airbnb↔VivaReal só é possível em nível **bairro×tipo(×quartos)**; nenhuma união de imóvel individual. O indicador de custo (VivaReal) e potencial de preço (Airbnb) só se cruzam agregados — comunicar como agregado, não como yield de imóvel específico.
- **Confiança:** alta (estrutural).

**A8. Outliers de VivaReal exigem segmentação por tipo antes de decidir.**
- **Muda a decisão? SIM.** Decisão: limpeza/filtro do custo de aquisição por tipo (ex.: terrenos fora da análise de apartamentos; suspeitos: área 66.585 m² em apartamento, condomínio = preço). Sem remoção cega.
- **Confiança:** alta para "existir casos suspeitos"; média para rotular cada caso.

**A9. Janela temporal só jan–abr/2025 (alta temporada parcial); capturas em janeiro.**
- **Muda a decisão? SIM.** Decisão: qualquer "diária média anual" exige hipótese de sazonalidade; indicar recorte. Afeta comparação entre bairros e perfis (o nível de preço captura verão, não o ano).
- **Confiança:** alta (estrutural).

**A10. Velocidade de oscilação: amplitude >25% em 3,8% dos pares; 39,2% dos imóveis mudam ≥50% das noites.**
- **Muda a decisão? PARCIAL.** Decisão: não é necessário modelar micro-dinâmica de preço para a recomendação; mas a escolha mediana-vs-última deve ser documentada. Secundário para o investidor-escopo.
- **Confiança:** alta.

**A11. 6 listings com preço sem Details/Mesh; 36 duplicados VivaReal; `min_nights`=0.**
- **Muda a decisão? SIM (pipeline).** Decisão: pipeline de limpeza deve (a) excluir/registrar os 6 órfãos, (b) deduplicar VivaReal por `listing_id`, (c) ignorar/remarcar `min_nights`. Não afeta a direção da recomendação, mas afeta a corretude da implementação.
- **Confiança:** alta.

**A12. Sazonalidade interna do calendário (+ docs implícitas: date=futura, price=por noite).**
- **Muda a decisão? SIM na normalização.** Decisão: normalizar o preço por janela de datas (mês de estadia) para comparar imóveis de forma justa.
- **Confiança:** alta.

**Achados secundários (não mudam decisão):** distribuição de quartos/banheiros/tipos; concentração de owners; duração da coleta (~1,7h/dia); quantidade exata de timestamps por dia (relevante apenas para validação de processo, não para o modelo).

---

## 4. Tabela final — Questão | Evidência | Confiança | Impacto na solução

| Questão | Evidência encontrada | Confiança | Impacto na solução |
|---|---|---|---|
| Por que só 1.005 de 4.441 têm Price? | Seleção não-aleatória: guest favorite 69,1% vs 11,1%; superhost 48,7% vs 15,9%; profissional 48,6%; instant-book 36,3%; novo 2,1%; reviews mediana 16 vs 1; star≥4,5 35,8% vs 6,7% (chi² p<0,001 em bairro, tipo, reviews, rating, favorito, superhost, prof, instant, novo). | **Alta** | Toda conclusão sobre perfil/locação vale **entre anúncios ativos/profissionais**. A tese "compactos no Centro" precisa controlar isso. Não tratar 1.005 como amostra representativa de 4.441. |
| O que é `aquisition_date`? | Timestamp com hora; 4.172 em 3 dias (1.364/1.364/1.444); cada timestamp tem ~1,2 imóveis e ~28,5 pares; janela por captura Q50 18 dias; espaçamento entre páginas ~18 min. | **Alta** (interpretação) | `aquisition_date` = momento da coleta da **fatia de calendário** de um imóvel. Não é "snapshot completo de mercado" nem "preço atual". Decisão: usar nível dia-calendário (06/07/20) como unidade de coleta. |
| O que é `date`? | 100% das `date` ≥ dia da captura; preço decresce por mês de estadia (jan 800 → abr 480). | **Alta** (interpretação) | `date` = noite de estadia. Permite (e exige) normalizar por mês de estadia ao comparar imóveis. |
| Por que múltiplos timestamps no mesmo dia não se sobrepõem? | 2.691 pares de janelas consecutivas: 88,7% contíguas, 11,3% com gap, **0% overlap**; ordenação preservada em 1303/1303. | **Alta** | É **particionamento (paginação)**, não coletas independentes. Sem impacto no modelo; valida que o dia-calendário é a unidade de coleta correta. |
| Como representar múltiplas observações de preço? | 56% dos pares constantes; qm mudaram, mediana −6,25%; amplitude >25% em 3,8%. | **Alta** | Decisão: **mediana das capturas por (imóvel,noite)** como valor-base (robusto), reportando sensibilidade; documentar que não é "preço atual". |
| Reviews são demanda? | Correlação com idade 0,22, tenure 0,25, rating 0,28; reviews/ano: com price 18,99 vs 0,95. | **Alta** (associação) | NÃO usar reviews como receita/ocupação. Usar como **covariável de atividade** em análise descritiva. |
| `star_rating=0` é nota real? | 1.540 casos: rating 0 ⟺ 0 reviews (0 contradições; sub-ratings idênticos). | **Alta** | Tratar como "sem avaliação". Previne viés de comparação. |
| Hosts pode ser dimensão de proprietário? | Atributos constantes por owner (3.057/3.057); 1 variação trivial (41.261↔41.299). | **Alta** | Deduplicar por owner; considerar multi-listings na recomendação. |
| Airbnb ↔ VivaReal, como unir? | Zero IDs em comum; 13 bairros comuns (81,2%); 60 combinações bairro+tipo+quartos nos 2 universos; sem área (m²) no Airbnb; sem lating no VivaReal. | **Alta** | União **somente agregada** (bairro×tipo×quartos). Custo e potencial de preço cruzam-se em nível agregado; comunicar como tal, nunca como yield de imóvel individual. |
| Ausência em Price = indisponível? | Sem coluna de disponibilidade; cobertura mediana 62/105; fatias disjuntas explicam "buracos". | **Alta** | **Não inferir ocupação**. Qualquer cenário de receita exige hipótese explícita de ocupação. |
| Dá para estimar ocupação/receita/ROI? | Nenhuma coluna de reserva/receita/RevPAR; rental_price 2 não-nulos; min_nights=[0]; janela jan–abr/25. | **Alta** (limitação) | Só **potencial de preço e potencial agregado** são sustentáveis. ROI real não é calculável com os dados. |
| Outliers de VivaReal são erro? | Suspeitos evidenciados: apto 66.585 m², condomínio=preço (3M/3M), terreno área 0; plausíveis: terreno 188.000 m², apto 44M frente-mar. | **Média/Alta** | Segmentar por listing_type antes de qualquer filtro; sem remoção cega. |
| Janela temporal afeta comparação? | Apenas jan–abr/2025; capturas em janeiro. | **Alta** | Normalizar/qualificar por período; qualquer projeção anual é hipótese. |

**Convertendo a resposta à pergunta central no item 2 do Teste 1:** sim, os dados do próprio dataset sustentam que `aquisition_date` = momento da coleta (date sempre futura; espaçamento de requisições ~18 min) e `date` = data de estadia (sazonalidade de calendário). Não há documentação formal; a interpretação é robusta, porém não é prova.

---

## 5. Fatos observados × interpretações × hipóteses × limitações (declarações explícitas)

- **Fatos observados (medidos diretamente):** todos os números nas tabelas de §1–§3 (n de timestamps, contiguidade, % mudanças, medianas, p-valores, ausência de colunas, 100% date≥captura).
- **Interpretações (leitura defensável a partir dos fatos):** `aquisition_date`=momento da coleta de fatia; `date`=noite de estadia; ausência de preço ⇒ não estimável; hosts=owner; junção Airbnb↔Viva agredada; mediana como representação robusta de preço.
- **Hipóteses (suposições plausíveis ainda não demonstradas):** paginação via interface/API do Airbnb; que a variação −6,25% reflita mudança de tarifa de alta temporada; que a sazonalidade jan–abr generalize o ano; que a ausência num dataset signifique ausência real de mercado; que os outliers "suspeitos" sejam de fato erros.
- **Limitações (barreiras estruturais dos dados):** sem ocupação/receita/ROI; sem m² no Airbnb; sem lating na VivaReal; `min_nights`=0; sem documentação do crawler; janela jan–abr; capturas só em janeiro; seleção auto-selecionada de Price.

---

## 6. Decisões que TODO o material de agora confirma (e que a próxima etapa precisará tomar, ainda sem setar pesos)

1. Unidade da análise: **anúncio** (4.441). Preço agregado por **mediana das capturas** por (imóvel, noite) e recorte janela de datas documentado.
2. Relacionamento Airbnb↔VivaReal **agregado** (bairro×tipo×quartos).
3. `has_price` como **bandeira de cobertura**, não amostra aleatória.
4. `star_rating=0` → "sem avaliação".
5. Limpeza mínima: deduplicar VivaReal; marcar/os excluir os 6 órfãos e `min_nights=0`; segmentar outliers por tipo.
6. Entregar **potencial de preço agregado** (não receita) e, se desejado, cenário financeiro **sob hipóteses explícitas de ocupação/custos** com faixas.

*Nenhum score, nenhum peso, nenhuma recomendação de investimento foi produzida nesta etapa.*