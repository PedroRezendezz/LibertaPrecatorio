# -*- coding: utf-8 -*-
"""
PASSO 1: Descoberta de IDs do Pipefy
Consulta a API do Pipefy e lista todos os Pipes, Fases e Campos disponiveis.
Gera o arquivo pipefy_ids.json para uso nos proximos scripts.
"""

import io
import json
import os
import sys
import requests
from pathlib import Path

# Forca UTF-8 no stdout para evitar erros no Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Carrega .env se existir
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

PIPEFY_TOKEN = os.environ.get("PIPEFY_TOKEN", "")
PIPEFY_URL   = "https://api.pipefy.com/graphql"

PIPES_ALVO = ["COMERCIAL", "COMPLIANCE", "JURIDICO", "FINANCEIRO"]


def gql(query: str) -> dict:
    if not PIPEFY_TOKEN:
        print("ERRO: PIPEFY_TOKEN nao definido no .env")
        sys.exit(1)
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
        sys.exit(1)
    return data


def listar_pipes():
    # API atual do Pipefy: organizations é query root; pipes vêm de organization(id)
    query_orgs = """
    {
      organizations {
        id
        name
      }
    }
    """
    data_orgs = gql(query_orgs)
    orgs = data_orgs.get("data", {}).get("organizations") or []
    pipes = []
    for org in orgs:
        oid = org.get("id")
        if not oid:
            continue
        query_pipes = f"""
        {{
          organization(id: {oid}) {{
            pipes {{
              id
              name
            }}
          }}
        }}
        """
        data_pipes = gql(query_pipes)
        org_data = data_pipes.get("data", {}).get("organization") or {}
        pipes.extend(org_data.get("pipes") or [])
    return pipes


def detalhar_pipe(pipe_id: str):
    query = f"""
    {{
      pipe(id: {pipe_id}) {{
        id
        name
        phases {{
          id
          name
          fields {{
            id
            label
            type
          }}
        }}
      }}
    }}
    """
    data = gql(query)
    return data["data"]["pipe"]


def normalizar(texto: str) -> str:
    import unicodedata
    nfkd = unicodedata.normalize("NFD", texto.upper())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).strip()


def main():
    print("=" * 60)
    print("  DESCOBERTA DE IDs DO PIPEFY")
    print("=" * 60)

    print("\n[*] Buscando lista de pipes...\n")
    todos_pipes = listar_pipes()

    if not todos_pipes:
        print("Nenhum pipe encontrado. Verifique o token.")
        sys.exit(1)

    print(f"   Encontrados {len(todos_pipes)} pipes na sua organizacao.\n")
    print("   Todos os pipes encontrados:")
    for p in todos_pipes:
        print(f"     [{p['id']}] {p['name']}")

    resultado = {}

    for pipe in todos_pipes:
        nome_norm = normalizar(pipe["name"])
        pipe_alvo = None
        for alvo in PIPES_ALVO:
            if alvo in nome_norm or nome_norm in alvo:
                pipe_alvo = alvo
                break

        if not pipe_alvo:
            continue

        print(f"\n[>] Detalhando pipe: [{pipe_alvo}] ID={pipe['id']} Nome='{pipe['name']}'")
        detalhes = detalhar_pipe(pipe["id"])

        fases_map = {}
        for fase in detalhes.get("phases", []):
            fases_map[fase["id"]] = {
                "nome": fase["name"],
                "campos": [
                    {"id": f["id"], "label": f["label"], "tipo": f["type"]}
                    for f in fase.get("fields", [])
                ],
            }
            print(f"   Fase [{fase['id']}]: {fase['name']} ({len(fase.get('fields', []))} campos)")

        resultado[pipe_alvo] = {
            "pipe_id": pipe["id"],
            "pipe_nome": pipe["name"],
            "fases": fases_map,
        }

    if not resultado:
        print("\n[!] Nenhum dos pipes alvo foi encontrado pelo nome.")
        print("    Pipes disponiveis acima. Adicione os IDs manualmente ao .env:")
        print("    PIPE_ID_COMERCIAL=<id>")
        print("    PIPE_ID_COMPLIANCE=<id>")
        print("    PIPE_ID_JURIDICO=<id>")
        print("    PIPE_ID_FINANCEIRO=<id>")
        sys.exit(1)

    # Salva JSON com todos os IDs
    out_path = Path(__file__).parent / "pipefy_ids.json"
    out_path.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] IDs salvos em: {out_path}")

    # Exibe instrucoes para o .env
    print("\n" + "=" * 60)
    print("  ADICIONE AO SEU .env:")
    print("=" * 60)
    for alvo, dados in resultado.items():
        print(f"PIPE_ID_{alvo}={dados['pipe_id']}")

    print("\n" + "=" * 60)
    print("  PROXIMO PASSO: rode python 2_setup_supabase.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
