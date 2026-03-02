# -*- coding: utf-8 -*-
"""
PASSO 2: Setup do Supabase
  a) Cria a tabela 'eventos' via Management API
  b) Faz deploy da Edge Function 'pipefy-events'
  c) Define variaveis de ambiente na Edge Function
"""

import base64
import io
import json
import os
import sys
import zipfile
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

SUPABASE_URL         = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_PROJECT_REF = os.environ.get("SUPABASE_PROJECT_REF", "")
# Token da CONTA Supabase (Management API). Gerar em: supabase.com/dashboard/account/tokens
SUPABASE_ACCESS_TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
PIPEFY_TOKEN         = os.environ.get("PIPEFY_TOKEN", "")

MGMT_BASE     = "https://api.supabase.com/v1"
FUNCTION_NAME = "pipefy-events"

SQL_FILE = Path(__file__).parent / "sql" / "001_create_eventos.sql"
TS_FILE  = Path(__file__).parent / "edge_function" / "index.ts"
REQ_FIELDS_FILE = Path(__file__).parent / "edge_function" / "required_fields_by_phase.json"


def check_env():
    missing = []
    for var in ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_PROJECT_REF", "PIPEFY_TOKEN"]:
        if not os.environ.get(var):
            missing.append(var)
    if missing:
        print(f"ERRO: Variaveis faltando no .env: {', '.join(missing)}")
        sys.exit(1)


def mgmt_headers():
    # Management API exige Personal Access Token (conta), nao service_role do projeto
    token = SUPABASE_ACCESS_TOKEN or SUPABASE_SERVICE_KEY
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------
# Passo A: Criar tabela via Management API
# ---------------------------------------------------------------
def criar_tabela():
    print("\n[A] Criando tabela 'eventos' no Supabase...")
    sql = SQL_FILE.read_text(encoding="utf-8")

    url = f"{MGMT_BASE}/projects/{SUPABASE_PROJECT_REF}/database/query"
    resp = requests.post(url, json={"query": sql}, headers=mgmt_headers(), timeout=30)

    if resp.status_code in (200, 201):
        print("    [OK] Tabela criada com sucesso!")
    elif resp.status_code == 401:
        print("    [!] 401 JWT failed verification.")
        print("    Para automatizar: crie um Personal Access Token em")
        print("    supabase.com/dashboard/account/tokens e defina no .env:")
        print("    SUPABASE_ACCESS_TOKEN=sbp_xxxx...")
        print("    ALTERNATIVA: execute o SQL no Supabase Dashboard > SQL Editor:")
        print(f"    Arquivo: {SQL_FILE}")
    elif "already exists" in resp.text.lower():
        print("    [OK] Tabela ja existe, pulando.")
    else:
        print(f"    [!] Resposta: {resp.status_code} - {resp.text[:400]}")
        print("    ALTERNATIVA: execute o SQL no Supabase Dashboard > SQL Editor:")
        print(f"    Arquivo: {SQL_FILE}")


