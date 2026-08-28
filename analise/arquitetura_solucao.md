# Arquitetura da Solução — Fase 2 (Decisão apoiada pelos dados)

> **ESTE DOCUMENTO FOI SUPERADO PELA FASE 3.** O fluxo "dados → tratamento → segmentação → elegibilidade → indicadores → incerteza → comparação → shortlist → evidências", a separação entre **Decisão A (segmento)** e **Decisão B (candidato operacional)**, o novo enquadramento do indicador diária/preço e a separação entre **atratividade / evidência / elegibilidade** estão definidos em `analise/metodologia_decisao.md`.
> Seções 7–9 desta fase 2 não devem ser implementadas tal como escritas.

**Projeto:** Hackathon Seazone — Itapema (SC)
**Objetivo desta fase:** desenhar a estrutura da solução de recomendação **antes** de qualquer score/peso, baseada unicamente no que os datasets permitem afirmar.
**Não** produzido nesta fase: score, pesos, ranking, ocupação, receita, ROI ou disponibilidade inventada.

---

## 1. Qual decisão esta solução consegue apoiar?

Com as evidências disponíveis (auditadas), a solução suporta **exatamente uma classe** de decisão:

> **"Dentre o estoque observado de anúncios ativos de curta temporada em Itapema (com presença no Price), quão atrativo é cada imóvel/perfil/localização como CANDIDATO à operação de curta temporada (captação/gestão pela Seazone), dado o seu potencial de geração de diária e o custo aproximado de aquisição no mercado de venda do mesmo bairro/tipo?"**

A solução **não** apoia (limitação estrutural, já demonstrada):
- Estimar retorno, ROI, receita realizada, ocupação ou RevPAR.
- Prever demanda futura.
- Comparar imóveis sem preço (Price) com imóveis com preço em pé de igualdade.
- Fazer matching individual Airbnb ↔ VivaReal.

Palavra-chave: **potencial**. A saída é um *screening* para originação/gestão — não uma promessa de lucro.

---

## 2. Sinais observáveis e classificação (fato/proxy/hipótese/não observável)

### 2.1 Potencial de geração de diária
- **Preço da noite (Price.price)** — **observado diretamente** (anunciado; não receita). Preço por noite, por data de estadia, por captura.
- **Preço mediano por noite por perfil/bairro** — **observado** (agregado).
- **Sazonalidade (diária por mês de estadia)** — **observado** (jan 800 → abr 480, mediana).
- **Capacidade de tarifa por hóspede** (price/guests) — **derivado (proxy)**, usado só descritivamente.
- **Receita/ocupação** — **não observável**.

### 2.2 Atratividade de geração de diária
- **Tração/atividade do anúncio**: `number_of_reviews`, `star_rating`, `is_guest_favorite`, `picture_count`, `number_of_reviews_host` — **proxy de atividade** (auditado: correlação com tração; NÃO demanda).
- **Reviews/ano** (normalizado por tempo, via `mesh.aquisition_date` = primeiro tracking e `years_host`) — **proxy** melhor calibrado.
- **`is_professional`, `is_superhost`, `can_instant_book`** — **fato observado** (status do anúncio/host), proxy de operação ativa.
- **Demanda** — **não observável** (hipótese estrutural).

### 2.3 Custo de aquisição
- **`VivaReal.sale_price`** — **observado** (anúncio, não negociação); agregado por bairro/tipo.
- **`monthly_condo_fee`, `yearly_iptu`** — **observado** (parcial: 30–33% nulos), custos recorrentes anunciados.
- **`usable_area`** — **observado** (com outliers a tratar); base de R$/m².
- **Preço/m²** (sale/area) — **derivada**, com ressalvas de outliers.

### 2.4 Características do imóvel
- **`listing_type`, `number_of_bedrooms/bathrooms/beds`, `number_of_guests`, `cleaning_fee`** — **observado**.
- **Amenidades** (`amenities`, `safety_features`) — **observado** (texto estruturado).
- **Área** — **observado** em VivaReal; **NÃO observável** em Airbnb (limitação).
- **Localização**: `suburb` (Mesh/VivaReal) **observado**; **lat/lon só no Airbnb** (Mesh), não em VivaReal.

