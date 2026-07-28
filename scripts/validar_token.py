#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Valida um API token do Zabbix 7.4.

Faz 3 checagens:
  1. Conecta no endpoint e confirma a versao da API (nao precisa de token).
  2. Usa o token para uma chamada autenticada leve (host.get, limit 1).
  3. Mostra qual usuario esta por tras do token e suas permissoes basicas.

Uso:
  python scripts/validar_token.py
  (ou defina as variaveis de ambiente ZBX_URL e ZBX_TOKEN)

Dependencia: apenas a biblioteca padrao do Python (urllib), via
src/zbx_api.py — o cliente unico de acesso a API deste projeto (ver
prompts/politicas/arquitetura.txt).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from zbx_api import call, ZBX_URL, ZBX_TOKEN  # noqa: E402 — import apos sys.path


def ok(msg):
    print(f"  [OK]   {msg}")


def fail(msg):
    print(f"  [FALHA] {msg}")


def main():
    print("=" * 60)
    print("  Validacao de API token - Zabbix 7.4")
    print("=" * 60)
    print(f"Endpoint: {ZBX_URL}")
    print()

    if "SEU_ZABBIX" in ZBX_URL:
        fail("Edite ZBX_URL no topo do script (ou defina a env var ZBX_URL).")
        sys.exit(1)
    if "COLE_SEU_TOKEN" in ZBX_TOKEN or not ZBX_TOKEN:
        fail("Edite ZBX_TOKEN no topo do script (ou defina a env var ZBX_TOKEN).")
        sys.exit(1)

    # ---- 1. Versao da API (sem token) -----------------------------------
    print("1) Conexao e versao da API...")
    r = call("apiinfo.version")
    if "result" in r:
        ok(f"Servidor respondeu. Versao da API: {r['result']}")
    else:
        fail(f"Nao conseguiu obter a versao: {r}")
        print("\nToken NAO validado (servidor inacessivel).")
        sys.exit(1)
    print()

    # ---- 2. Chamada autenticada com o token -----------------------------
    print("2) Autenticacao com o token (host.get, limit 1)...")
    r = call("host.get", {"output": ["hostid", "host"], "limit": 1}, token=ZBX_TOKEN)
    if "result" in r:
        n = len(r["result"])
        ok(f"Token valido e autenticado. Hosts visiveis (amostra): {n}")
        if n:
            h = r["result"][0]
            print(f"         ex.: hostid={h.get('hostid')} host={h.get('host')}")
    elif "error" in r:
        fail(f"Token rejeitado: {r['error'].get('data') or r['error'].get('message')}")
        print("\nToken INVALIDO ou sem permissao.")
        sys.exit(1)
    else:
        fail(f"Resposta inesperada: {r}")
        sys.exit(1)
    print()

    # ---- 3. Quem e o dono do token / permissoes -------------------------
    print("3) Usuario associado ao token...")
    r = call("user.get", {"output": ["userid", "username", "name", "surname", "roleid"]}, token=ZBX_TOKEN)
    if "result" in r and r["result"]:
        u = r["result"][0]
        nome = f"{u.get('name', '')} {u.get('surname', '')}".strip()
        ok(f"Usuario: {u.get('username')} ({nome or 's/ nome'}) | userid={u.get('userid')} roleid={u.get('roleid')}")
    elif "error" in r:
        # Nem todo usuario tem permissao de ler user.get; nao e um erro fatal.
        print(f"  [info] Nao foi possivel ler dados do usuario (permissao limitada): "
              f"{r['error'].get('data') or r['error'].get('message')}")
    print()

    print("=" * 60)
    print("  RESULTADO: token VALIDO e funcionando.")
    print("=" * 60)


if __name__ == "__main__":
    main()
