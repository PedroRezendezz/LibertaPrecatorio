# -*- coding: utf-8 -*-
"""
PASSO 3: Criacao dos Webhooks no Pipefy
Cria um webhook por pipe apontando para a Edge Function do Supabase.
Cada webhook escuta card.create e card.move.
"""

import io
import json
import os
import sys
import requests
from pathlib import Path

# Forca UTF-8 no stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Carrega .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

PIPEFY_TOKEN = os.environ.get("PIPEFY_TOKEN", "")
PIPEFY_URL   = "https://api.pipefy.com/graphql"

# URL da Edge Function
fn_url_file = Path(__file__).parent / "edge_function_url.txt"
if fn_url_file.exists():
    EDGE_FUNCTION_URL = fn_url_file.read_text(encoding="utf-8").strip()
else:
    EDGE_FUNCTION_URL = os.environ.get("EDGE_FUNCTION_URL", "")

PIPES = {
    "COMERCIAL":  os.environ.get("PIPE_ID_COMERCIAL",  ""),
    "COMPLIANCE": os.environ.get("PIPE_ID_COMPLIANCE", ""),
    "JURIDICO":   os.environ.get("PIPE_ID_JURIDICO",   ""),
    "FINANCEIRO": os.environ.get("PIPE_ID_FINANCEIRO", ""),
}

WEBHOOK_ACTIONS = ["card.create", "card.move"]


def gql(query: str) -> dict:
    resp = requests.post(
        PIPEFY_URL,
        json={"query": query},
        headers={
            "Authorization": f"Bearer {PIPEFY_TOKEN}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        print("Erros GraphQL:", json.dumps(data["errors"], indent=2, ensure_ascii=False))
        return {}
    return data


def listar_webhooks_existentes(pipe_id: str) -> list:
    query = f"""
    {{
      pipe(id: {pipe_id}) {{
        webhooks {{ id name url actions }}
      }}
    }}
    """
    data = gql(query)
    return data.get("data", {}).get("pipe", {}).get("webhooks", [])


def deletar_webhook(webhook_id: str):
    gql(f'mutation {{ deleteWebhook(input: {{ id: "{webhook_id}" }}) {{ success }} }}')


def criar_webhook(pipe_id: str, nome: str, url: str) -> dict:
    actions_str = json.dumps(WEBHOOK_ACTIONS)
    mutation = f"""
    mutation {{
      createWebhook(input: {{
        pipe_id: {pipe_id},
        name: "{nome}",
        url: "{url}",
        actions: {actions_str}
      }}) {{
        webhook {{ id name url actions }}
      }}
    }}
    """
    data = gql(mutation)
    return data.get("data", {}).get("createWebhook", {}).get("webhook", {})


def check_env():
    if not PIPEFY_TOKEN:
        print("ERRO: PIPEFY_TOKEN nao configurado")
        sys.exit(1)
    if not EDGE_FUNCTION_URL:
        print("ERRO: edge_function_url.txt nao encontrado.")
        print("      Rode o passo 2 primeiro, ou crie o arquivo manualmente com a URL da Edge Function.")
        sys.exit(1)

    pipes_vazios = [k for k, v in PIPES.items() if not v]
    if pipes_vazios:
        print(f"\n[!] Pipe IDs nao configurados para: {', '.join(pipes_vazios)}")
        print("    Esses pipes serao pulados.")
        print("\n    Pipes configurados:")
        for k, v in PIPES.items():
            status = "[OK]" if v else "[--]"
            print(f"      {status} {k}: {v or 'nao configurado'}")
        print()


def main():
    check_env()
    print("=" * 60)
    print("  CRIACAO DE WEBHOOKS NO PIPEFY")
    print("=" * 60)
    print(f"\n  Edge Function URL: {EDGE_FUNCTION_URL}")
    print(f"  Eventos: {', '.join(WEBHOOK_ACTIONS)}\n")

    webhooks_criados = []
    webhooks_falhos  = []

    for pipe_nome, pipe_id in PIPES.items():
        if not pipe_id:
            print(f"\n[--] Pulando {pipe_nome} (sem ID configurado)")
            continue

        print(f"\n[>] Configurando pipe: {pipe_nome} (ID={pipe_id})")

        # Remove webhooks antigos
        existentes   = listar_webhooks_existentes(pipe_id)
        nome_webhook = f"Supabase-Eventos-{pipe_nome}"

        for wh in existentes:
            if wh.get("name") == nome_webhook or wh.get("url") == EDGE_FUNCTION_URL:
                print(f"    Removendo webhook antigo: [{wh['id']}] {wh['name']}")
                deletar_webhook(wh["id"])

        wh = criar_webhook(pipe_id, nome_webhook, EDGE_FUNCTION_URL)
        if wh.get("id"):
            print(f"    [OK] Webhook criado: [{wh['id']}] {wh['name']}")
            print(f"         URL: {wh['url']}")
            print(f"         Acoes: {wh['actions']}")
            webhooks_criados.append({
                "pipe": pipe_nome, "pipe_id": pipe_id,
                "webhook_id": wh["id"], "webhook_nome": wh["name"],
                "url": wh["url"], "actions": wh["actions"],
            })
        else:
            print(f"    [!] Falha ao criar webhook para {pipe_nome}")
            webhooks_falhos.append(pipe_nome)

    resultado_path = Path(__file__).parent / "webhooks_criados.json"
    resultado_path.write_text(
        json.dumps(webhooks_criados, indent=2, ensure_ascii=False), encoding="utf-8",
    )

    print("\n" + "=" * 60)
    print("  RESULTADO")
    print("=" * 60)
    print(f"\n  Webhooks criados: {len(webhooks_criados)}")
    if webhooks_falhos:
        print(f"  Falhas: {', '.join(webhooks_falhos)}")
    print(f"\n  Detalhes salvos em: {resultado_path}")

    print("\n" + "=" * 60)
    print("  INTEGRACAO ATIVA!")
    print("=" * 60)
    print("""
  Fluxo:
  Pipefy (card criado/movido)
      -> webhook HTTP POST
  Supabase Edge Function (pipefy-events)
      -> GraphQL query no Pipefy (busca campos)
  Supabase tabela 'eventos' (upsert)
      -> PostgreSQL connector
  Looker Studio
    """)


if __name__ == "__main__":
    main()
