# Integração Pipefy → Supabase → Looker Studio

Captura movimentações de cards em todos os pipes do Pipefy e disponibiliza os dados no Looker Studio via Supabase.

---

## Pipes integrados

| Pipe | ID | Webhook ID | Status |
|------|----|-----------|--------|
| SDR - COMERCIAL | 306972940 | 300640944 | ✅ Ativo |
| COMERCIAL | 306972949 | 300640945 | ✅ Ativo |
| COMPLIANCE | 306972971 | 300640946 | ✅ Ativo |
| FINANCEIRO | 306972979 | 300640947 | ✅ Ativo |
| JURÍDICO | 306972975 | 300640949 | ✅ Ativo |

Todos os webhooks escutam os eventos `card.create` e `card.move`, apontando para a Edge Function:
```
https://jfclxizmtdsxatwsxznb.supabase.co/functions/v1/pipefy-events
```

---

## Fluxo de dados

```
Pipefy (card criado ou movido)
    ↓  webhook HTTP POST
Supabase Edge Function  (pipefy-events)
    ↓  GraphQL query → busca campos do card
Supabase tabela 'eventos'  (upsert por card_id + fase)
    ↓  conector PostgreSQL
Looker Studio
```

---

## Estrutura da tabela `eventos`

| Coluna | Descrição |
|--------|-----------|
| `card_id` | ID do card no Pipefy |
| `card_title` | Título/nome do card |
| `pipe` | Nome do pipe (ex.: "SDR - COMERCIAL") |
| `fase` | Nome da fase em que o card entrou |
| `created_at` | Timestamp do evento |
| `valor_credito` | Valor do crédito |
| `valor_credito_proposta_inicial` | Valor do crédito para proposta inicial |
| `valor_proposta_cliente` | Valor da proposta ao cliente |
| `cliente_aceitou_proposta_inicial` | Sim/Não |
| `conseguiu_negociar` | Sim/Não |
| `valor_renegociado_proposta` | Valor renegociado |
| `proposta_deve_ser_alterada` | Sim/Não |
| `cliente_aceitou_proposta_corrigida` | Sim/Não |
| `valor_final_proposta` | Valor final da proposta |
| `inconsistencia_due` | Existe inconsistência na DUE |
| `descricao_inconsistencia` | Descrição da inconsistência |
| `prazo_conclusao_analise` | Prazo de conclusão da análise jurídica |
| `valor_pago_cedente` | Valor pago ao cedente |

**Constraint:** `unique(card_id, fase)` — upsert automático, sem duplicatas.

---

## Fases por pipe (com campos monitorados)

### SDR - COMERCIAL (306972940)
| Fase | Campos capturados |
|------|------------------|
| TODOS | nome_completo, CPF, número do processo, consegue identificar o processo |
| NAO IDENTIFICADO | *(apenas timestamp)* |
| EM ATENDIMENTO | valor do crédito, ente pagador, tribunal, honorários, etapa, análise IA, qualificado?, motivo desqualificação |
| QUALIFICADO | *(apenas timestamp)* |
| DESQUALIFICADO | *(apenas timestamp)* |

### COMERCIAL (306972949)
Fases monitoradas: BACKLOG, CLIENTE-APROVAÇÃO, CLIENTE-STAND BY, FORMULAÇÃO-PROPOSTA INICIAL, APRESENTAÇÃO-PROPOSTA INICIAL, AGUARDANDO DOCUMENTAÇÃO, ENVIADO PARA COMPLIANCE, ANÁLISE JURÍDICA CONCLUÍDA, ARREMATE COMERCIAL, ELABORAÇÃO DO CONTRATO, VALIDAÇÃO DO CONTRATO, CONTRATO ENVIADO, CARTÓRIO EM AGENDAMENTO, AGUARDANDO ANEXO, ANEXADO NOS AUTOS, PERDIDO (4 tipos).

### COMPLIANCE (306972971)
Fases: BACKLOG, AGUARDANDO DUE, DUE EM ANDAMENTO (captura inconsistências), DUE CONCLUÍDA.

### JURÍDICO (306972975)
Fases: DUE INCONSISTENTE, ANÁLISE JURÍDICA FILA/EM ANDAMENTO/CONCLUÍDA, ANEXAR NOS AUTOS, ANEXADO NOS AUTOS, PERDIDO.

### FINANCEIRO (306972979)
Fases: PAGAMENTO LIBERADO, PAGAMENTO REALIZADO.

---

## Scripts de configuração

Execute na pasta `integration/` na ordem abaixo:

