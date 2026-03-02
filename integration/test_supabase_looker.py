# -*- coding: utf-8 -*-
"""
Testa se o Supabase está acessível e se a tabela 'eventos' existe e tem dados.
Usa a REST API (SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY) — não usa senha do banco.
Útil antes de configurar o Looker Studio.
Uso: python test_supabase_looker.py
"""

import io
import os
import sys
import requests
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

def main():
    print("=" * 60)
    print("  TESTE SUPABASE (para integração Looker Studio)")
    print("=" * 60)

    if not SUPABASE_URL or "xxxx" in SUPABASE_URL:
        print("\n  [X] SUPABASE_URL nao configurada no .env")
        sys.exit(1)
    if not SUPABASE_SERVICE_ROLE_KEY or "eyJ" not in SUPABASE_SERVICE_ROLE_KEY[:5]:
        print("\n  [X] SUPABASE_SERVICE_ROLE_KEY nao configurada no .env")
        sys.exit(1)

    url = f"{SUPABASE_URL}/rest/v1/eventos"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }
    params = {"select": "id,card_id,card_title,pipe,fase,created_at", "order": "created_at.desc", "limit": "5"}

    print(f"\n  URL do projeto: {SUPABASE_URL}")
    print(f"  Consultando tabela 'eventos' (ultimos 5 registros)...\n")

    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
    except requests.RequestException as e:
        print(f"  [X] Erro de rede: {e}")
        sys.exit(1)

    if r.status_code == 401:
        print("  [X] 401 Unauthorized. Verifique SUPABASE_SERVICE_ROLE_KEY no .env")
        sys.exit(1)
    if r.status_code == 404:
        print("  [X] Tabela 'eventos' nao encontrada. Execute o passo 2 da integracao (criar tabela).")
        sys.exit(1)
    if r.status_code != 200:
        print(f"  [X] Resposta inesperada: {r.status_code}")
        print(f"      {r.text[:300]}")
        sys.exit(1)

    data = r.json()
    print(f"  [OK] Conexao com Supabase funcionando.")
    print(f"  [OK] Tabela 'eventos' existe e e acessivel.")
    print(f"       Total de registros retornados nesta amostra: {len(data)}")

    if data:
        print("\n  Amostra (ultimos registros):")
        for i, row in enumerate(data, 1):
            card = row.get("card_id", "?")[:12]
            pipe = row.get("pipe") or "-"
            fase = row.get("fase") or "-"
            created = (row.get("created_at") or "")[:19]
            print(f"     {i}. card_id={card}... pipe={pipe} fase={fase} created_at={created}")
    else:
        print("\n  (Nenhum registro ainda. Movimente um card no Pipefy para gerar dados.)")

    print("\n" + "=" * 60)
    print("  Proximo passo: configurar Looker Studio conforme")
    print("  integration/docs/SUPABASE_LOOKER_PASSO_A_PASSO.md")
    print("=" * 60)

if __name__ == "__main__":
    main()
