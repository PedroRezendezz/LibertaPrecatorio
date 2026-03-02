-- ================================================================
-- Migração 002: Suporte ao Pipe SDR (306972940)
-- ================================================================
-- O pipe SDR (Sales Development Representative) foi adicionado ao
-- sistema de integração. Não são necessárias novas colunas, pois
-- os dados do SDR usam apenas os campos já existentes:
--
--   card_id        → ID do card no pipe SDR
--   card_title     → Nome do lead
--   pipe           → "SDR - COMERCIAL"
--   fase           → "NAO IDENTIFICADO" | "QUALIFICADO" | "DESQUALIFICADO"
--   created_at     → Data/hora em que o card entrou na fase (timestamp do evento)
--
-- Fases monitoradas por webhook:
--   - NAO IDENTIFICADO
--   - QUALIFICADO
--   - DESQUALIFICADO
--
-- Para acompanhar o funil completo no Looker Studio, use a coluna
-- 'pipe' para filtrar eventos do SDR e a coluna 'fase' para saber
-- o resultado da qualificação de cada lead.
-- ================================================================

-- View auxiliar: une SDR + COMERCIAL para análise de funil completo
create or replace view public.v_funil_sdr_comercial as
select
    s.card_id,
    s.card_title                                      as lead_nome,
    s.fase                                            as fase_sdr,
    s.created_at                                      as dt_fase_sdr,
    c.card_id                                         as card_id_comercial,
    c.fase                                            as fase_comercial,
    c.created_at                                      as dt_fase_comercial,
    c.valor_proposta_cliente,
    c.valor_final_proposta,
    c.cliente_aceitou_proposta_inicial,
    c.cliente_aceitou_proposta_corrigida
from public.eventos s
left join public.eventos c
    on c.pipe not ilike '%sdr%'
    and c.card_title = s.card_title                   -- correlaciona pelo nome do lead
    and c.pipe ilike '%comercial%'
where s.pipe ilike '%sdr%';

-- Garante que a view seja acessível para o Looker Studio (via anon key)
grant select on public.v_funil_sdr_comercial to anon;
grant select on public.v_funil_sdr_comercial to authenticated;
