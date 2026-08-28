# Relatório — Testes Empíricos de Validação

> **⚠️ AVISO DE AUDITORIA (2026-08-28):** este relatório foi submetido a uma auditoria rigorosa (ver `analise/relatorio_auditoria.md`).
> Os números do **Teste 1** foram recalculados por um script corrigido (os anteriores vieram de execução inline). Rótulos do **Teste 3** foram corrigidos (07→20 = 13 dias; 06→20 = 14 dias). Todos os scripts agora rodam com exit code 0. Nenhuma conclusão abaixo se baseia em execução com erro.

**Projeto:** Hackathon Seazone — Itapema (SC)
**Etapa:** Validação empírica das hipóteses da análise exploratória
**Data:** 2026-08-28
**Escopo:** Somente diagnóstico. Nenhuma recomendação de investimento, nenhum modelo, nenhum score. Sem alteração dos datasets originais.
**Reprodutibilidade:** scripts em `analise/scripts/teste1..11_*.py`; saídas em `analise/saida/`.

> Convenção de linguagem ao longo do texto:
> **Fato observado** = número medido nos dados. **Hipótese** = suposição não demonstrada. **Inferência** = leitura baseada em fatos + premissas explícitas.

---

## 1. Resumo executivo

A base tem 4.441 anúncios Airbnb (Details/Mesh), **1.005 dos quais com preço** (Price), e 8.293 anúncios de venda (VivaReal). Esta rodada executou **11 testes** e produziu evidências que **mudam o que podemos afirmar**:

1. **SELECÇÃO NÃO-ALEATÓRIA DE Price (Confirmada).** Os 1.005 anúncios com preço NÃO são uma amostra aleatória dos 4.441. São sistematicamente os anúncios **mais ativos/estabelecidos**: com reviews (mediana 16 vs 1), superhosts (48,7% vs 15,9% de cobertura), guest favorites (69,1% vs 11,1%), profissionais (48,6%), instant-book (36,3%), mais fotos (mediana 21 vs 8) e **quase nunca anúncios novos** (2,1%). A diferença é estatisticamente significativa (p<0,001) e inequívoca.
2. **GRANULARIDADE REAL DE Price (Revista).** `aquisition_date` é um **timestamp completo com hora**, mas o conceito de “captura” é mais fino do que dia-calendário. Há **3 dias-calendário** (06, 07 e 20/01), mas **4.172 timestamps** (≈1.360–1.440/dia). Capturas **no mesmo dia cobrem janelas DISJUNTAS de datas** (overlap médio = 0 em 2.691 pares): cada timestamp é um *fatia do calendário* de estadia, não uma repetição completa. Cada lista tem **1–19 capturas** (mediana 5), em **1–3 dias** (mediana 3).
3. **VARIAÇÃO DE PREÇO É REAL E DIRECIONADA, MAS MODESTA NA MAIORIA.** De 59.040 pares (listing,date), 43,1% têm 1 captura, 12,5% têm 2 e 44,4% têm 3. Entre os que têm >1 captura: **56% não mudam**; dos que mudam, a mediana da variação é **−6,25%**, e **mais caem (31,9%) do que sobem (12,1%)** entre 06/07 → 20/01. Amplitudes >25% ocorrem em só 3,8% dos pares. → Preço NÃO é estático, mas a escolha da captura altera pouco a maioria das estimativas; a direção (queda entre janeiro) é sistemática e não deve ser atribuída a demanda.
4. **`aquisition_date` ≠ “atualidade”.** A captura mais recente é de **20/01/2025**; hoje seria ago/2026. O máximo defensável é **“último preço observado no dataset”**, jamais “preço atual”. E como as capturas do *mesmo* dia são fatias disjuntas, “última captura por (listing,date)” nem sempre existe: um dado par (listing,date) pode ter sido coletado uma única vez.
5. **ABSÊNCIA DE PREÇO = INDETERMINADO.** Não há coluna de calendário/disponibilidade. Ausência pode significar não-coletado, bloqueado ou faixa de calendário não capturada (as janelas disjuntas provam que a própria coleta gera “buracos”). **Os dados NÃO permitem inferir ocupação.**
6. **REVIEWS = TRAÇÃO HISTÓRICA, não demanda atual.** Correlacionam com idade (0,22), tenure do host (0,25), rating (0,28) e fotos (0,29). Normalizado por tempo, quem tem price tem mediana de **~19 reviews/ano vs 0,95** sem price. Uso como proxy de “demanda” exigiria qualificação; serve como indicador de **atividade/tração acumulada**.
7. **star_rating=0 = sem avaliação (evidência interna robusta).** Em 100% dos casos (1.540), rating=0 coincide com **zero reviews**; nenhum caso de rating=0 com reviews>0 e nenhum de rating>0 com reviews=0. Todos os 6 sub-ratings e o `guest_satisfaction_overall` seguem o mesmo padrão.
8. **Hosts é dimensão de PROPRIETÁRIO (deduplicável).** `is_superhost`, `is_verified`, `star_rating_host`, `years_host`, `months_host` são **constantes dentro do owner** (3.057/3.057). Só `number_of_reviews_host` varia para 1 único owner (variação trivial 41.261↔41.299). Deduplicar por `owner_id` é seguro.
9. **Relacionamento Airbnb↔VivaReal: só por bairro/agregação.** Não há chave direta. **13 bairros** são comuns (81,2% dos bairros Airbnb têm oferta VivaReal); 60 combinações **bairro+tipo+quartos** existem nos dois universos. Área é inviável (Airbnb sem m²) e georreferenciamento ponto-a-ponto é inviável (VivaReal sem lat/lon). **Qualquer “rendimento” é necessariamente agregado por bairro/tipo, não de imóvel específico.**
10. **CAPACIDADE ANALÍTICA: SÓ POTENCIAL DE MERCADO.** Não existe ocupação, reserva, receita, RevPAR nem custos. `rental_price` da VivaReal tem só 2 valores não-nulos. `min_nights` é todo zero. → **Não dá para estimar receita realizada nem ROI real.** Dá para estimar **potencial de preço (diária) e potencial agregado** por bairro×tipo, sob hipóteses explícitas (ocupação, custos) que precisam ser assumidas, nunca inventadas como se fossem dado.