```bash
# 1. Descobre IDs de pipes e fases (gera pipefy_ids.json)
py 1_discover_pipefy.py

# 2. Cria tabela no Supabase + faz deploy da Edge Function
py 2_setup_supabase.py

# 3. Cria webhooks no Pipefy para todos os pipes
py 3_create_webhooks.py

# Ou rode tudo de uma vez:
py run_all.py
```

**Pré-requisito:** arquivo `.env` na pasta `integration/` com:
```
PIPEFY_TOKEN=...
SUPABASE_URL=https://jfclxizmtdsxatwsxznb.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_PROJECT_REF=jfclxizmtdsxatwsxznb
PIPE_ID_COMERCIAL=306972949
PIPE_ID_COMPLIANCE=306972971
PIPE_ID_JURIDICO=306972975
PIPE_ID_FINANCEIRO=306972979
# SDR já vem hardcoded como 306972940
```

---

## Arquivos do projeto

```
integration/
├── .env                          # Credenciais (não versionar)
├── 1_discover_pipefy.py          # Descobre IDs de pipes e fases
├── 2_setup_supabase.py           # Setup Supabase (tabela + edge function)
├── 3_create_webhooks.py          # Cria webhooks no Pipefy
├── run_all.py                    # Executa os 3 passos em sequência
├── test_supabase_looker.py       # Testa conexão Supabase sem Looker
├── pipefy_ids.json               # IDs mapeados (gerado pelo script 1)
├── webhooks_criados.json         # Registro dos webhooks ativos
├── edge_function_url.txt         # URL da Edge Function
├── edge_function/
│   └── index.ts                  # Supabase Edge Function (processa webhooks)
├── sql/
│   ├── 001_create_eventos.sql    # Schema da tabela eventos
│   └── 002_add_sdr_pipe.sql      # View v_funil_sdr_comercial (funil cruzado)
└── docs/
    ├── LOOKER_SDR_E_FUNIL_COMPLETO.md   # Guia completo do Looker Studio (5 páginas)
    ├── LOOKER_ESTRUTURA_VISUALIZACAO.md
    ├── LOOKER_REFERENCIA_RAPIDA.txt
    └── SUPABASE_LOOKER_PASSO_A_PASSO.md
```

---

## Conectar ao Looker Studio

### Parte 1 — Preparar o Supabase (senha do banco)

O Looker Studio conecta via **PostgreSQL**. É necessário definir a senha do banco:

1. Acesse **https://supabase.com/dashboard/project/jfclxizmtdsxatwsxznb**
2. Menu lateral: **Project Settings** → **Database**
3. Em **Database password**, clique em **Reset database password**
4. Defina uma senha forte e guarde — você vai usar no Looker Studio

### Parte 2 — Dados de conexão

| Campo | Session Pooler (recomendado) | Conexão Direta |
|-------|------------------------------|----------------|
| **Host** | `aws-0-us-east-1.pooler.supabase.com` | `db.jfclxizmtdsxatwsxznb.supabase.co` |
| **Port** | `6543` | `5432` |
| **Database** | `postgres` | `postgres` |
| **Username** | `postgres.jfclxizmtdsxatwsxznb` | `postgres` |
| **Password** | *(senha definida acima)* | *(senha definida acima)* |

### Parte 3 — Criar a fonte de dados

1. Acesse **https://lookerstudio.google.com**
2. **Criar** → **Fonte de dados** → conector **PostgreSQL**
3. Preencha os dados de conexão acima e marque **SSL**
4. Em Schema: **public** → Tabela: **eventos**
5. Nomeie como "Liberta – Eventos Pipefy" e clique em **Conectar**

### Parte 4 — Estrutura de relatório sugerida

Consulte o guia completo em `integration/docs/LOOKER_SDR_E_FUNIL_COMPLETO.md`.

**5 páginas recomendadas:**
1. **Visão Geral** — funil completo SDR → Comercial → Compliance → Jurídico → Financeiro
2. **SDR** — qualificação de leads (qualificado / desqualificado / em atendimento)
3. **Comercial** — propostas, valores e taxas de aceite
4. **Compliance & Jurídico** — DUE e prazos de análise
5. **Financeiro** — pagamentos realizados e valores pagos

### Testar sem o Looker

```bash
cd integration
py test_supabase_looker.py
```

---

## View para análise de funil cruzado (opcional)

A migration `sql/002_add_sdr_pipe.sql` cria a view `v_funil_sdr_comercial`, que cruza eventos do SDR com eventos do Comercial pelo nome do lead. Execute no **Supabase Dashboard → SQL Editor** para habilitar análises de conversão SDR → Comercial.
