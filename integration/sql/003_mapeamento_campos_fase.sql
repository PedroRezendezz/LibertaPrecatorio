-- Gerado automaticamente a partir de 'Mapeamento de Eventos Necessários.xlsx' (aba 'campos')
-- NÃO editar manualmente; rode generate_mapeamento_campos_sql.py se a planilha mudar.

drop view if exists public.v_funil_sdr_comercial;
drop view if exists public.v_mapeamento_campos_fase;
drop table if exists public.mapeamento_campos_fase cascade;

create table if not exists public.mapeamento_campos_fase (
    id          bigserial primary key,
    pipe        text not null,
    fase        text not null,
    campo_label text not null,
    unique (pipe, fase, campo_label)
);

truncate table public.mapeamento_campos_fase;

insert into public.mapeamento_campos_fase (pipe, fase, campo_label) values
    ('COMERCIAL', 'AGUARDANDO DOCUMENTAÇÃO', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'AGUARDANDO PARA ANEXO NOS AUTOS', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'ANEXADO NOS AUTOS', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'ANÁLISE JURÍDICA CONCLUÍDA', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'APRESENTAÇÃO - PROPOSTA INICIAL', 'CLIENTE ACEITOU A PROPOSTA INICIAL'),
    ('COMERCIAL', 'APRESENTAÇÃO - PROPOSTA INICIAL', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'APRESENTAÇÃO - PROPOSTA INICIAL', 'VALOR DA PROPOSTA AO CLIENTE'),
    ('COMERCIAL', 'APRESENTAÇÃO - PROPOSTA INICIAL', 'VALOR RENEGOCIADO DA PROPOSTA AO CLIENTE'),
    ('COMERCIAL', 'ARREMATE COMERCIAL', 'CLIENTE ACEITOU A PROPOSTA CORRIGIDA?'),
    ('COMERCIAL', 'ARREMATE COMERCIAL', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'ARREMATE COMERCIAL', 'PROPOSTA DEVERA SER ALTERADA'),
    ('COMERCIAL', 'ARREMATE COMERCIAL', 'VALOR FINAL DA PROPOSTA'),
    ('COMERCIAL', 'BACKLOG - COMERCIAL', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'BACKLOG - COMERCIAL', 'VALOR DO CREDITO'),
    ('COMERCIAL', 'CARTÓRIO EM AGENDAMENTO', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'CLIENTE - STAND BY', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'CONTRATO ENVIADO PARA ASSINATURA', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'ENVIADO PARA COMPLIANCE - DUE', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'FORMULAÇÃO - PROPOSTA INICIAL', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'FORMULAÇÃO - PROPOSTA INICIAL', 'VALOR DA PROPOSTA AO CLIENTE'),
    ('COMERCIAL', 'FORMULAÇÃO - PROPOSTA INICIAL', 'VALOR DO CREDITO CONSIDERADO PARA PROPOSTA INICIAL'),
    ('COMERCIAL', 'PERDIDO - BARREIRA JURÍDICA', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'PERDIDO - DUE INCONSISTENTE', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'PERDIDO - PROPOSTA CORRIGIDA NEGADA', 'Data e Horário da alteração/criação de fase'),
    ('COMERCIAL', 'PERDIDO - PROPOSTA INICIAL NEGADA', 'Data e Horário da alteração/criação de fase'),
    ('COMPLIANCE', 'BACKLOG - COMPLIANCE', 'Data e Horário da alteração/criação de fase'),
    ('COMPLIANCE', 'DUE CONCLUÍDA', 'Data e Horário da alteração/criação de fase'),
    ('COMPLIANCE', 'DUE CONCLUÍDA', 'EXISTE ALGUMA INCONSISTENCIA NA DUE'),
    ('COMPLIANCE', 'DUE CONCLUÍDA', 'O QUE E A INCONSISTENCIA'),
    ('FINANCEIRO', 'PAGAMENTO LIBERADO', 'Data e Horário da alteração/criação de fase'),
    ('FINANCEIRO', 'PAGAMENTO REALIZADO', 'Data e Horário da alteração/criação de fase'),
    ('FINANCEIRO', 'PAGAMENTO REALIZADO', 'VALOR PAGO AO CEDENTE'),
    ('JURIDICO', 'ANEXADO NOS AUTOS', 'Data e Horário da alteração/criação de fase'),
    ('JURIDICO', 'ANEXAR NOS AUTOS DO PROCESSO', 'Data e Horário da alteração/criação de fase'),
    ('JURIDICO', 'ANÁLISE JURÍDICA - EM ANDAMENTO', 'Data e Horário da alteração/criação de fase'),
    ('JURIDICO', 'ANÁLISE JURÍDICA - FILA', 'Data e Horário da alteração/criação de fase'),
    ('JURIDICO', 'ANÁLISE JURÍDICA - FILA', 'PRAZO PARA CONCLUSAO DA ANALISE'),
    ('JURIDICO', 'ANÁLISE JURÍDICA -CONCLUÍDA', 'Data e Horário da alteração/criação de fase'),
    ('JURIDICO', 'DUE INCONSISTENTE', 'Data e Horário da alteração/criação de fase'),
    ('JURIDICO', 'PERDIDO - DUE INCONSISTENTE', 'Data e Horário da alteração/criação de fase'),
    ('PIPE SDR - COMERCIAL', 'DESQUALIFICADO', 'Data e Horário da alteração/criação de fase'),
    ('PIPE SDR - COMERCIAL', 'NAO IDENTIFICADO', 'Data e Horário da alteração/criação de fase'),
    ('PIPE SDR - COMERCIAL', 'QUALIFICADO', 'Data e Horário da alteração/criação de fase'),
    ('PIPE SDR - COMERCIAL', 'TODOS', 'Data e Horário da alteração/criação de fase');

