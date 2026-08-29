# Hackathon Jovens Talentos AI Builder 2026 — Seazone

Análise de potencial para a **operação de curta temporada em Itapema (SC)**, apoiada por uma cascata explicável de **priorização de segmentos (S1)** → **candidatos operacionais (S2)** → **evidências**. A solução é construída exclusivamente a partir dos datasets fornecidos e está documentada nos relatórios técnicos (`analise/`).

Este repositório reúne: (1) o **pipeline analítico** (reproduzível de ponta a ponta), (2) os **outputs** em `analise/saida/`, e (3) o **Radar Seazone**, uma interface de produto que apresenta os resultados como uma jornada de decisão.

> A análise **não prevê** ROI, receita, ocupação, yield ou retorno individual de imóvel. Ela produz uma **leitura comparativa de potencial** para guiar originação e captação — não uma promessa de ganho e não uma recomendação de compra de imóvel específico.

## 👉 Enunciado do desafio

O desafio completo (missão, dados, entregáveis, regras, prazo e avaliação) está publicado em:

**[ABRIR O DESAFIO COMPLETO](https://seazone-tech.github.io/jovens-talentos-2026-hackathon-data/)**

> Se o link não abrir, o mesmo conteúdo está no arquivo [`index.html`](index.html) da raiz deste repositório (baixe e abra no navegador).

---

## O problema de negócio

A Seazone gere mais de 3.000 imóveis de curta temporada no Brasil e precisa decidir **onde e no que atuar** na captação/originação de novas unidades. Para apoiar essa decisão em Itapema (SC), perguntamos:

- Quais **segmentos de mercado** (bairro × tipo × nº de quartos) apresentam a relação mais intensa entre a **diária anunciada** e o **preço de venda anunciado**?
- Dentro desses segmentos, quais **anúncios Airbnb** têm sinais operacionais compatíveis com uma eventual estratégia de captação/operação?

A solução entrega **duas decisões separadas e explicáveis**:

- **S1 — Segmentos prioritários.** Onde atuar (nível agregado de mercado).
- **S2 — Candidatos operacionais.** Quais anúncios olhar dentro dos segmentos prioritários.

**A decisão NÃO atribui a um anúncio Airbnb o preço de um anúncio VivaReal**: a relação diária/preço existe **somente no agregado do segmento**, porque não há chave única de junção imóvel a imóvel entre os dois universos (auditoria A7/A11 — ver `relatorio_auditoria.md`).

---

## Dados utilizados

Snapshot estático do mercado de Itapema (SC), fornecido no desafio. Mesma base para todos os candidatos:

| Arquivo | Papel | Uso na análise |
|---|---|---|
| `data/Details_Itapema.csv` | Anúncios Airbnb (tipologia, capacidade, reviews, rating) | Caracterização e tração dos anúncios |
| `data/Hosts_ids_Itapema.csv` | Anfitriões (superhost, reviews, tempo como host) | Dimensão de proprietário (deduplicada) |
| `data/Mesh_Ids_Data_Itapema.csv` | Bairro + latitude/longitude por anúncio | Localização e segmentação por bairro |
| `data/Price_AV_Itapema.csv` | Diária por noite × data de estadia × data de captura | Base do potencial de diária (preço **anunciado**) |
| `data/VivaReal_Itapema.csv` | Anúncios de venda (preço, condomínio, IPTU, área) | Referência agregada de mercado de venda (preço **anunciado**) |

Os datasets originais não são alterados; o pipeline verifica a integridade por hash (SHA-256) antes e depois (`analise/saida/pipeline_resultados.json`). Detalhes de estrutura, granularidade e qualidade em `analise/relatorio_auditoria.md` e `analise/p1_p2_relatorio.md`.

---

## Metodologia (resumo)

A metodologia completa e **congelada** está em [`analise/metodologia_decisao.md`](analise/metodologia_decisao.md). Resumo:

- **Segmentação:** células `bairro × tipo × quartos` (apartamento/casa/outros; quartos 1 | 2 | 3 | 4+; 0 quartos fora — "sem informação").
- **Fallback hierárquico:** se uma célula fina não atinge elegibilidade, sobe para `bairro × tipo` e depois `bairro`. O nível agregado **substitui** o detalhe que falhou, sem concorrer com ele.
- **R (indicador comparativo de segmento):** R é a razão entre a mediana da diária anunciada no Airbnb e a mediana dos preços de venda observados no VivaReal para o mesmo segmento. É um **índice comparativo de potencial**, calculado somente no nível de segmento — não estima retorno de imóvel individual.
- **Incerteza:** bootstrap **por cluster (anúncio)**, com amostras independentes Airbnb/VivaReal → `IC95(R)`. Comparações via `Δ = ln(R_i / R_j)` com `Δ_min = ln(1,25)`, `P(Δ > 0) ≥ 0,975` e correção **Benjamini–Hochberg (FDR)**.
- **Elegibilidade:** `n_ai ≥ 5`, `n_vi_com_sale_price ≥ 5` e meia-largura do `IC95(R) ≤ 0,60`. Célula sem evidência suficiente → **inconclusiva** (não vira recomendação).
- **S1:** prioriza células elegíveis não dominadas que **dominam ao menos uma outra célula** (dominância estatística). Não dominada sem dominar ninguém não é priorizada.
- **S2:** anúncios nas células prioritárias com `has_price = 1`, `n_datas ≥ 20` (critério operacional conservador), não novos e não órfãos. Sinais operacionais (reviews, rating, superhost, favorito, profissional, reserva instantânea, limpeza, maturidade) são apresentados **descritivamente** — nunca interpretados como upside.

### Separação de conceitos (mantida em todos os artefatos)

| Conceito | Papel |
|---|---|
| **Atratividade comparativa** | R + IC95 + dominância: posição relativa do segmento. |
| **Evidência** | o que sustenta a leitura: observações, cobertura do Price, precisão, FDR, limitações. |
| **Elegibilidade** | critérios mínimos (volume e precisão) para o segmento ser avaliado. |
| **Candidato operacional** | anúncio com sinais operacionais dentro de um segmento prioritário — **não** é recomendação de compra. |

Atratividade ≠ evidência ≠ elegibilidade. Evidência fraca vira **inconclusivo**, nunca "peso menor". Parâmetros e critérios estão centralizados em `analise/scripts/config.py`.

---

## S1 — Segmentos prioritários e S2 — Candidatos operacionais

- **S1** define em nível agregado quais células `bairro × tipo × quartos` apresentam a relação mais alta entre **diária anunciada** e **preço de venda anunciado** do mesmo segmento. Produz segmentos *prioritários*, *não priorizáveis* e *inconclusivos* — sempre com as evidências da decisão (`s1_segmentos.csv`, `s1_inconclusivas.csv`).
- **S2** lista, dentro dos segmentos prioritários, anúncios Airbnb com sinais operacionais compatíveis com uma eventual captação/operação (`s2_candidatos.csv`). **Não é recomendação de compra de um imóvel específico**: não há preço de venda individual atribuído a nenhum anúncio.

Resultados consolidados gerados pelo pipeline (detalhe completo em [`analise/relatorio_implementacao.md`](analise/relatorio_implementacao.md)):

| Status | Quantidade |
|---|---|
| Segmentos **prioritários** (S1) | **7** |
| Segmentos **não priorizáveis** | 10 |
| Segmentos **inconclusivos** (evidência insuficiente / não elegíveis) | 167 |
| **Candidatos operacionais** (S2, únicos) | **98** |

> **Importante:** "prioritário" refere-se à posição **dentro da metodologia adotada** — não significa "melhor investimento garantido". As restrições de dados estão em Limitações.

---

## Resultados — recomendação final de negócio

Os 7 segmentos prioritários (S1), com o nível avaliado:

| Segmento | Nível | R |
|---|---|---|
| `morretes | apartamento | 3` | bairro×tipo×quartos | 0,00077 |
| `morretes | apartamento | 2` | bairro×tipo×quartos | 0,00060 |
| `tabuleiro dos oliveiras | apartamento | 2` | bairro×tipo×quartos | 0,00058 |
| `morretes | casa | (todos os quartos)` | bairro×tipo *(fallback)* | 0,00057 |
| `casa branca | apartamento | 2` | bairro×tipo×quartos | 0,00054 |
| `centro | apartamento | 2` | bairro×tipo×quartos | 0,00053 |
| `centro | apartamento | 1` | bairro×tipo×quartos | 0,00050 |

Se a Seazone fosse priorizar onde olhar hoje, a recomendação **dentro do que os dados sustentam** é:

1. **Focar a originação/captação nos segmentos acima**, em especial nos que combinam maior R com observação suficiente: **Morretes (apartamentos 2 e 3 quartos e casas)** e **Centro (apartamentos 1 e 2 quartos)**. Esses segmentos são os que a metodologia aponta como mais intensos na relação diária anunciada/preço de venda anunciado, com dominância estatística sobre outros segmentos avaliados.
2. **Usar S2 como lista de alvos de prospecção operacional** (98 candidatos), não como carteira de compra: para cada anúncio, verificar capacidade, tração e sinais de operação antes de qualquer abordagem.

### Posição sobre a tese dos compactos no Centro

A hipótese interna de que **apartamentos compactos (studio/1 quarto) no Centro** seriam a aposta mais eficiente recebe **suporte parcial** na metodologia:

- O segmento **Centro | apartamento | 1 quarto** é **prioritário** (R = 0,00050; IC95 [0,00044, 0,00072]; maior cobertura de Price entre os prioritários, 67,2%), e **Centro | apartamento | 2 quartos** também (R = 0,00053). Ou seja: **dentro dos dados ancorados em preço anunciado, o Centro compacto merece atenção confirmada pela cascata S1**.
- A análise **não prova** aquisição: sem ocupação, sem receita, sem pagamento de transação observado, e a relação diária/preço vale **no agregado do segmento**, não imóvel a imóvel.

**Conclusão:** apartamentos compactos no Centro são um segmento **a priorizar na captação**, consistentes com a tese interna — porém isso **não significa que qualquer imóvel individual seja uma boa aquisição**. A decisão de compra de um imóvel específico exige dados que este conjunto não possui (calendário real, histórico de receita, custos e negociação). Esta análise sustenta **priorização de segmentos e originação de candidatos**, não recomendação individual de compra.

---

## Limitações

Os datasets **não permitem** estimar diretamente:

- ocupação;
- receita realizada;
- ROI / yield / payback;
- disponibilidade de calendário;
- retorno individual de um imóvel.

Limitações estruturais que restringem o que é possível afirmar:

- **Cobertura seletiva do Price:** o preço existe para ~22% dos anúncios (999 de 4.441), concentrados em ativos/profissionais. As conclusões valem para esse subconjunto, sem extrapolar para anúncios sem preço.
- **Sem matching individual Airbnb × VivaReal:** não há chave única entre os dois universos; a relação diária/preço é calculada agregando por segmento, não imóvel a imóvel.
- **Janela temporal:** preços observados de jan–abr/2025 (alta temporada parcial, capturas em janeiro); não generaliza o ano.
- **Preço anunciado ≠ transação:** diária e preço de venda são ofertas, não negócios fechados.
- **Parâmetros de materialidade:** `n_datas ≥ 20` e `Δ_min = 25%` são, respectivamente, um critério operacional conservador e uma hipótese metodológica provisória (ver `p1_p2_relatorio.md`).

Auditoria empírica completa dos dados (coleta, cobertura, junção, outliers) em [`analise/relatorio_auditoria.md`](analise/relatorio_auditoria.md).

---

## Radar Seazone — interface de produto

A interface apresenta os outputs como uma **jornada de decisão**, sem recalcular nenhuma métrica: tudo vem direto de `analise/saida/`.

**Navegação:**

```
Mercado → Segmentos avaliados → Detalhe do segmento → Candidatos operacionais → Evidências
```

- **Mercado:** visão geral com contagens reais (7 prioritários, 98 candidatos, 17 avaliados, 167 inconclusivos), as confianças da leitura (sem ocupação/receita/ROI/matching) e a distinção entre atratividade, evidência, elegibilidade e candidato operacional. Segmentos inconclusivos continuam visíveis, marcados como **evidência insuficiente** com o motivo registrado pelo pipeline.
- **Segmentos avaliados:** os 17 segmentos elegíveis com R, banda IC95, observações, cobertura e dominância (FDR).
- **Detalhe do segmento:** R, IC95(R), observações, cobertura, precisão, a razão da priorização, a evidência completa (verbatim do `evidencias.csv`), elegibilidade e limitações.
- **Candidatos operacionais:** anúncios do segmento com características descritivas (diária mediana anunciada, rating, reviews, capacidade, superhost/profissional/instantâneo, maturidade) — **sem** sugerir compra de imóvel específico.
- **Evidências:** a explicação textual por segmento é exibida no detalhe e está, em formato bruto, em `evidencias.csv` e `recomendacao_segmentos.csv`.

**Como abrir a interface** (exige um servidor HTTP — o navegador bloqueia o carregamento dos CSV via `fetch` em caminho `file://`):

```bash
python interface/run.py
```

Depois abra **http://localhost:8000/interface/** no navegador (o script já abre automaticamente). Servindo a partir da raiz, `interface/` busca os outputs em `analise/saida/` — não mova os arquivos de `analise/saida/`.

---

## Como executar o pipeline

Pré-requisitos: Python 3 com `pandas`, `numpy` (e `matplotlib` para os gráficos de sensibilidade). Na raiz do repositório:

```bash
python analise/scripts/run_pipeline.py
```

O pipeline:

- parte **sempre dos datasets originais** (`data/`) e regenera os outputs derivados;
- **não altera** os datasets originais (verifica integridade por hash SHA-256);
- é **determinístico** (bootstrap com seed fixa em `analise/scripts/config.py`);
- roda de ponta a ponta: carregamento → tratamento → features → elegibilidade/fallback → inferência → comparação → S1 → S2 → evidências → recomendação → relatório final → validação de consistência.

### Onde estão os resultados

Outputs principais em `analise/saida/`:

| Arquivo | Conteúdo |
|---|---|
| `s1_segmentos.csv` | 17 segmentos avaliados (7 prioritários, 10 não priorizáveis) com R, IC95, observações, cobertura |
| `s1_inconclusivas.csv` | 167 segmentos inconclusivos com o motivo (volume/precisão/cobertura) |
| `s2_candidatos.csv` | 98 candidatos operacionais com características descritivas |
| `evidencias.csv` | Explicação textual por segmento (dominância, IC, limitações) |
| `recomendacao_segmentos.csv` | Segmentos recomendados × nº de alvos (S2) |
| `pipeline_resultados.json` | Metadados: contagens, hashes, flags de confiança |
| `relatorio_implementacao.md` | Relatório da implementação/resultados |

Relatórios técnicos em `analise/`: `relatorio_implementacao.md`, `relatorio_auditoria.md`, `relatorio_testes.md`, `p1_p2_relatorio.md`, `arquitetura_solucao.md`, `metodologia_decisao.md`.

---

## Documentação complementar

- [`analise/metodologia_decisao.md`](analise/metodologia_decisao.md) — metodologia congelada (segmentos, R, bootstrap, FDR, elegibilidade, S1/S2).
- [`analise/arquitetura_solucao.md`](analise/arquitetura_solucao.md) — desenho da arquitetura e definição das decisões.
- [`analise/relatorio_implementacao.md`](analise/relatorio_implementacao.md) — resultados da implementação e contagens S1/S2.
- [`analise/relatorio_auditoria.md`](analise/relatorio_auditoria.md) — auditoria técnica e decisões de consistência.
- [`analise/relatorio_testes.md`](analise/relatorio_testes.md) — testes empíricos de validação de hipóteses.
- [`analise/p1_p2_relatorio.md`](analise/p1_p2_relatorio.md) — calibração de parâmetros (perfil de células e efeito mínimo).

---

## Como a IA foi utilizada

IA foi usada como **ferramenta de trabalho em todo o processo**, com verificação empírica e senso crítico em cada etapa — não como substituta do raciocínio:

- **Exploração e entendimento dos dados:** auditorias de estrutura, granularidade e qualidade, com scripts reproduzíveis e re-execução após correções.
- **Crítica metodológica:** revisão de métodos de inferência (bootstrap por cluster, FDR, efeito mínimo), prevenção de viés e separação entre fato observado, interpretação, hipótese e limitação.
- **Implementação:** código do pipeline e módulos (tratamento, elegibilidade, inferência, S1/S2, evidências, relatórios).
- **Revisão e auditoria:** testes de consistência, integridade dos dados por hash e revisão crítica dos resultados (nenhuma conclusão sobre execução falha).
- **Documentação:** estruturação dos relatórios técnicos, do README e da interface de produto.

O processo priorizou **defensabilidade e reprodutibilidade**: todo número da interface e do README vem de `analise/saida/`, e a metodologia não foi alterada após a congelada.

---

## Estrutura do projeto

```
.
├── data/                      # Datasets originais (intactos)
├── index.html                 # Enunciado do desafio
├── interface/                 # Radar Seazone — interface de produto (HTML/CSS/JS puro, sem build)
│   ├── index.html
│   ├── styles.css
│   ├── data.js                # Leitura/estruturação dos outputs (sem cálculo analítico novo)
│   ├── app.js                 # Jornada de navegação
│   └── run.py                 # Servidor local
├── analise/
│   ├── scripts/               # Código: pipeline, módulos e testes
│   ├── saida/                 # Outputs primários (S1, S2, evidências, relatórios)
│   ├── output/                # Saídas dos testes exploratórios
│   ├── metodologia_decisao.md
│   ├── arquitetura_solucao.md
│   ├── relatorio_implementacao.md
│   ├── relatorio_auditoria.md
│   ├── relatorio_testes.md
│   └── p1_p2_relatorio.md
├── .gitignore
└── README.md
```

---

*Seazone — Jovens Talentos AI Builder 2026*