---

## 2. Testes executados (método + resultados principais)

### Teste 1 — Granularidade temporal de Price
**Método:** parse de `aquisition_date`; contagem de dias-calendário, timestamps, capturas por listing, janelas de datas, overlap entre capturas.
**Resultados:**
- `aquisition_date` = datetime **com hora/min/seg** (ex.: `2025-01-07 13:25:06.000`), 0 unparseable.
- **3 dias-calendário**: 06/01 (37.825 linhas), 07/01 (38.991), 20/01 (42.023).
- **4.172 timestamps** (06: 1.364, 07: 1.364, 20: 1.444). Cada dia de coleta durou ~1,6–1,8 h (13:22→15:0x).
- Capturas (timestamps) por listing: **min 1, mediana 5, média 4,97, max 19**. Por dia-calendário: min 1, mediana 3, max 3.
- **769 listings** têm nº de timestamps ≠ nº de dias (capturas múltiplas no mesmo dia).
- Observações (datas de estadia) por captura: 1 a 91 (mediana 10).
- **Overlap entre capturas consecutivas do mesmo dia = 0 em 2.691/2.691 pares** → janelas disjuntas.
- Cobertura por dia: 06→753 listings, 07→773, 20→780; **628 listings** vistos nos 3 dias.
- Chave única real: **(airbnb_listing_id, date, aquisition_date)**.

**Leitura:** cada “captura” é uma fatia do calendário de um anúncio, não um reprint completo. Isso invalida a presunção de “3 snapshots completos”.