### 2.5 Maturidade/atividade
- **`is_new_listing`** — **observado** (ativamente usado; 2,1% dos com preço).
- **`number_of_reviews`, `years_host`, `months_host`** — **observado**.
- **`first_seen` (mesh.aquisition_date)** — **observado** (primeiro tracking); permite idade aproximada.
- **Status "ativo/em Price" (`has_price`)** — **observado**; e é a principal fonte de viés de seleção.

### 2.6 Estabilidade / volatilidade do preço
- **Variação entre capturas (06/07/20)** — **observado** (56% constantes; mediana −6,25% qm mudam; amp>25% em 3,8%). Indicador calculável ao nível de imóvel: `frac_mudou`, `media_ampl_rel`. **Cuidado metodológico:** variação pequena/modiesta NÃO é "estabilidade de mercado"; é pequena janela em 3 dias. Não usar como prova de preço estável.
- **Volatilidade real (diária ao longo do ano)** — **não observável**.

### 2.7 Qualidade/confiança dos dados
- **Cobertura de Price por imóvel** (`n_datas`, `n_capturas`) — **observado**; proxy de completude da observação.
- **Nulidade** (`can_instant_book`, `is_professional`, `is_new_listing`, `cleaning_fee`, área, condomínio/IPTU) — **observado**; métrica de confiança por feature.
- **Consistência** (duplicados, min_nights=0, lat=0, rating 0, outliers) — **observado**; flags, não exclusão cega.
- **Fonte da observação** (captura/última vs mediana) — **metodológica**; documentar.

---

## 3. Redundância e correlação (não contar o mesmo fenômeno duas vezes)

Com base nas correlações medidas em Teste 5:
- **Tração única (reviews, rating, favorito, fotos, superhost, reviews_host)**: `number_of_reviews` (r≈0,28 c/ rating), `star_rating` (0,28), `picture_count` (0,29), `is_guest_favorite`, `is_superhost`, `years_host`, `number_of_reviews_host` (0,25 a 0,29). → **Consolidar em UMA família "atividade/tração"**; não contar reviews, favorito e fotos como 3 fenômenos independentes.
- **Capacidade (quartos/banheiros/camas/hóspedes)**: altamente correlacionados (quarto↔cama↔hóspedes). → Usar **um vetor de capacidade** (tipologia + 1 dimensão de escala).
- **Localização**: `suburb` + lat/lon juntos? Para decisão de investimento, **bairro é a unidade de segmentação** (a única que se conecta ao VivaReal). lat/lon ficam para enriquecimento geo (clusterização aninhada), não como variável independente no score por imóvel.
- **has_price está fortemente correlacionado com tração** (auditado) — não incluir tração e has_price como se fossem independentes: has_price é **flag de cobertura**, não sinal.
- **`min_nights`=0**, `response_rate`/`time` 100% nulos, `rental_price` — **descartados** (não informativos).

---

## 4. Viés de seleção e como mitigá-lo

A cobertura de Price é **auto-selecionada** (1.005/4.441; fortemente entre ativos/profissionais). Consequências e mitigação:
- Indicadores de "potencial de diária/tração" só valem **dentro do grupo com preço**; **nunca** extrapolar para os 3.442 sem preço como se pertencessem à mesma população.
- Qualquer comparação de perfis/localizações deve ser **condicionada à presença em Price** (estratificar/segmentar por `has_price`; ou restringir a análise ao subconjunto com preço).
- Imóveis **novos** (2,1% com preço) quase não têm representação → conclusões sobre "imóveis novos" são inviáveis no Price.
- Variações de **cobertura por bairro** (Centro 31%, Morretes 19%, Leopoldo 6%) → indicadores por bairro devem reportar **n e cobertura**, e não comparar bairros com N→1 imóvel.
- Imóveis sem preço ainda podem entrar como **contexto de estoque** (oferta), nunca com preço potencial imputado.

---

## 5. Combinação Airbnb × VivaReal (agregada e defensável)

