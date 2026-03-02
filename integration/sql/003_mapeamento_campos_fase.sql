-- ================================================================
-- Tabela: mapeamento_campos_fase
-- Mapeia, para cada PIPE e FASE, quais campos são considerados
-- "necessários" conforme a planilha
--   Mapemanto de eventos necessários - fase x campos por fase.xlsx
--
-- Esta tabela é puramente estrutural (não depende de eventos reais).
-- Ela serve para montar visões no Looker Studio em que:
--   - As FASES aparecem como colunas (pivot)
--   - Os CAMPOS aparecem como linhas
-- ================================================================

create table if not exists public.mapeamento_campos_fase (
    id           bigserial primary key,
    pipe         text not null,
    fase         text not null,
    campo_label  text not null,
    -- Extras para facilitar no Looker (podem ser usados ou ignorados)
    card_title   text,
    created_at   timestamptz default now(),
    unique (pipe, fase, campo_label)
);

-- Limpa o conteúdo atual para reaplicar o mapeamento completo
truncate table public.mapeamento_campos_fase;

-- ============================
-- PIPE: COMERCIAL
-- ============================
insert into public.mapeamento_campos_fase (pipe, fase, campo_label) values
  ('COMERCIAL', 'BACKLOG - COMERCIAL', 'valor do credito'),
  ('COMERCIAL', 'FORMULACAO - PROPOSTA INICIAL', 'valor do credito considerado para proposta inicial'),
  ('COMERCIAL', 'FORMULACAO - PROPOSTA INICIAL', 'valor da proposta ao cliente'),
  ('COMERCIAL', 'APRESENTACAO - PROPOSTA INICIAL', 'valor da proposta ao cliente'),
  ('COMERCIAL', 'APRESENTACAO - PROPOSTA INICIAL', 'cliente aceitou a proposta inicial'),
  ('COMERCIAL', 'APRESENTACAO - PROPOSTA INICIAL', 'valor renegociado da proposta ao cliente'),
  ('COMERCIAL', 'ARREMATE COMERCIAL', 'proposta devera ser alterada'),
  ('COMERCIAL', 'ARREMATE COMERCIAL', 'cliente aceitou a proposta corrigida'),
  ('COMERCIAL', 'ARREMATE COMERCIAL', 'valor final da proposta');

-- ============================
-- PIPE: COMPLIANCE
-- ============================
insert into public.mapeamento_campos_fase (pipe, fase, campo_label) values
  ('COMPLIANCE', 'DUE CONCLUIDA', 'existe alguma inconsistencia na due'),
  ('COMPLIANCE', 'DUE CONCLUIDA', 'o que e a inconsistencia');

-- ============================
-- PIPE: JURIDICO
-- ============================
insert into public.mapeamento_campos_fase (pipe, fase, campo_label) values
  ('JURIDICO', 'ANALISE JURIDICA - FILA', 'prazo para conclusao da analise');

-- ============================
-- PIPE: FINANCEIRO
-- ============================
insert into public.mapeamento_campos_fase (pipe, fase, campo_label) values
  ('FINANCEIRO', 'PAGAMENTO REALIZADO', 'valor pago ao cedente');

-- ================================================================
-- View auxiliar: lista simples (pipe, fase, campo_label)
-- Esta view é redundante, mas facilita se você quiser restringir
-- permissões só à view no futuro.
-- ================================================================

create or replace view public.v_mapeamento_campos_fase as
select pipe, fase, campo_label, card_title, created_at
from public.mapeamento_campos_fase;

grant select on public.mapeamento_campos_fase to anon, authenticated;
grant select on public.v_mapeamento_campos_fase to anon, authenticated;