### Teste 2 — Viés de seleção (has_price)
**Método:** `has_price = listing ∈ Price?`; compara grupos em bairro, tipo, quartos, reviews, rating, favorito, superhost, profissional, instant-book, novos, photo, cleaning; chi² e Mann-Whitney.
**Resultados:** cobertura global 22,5% (999/4.441). Diferenças grandes e significativas (p<0,001 na maioria):
- `is_guest_favorite`: 69,1% vs 11,1% | `is_superhost`: 48,7% vs 15,9% | `is_professional`: 48,6% | instant-book: 36,3% vs 20,5% | `is_new_listing` True: **2,1%** | `is_verified` False: 0/29.
- `number_of_reviews` mediana 16 (com price) vs 1 (sem).
- `star_rating` mediana 4,93 vs 4,50 (≥4,5: 35,8% vs 6,7% p/ <4,5).
- `picture_count` mediana 21 vs 8; `cleaning_fee` 250 vs 230 (p<0,001).
- Bairro: Centro 31,2%, Canto da Praia 32,1%, Meia Praia 22,1%, Morretes 18,8%, Leopoldo Zarling 5,6%.
- Owners: média de cobertura ~constante por porte, mas **593 owners com todas as listas em Price vs 2.319 com nenhuma** (concentração).

**Conclusão:** **existe viés de seleção** na cobertura de Price (os selecionados são os anúncios ativos/estabelecidos). Não é só o “22,6%”: há correlações sistemáticas com tração e profissionalização.

### Teste 3 — Estabilidade/direção do preço
**Método:** por (listing,date): n capturas, min/max/mediana/amplitude relativa, variação prim→ult (abs, %, direção); segmentação por intervalo de dias.
**Resultados:**
- Distribuição de capturas: 1→25.452, 2→7.377, 3→26.211 (total 59.040 pares).
- Amplitude relativa (max−min)/mediana: **73,6% dos pares constantes**; 86,1% com variação <10%; só **3,8%** >25% e **0,5%** >50%.
- Variação prim→ult (n>1 capturas = 33.588 pares): **56,0% sem mudança, 31,9% caíram, 12,1% subiram**; mediana dos que mudaram **−6,25%** (P5 −31%, P95 +20%).
- Segmentação: no intervalo 07→20, de 26.328 pares, 9.015 caíram e 3.537 subiram (mediana −6,25%). No 06→07 também predomina queda leve.
- Por listing: 39,2% têm ≥50% das datas mudando; mediana da amplitude de mudança 4,3%.

**Leitura:** preço varia de forma **sistemática para baixo** entre as capturas de janeiro (provável efeito de janela/tarifa), mas **magnitude modesta na maioria**. Interpretar como “demanda” seria **não suportado** (Hipótese refutada enquanto “sinal de demanda”).

### Teste 4 — Ausência em Price / cobertura
**Método:** cobertura de datas por listing; gaps; características dos grupos por cobertura; sem coluna de disponibilidade.
**Resultados:**
- Cobertura de datas (union) por listing: mediana 62 de 105; faixas: 1–9 → 17, 10–29 → 129, 30–59 → 341, 60–89 → 458, 90–105 → 60.
- Min de calendário varia (21 listas cobrem a partir de 06/01, muitas de meados de janeiro); 474 listas vão até 20/04.
- Continuidade: só **244/1.005 contíguos**; 734 têm >5% de faltas internas.
- Grupo “cheio” (≥60d) têm mediana de reviews **menor** (14) que o “magro” (<30d, 20,5) — cobertura de datas não se resume a “quanto tempo no mercado”.
- Corr(cobertura de datas, n_capturas) = 0,31.
- **Nenhuma coluna distingue indisponibilidade de não-coleta.**

**Conclusão estrutural:** ausência ≠ indisponibilidade; não há como estimar ocupação. Limitação estrutural registrada.

