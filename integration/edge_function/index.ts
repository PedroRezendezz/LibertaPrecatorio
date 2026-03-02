// Supabase Edge Function: pipefy-events
// Recebe webhooks do Pipefy, busca campos do card via GraphQL e persiste na tabela 'eventos'

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const PIPEFY_API_URL = "https://api.pipefy.com/graphql";

// ---------------------------------------------------------------
// REGRAS POR EVENTO (fase): quais campos salvar por pipe/fase
// Exportado da planilha via integration/0_export_required_fields_from_excel.py
// ---------------------------------------------------------------
import REQUIRED_FIELDS_BY_PHASE from "./required_fields_by_phase.json" assert { type: "json" };

// ---------------------------------------------------------------
// MAPEAMENTO PRIMÁRIO: field_id do Pipefy → coluna eventos
// IDs descobertos via GraphQL introspection do pipe COMERCIAL (306972949)
// ---------------------------------------------------------------
const FIELD_ID_MAP: Record<string, string> = {
  // PIPE: COMERCIAL (306972949)
  "valor_do_cr_dito":                       "valor_credito_proposta_inicial",
  "valor_da_proposta_ao_cliente":            "valor_proposta_cliente",
  "valor_da_proposta_ao_cliente_1":          "valor_proposta_cliente",
  "cliente_aceitou_a_proposta_inicial":      "cliente_aceitou_proposta_inicial",
  "conseguiu_negociar":                      "conseguiu_negociar",
  "valor_negociado_da_proposta_ao_cliente":  "valor_renegociado_proposta",
  "proposta_devera_ser_alterada":            "proposta_deve_ser_alterada",
  "cliente_aceitou_a_proposta_corrigida":    "cliente_aceitou_proposta_corrigida",
  "valor_final_da_proposta":                 "valor_final_proposta",
  "prazo_para_conclusao_da_analise":         "prazo_conclusao_analise",

  // PIPE: COMPLIANCE (306972971) — fase DUE EM ANDAMENTO
  "existe_alguma_inconsistencia_na_due":     "inconsistencia_due",
  "o_que_e_a_inconsistencia":               "descricao_inconsistencia",

  // PIPE: JURIDICO (306972975) — prazo_para_conclusao_da_analise já mapeado acima (mesmo field_id)

  // PIPE: FINANCEIRO (306972979) — campo valor_pago_cedente não existe no pipe ainda
};

// ---------------------------------------------------------------
// MAPEAMENTO FALLBACK: label normalizado → coluna eventos
// Usado quando o field_id não está no mapa acima
// ---------------------------------------------------------------
const FIELD_LABEL_MAP: Record<string, string> = {
  "valor do credito": "valor_credito",
  "valor do credito considerado para proposta inicial": "valor_credito_proposta_inicial",
  "valor da proposta ao cliente": "valor_proposta_cliente",
  "cliente aceitou a proposta inicial": "cliente_aceitou_proposta_inicial",
  "conseguiu negociar": "conseguiu_negociar",
  "valor renegociado da proposta ao cliente": "valor_renegociado_proposta",
  "proposta devera ser alterada": "proposta_deve_ser_alterada",
  "cliente aceitou a proposta corrigida": "cliente_aceitou_proposta_corrigida",
  "valor final da proposta": "valor_final_proposta",
  "existe alguma inconsistencia na due": "inconsistencia_due",
  "o que e a inconsistencia": "descricao_inconsistencia",
  "prazo para conclusao da analise": "prazo_conclusao_analise",
  "valor pago ao cedente": "valor_pago_cedente",
};

// Remove acentos e normaliza string para comparação
function normalize(str: string): string {
  return str
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[?!,.]/g, "")
    .trim();
}

function normalizePipe(str: string): string {
  const s = normalize(str).replace(/\s+/g, " ");
  return s.startsWith("pipe ") ? s.slice("pipe ".length).trim() : s;
}

const EVENT_OPTIONAL_COLUMNS = [
  "valor_credito",
  "valor_credito_proposta_inicial",
  "valor_proposta_cliente",
  "valor_renegociado_proposta",
  "valor_final_proposta",
  "valor_pago_cedente",
  "cliente_aceitou_proposta_inicial",
  "conseguiu_negociar",
  "proposta_deve_ser_alterada",
  "cliente_aceitou_proposta_corrigida",
  "inconsistencia_due",
  "descricao_inconsistencia",
  "prazo_conclusao_analise",
] as const;

function getAllowedColumnsForEvent(pipeName: string, phaseName: string): Set<string> | null {
  const pipeKey = normalizePipe(pipeName);
  const phaseKey = normalize(phaseName).replace(/\s+/g, " ");

  const pipeMap = (REQUIRED_FIELDS_BY_PHASE as Record<string, Record<string, string[]>>)[pipeKey];
  if (!pipeMap) return null;

  const labelKeys = [
    ...(pipeMap["todos"] ?? []),
    ...(pipeMap[phaseKey] ?? []),
  ];

  // Se o pipe existe mas não achamos fase nem "todos", não filtra (evita perder dados por mismatch)
  if (!labelKeys.length) {
    console.warn(`[WARN] Sem regra de campos para pipe='${pipeName}' fase='${phaseName}'. Mantendo comportamento atual.`);
    return null;
  }

  const cols = new Set<string>();
  for (const lk of labelKeys) {
    const col = FIELD_LABEL_MAP[lk];
    if (col) cols.add(col);
    else console.warn(`[WARN] Label não mapeado no FIELD_LABEL_MAP: '${lk}' (pipe='${pipeName}', fase='${phaseName}')`);
  }
  return cols;
}

