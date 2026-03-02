# Looker Studio — Estrutura Completa (SDR + Comercial + Compliance + Jurídico + Financeiro)

## 1. Fontes de Dados

Use **duas fontes** no Looker Studio:

| # | Nome | Tipo | Tabela/View |
|---|------|------|-------------|
| 1 | Eventos Pipefy | PostgreSQL | `public.eventos` |
| 2 | Funil SDR→Comercial | PostgreSQL | `public.v_funil_sdr_comercial` |

> A view `v_funil_sdr_comercial` foi criada pela migration `002_add_sdr_pipe.sql`.
> Para criar, execute o SQL no Supabase Dashboard → SQL Editor.

---

## 2. Campos Calculados (criar na Fonte 1 — `eventos`)

No Looker Studio, após conectar a fonte, crie os campos calculados abaixo:

### `pipe_grupo`
Agrupa os pipes em categorias para filtros globais.
```
CASE
  WHEN REGEXP_MATCH(pipe, "(?i)sdr") THEN "SDR"
  WHEN REGEXP_MATCH(pipe, "(?i)comercial") THEN "COMERCIAL"
  WHEN REGEXP_MATCH(pipe, "(?i)compliance") THEN "COMPLIANCE"
  WHEN REGEXP_MATCH(pipe, "(?i)jur") THEN "JURIDICO"
  WHEN REGEXP_MATCH(pipe, "(?i)financ") THEN "FINANCEIRO"
  ELSE pipe
END
```

### `fase_resultado_sdr`
Para eventos do pipe SDR, classifica o resultado:
```
CASE
  WHEN fase = "QUALIFICADO" THEN "Qualificado"
  WHEN fase = "DESQUALIFICADO" THEN "Desqualificado"
  WHEN fase = "NAO IDENTIFICADO" THEN "Não Identificado"
  ELSE NULL
END
```

### `fase_perdida`
Sinaliza se o card está em uma fase de perda:
```
CASE
  WHEN REGEXP_MATCH(fase, "(?i)perdido") THEN "Sim"
  ELSE "Não"
END
```

### `valor_proposta_num`
Converte o campo texto de valor para número:
```
CAST(REGEXP_REPLACE(valor_proposta_cliente, "[^0-9.]", "") AS NUMBER)
```

### `valor_final_num`
```
CAST(REGEXP_REPLACE(valor_final_proposta, "[^0-9.]", "") AS NUMBER)
```

---

## 3. Estrutura de Páginas do Relatório

### Página 1 — Visão Geral (Funil Completo)

**Objetivo:** enxergar o funil do primeiro contato ao pagamento.

**Componentes:**

| Componente | Tipo | Dimensão | Métrica | Filtro |
|-----------|------|----------|---------|--------|
| KPI: Leads SDR | Scorecard | — | CONTAGEM(card_id) onde pipe_grupo = "SDR" | pipe_grupo = SDR |
| KPI: Qualificados | Scorecard | — | CONTAGEM(card_id) onde fase = "QUALIFICADO" | — |
| KPI: Em Proposta | Scorecard | — | CONTAGEM(card_id) onde fase contém "PROPOSTA" | — |
| KPI: Pagos | Scorecard | — | CONTAGEM(card_id) onde fase = "PAGAMENTO REALIZADO" | — |
| Funil | Gráfico de Funil | fase_grupo | CONTAGEM(card_id) | — |
| Evolução mensal | Linha | Mês(created_at) | CONTAGEM(card_id) | — |
| Tabela top leads | Tabela | card_title, pipe_grupo, fase | created_at | ordenar por data desc |

**Funil sugerido (ordem):**

```
SDR: Leads Totais
  ↓
SDR: Qualificados
  ↓
COMERCIAL: Formulação de Proposta
  ↓
COMERCIAL: Proposta Aceita
  ↓
COMPLIANCE: DUE Concluída
  ↓
JURÍDICO: Análise Concluída
  ↓
FINANCEIRO: Pagamento Realizado
```

---

### Página 2 — SDR: Qualificação de Leads

**Objetivo:** acompanhar a eficiência do SDR em qualificar leads.

**Componentes:**

| Componente | Tipo | Dimensão | Métrica |
|-----------|------|----------|---------|
| KPI: Total de leads | Scorecard | — | CONTAGEM(card_id) |
| KPI: Taxa de qualificação | Scorecard | — | CONTAGEM(fase="QUALIFICADO") / CONTAGEM(total) |
| KPI: Taxa de desqualificação | Scorecard | — | CONTAGEM(fase="DESQUALIFICADO") / CONTAGEM(total) |
| Distribuição resultado | Pizza/Donut | fase_resultado_sdr | CONTAGEM(card_id) |
| Evolução semanal | Área empilhada | Semana(created_at) | CONTAGEM(card_id) por fase_resultado_sdr |
| Tabela de leads | Tabela | card_title, fase, created_at | — |

**Filtro de página:** `pipe_grupo = "SDR"`

---

### Página 3 — Comercial: Propostas e Negociação

**Objetivo:** monitorar o valor das propostas e a taxa de fechamento.

**Componentes:**