### Teste 5 — Reviews como proxy de tração
**Método:** correl com idade (mesh first_seen), tenure, rating, fotos; reviews/ano; relação com has_price.
**Resultados:**
- Corr: reviews×idade 0,218; ×years_host 0,253; ×rating 0,279; ×fotos 0,292; reviews_ano×reviews 0,565.
- `is_new_listing` True → mediana 0 reviews (max 2).
- reviews/ano: **has_price=1 → mediana 18,99; has_price=0 → 0,95**.
- Bairro com maior mediana de reviews: Canto da Praia 10; Maioria ~2 (Meia Praia, Centro, Morretes).
- reviews 0–5: só 3,6% têm price, 23,9% são novos; reviews >50: 74,5% têm price, 0% novos.

**Leitura:** reviews = proxy de **tração acumulada/atividade**, fortemente correlacionado à presença em Price; **não** é demanda atual (Hipótese: parcialmente suportada como tração, refutada como “demanda direta”).

### Teste 6 — Semântica de star_rating=0
**Resultado:** star=0 & rev=0 → 1.540; star=0 & rev>0 → **0**; star>0 & rev=0 → **0**; star>0 & rev>0 → 2.901. Todos os sub-ratings e guest_satisfaction idênticos (0 iff 0 reviews). **Interpretação defensável: 0 = ausência de avaliação.** (Documentação externa ainda recomendada; mas a evidência interna é forte.)

### Teste 7 — Consistência de Hosts
**Resultado:** todas as colunas de atributo do host **constantes por owner** (3.057/3.057). Apenas `number_of_reviews_host` varia para 1 único owner (41.261–41.299). `host_snapshot_date` varia por listing (é data do crawl). **→ Hosts pode ser reduzido a 1 linha/owner sem fan-out.**

### Teste 8 — Normalização de bairros
**Resultado:** mapeamento proposto:
- **União textual pura** (mesmo bairro após acento/caixa): Alto São Bento, Centro/CENTRO, Meia Praia (4 grafias), Sertão do Trombudo, Sertãozinho.
- **União semântica (ambígua, decidir):** Tabuleiro/Taboleiro→Tabuleiro dos Oliveiras; Jardim Praiamar=Jardim Praia Mar.
- **NÃO unir (semanticamente diferente):** “Meia Praia - Frente Mar” (frente mar = característica locacional), “Ocean Tower”, “Itapema”, “Estreito” (cidade/empreendimento).
- “none” (airbnb) = ausência de bairro.
- Bairros só Airbnb: Areal, Lameiro, Leopoldo Zarling. Só VivaReal: Andorinha, Castelo Branco, Estreito, Itapema, Ocean Tower. **Ausência num dataset NÃO prova ausência de mercado** (coberturas/nomenclatura distintas).

### Teste 9 — Outliers VivaReal
**Resultados por tipo** (medianas): apartamento sale 1,84M / área 129 m² / R$/m² 14.414; casa 743k / 100 m² / 7.440; terreno 737k / 300 m² / 2.257; comercial 1,5M / 92 m² / 14.625.
- **Provável erro:** apartamentos com área 4.000–66.585 m² (1 quarto) — área claramente trocada/em unidade errada; **condomínio igual ao preço de venda** (ex.: apt 3,15M com cond 3,15M; apt 898k com cond 898k) — erro de preenchimento; terrenos com área 0 (11); R$/m² ~429.000–669.000 com área minúscula (inconsistente).
- **Suspeito:** R$/m² acima de IQR×3 (apt ~38.548; casa ~18.034; terreno ~5.702) — pode ser frente-mar/luxo; áreas 440–500 m² de apartamento (possível penthouse).
- **Plausível:** terreno 188.000 m² (Casa Branca, 2,4M); apartamento 966 m² frente-mar a R$ 44M (Lançamento); terrenos 11.500 m² (Tabuleiro, 14,5M); casas até 25M (Ilhota, alto padrão).
- **Importante:** listas duplicadas (36 IDs com linhas repetidas no fim do arquivo — artefato de construção; deduplicar antes).
- **Regra:** NÃO remover por estatística; segmentar por tipo antes de qualquer dedução de outliers.