// Busca todos os campos do card na API do Pipefy
async function fetchCardData(cardId: string, token: string) {
  const query = `
    query {
      card(id: ${cardId}) {
        id
        title
        current_phase { id name }
        pipe { id name }
        fields {
          field { id }
          name
          value
          array_value
          date_value
          datetime_value
        }
      }
    }
  `;

  const res = await fetch(PIPEFY_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ query }),
  });

  if (!res.ok) {
    throw new Error(`Pipefy API error: ${res.status} ${res.statusText}`);
  }

  const json = await res.json();
  if (json.errors) {
    throw new Error(`Pipefy GraphQL error: ${JSON.stringify(json.errors)}`);
  }

  return json.data?.card ?? null;
}

// Monta o registro de evento a partir dos dados do card
function buildEventRecord(
  card: Record<string, unknown>,
  phaseName: string,
): Record<string, unknown> {
  const record: Record<string, unknown> = {
    card_id: String(card.id),
    card_title: card.title,
    pipe: (card.pipe as Record<string, string>)?.name ?? null,
    fase: phaseName,
    created_at: new Date().toISOString(),
  };

  const pipeName = String(((card.pipe as Record<string, string>)?.name ?? "") || "");
  const allowedCols = getAllowedColumnsForEvent(pipeName, phaseName);

  const fields = (card.fields as Array<Record<string, unknown>>) ?? [];
  for (const field of fields) {
    const fieldId  = (field.field as Record<string, string>)?.id ?? "";
    const rawLabel = String(field.name ?? "");
    const labelKey = normalize(rawLabel);

    // Usa field_id primeiro (mais confiável), fallback para label normalizado
    const col = FIELD_ID_MAP[fieldId] ?? FIELD_LABEL_MAP[labelKey];
    if (col) {
      // Se existir regra para o evento, ignora colunas fora da lista permitida
      if (allowedCols && !allowedCols.has(col)) continue;

      // Prefere date_value/datetime_value quando disponível
      const val =
        field.date_value ??
        field.datetime_value ??
        field.value ??
        null;
      // Não sobrescreve se já tem valor (evita que campo duplicado apague o preenchido)
      if (record[col] === undefined || record[col] === null) {
        record[col] = val;
      }
    }
  }

  // Se filtragem ativa, garante que colunas fora da regra virem NULL no upsert
  if (allowedCols) {
    for (const col of EVENT_OPTIONAL_COLUMNS) {
      if (!allowedCols.has(col)) record[col] = null;
      else if (record[col] === undefined) record[col] = null;
    }
  }

  return record;
}

// Handler principal
serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  let payload: Record<string, unknown>;
  try {
    payload = await req.json();
  } catch {
    return new Response("Invalid JSON", { status: 400 });
  }

  const webhookData = payload.data as Record<string, unknown> | undefined;
  if (!webhookData) {
    return new Response("Missing 'data' in payload", { status: 400 });
  }

  const action = webhookData.action as string;
  const card = webhookData.card as Record<string, string> | undefined;

  if (!card?.id) {
    return new Response("Missing card ID", { status: 400 });
  }

  // Determina o nome da fase destino
  const toPhase = webhookData.to as Record<string, string> | undefined;
  const phaseName = toPhase?.name ?? "";

  const pipefyToken = Deno.env.get("PIPEFY_TOKEN");
  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

  if (!pipefyToken || !supabaseUrl || !supabaseKey) {
    console.error("Missing environment variables");
    return new Response("Server misconfiguration", { status: 500 });
  }

  try {
    // Busca dados completos do card no Pipefy
    const cardData = await fetchCardData(card.id, pipefyToken);
    if (!cardData) {
      return new Response("Card not found in Pipefy", { status: 404 });
    }

    // Usa a fase do webhook (to.name) ou a fase atual do card
    const fase = phaseName || (cardData.current_phase as Record<string, string>)?.name || "";

    const record = buildEventRecord(cardData, fase);

    // Persiste no Supabase (upsert por card_id + fase)
    const supabase = createClient(supabaseUrl, supabaseKey);
    const { error } = await supabase
      .from("eventos")
      .upsert(record, { onConflict: "card_id,fase" });

    if (error) {
      console.error("Supabase upsert error:", error);
      return new Response(
        JSON.stringify({ success: false, error: error.message }),
        { status: 500, headers: { "Content-Type": "application/json" } },
      );
    }

    console.log(`[OK] action=${action} card=${card.id} fase=${fase}`);
    return new Response(
      JSON.stringify({ success: true, card_id: card.id, fase }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    );
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("Unexpected error:", msg);
    return new Response(
      JSON.stringify({ success: false, error: msg }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }
});