Sem chave individual (zero overlap de IDs; sem m² na Airbnb; sem lat/lon na VivaReal), a única junção defensável é **em nível agregado**:

1. **Bairro normalizado** (canônico; casos textuais unidos; casos semânticos separados — `_frente_mar` à parte).
2. **Camadas progressivas de agregação**: `bairro` → `bairro×tipo` → `bairro×tipo×faixa_quartos`.
3. **Indicador cruzado**: `potencial_de_diária_mediana (bairro×tipo×quartos)` ÷ `preço_de_venda_mediano (bairro×tipo×quartos)` → **razão de potencial (não-ROI)**. Explicitar: é razão de duas distribuições; não atribuível a um imóvel específico; não inclui custos nem ocupação.
4. **Regras de robustez**: mínimos de observação (ex.: ≥N imóveis com preço e ≥N anúncios de venda por célula; célula sem mínimo → reportada como sem estimativa confiável); outliers por tipo segmentados antes de medianas.

**Limitação explícita:** padrões de frente-mar (novos lançamentos, `Lançamento`), terrenos, e bairros sem Airbnb ficam *fora* do cruzamento; listar como exceções.

---

## 6. Nível de cálculo dos indicadores

| Indicador | Nível |
|---|---|
| Diária mediana / noite (por imóvel), preço mediano por mês de estadia | **Imóvel** |
| Cobertura de datas, n capturas, frac_mudou (vol per capturas) | **Imóvel** |
| Tração: reviews, reviews/ano, rating>0, favorito, superhost, fotos | **Imóvel** (descritivo) |
| Potencial de diária mediana (bairro×tipo) | **Bairro** |
| Potencial de diária mediana (bairro×tipo×quartos) | **Bairro×tipo×quartos** |
| Custo: preço mediano de venda, R$/m², condomínio/IPTU mediano | **Bairro×tipo×quartos** (VivaReal) |
| Razão potencial/custo ("atração de entrada") | **Bairro×tipo×quartos** |
| Cobertura, n, observações por célula | **Bairro (e células)** |
| Cluster geo (lat/lon), distância ao mar/centro | **Imóvel** (enriquecimento) |

---

## 8. Tabela de features