### Teste 10 — Relacionamento Airbnb ↔ VivaReal
**Resultados:**
- **Estratégia A (bairro):** 13 bairros comuns; 81,2% dos bairros Airbnb têm oferta VivaReal; bairros sem contraparte listados.
- **Estratégia B (bairro+tipo):** tabelas comparáveis (ex.: Meia Praia apart 2.602 ai × 3.414 vi; casa 90 × 19).
- **Estratégia C (bairro+tipo+quartos):** **60 combinações** presentes nos dois universos (de 177). Ex.: Meia Praia/apto/3q → 1.451 ai × 1.704 vi; Meia Praia/apto/2q → 723×244; Centro/apto/3q → 211×438.
- **Estratégia D (área):** inviável — Airbnb sem m².
- **Estratégia E (geo):** inviável ponto-a-ponto — VivaReal sem lat/lon; só nível bairro.
- Perfil por bairro (mediana, apenas p/ quem tem price): Meia Praia 3q/2,31M; Centro 2q/2,6M; Morretes 2q/797k; Canto da Praia 2q/1,69M.

**Leitura:** relacionamento **somente por agregação** (bairro, bairro+tipo, bairro+tipo+quartos). **Não** transformar em match de imóvel individual.

### Teste 11 — Capacidade analítica
**Fatos:**
- Nenhuma coluna de reserva/ocupação/receita/RevPAR em Details/Price.
- `rental_price` VivaReal: **2 valores** não-nulos (99,98% nulo).
- `min_nights`: único valor **0** (inutilizável para política de estadia).
- Preço/noite por mês: jan mediana 800 / média 943; fev 700/796; mar 573/670; abr 480/570. Percentis gerais: P25 450, P50 607, P75 842.
- Período coberto: 06/01–20/04/2025 (≈3,5 meses).

**Respostas:**
- **Ocupação?** Não estimável (sem dados). 
- **Receita realizada?** Não estimável.
- **ROI real?** Não calculável.
- **Potencial econômico?** Parcialmente. Suportado: **preço/diária anunciado** (nível listing, agregável por bairro×tipo×quartos) e **preço de compra** (nível anúncio VivaReal, segmentado por tipo). Não suportado diretamente: ocupação, custos, receita.
- **Hipóteses necessárias para cenário financeiro (todas explícitas, NUNCA inventadas como dado):** (i) ocupação/taxa de reserva por perfil/bairro; (ii) nº de noites comercializáveis/ano (sazonalidade, 3,5 meses só); (iii) custos (limpeza, comissão/gestão Seazone, condomínio, IPTU, manutenção); (iv) correspondência bairro→imóvel (agregada, não individual); (v) projeção além de 01/2025–04/2025.

---

## 3. Resultados quantitativos (resumo numérico)

| Grandeza | Valor |
|---|---|
| Listings Airbnb (Details/Mesh) | 4.441 |
| Listings com preço (Price) | 1.005 (22,5% dos 4.441; 999 com join em Details) |
| Listings VivaReal | 8.293 (36 IDs duplicados) |
| Dias-calendário de captura (Price) | 3 (06, 07, 20/01/2025) |
| Timestamps de captura | 4.172 (≈1.360–1.444/dia) |
| Capturas por listing | mediana 5 (1–19) |
| Janela de estadia coberta | 06/01–20/04/2025 (105 datas) |
| Overlap entre capturas do mesmo dia | 0 / 2.691 pares |
| Preço/noite (mediana) | R$ 607 (P25 450, P75 842, max 29.000) |
| Pares (listing,date) com >1 captura | 33.588 (56,9%) |
| — sem mudança | 56,0% |
| — caíram | 31,9% | — subiram | 12,1% |
| — variação prim→ult mediana (mudou) | −6,25% |
| Amplitudes >25% (geral) | 3,8% |
| Cobertura de datas por listing | mediana 62/105 |
| Listing por bairro mais oneroso (has_price, mediana sale) | Centro 2,6M |
| Reviews mediana (com price vs sem) | 16 vs 1 |
| Reviews/ano mediana (com price vs sem) | 18,99 vs 0,95 |
| star=0 & rev=0 / star=0&rev>0 / star>0&rev=0 | 1.540 / 0 / 0 |
| Combinações bairro+tipo+quartos nos 2 universos | 60 |
| Rental_price não-nulos (VivaReal) | 2 |
| min_nights valores únicos | [0] |

