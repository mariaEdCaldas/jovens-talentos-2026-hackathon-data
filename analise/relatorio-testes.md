# Relatório de testes empíricos — validação de hipóteses

**Etapa 2 — antes de qualquer recomendação de investimento.** Este relatório registra os testes
executados, os comandos, os *fatos* observados, as *hipóteses* e as *inferências* — sem construir
modelo de ML, sem escolher score de investimento e **sem** modificar os datasets originais.

Todos os scripts são reprodutíveis: `python -X utf8 analise\scripts\<script>.py` (rodar na raiz
do repositório). Saídas em `analise/output/*.txt`. Pré-requisito: `python -m pip install pandas numpy scipy`.

Scripts:
- `analise/scripts/prep.py` — carga somente-leitura + flag `has_price` + normalização de bairro.
- `analise/scripts/t1_q1.py` → `output/t1_q1_presenca_preco.txt`
- `analise/scripts/t2_q2_q3.py` → `output/t2_q2_q3_granularidade.txt`
- `analise/scripts/t3_q4_q5.py` → `output/t3_q4_q5_reviews_ocupacao.txt`
- `analise/scripts/t4_integracao_qualidade.py` → `output/t4_integracao_qualidade.txt`

> Nota de escopo: em concordância com a orientação, **não** há modelo de ML nem score de
> investimento; apenas estatística descritiva e testes de associação (qui-quadrado, Mann-Whitney,
> Kendall tau) usados para *validar/refutar* hipóteses.

---

## Teste T1 — Por que apenas 1.005 (999) dos 4.441 listings têm preço?

**Fatos medidos**
- Price tem **1.005** listings; **999** deles também existem em Details (6 órfãos, ver T4). Cobertura
  = 999/4.441 = **22,5%** — a amostra com preço é um **subconjunto selecionado**, não aleatório.
- O grupo *com* preço difere sistematicamente do grupo *sem* preço:
  - Reviews: **97,9%** dos com-preço têm ≥1 review vs **55,9%** sem-preço (qui² p≈0).
  - Reviews em geral: mediana **16** (com preço) vs **1** (sem preço) (Mann-Whitney p≈0).
  - `is_professional`: 18,9% vs 6,5%. `is_guest_favorite`: **60,5% vs 7,8%**. Superhost: 43,4% vs 13,3%.
  - `listing_type`: quase todos os hotels (42/43) sem preço.
  - Bairro: cobertura varia (Centro 31%, Meia Praia 22%, Morretes 19%, Alto São Bento 8%).
  - Imóveis mais antigos no rastreio (mesh_first_seen) têm mais chance de ter preço (Mann-Whitney p≈0).

**Hipótese validada:** o preço não existe ao acaso — ele está **fortemente associado a anúncios
ativos/estabelecidos** (com histórico de reviews, favoritos, profissionais, em bairros como Centro).

**Inferência metodológica (não é conclusão de investimento):** analisar só os 999 com preço
enviesa qualquer conclusão para o subconjunto "maduro/ativo" do mercado short-stay. Resultados
de "melhor performance" devem ser lidos como *performance entre anúncios com preço*, não do
mercado inteiro.

---

## Teste T2 — O que é `aquisition_date`? Verdadeira granularidade das capturas

**Fatos medidos**
- Existem **3 dias-calendário** de captura no Price: `2025-01-06` (37.825 linhas), `2025-01-07`
  (38.991), `2025-01-20` (42.023). Os 4.172 timestamps únicos são o instante (data±hora) da
  raspagem de cada listing em cada rodada.
- Por listing: **62,5%** foram capturados nos **3 dias**; 33% em 1 dia; 5% em 2 dias. Média de ~5
  capturas por listing (mín 1, máx 19) — alguns têm >1 captura no mesmo dia.
- Granularidade real do Price = **listing × data de estadia × rodada de captura** (chave única,
  zero duplicatas nesse nível).

**Interpretação:** `aquisition_date` = timestamp de uma rodada de captura do calendário de preços;
não é a data de criação/estação do anúncio. Representar linhas de Price como observações
i.i.d. seria incorreto.

---

## Teste T3 — Como representar múltiplas observações de preço?

**Fatos medidos**
- Sobre os 59.040 pares (listing, data de estadia): em **47,7%** dos pares com ≥2 capturas o preço
  **mudou** entre a 1ª (06/01) e a última (20/01) captura; mas a mediana da variação relativa é ~0
  (75% das variações ≤ +6,25%).
- Comparando representações para o mesmo par: **25%** dos pares têm `última ≠ primeira`; **21,9%**
  têm `última ≠ mediana`. A diferença média |última − mediana| é ~**R$ 20/noite**.
- No nível do imóvel (agregando noites): a diferença média entre usar "última" vs "mediana" é
  ~R$ 14/imóvel; só **9,1%** dos imóveis divergem em >R$ 50 na diária média.

**Inferência defensável:** para análise futura, representar cada (listing, data) por **uma** diária
canônica (sugestão: a última captura ou a mediana entre capturas) é robusto — as capturas múltiplas
adicionam ruído modesto. **Não** usar as linhas brutas como unidades independentes.

