# Estrutura de visualização no Looker Studio (Eventos Pipefy)

Use este documento como guia para montar o relatório no Looker Studio. Cada seção indica o que criar e com quais campos.

**Fonte de dados:** conexão PostgreSQL ao Supabase → tabela `public.eventos`.

---

## Visão geral da estrutura

| Página | Nome sugerido | Conteúdo |
|--------|----------------|----------|
| 1 | Visão geral | KPIs + cards por pipe/fase + timeline |
| 2 | Comercial | Funnel e valores (proposta, negociação) |
| 3 | Compliance & Jurídico | DUE, inconsistências, prazos |
| 4 | Tabela de eventos | Tabela completa com filtros |

---

## PÁGINA 1 – Visão geral

### 1. Filtros globais (topo da página)

- **Controle** → **Filtro de dados**
  - Campos: `Pipe`, `Fase`
  - Aplicar a: Todos os gráficos / Todas as páginas (conforme preferir)

- **Controle** → **Filtro de intervalo de datas**
  - Campo: `created_at`
  - Aplicar aos gráficos que usam data

### 2. Bloco de KPIs (métricas em cards)

Criar **4 cartões de pontuação** (Adicionar → Cartão de pontuação), cada um com:

| Cartão | Métrica | Configuração |
|--------|---------|--------------|
| Total de eventos | Contagem de registros | Métrica: **Registros** (ou COUNT de `id`) |
| Cards únicos | Contagem de cards | Métrica: **COUNT_DISTINCT** de `card_id` |
| Pipes com movimento | Pipes distintos | Métrica: **COUNT_DISTINCT** de `pipe` |
| Fases distintas | Fases distintas | Métrica: **COUNT_DISTINCT** de `fase` |

Alinhe os 4 em uma linha no topo.

### 3. Gráfico: Eventos por pipe

- **Gráfico de barras** (horizontal ou vertical)
  - Dimensão: `pipe`
  - Métrica: **Registros** (ou COUNT)
  - Ordenar por: valor decrescente
  - Título: "Eventos por pipe"

### 4. Gráfico: Eventos por fase

- **Gráfico de barras** ou **gráfico de pizza**
  - Dimensão: `fase`
  - Métrica: **Registros**
  - Título: "Eventos por fase"
  - Dica: se tiver muitas fases, use barras horizontais para ler os nomes.

### 5. Gráfico: Timeline (eventos ao longo do tempo)

- **Gráfico de linhas** ou **área**
  - Dimensão: `created_at` → definir agregação como **Data** (dia ou semana)
  - Métrica: **Registros**
  - Título: "Eventos ao longo do tempo"
  - Opcional: quebrar por `pipe` (séries por cor).

### 6. Tabela resumo: Pipe × Fase

- **Tabela**
  - Dimensões: `pipe`, `fase`
  - Métrica: **Registros**
  - Título: "Resumo Pipe × Fase"
  - Opcional: ativar **Grãos de calor** (heatmap) na métrica para destacar volume.

---

## PÁGINA 2 – Comercial

Filtro sugerido no topo: **Pipe** = COMERCIAL (fixo ou filtro de página).

### 1. KPIs do pipe Comercial

| Cartão | Métrica |
|--------|---------|
| Eventos Comercial | Registros (com filtro Pipe = COMERCIAL) |
| Cards únicos | COUNT_DISTINCT `card_id` |
| Fases com movimento | COUNT_DISTINCT `fase` |

### 2. Gráfico: Fases do Comercial (funnel visual)

- **Gráfico de barras horizontais**
  - Dimensão: `fase`
  - Métrica: **Registros**
  - Título: "Comercial – eventos por fase"

### 3. Campos de valor (proposta / negociação)

Os valores estão em texto na base. Para usar como número no Looker:

- Crie **campos calculados** na fonte de dados (ou no relatório), convertendo texto em número quando possível, por exemplo:
  - `valor_credito_proposta_inicial`, `valor_proposta_cliente`, `valor_final_proposta`, `valor_renegociado_proposta`