---

## 4. Fatos confirmados

1. Granularidades distintas entre datasets (1/1/múltiplas/owner/venda).
2. Details↔Mesh: 4.441 IDs idênticos; coordenadas reais só em Mesh.
3. Price: 1.005 listings; múltiplas observações por imóvel (não 118.839 imóveis).
4. 6 listings de Price sem Details/Mesh (509 linhas).
5. VivaReal↔Airbnb: zero sobreposição de chave; sem chave direta.
6. Múltiplas capturas existem e o preço muda (31,9% caem) — dimensão temporal real.
7. star=0 = ausência de avaliação (evidência interna robusta).
8. Preço anunciado ≠ receita.
9. Cobertura de Price é **não-aleatória** (viés de seleção confirmado em múltiplas dimensões).
10. Hosts = dimensão de proprietário, deduplicável sem fan-out.
11. Ausência de preço ≠ indisponibilidade (indistinguível) → sem ocupação.
12. Relacionamento Airbnb↔VivaReal apenas agregado (bairro/tipo/quartos).

## 5. Hipóteses refutadas (empiricamente)

- **“1.005 é amostra aleatória/representativa” — REFUTADA.** Forte viés de seleção (Teste 2, 5).
- **“Mudança de preço entre capturas = sinal de demanda” — REFUTADA como causalidade.** Variação direcional (−6,25%) sem dados de reserva; não há suporte causal (Teste 3).
- **“Captura mais recente = preço atual do imóvel” — REFUTADA como fórmula geral.** Captura mais recente é janeiro/2025; e nem todo (listing,date) tem uma “última captura” comparável (fatias disjuntas). Máximo: “último preço observado” (Testes 1, 3).
- **“Reviews medem demanda” — REFUTADA como demanda direta.** São tração acumulada/atividade (Teste 5).
- **“star_rating=0 é nota baixa real” — REFUTADA** (0 ≡ sem reviews).
- **“guests > beds = erro” — NÃO confirmado como erro** (ver §7; revisão correta de considerar capacity legítima).

## 6. Hipóteses ainda não comprovadas (em aberto)

- Que a variação −6,25% entre capturas reflita tarifa de alta temporada vs normal (plausível, não demonstrável).
- Que o padrão jan–abr generalize para o ano inteiro (sazonalidade anual desconhecida).
- Que reviews/ano seja um preditor estável de performance futura (proxy, não demonstrado).
- Que bairros sem oferta no outro dataset não tenham oferta real (não verificável nos dados).
- Que os outliers “suspeitos” sejam de fato erro (ex.: R$/m² alto no fronte-mar pode ser legítimo).
- Qual a causa exata das 36 linhas duplicadas de VivaReal (provável artefato, não confirmado).

## 7. Problemas de qualidade dos dados (recém-evidenciados)