| Feature | Dataset | Granularidade | O que mede | Tipo de evidência | Risco de viés | Uso na decisão |
|---|---|---|---|---|---|---|
| `price` (noite, captura) | Price | imóvel×noite×captura | Diária anunciada | Observado | — | Base do potencial de diária |
| `diaria_mediana` (imóvel) | Price | Imóvel | Nível de preço do anúncio | Observado | Sensível à janela jan–abr | Ranking de potencia de diária |
| `diaria_mediana` (bairro×tipo×q) | Price | Agregado | Nível de mercado do segmento | Observado (agregado) | Seleção da amostra Price | Segmento mais atrativo |
| `sazonalidade` (por mês) | Price | Imóvel/segmento | Diferença jan vs abr | Observado | Jan–abr só | Contexto, não score |
| `frac_mudou`, `ampl_rel_mediana` | Price | Imóvel | Variação entre capturas (3d) | Observado | NÃO é volatilidade anual | Documentação/robustez, não score |
| `n_datas`, `n_capturas` | Price | Imóvel | Completude da observação | Observado | Correlação com cobertura | Confiança da feature de preço |
| `number_of_reviews`, `reviews_ano` | Details+Mesh | Imóvel | Tração/atividade acumulada | Proxy | Seletiva (sobrevivência) | Atividade; NÃO receita |
| `star_rating` (>0) | Details | Imóvel | Satisfação (sem 0) | Proxy | =0 → sem avaliação | Qualidade percebida |
| `is_guest_favorite` | Details | Imóvel | Curadoria Airbnb | Proxy | Correlação c/ cobertura | Atividade |
| `is_superhost`, `is_professional`, `can_instant_book` | Details+Hosts | Imóvel | Operação ativa | Observado | Correlacionados c/ Price | Atividade; participação |
| `picture_count` | Details | Imóvel | Apresentação | Proxy | Correlacionado com tração | Descritivo |
| `cleaning_fee` | Details | Imóvel | Taxa de limpeza | Observado | — | Custo operacional parcial |
| `listing_type`, `n_bed/bath/beds`, `n_guests` | Details | Imóvel | Tipologia/capacidade | Observado | Capacidade ≠ qualidade | Segmentação perfil |
| `amenities` | Details | Imóvel | Comodidades | Observado (texto) | Não estruturado | Descritivo/features |
| `min_nights` | Details | Imóvel | (todos 0) | Não informativo | — | Descartado |
| `sale_price`, `R$/m2` | VivaReal | Anúncio | Custo de aquisição | Observado | Outliers por tipo | Custo de entrada |
| `monthly_condo_fee`, `yearly_iptu` | VivaReal | Anúncio | Custos recorrentes | Observado | 30–33% nulos; outliers | Custo recorrente |
| `usable_area` | VivaReal | Anúncio | Tamanho | Observado | Outliers; 0; ausente no Airbnb | R$/m²; apenas VivaReal |
| `suburb` (canônico) | Mesh+VivaReal | Imóvel/bairro | Localização de mercado | Observado | Naming; ausência ≠ ausência real | Unidimensional de segmentação |
| `lat/lon` | Mesh | Imóvel | Posição precisa | Observado | Só Airbnb | Enriquecimento geo |
| `has_price` | derivado | Imóvel | Cobertura de Price | Observado | **Não é sinal;** correlacionado c/ tração | Flag de grupo/restrição |
| `first_seen` | Mesh | Imóvel | Idade aproximada | Observado | = primeiro tracking, não criação | Idade para reviews/ano |
| `is_new_listing` | Details | Imóvel | Novo anúncio | Observado | 2,1% com preço | Excluir/alertar em rankings |
| `is_verified`, `owner_id` | Hosts/Details | Owner | Identidade e multi-listing | Observado | — | Exposição de carteira |
| `#duplicados_VivaReal`, `min_nights=0`, rating=0, lat=0 | — | Quality flag | Qualidade/consistência | Observado | — | Flags de confiança (pipeline) |

**Nota:** todas as features são **observadas ou proxies validados**; nenhuma depende de ocupação/receita.

---

## 7. Arquitetura da solução (proposta, sem pesos)

```
ENTRADA
  Details_Itapema.csv   (anúncios Airbnb: tipologia, capacidade, reviews, custos anexos)
  Hosts_ids_Itapema.csv   (perfil do anfitrião; deduplicado por owner)
  Mesh_Ids_Data_Itapema.csv (bairro, lat/lon, first_seen)
  Price_AV_Itapema.csv     (diária por noite × captura)
  VivaReal_Itapema.csv     (oferta de venda: preço, condomínio, IPTU, área)

TRATAMENTO (pipeline reproduzível, sem alterar originais)
  1. Dedup VivaReal por listing_id; marcar duplicados.
  2. Excluir/marcar: 6 listings Price sem Details/Mesh; min_nights=0; lat/lon=0 (usar Mesh);
     rating=0 → "sem avaliação"; normalizar suburb (canônico);
     segmentar outliers VivaReal por listing_type antes de qualquer estatística.
  3. Price: união das fatias por dia-calendário (06/07/20) → grid (imóvel×noite) com
     mediana das capturas como valor-base; manter flags n_datas/n_capturas.
  4. has_price = bandeira de cobertura (NÃO variável de score).

FEATURES (de acordo com tabela §8)
  · imóvel: diária mediana/noite, sazonalidade, tração (reviews/ano, rating>0, favorito,
    fotos), capacidade (tipo, quartos, camas, hóspedes), cleaning_fee, flags p/ has_price,
    novos, n_datas, n_capturas, lat/lon, first_seen, owner.
  · agregado (bairro×tipo×quartos): diária mediana, preço de venda mediano, R$/m²,
    condomínio/IPTU medianos, nº de observações, cobertura.

INDICADORES (nível por §6; decisões por §8)
  · Potencial de diária: diária_mediana por imóvel e por segmento (+sazonalidade).
  · Atratividade de entrada: razão potencial/custo no nível bairro×tipo×quartos.
  · Atividade: tração/ano; maturidade (first_seen, is_new); estabilidade de capturas (frac_mudou)
    documentada como robustez, não score.
  · Confiança: n_datas, n_capturas, cobertura por célula, flags de qualidade.

EVIDÊNCIA
  · Todos os indicadores são calculados de observações diretas (Price/VivaReal/Details).
  · Cada feature tem tipo de evidência e risco de viés na tabela §8.
  · Agregações reportam n e cobertura (≥ mínimo por célula) → nenhuma célula fraca sustenta conclusão.

RECOMENDAÇÃO
  · Saída proposta: shortlist de candidatos por nível:
      (a) melhor SEGMENTO (bairro×tipo×quartos) por razão potencial/custo;
      (b) dentro do segmento, imóveis com alta tração + cobertura de preço adequada (preço
          e atividade) para operação/captação;
      (c) alertas de qualidade (novos, sem preço, outliers, células sem mínimos).
  · Formato: ranking/rotação sem pesos "mágicos" (a definir na fase 3); cada candidato
    acompanha suas evidências e limitações.
  · DOC sempre: "potencial", não receita/ROI; janela jan–abr/2025; não generaliza ano.
```

