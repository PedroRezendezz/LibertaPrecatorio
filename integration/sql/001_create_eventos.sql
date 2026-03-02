-- ================================================================
-- Tabela: eventos
-- Criada para rastrear movimentações de cards no Pipefy por fase
-- ================================================================

create table if not exists public.eventos (
    id                              bigserial primary key,

    -- Identificação do card
    card_id                         text        not null,
    card_title                      text,

    -- Contexto do card
    pipe                            text,
    fase                            text        not null,
    created_at                      timestamptz default now(),

    -- Campos financeiros - Pipe Comercial
    valor_credito                   text,
    valor_credito_proposta_inicial  text,
    valor_proposta_cliente          text,
    valor_renegociado_proposta      text,
    valor_final_proposta            text,
    valor_pago_cedente              text,

    -- Campos de proposta - Pipe Comercial
    cliente_aceitou_proposta_inicial    text,
    conseguiu_negociar                  text,
    proposta_deve_ser_alterada          text,
    cliente_aceitou_proposta_corrigida  text,

    -- Campos de compliance - Pipe Compliance
    inconsistencia_due              text,
    descricao_inconsistencia        text,

    -- Campos jurídicos - Pipe Jurídico
    prazo_conclusao_analise         text,

    -- Constraint: cada card só aparece uma vez por fase
    unique (card_id, fase)
);

-- Index para consultas por pipe e fase (performance no Looker Studio)
create index if not exists idx_eventos_pipe_fase
    on public.eventos (pipe, fase);

create index if not exists idx_eventos_created_at
    on public.eventos (created_at desc);

create index if not exists idx_eventos_card_id
    on public.eventos (card_id);

-- Row Level Security: leitura pública (para Looker Studio via anon key)
alter table public.eventos enable row level security;

create policy "Leitura pública de eventos"
    on public.eventos for select
    using (true);

create policy "Inserção via service role"
    on public.eventos for insert
    with check (true);

create policy "Update via service role"
    on public.eventos for update
    using (true);