# ---------------------------------------------------------------
# Passo B: Deploy da Edge Function via Management API
# ---------------------------------------------------------------
def deploy_edge_function():
    print(f"\n[B] Fazendo deploy da Edge Function '{FUNCTION_NAME}'...")

    ts_code = TS_FILE.read_text(encoding="utf-8")
    # Arquivo JSON de regras por fase (exportado da planilha)
    if REQ_FIELDS_FILE.exists():
        req_fields_json = REQ_FIELDS_FILE.read_text(encoding="utf-8")
    else:
        req_fields_json = "{}"
        print(f"    [!] Aviso: {REQ_FIELDS_FILE.name} não encontrado. Usando mapeamento vazio.")

    # Cria zip em memoria
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.ts", ts_code)
        zf.writestr(REQ_FIELDS_FILE.name, req_fields_json)
    zip_b64 = base64.b64encode(zip_buf.getvalue()).decode()

    # Verifica se funcao ja existe
    resp_list = requests.get(
        f"{MGMT_BASE}/projects/{SUPABASE_PROJECT_REF}/functions",
        headers=mgmt_headers(), timeout=30,
    )
    existing = []
    if resp_list.ok:
        existing = [f["slug"] for f in resp_list.json()]

    if FUNCTION_NAME in existing:
        url    = f"{MGMT_BASE}/projects/{SUPABASE_PROJECT_REF}/functions/{FUNCTION_NAME}"
        method = requests.patch
        print(f"    Atualizando funcao existente...")
    else:
        url    = f"{MGMT_BASE}/projects/{SUPABASE_PROJECT_REF}/functions"
        method = requests.post
        print(f"    Criando nova funcao...")

    payload = {
        "slug": FUNCTION_NAME,
        "name": FUNCTION_NAME,
        "body": zip_b64,
        "verify_jwt": False,
    }

    resp = method(url, json=payload, headers=mgmt_headers(), timeout=60)
    fn_url = f"{SUPABASE_URL}/functions/v1/{FUNCTION_NAME}"

    if resp.status_code in (200, 201):
        print(f"    [OK] Edge Function deployada!")
        print(f"    URL: {fn_url}")
    elif resp.status_code == 401:
        print(f"    [!] 401. Defina SUPABASE_ACCESS_TOKEN no .env (supabase.com/dashboard/account/tokens).")
        print(f"    URL estimada: {fn_url}")
        print("    ALTERNATIVA: supabase login && supabase functions deploy pipefy-events --project-ref " + SUPABASE_PROJECT_REF)
    else:
        print(f"    [!] Erro no deploy: {resp.status_code}")
        print(f"    Resposta: {resp.text[:500]}")
        print(f"    URL estimada: {fn_url}")
        print("    ALTERNATIVA: supabase login && supabase functions deploy pipefy-events --project-ref " + SUPABASE_PROJECT_REF)

    return fn_url


# ---------------------------------------------------------------
# Passo C: Definir variaveis de ambiente na Edge Function
# ---------------------------------------------------------------
def set_env_vars(fn_url: str):
    print(f"\n[C] Configurando variaveis de ambiente da Edge Function...")

    secrets = [
        {"name": "PIPEFY_TOKEN",            "value": PIPEFY_TOKEN},
        {"name": "SUPABASE_URL",            "value": SUPABASE_URL},
        {"name": "SUPABASE_SERVICE_ROLE_KEY","value": SUPABASE_SERVICE_KEY},
    ]

    url  = f"{MGMT_BASE}/projects/{SUPABASE_PROJECT_REF}/secrets"
    resp = requests.post(url, json=secrets, headers=mgmt_headers(), timeout=30)

    if resp.status_code in (200, 201, 204):
        print("    [OK] Variaveis configuradas!")
    elif resp.status_code == 401:
        print("    [!] 401. Use SUPABASE_ACCESS_TOKEN no .env para automatizar.")
        print("    Configure manualmente: Dashboard > Edge Functions > pipefy-events > Secrets")
    else:
        print(f"    [!] Resposta: {resp.status_code} - {resp.text[:300]}")
        print("    Configure manualmente: Dashboard > Edge Functions > pipefy-events > Secrets")
        for s in secrets:
            print(f"      {s['name']} = {s['value'][:20]}...")

    return fn_url


def main():
    check_env()
    print("=" * 60)
    print("  SETUP DO SUPABASE")
    print("=" * 60)

    criar_tabela()
    fn_url = deploy_edge_function()
    fn_url = set_env_vars(fn_url)

    # Salva URL para o proximo script
    url_path = Path(__file__).parent / "edge_function_url.txt"
    url_path.write_text(fn_url, encoding="utf-8")

    print("\n" + "=" * 60)
    print("  SETUP CONCLUIDO")
    print("=" * 60)
    print(f"\n  Edge Function URL:")
    print(f"  {fn_url}")
    print("\n  PROXIMO PASSO: rode python 3_create_webhooks.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
