"""
SCRIPT PRINCIPAL: Executa todos os passos da integração em sequência.
Uso: python run_all.py
"""

import io
import subprocess
import sys
from pathlib import Path

# Força UTF-8 no stdout para evitar UnicodeEncodeError no Windows (cp1252)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
SCRIPTS = [
    ("0_export_required_fields_from_excel.py", "Export do mapeamento de campos por fase (planilha → JSON)"),
    ("1_discover_pipefy.py",  "Descoberta de IDs do Pipefy"),
    ("2_setup_supabase.py",   "Setup do Supabase (tabela + Edge Function)"),
    ("3_create_webhooks.py",  "Criação de Webhooks no Pipefy"),
]


def checar_env():
    env_path = BASE / ".env"
    if not env_path.exists():
        print("\n❌ Arquivo .env não encontrado!")
        print(f"   Copie o template: cp {BASE}/.env.example {BASE}/.env")
        print("   Preencha com suas credenciais e rode novamente.\n")
        sys.exit(1)

    conteudo = env_path.read_text(encoding="utf-8")
    for linha in conteudo.splitlines():
        if linha.strip().startswith("PIPEFY_TOKEN=") and "seu_personal" in linha:
            print("\n❌ PIPEFY_TOKEN não foi preenchido no .env!")
            print("   Gere em: app.pipefy.com → Perfil → Tokens de API\n")
            sys.exit(1)
        if linha.strip().startswith("SUPABASE_URL=") and "xxxx" in linha:
            print("\n❌ SUPABASE_URL não foi preenchida no .env!")
            print("   Encontre em: supabase.com → Projeto → Settings → API\n")
            sys.exit(1)


def rodar(script: str, descricao: str) -> bool:
    print(f"\n{'=' * 60}")
    print(f"  ETAPA: {descricao}")
    print(f"{'=' * 60}\n")
    result = subprocess.run(
        [sys.executable, str(BASE / script)],
        check=False,
    )
    if result.returncode != 0:
        print(f"\n❌ Falha na etapa '{descricao}' (código {result.returncode})")
        return False
    return True


def main():
    print("\n" + "=" * 60)
    print("  INTEGRAÇÃO PIPEFY → SUPABASE → LOOKER STUDIO")
    print("=" * 60)
    print("\n  Verificando configurações...\n")
    checar_env()
    print("  ✅ .env encontrado!")

    for script, descricao in SCRIPTS:
        ok = rodar(script, descricao)
        if not ok:
            print(f"\n⚠️  Interrompido em '{descricao}'.")
            print("   Corrija o erro acima e rode este script novamente,")
            print(f"   ou rode diretamente: python {script}\n")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("  ✅ INTEGRAÇÃO CONFIGURADA COM SUCESSO!")
    print("=" * 60)
    print("""
  Resumo do que foi feito:
  ✔ Tabela 'eventos' criada no Supabase
  ✔ Edge Function 'pipefy-events' deployada
  ✔ Webhooks criados nos 4 pipes do Pipefy

  Agora, toda vez que um card for criado ou movido
  de fase no Pipefy, os dados aparecerão automaticamente
  na tabela 'eventos' do Supabase — pronta para o Looker Studio.
    """)


if __name__ == "__main__":
    main()