- Se o formato for "1.500,00" (BR), pode ser necessário um cálculo tipo:  
  `CAST(REPLACE(REPLACE(valor_final_proposta, '.', ''), ',', '.') AS NUMBER)`  
  (ajuste conforme o formato real no Supabase.)

Depois:

- **Tabela** com dimensões: `card_id`, `card_title`, `fase`, `created_at`
- Métricas: soma/média dos valores calculados (ex.: soma de valor final da proposta)
- Título: "Valores por card/fase (Comercial)"

### 4. Proposta aceita / negociada

- **Gráfico de pizza** ou **barras**
  - Dimensão: `cliente_aceitou_proposta_inicial` ou `conseguiu_negociar`
  - Métrica: **Registros**
  - Título: "Cliente aceitou proposta inicial" ou "Conseguiu negociar"

---

## PÁGINA 3 – Compliance e Jurídico

### 1. Filtro

- **Pipe**: COMPLIANCE ou JURIDICO (ou dois gráficos separados por pipe).

### 2. Compliance – DUE

- **Tabela**
  - Dimensões: `card_id`, `pipe`, `fase`, `inconsistencia_due`, `descricao_inconsistencia`, `created_at`
  - Métrica: **Registros**
  - Título: "Compliance – DUE e inconsistências"

- **Gráfico de barras**
  - Dimensão: `inconsistencia_due`
  - Métrica: **Registros**
  - Título: "Inconsistência na DUE (Sim/Não)"

### 3. Jurídico – Prazos

- **Tabela**
  - Dimensões: `card_id`, `fase`, `prazo_conclusao_analise`, `created_at`
  - Título: "Jurídico – prazos de análise"

---

## PÁGINA 4 – Tabela de eventos (detalhe)

### 1. Tabela completa

- **Tabela**
  - Dimensões (em ordem sugerida):  
    `created_at`, `card_id`, `card_title`, `pipe`, `fase`,  
    `valor_credito_proposta_inicial`, `valor_proposta_cliente`, `valor_final_proposta`,  
    `cliente_aceitou_proposta_inicial`, `conseguiu_negociar`,  
    `inconsistencia_due`, `descricao_inconsistencia`, `prazo_conclusao_analise`, `valor_pago_cedente`
  - Métrica: **Registros** (opcional; pode deixar só as dimensões)
  - Título: "Eventos – detalhe"
  - Paginação: habilitar (ex.: 25 ou 50 linhas por página)

### 2. Filtros na página

- Filtros de dados: **Pipe**, **Fase**, **Intervalo de datas** (`created_at`)
- Manter os filtros visíveis no relatório para o usuário refinar.

---

## Resumo rápido (checklist)

- [ ] Página 1: 4 KPIs + eventos por pipe + eventos por fase + timeline + tabela Pipe × Fase + filtros (pipe, fase, data).
- [ ] Página 2: filtro Pipe = COMERCIAL + KPIs + barras por fase + tabela/gráficos de valores e proposta aceita/negociada.
- [ ] Página 3: filtro Compliance/Jurídico + tabelas e gráficos de DUE e prazos.
- [ ] Página 4: tabela detalhada de eventos + filtros (pipe, fase, data).

---

## Dicas de formatação

1. **Datas:** em gráficos, use `created_at` como **Data** e escolha granularidade (Dia/Semana/Mês).
2. **Valores em texto:** para gráficos numéricos, crie campos calculados convertendo os campos de valor (e ajuste formato BR se necessário).
3. **Cores:** use tema consistente; pode definir paleta por `pipe` (ex.: Comercial = azul, Compliance = verde, Jurídico = laranja, Financeiro = roxo).
4. **Títulos:** deixe títulos claros em cada gráfico/tabela para facilitar o uso do relatório.

Se quiser, na próxima iteração podemos detalhar só uma página (por exemplo a 1) com passos literalmente “clique em X, depois em Y” conforme a interface atual do Looker Studio.