---

## Teste T4 — Reviews como proxy de demanda?

**Fatos medidos**
- Reviews é um **contador acumulado (stock)**. **34,7%** dos 4.441 anúncios têm **0 reviews**.
- Reviews **aumentam com a idade** do host (Kendall τ=0,24, p≈0): mediana sobe de ~1 (host 1º ano)
  para ~4–17 conforme os anos. Logo, reviews estão **confundidos com tempo** (acúmulo), não são
  demanda corrente.
- Na amostra com preço, reviews correlacionam **negativamente** com a diária (τ=−0,12, p<0,001):
  diárias maiores têm *menos* reviews (endogeneidade clássica: preço alto → menos reservas → menos
  reviews). Reviews **NÃO** é proxy direta de "demanda atual".
- Estruturalmente, reviews < reservas (nem todo hóspede avalia) — subestima o uso.

**Conclusão da hipótese:** reviews são um proxy **fraco e enviesado** de demanda/ocupação; podem
servir como proxy de *atividade/acúmulo histórico* (e maturidade do anúncio), **nunca** de ocupação
corrente — e sempre com as ressalvas acima.

---

## Teste T5 — É possível inferir ocupação/receita, ou só potencial de mercado?

**Fatos medidos**
- **Nenhum** campo registra reservas realizadas, noites ocupadas ou ocupação (Price só tem
  `date` e `aquisition_date`; Details tem reviews/ratings = histórico, não ocupação).
- Cobertura do calendário por imóvel é incompleta: só **0,1%** dos imóveis cobre as 105 datas da
  janela; **34,6%** cobrem <50 datas. **Data sem preço é ambígua** (não disponível, calendário não
  preenchido, ou falha de captura) — **não** pode ser tratada como "dia ocupado".
- `VivaReal.rental_price` é **100% nulo** (8327/8329) — não há benchmark de aluguel tradicional.

**Inferência:** receita realizada = diária × noites ocupadas; as noites ocupadas **não existem** nos
dados. Qualquer número de receita exigiria assumir uma taxa de ocupação — uma hipótese não validável
com estes dados. Portanto a análise fica ancorada no **potencial de mercado** (diária anunciada por
perfil/localização e preço de aquisição), e apenas como potencial, não como retorno realizado.

---

## Teste T6 — Validação dos problemas de integração/qualidade

**Fatos medidos**
- **VivaReal:** 36 `listing_id` duplicados (72 linhas). **35 são duplicatas exatas** (mesmo anúncio
  aparece 2× no arquivo — arte, manter 1); **1** (2655470871) diverge entre linhas (provável mesmo
  imóvel em 2 anúncios).
- **Hosts:** `owner_id` aparece em várias linhas: 3.057 owners distintos / 4.440 linhas; **509 owners**
  têm >1 linha (fan-out). Deduplicar antes de agregar por host.
- **Integração Airbnb↔VivaReal por bairro:** após normalizar nomes, restam 12 bairros com
  correspondência. **3 bairros só no Airbnb** (Areal, Lameiro, Leopoldo Zarling; só 29 linhas) e
  **5 só na VivaReal** (Andorinha 782, Castelo Branco 510, etc.) → **16,8% das linhas de venda** não
  têm oferta Airbnb no mesmo bairro para acoplar (e vice-versa). A junção é **parcial** e por
  agregação de bairro (sem chave direta).
- **Price:** 6 listings órfãos (0,43% das linhas) sem Details/Mesh → não agregáveis.
- **Details:** `latitude`/`longitude` = **0 em todos** os 4.441 (usar Mesh); `min_nights` = 0 em todos
  (inválido).
- **Mesh:** 231 coordenadas são compartilhadas por 2+ listings (máx 25 na mesma coord) → várias
  unidades no mesmo prédio; permite análise intra-prédio mas gera cuidado com "mesma localização".

---

## Síntese (o que os testes decidem, sem recomendar investimento)

| Questão da revisão | Verdicto empírico |
|---|---|
| Por que só 1.005 têm preço? | Subconjunto **selecionado** (ativos/maduros/profissionais/qualificados); não aleatório. |
| O que é `aquisition_date`? | Timestamp de **rodada de captura**; 3 rodadas (06, 07, 20/01/2025); granularidade listing×data×captura. |
| Como representar preço? | 1 diária canônica por (listing, data) — última captura ou mediana; não usar linhas cruas. |
| Reviews = proxy de demanda? | Só **proxy de atividade histórica/acúmulo**, confundida com tempo; **não** é demanda/ocupação corrente. |
| Inferir ocupação/receita? | **Não** sem assumir ocupação; restringe-se a **potencial de mercado** (diária × aquisição). |
| Integração/qualidade | VivaReal tem 35 dups exatos (+1 divergente); hosts com fan-out; junção por bairro **parcial** (16,8% da venda sem par); 6 órfãos; coords zeradas no Details; min_nights inválido. |

Estes fatos definem **restrições** de metodologia para a próxima etapa — não recomendação de investimento.