---

## 9. Escolha de metodologia: 2–3 propostas (sem escolher)

### Proposta A — Referencial de segmento (score de atratividade relativa por célula)
- Ranquear **segmentos** (bairro×tipo×quartos) por **razão potencial/custo** (diária_mediana ÷ preço_de_venda_mediano), com correção por confiança (n e cobertura) e filtro de outliers por tipo.
- **Força:** simples, explicável, defensável, resistente a dados ausentes (medianas), produz imediatamente a tese "qual perfil é o mais promissor".
- **Fragilidade:** razão de medianas ignora dispersão e pode distorcer em células pequenas; não agrega imóveis individuais ("qual imóvel").

### Proposta B — Indicador imobiliário ponderado por redução de viés (otimização de originação)
- Calcular o score **por imóvel dentro de cada segmento**: combinar (sem pesos arbitrários — usar os sinais em §2) diária mediana, sazonalidade, tração/ano, capacidade, cobertura de preço, e flags de qualidade; cada eixo com justificativa de negócio e teste de sensibilidade.
- **Força:** direto para a ação (originação/captação), explica cada candidato.
- **Fragilidade:** exige definir como agregar sinais sem "peso mágico" (poderia usar análise de componentes/ordenação pareada, e sensibilidade explícita); maior risco de dar peso a sinais correlacionados (tração × cobertura).

### Proposta C — Framework explicável de decisão baseado em regras + evidências (argumentativo)
- Construir **regras explícitas** (ex.: exigir mínimo de observação; excluir novos sem preço; rankear por razão potencial/custo; bloquear células com preço < X ou VivaReal < Y) e apresentar **evidência por candidato** — sem um score numérico único; a "recomendação" é um conjunto ordenado de candidaturas com argumentos.
- **Força:** máxima defensabilidade e explicabilidade; nada inventado; fácil auditar.
- **Fragilidade:** sem ranking consolidado, a comparação final exige que o decisor sopesa (mas isso é transparente).

**Pontos a decidir na fase 3:** (i) nível final (segmento vs imóvel vs híbrido); (ii) como agregar sinais (ordenação pareada, análise de sensibilidade, ou regras); (iii) mínimo de observação por célula; (iv) como apresentar incerteza (intervalos de confiança bootstrap sobre medianas).

---

## 10. Princípios da solução (recapitulando parte dos 8 requisitos)

- **Explicável:** cada candidato chega com suas features; regras ou agregações transparentes.
- **Reproduzível:** pipeline em scripts (sem dependência de interação manual).
- **Defensável:** só usa sinais observados/proxies validados; reporta n e cobertura.
- **Resistente a ausentes/outliers:** medianas, mínimos por célula, outlier por tipo.
- **Explícita sobre limitações:** janela jan–abr, ausência de ocupação/receita, seleção de Price, junção agregada.
- **Útil:** gera shortlist de candidatos (imóveis e segmentos) para originação.