- **Viés de seleção estrutural em Price** (maior achado desta rodada).
- **`min_nights` todo 0** (inutilizável).
- **Details lat/lon = 0** (usar Mesh).
- **Capturas como fatias disjuntas** → cuidados com granulação ao agregar por “captura”.
- **Hosts com fan-out** (deduplicar por owner, seguro).
- **VivaReal duplicados (36 IDs)**, artefato de arquivo.
- **Outliers suspeitos** em VivaReal (área gigante em “apartamento”, condomínio = preço, terreno área 0).
- **Nomenclatura de bairro inconsistente** (Textual ∪ Semântica ∪ casos ambíguos).
- **Campos majoritariamente nulos:** `response_rate/time_shown` (100%), `rental_price/period` (99,98%), `space` (56,9%).
- **`star_rating`=0 como sentinela de “sem reviews”** (não é nota — tratar como categoria à parte).
- **Discrepâncias de capacidade** (guests > beds em ~96%) — ver revisão: pode ser capacidade configurada, não inconsistência comprovada.

## 8. Limitações econômicas (prioridade alta)

- Sem ocupação, reservas, receita ou RevPAR.
- Sem custos operacionais (limpeza, comissão Seazone, energia, manutenção).
- Sem preço de aluguel tradicional (rental_price ~vazio) → sem yield de locação direta.
- Sem m² no Airbnb → sem R$/m² comparável; sem valorização histórica.
- Janela de ~3,5 meses (jan–abr/25) e capturas só em janeiro → sazonalidade anual desconhecida.
- “Última captura” é de jan/2025, não atualidade.
- Airbnb↔VivaReal só agregado (sem candidato ponto-a-ponto) → yield individual não observável.
- Vieses de sobrevivência/tração (o que está em Price é o que “sobreviveu/é ativo”).

## 9. Implicações para a metodologia futura

1. **Unidade-mestre = anúncio** (4.441), com `has_price` como bandeira de cobertura (não como amostra representativa).
2. **Preço:** representar por listing como distribuição sobre as noites coletadas; escolher a agregação POR PERGUNTA (mediana/noite é mais robusta que “última captura”); registrar explicitamente que não é “preço atual”.
3. **Demanda:** usar reviews/tração como **covariável de atividade**, não como receita; indexar por tempo (reviews/ano).
4. **Segmentação:** análise de potencial deve ser **por bairro×tipo×quartos** (único nível de correspondência Airbnb–VivaReal com cobertura), não por imóvel.
5. **Outliers:** segmentar por listing_type antes de qualquer tratamento; marcar candidatos, não remover cegamente.
6. **Resultado honesto:** entregar **potencial de preço / potencial agregado** por segmento, e, se desejado, cenários financeiros **sob hipóteses explícitas e sensíveis** (ocupação, custos) — nunca apresentar como receita/ROI observado.
7. **Recorte temporal:** qualquer absoluto anual exige hipótese de sazonalidade; indicar incerteza.

## 10. Decisões que o analista precisa tomar (antes do modelo)

1. **Agregação de preço por listing:** mediana/noite vs média vs “último observado” — e qual janela usar.
2. **Tratamento de rating=0:** categoria separada “sem avaliação” (recomendado), não nota 0.
3. **Mapa de bairros:** aprovar união textual, decidir os casos semânticos ambíguos (Tabuleiro, Jardim Praia Mar) e como tratar “none”.
4. **Granularidade da correspondência Airbnb–VivaReal:** bairro, bairro+tipo, ou bairro+tipo+quartos — e como comunicar que é agregado.
5. **Hipóteses de ocupação/custos** a serem assumidas (e faixas de sensibilidade) caso se queira cenário financeiro — deixando claro que são premissas.
6. **Tratamento de outliers VivaReal:** regras de classificação e exclusão condicionadas a listing_type.
7. **Escopo temporal:** limitar a jan–abr/2025 com ressalva de sazonalidade, ou extrapolar sob premissa.
8. **Como comunicar a tese dos “compactos no Centro”** à luz do viés de seleção — a verificação dessa tese exigirá comparar *dentro* da amostra com preço, controlando as variáveis de seleção.

---

*Nenhuma recomendação de investimento foi feita. Todos os scripts estão em `analise/scripts/` e podem ser re-executados contra os datasets originais (somente leitura).*