| Componente | Tipo | Dimensão | Métrica |
|-----------|------|----------|---------|
| KPI: Valor total em proposta | Scorecard | — | SOMA(valor_proposta_num) |
| KPI: Valor total aprovado | Scorecard | — | SOMA(valor_final_num) |
| KPI: Taxa de aceite proposta inicial | Scorecard | — | CONTAGEM(cliente_aceitou_proposta_inicial="Sim") / total |
| KPI: Deals em andamento | Scorecard | — | CONTAGEM(fase não PERDIDO) |
| Funil comercial | Barras horiz. | fase | CONTAGEM(card_id) |
| Propostas por valor | Barras vert. | card_title | valor_proposta_num |
| Distribuição de fases perdidas | Pizza | fase | CONTAGEM(card_id) onde fase_perdida="Sim" |
| Evolução mensal de valor | Linha | Mês(created_at) | SOMA(valor_final_num) |
| Tabela detalhada | Tabela | card_title, fase, valor_proposta_cliente, valor_final_proposta, cliente_aceitou_proposta_inicial | created_at |

**Filtro de página:** `pipe_grupo = "COMERCIAL"`

---

### Página 4 — Compliance & Jurídico: Due Diligence

**Objetivo:** controlar a fila de DUE e prazos jurídicos.

**Componentes:**

| Componente | Tipo | Dimensão | Métrica |
|-----------|------|----------|---------|
| KPI: Em DUE | Scorecard | — | CONTAGEM(fase="DUE EM ANDAMENTO") |
| KPI: DUE com inconsistência | Scorecard | — | CONTAGEM(inconsistencia_due="Sim") |
| KPI: Aguardando jurídico | Scorecard | — | CONTAGEM(fase="AGUARDANDO ANÁLISE JURÍDICA") |
| Status DUE | Pizza | inconsistencia_due | CONTAGEM(card_id) |
| Tipo de inconsistência | Barras | descricao_inconsistencia | CONTAGEM(card_id) |
| Tabela jurídico c/ prazos | Tabela | card_title, fase, prazo_conclusao_analise, created_at | — ordenar por prazo asc |

**Filtro de página:** `pipe_grupo = "COMPLIANCE" OR pipe_grupo = "JURIDICO"`

---

### Página 5 — Financeiro: Pagamentos

**Objetivo:** acompanhar pagamentos liberados e realizados.

**Componentes:**

| Componente | Tipo | Dimensão | Métrica |
|-----------|------|----------|---------|
| KPI: Pagamentos realizados | Scorecard | — | CONTAGEM(fase="PAGAMENTO REALIZADO") |
| KPI: Valor total pago | Scorecard | — | SOMA(valor_pago_cedente convertido) |
| Pagamentos por mês | Barras | Mês(created_at) | CONTAGEM(card_id) |
| Tabela de pagamentos | Tabela | card_title, fase, valor_pago_cedente, created_at | — |

**Filtro de página:** `pipe_grupo = "FINANCEIRO"`

---

## 4. Filtros Globais (Controles no Topo do Relatório)

Adicione estes controles disponíveis em todas as páginas:

| Controle | Campo | Tipo |
|---------|-------|------|
| Período | created_at | Intervalo de datas |
| Pipe | pipe_grupo | Lista suspensa (multi-seleção) |
| Fase | fase | Lista suspensa |
| Lead/Cliente | card_title | Entrada de texto |

---

## 5. Paleta de Cores Sugerida

| Pipe | Cor |
|------|-----|
| SDR | #4285F4 (azul) |
| COMERCIAL | #34A853 (verde) |
| COMPLIANCE | #FBBC04 (amarelo) |
| JURÍDICO | #EA4335 (vermelho) |
| FINANCEIRO | #9C27B0 (roxo) |
| Perdido | #9E9E9E (cinza) |

---

## 6. Passo a Passo para Criar no Looker Studio

### 6.1 Executar a migration 002
1. Acesse **Supabase Dashboard → SQL Editor**
2. Cole o conteúdo de `integration/sql/002_add_sdr_pipe.sql`
3. Execute — isso criará a view `v_funil_sdr_comercial`

### 6.2 Adicionar a 2ª fonte de dados
1. No Looker Studio, vá em **Recurso → Gerenciar fontes de dados adicionadas**
2. Clique em **Adicionar dados**
3. Use o mesmo conector PostgreSQL com a mesma conexão do Supabase
4. Em vez de tabela `eventos`, selecione a view `v_funil_sdr_comercial`
5. Nomeie como "Funil SDR→Comercial"

### 6.3 Criar o relatório
1. Crie um novo relatório com a fonte `eventos` como primária
2. Adicione as 5 páginas descritas acima
3. Para a Página 1 (Funil Completo), misture dados das duas fontes usando **gráficos combinados** ou **mesclar dados**

---

## 7. Observação sobre Correlação SDR → Comercial

O SDR e o Comercial usam **pipes separados**, então um lead qualificado no SDR cria um **novo card** no pipe Comercial. A view `v_funil_sdr_comercial` correlaciona os dois pelo `card_title` (nome do lead). Caso o nome possa variar, ajuste a lógica de JOIN na migration 002 para usar outro campo de correspondência (ex.: CPF, se capturado no SDR).
