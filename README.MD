# Passo a passo: Supabase → Looker Studio

Conectar o Looker Studio à tabela `eventos` do Supabase para montar relatórios a partir dos dados do Pipefy.

---

## Parte 1: Preparar o Supabase (senha do banco)

O Looker Studio conecta via **PostgreSQL**. Se você criou o projeto pelo GitHub, a senha do banco pode não estar definida.

### 1.1 Definir ou resetar a senha do banco

1. Acesse o Dashboard do Supabase:  
   **https://supabase.com/dashboard/project/jfclxizmtdsxatwsxznb**
2. No menu lateral: **Project Settings** (ícone de engrenagem) → **Database**.
3. Na seção **Database password**, clique em **Reset database password**.
4. Defina uma senha forte (ex.: `Liberta2024!Prec`) e guarde — você vai usar no Looker Studio.

---

## Parte 2: Dados de conexão (copie do Dashboard)

No mesmo lugar (**Settings → Database**), anote:

| Campo        | Onde está no Dashboard | Exemplo para este projeto |
|-------------|-------------------------|----------------------------|
| **Host**    | Connection string (Session pooler ou Direct) | Pooler: `aws-0-us-east-1.pooler.supabase.com` <br> Direto: `db.jfclxizmtdsxatwsxznb.supabase.co` |
| **Porta**   | Pooler: 6543 / Direto: 5432 | **6543** (pooler) ou **5432** (direto) |
| **Banco**   | Sempre `postgres` | `postgres` |
| **Usuário** | Pooler: `postgres.PROJECT_REF` / Direto: `postgres` | Pooler: `postgres.jfclxizmtdsxatwsxznb` <br> Direto: `postgres` |
| **Senha**   | A que você definiu no passo 1.1 | (a sua senha) |

**Recomendação:** usar o **Session pooler** (porta 6543 e usuário `postgres.jfclxizmtdsxatwsxznb`) — costuma dar menos problema com Looker Studio.

---

## Parte 3: Conectar no Looker Studio

### 3.1 Abrir o Looker Studio

1. Acesse **https://lookerstudio.google.com**
2. Faça login com a conta Google em que quer ver os relatórios.

### 3.2 Criar fonte de dados

1. Clique em **Criar** → **Fonte de dados**.
2. Na lista de conectores, procure **PostgreSQL** (pode estar em “Partner connectors” ou “Community”).
   - Se aparecer **“Supabase”** como conector, pode usar esse.
   - Caso contrário, use o conector **PostgreSQL** genérico.
3. Preencha os campos exatamente como abaixo (ajuste só a senha).

**Opção A – Session pooler (recomendado)**

| Campo        | Valor |
|-------------|--------|
| **Host**    | `aws-0-us-east-1.pooler.supabase.com` |
| **Port**    | `6543` |
| **Database**| `postgres` |
| **Username**| `postgres.jfclxizmtdsxatwsxznb` |
| **Password**| *(a senha que você definiu no passo 1.1)* |

**Opção B – Conexão direta**

| Campo        | Valor |
|-------------|--------|
| **Host**    | `db.jfclxizmtdsxatwsxznb.supabase.co` |
| **Port**    | `5432` |
| **Database**| `postgres` |
| **Username**| `postgres` |
| **Password**| *(a senha que você definiu no passo 1.1)* |

4. Marque **SSL** / **Use SSL** (recomendado).
5. Clique em **Test connection** (ou equivalente). Se der certo, prossiga.
6. Se der erro (ex.: códigos `0f08167d` ou `aeed68a0`):
   - Confirme que a **senha** está correta (reset no passo 1.1).
   - No pooler, confirme que o usuário é `postgres.jfclxizmtdsxatwsxznb` (não só `postgres`).
   - Tente a outra opção (pooler ↔ direto).

### 3.3 Escolher a tabela `eventos`

1. Depois da conexão bem-sucedida, em **Schema** selecione **public**.
2. Em tabelas, escolha **eventos**.
3. Os campos da tabela (card_id, card_title, pipe, fase, created_at, valor_credito, etc.) aparecerão para você montar métricas e dimensões.
4. Dê um nome à fonte de dados (ex.: “Liberta – Eventos Pipefy”) e clique em **Conectar** / **Create report**.

---

## Parte 4: Criar um relatório

1. **Criar** → **Relatório**.
2. Ao pedir fonte de dados, selecione a que você acabou de criar (“Liberta – Eventos Pipefy”).
3. Arraste campos da tabela `eventos` para gráficos e tabelas (ex.: pipe, fase, created_at, valores).

---

## Resumo rápido

| Etapa | Onde | O quê |
|-------|------|--------|
| 1 | Supabase → Settings → Database | Reset database password e anotar Host/Porta/Usuário |
| 2 | lookerstudio.google.com → Criar → Fonte de dados | Conector PostgreSQL (ou Supabase) |
| 3 | Formulário da conexão | Host, 6543, postgres, postgres.jfclxizmtdsxatwsxznb, senha, SSL |
| 4 | Após conectar | Schema **public**, tabela **eventos** |

---

## Testar se o Supabase está respondendo (sem Looker)

Na pasta `integration`, rode:

```bash
python test_supabase_looker.py
```

Esse script usa a REST API do Supabase (com o `.env` do projeto) e verifica se a tabela `eventos` existe e se há dados. **Não** usa a senha do banco; serve só para confirmar que o projeto e a tabela estão ok antes de configurar o Looker.
