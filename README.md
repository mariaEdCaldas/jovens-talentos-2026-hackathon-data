# Hackathon Jovens Talentos AI Builder 2026 — Seazone

Análise de potencial para **operação de curta temporada em Itapema (SC)**, apoiada por decisões de segmento (S1) e de candidato operacional (S2). Baseada exclusivamente nos datasets fornecidos.

## 👉 Leia o desafio completo

**[ABRIR O DESAFIO COMPLETO](https://seazone-tech.github.io/jovens-talentos-2026-hackathon-data/)**

Lá estão a missão, os dados, o que entregar, as regras, o prazo e como a entrega é avaliada.

> Se o link não abrir, o mesmo conteúdo está no arquivo [`index.html`](index.html) deste repositório (baixe e abra no navegador).

---

## O problema de negócio

A Seazone precisa decidir **onde e no que atuar** na operação de curta temporada.

Este trabalho apoia essa decisão identificando **segmentos de mercado potencialmente atrativos** (bairro × tipo × nº de quartos) e **candidatos operacionais** dentro deles, usando exclusivamente os dados observados:

- **diária anunciada** por noite (Airbnb) — preço de oferta, não transação;
- **preço de venda anunciado**, condomínio e IPTU (VivaReal) — referências agregadas de mercado, não negociação;
- características do anúncio e do anfitrião (Airbnb) e localização (Mesh).

> A solução **não prevê** ROI, receita, ocupação ou retorno individual de imóvel. Ela produz uma **leitura comparativa de potencial** para guiar originação/captação, não uma promessa de ganho.

---

## A solução

O fluxo segue uma cascata explicável e reproduzível:

```
dados → tratamento → features → S1 (priorização de segmentos)
      → S2 (candidatos operacionais) → evidências → recomendação explicável
```

- **S1 — Segmentos prioritários.** Define, em nível agregado, quais células
  `bairro × tipo × quartos` apresentam relação mais alta entre **diária anunciada** e
  **preço de venda anunciado** do mesmo segmento. Produz segmentos *prioritários*,
  *não priorizáveis* ou *inconclusivos* — sempre com as evidências da decisão.
- **S2 — Candidatos operacionais.** Dentro dos segmentos prioritários, lista anúncios
  Airbnb com sinais operacionais compatíveis com uma eventual captação/operação.
  **Não** é recomendação de compra de um imóvel específico.

A decisão **não** atribui a um anúncio Airbnb o preço de um anúncio VivaReal: a relação
diária/preço existe **somente no agregado do segmento**.

---

## Dados utilizados

Snapshot estático do mercado de Itapema (SC); mesma base para todos os candidatos.

| Arquivo | Papel | Uso na análise |
|---|---|---|
| `data/Details_Itapema.csv` | Anúncios Airbnb (tipologia, capacidade, reviews, rating) | Caracterização e tração dos anúncios |
| `data/Hosts_ids_Itapema.csv` | Anfitriões (superhost, reviews, tempo de host) | Dimensão de proprietário (deduplicada) |
| `data/Mesh_Ids_Data_Itapema.csv` | Bairro + latitude/longitude por anúncio | Localização e segmentação por bairro |
| `data/Price_AV_Itapema.csv` | Diária por noite × data de estadia × data de captura | Base do potencial de diária (anunciado) |
| `data/VivaReal_Itapema.csv` | Anúncios de venda (preço, condomínio, IPTU, área) | Referência agregada de capital de aquisição |

Detalhes de cada dataset e dos problemas de qualidade estão nos relatórios técnicos.

---

## Metodologia (resumo)

A metodologia completa e congelada está em [`analise/metodologia_decisao.md`](analise/metodologia_decisao.md). Resumo:

- **Segmentação:** células `bairro × tipo × quartos` (tipos apartamento/casa/outros; quartos 1|2|3|4+; 0 quartos fora).
- **Fallback hierárquico:** se uma célula fina não atinge elegibilidade, sobe para `bairro × tipo` e depois `bairro` — o nível agregado **substitui** o detalhe que falhou, sem concorrer com ele.
- **`R` (indicador comparativo de segmento):** mediana da diária anunciada (Airbnb) ÷ mediana do preço de venda observado (VivaReal) **no mesmo segmento**. É índice **comparativo de potencial**, não surgido de retorno.
- **Incerteza:** bootstrap **por cluster (anúncio)**, amostras independentes Airbnb/VivaReal → `IC95(R)`. Comparações via `Δ = ln(R_i/R_j)` com `Δ_min = ln(1,25)`, `P(Δ>0) ≥ 0,975` e correção **Benjamini–Hochberg (FDR)**.
- **Elegibilidade:** `n_ai ≥ 5`, `n_vi_com_sale_price ≥ 5`, meia-largura do `IC95(R) ≤ 0,60`. Célula sem evidência suficiente → **inconclusiva** (não vira recomendação).
- **S1:** prioriza células elegíveis não dominadas que dominam ao menos uma outra célula (dominância estatística).
- **S2:** anúncios nas células prioritárias com `has_price=1`, `n_datas ≥ 20` (critério operacional conservador), não novos; sinais operacionais descritivos (reviews, rating, superhost, favorito, etc.) — **nunca** interpretados como upside.

Parâmetros, critérios e hipóteses estão centralizados no `analise/scripts/config.py`.

---

## Resultados

Resultados produzidos pela implementação atual (detalhe completo no
[`relatorio_implementacao.md`](analise/relatorio_implementacao.md)):

| Status | Quantidade |
|---|---|
| Segmentos **prioritários** (S1) | **7** |
| Segmentos **não priorizáveis** | 10 |
| Segmentos **inconclusivos** (evidência insuficiente / não elegíveis) | 167 |
| **Candidatos operacionais** (S2, únicos) | **98** |

Os 7 segmentos prioritários são:

- `casa branca | apartamento | 2 quartos`
- `centro | apartamento | 1 quarto`
- `centro | apartamento | 2 quartos`
- `morretes | apartamento | 2 quartos`
- `morretes | apartamento | 3 quartos`
- `tabuleiro dos oliveiras | apartamento | 2 quartos`
- `morretes | casa | (todos os quartos)` *(nível de fallback bairro × tipo)*

> **Importante:** "prioritário" refere-se à posição **dentro da metodologia adotada** — não significa "melhor investimento garantido". As restrições de dados estão na seção de limitações.

---

## Limitações

Os datasets **não permitem** estimar diretamente:

- ocupação;
- receita realizada;
- ROI / yield / payback;
- disponibilidade de calendário;
- retorno individual de um imóvel.

Limitações estruturais que restringem o que é possível afirmar:

- **Cobertura seletiva do Price:** o preço existe para ~22% dos anúncios, concentrados nos ativos/profissionais; conclusões valem para esse subconjunto, sem extrapolar para anúncios sem preço.
- **Sem matching individual Airbnb × VivaReal:** não há chave única entre os dois universos; a relação diária/preço é calculada agregando por segmento, não imóvel a imóvel.
- **Janela temporal:** preços observados de jan–abr/2025 (alta temporada parcial); não generaliza o ano.
- **Preço anunciado ≠ transação:** diária e preço de venda são ofertas, não negócios fechados.

---

## Reproducibilidade

O pipeline completo pode ser executado a partir de um único comando, na raiz do repositório:

```bash
python analise/scripts/run_pipeline.py
```

O comando:

- parte **sempre dos datasets originais** (`data/`) e gera novamente os outputs derivados;
- **não altera** os datasets originais (verifica integridade por hash SHA-256);
- é **determinístico** (bootstrap com seed fixa em `analise/scripts/config.py`);
- roda de ponta a ponta: carregamento → tratamento → features → elegibilidade/fallback → inferência → comparação → S1 → S2 → evidências → recomendação → relatório final → validação.

Main outputs gerados em `analise/saida/`:

- `analise/saida/s1_segmentos.csv`
- `analise/saida/s1_inconclusivas.csv`
- `analise/saida/s2_candidatos.csv`
- `analise/saida/evidencias.csv`
- `analise/saida/recomendacao_segmentos.csv`
- `analise/saida/pipeline_resultados.json`
- `analise/relatorio_implementacao.md`

---

## Uso de IA

IA foi usada ao longo de **todo o processo** como ferramenta de trabalho — não como substituta do raciocínio:

- **Exploração e entendimento dos dados** — auditorias de estrutura, granularidade e qualidade (com scripts reproduzíveis).
- **Formulação e crítica de hipóteses** — separação entre fato observado, hipótese e inferência.
- **Revisão metodológica** — métodos de inferência, prevenção de viés e definição de critérios.
- **Implementação** — código do pipeline e módulos.
- **Auditoria e validação** — testes de consistência, integridade dos dados e revisão de resultados.

O processo priorizou **verificação empírica e defensabilidade** (ex.: bootstrap por cluster, controle de FDR, separação entre atratividade/evidência/elegibilidade) em vez de produzir um ranking não auditável.

---

## Estrutura do projeto

```
.
├── data/                      # Datasets originais (intactos)
├── index.html                 # Enunciado do desafio
├── analise/
│   ├── scripts/               # Código: pipeline, módulos e testes
│   ├── saida/                 # Outputs primários (S1, S2, evidências, relat.)
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

## Documentação complementar

- [`analise/metodologia_decisao.md`](analise/metodologia_decisao.md) — metodologia congelada (segmentos, R, bootstrap, FDR, elegibilidade, S1/S2).
- [`analise/arquitetura_solucao.md`](analise/arquitetura_solucao.md) — desenho da arquitetura e definição das decisões.
- [`analise/relatorio_implementacao.md`](analise/relatorio_implementacao.md) — resultados da implementação e contagens S1/S2.
- [`analise/relatorio_auditoria.md`](analise/relatorio_auditoria.md) — auditoria técnica e decisões de consistência.
- [`analise/relatorio_testes.md`](analise/relatorio_testes.md) — testes empíricos de validação de hipóteses.
- [`analise/p1_p2_relatorio.md`](analise/p1_p2_relatorio.md) — calibração de parâmetros (perfil de células e efeito mínimo).

---

*Seazone — Jovens Talentos AI Builder 2026*