#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplica as migrations pendentes do banco proprio do projeto (SQLite).

So aplica o que ainda nao foi aplicado (controlado pela tabela
esquema_versao), em ordem, dentro de uma transacao por migration. Nunca
edita uma migration ja aplicada — ver prompts/tarefas/banco_de_dados.txt.

Uso:
  python scripts/aplicar_migrations.py

Saidas:
  dados/acompanhamento.db criado/atualizado (pasta dados/ criada se nao
  existir). Imprime quais migrations foram aplicadas.

Dependencia: apenas a biblioteca padrao do Python (sqlite3).
"""

import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_MIGRATIONS = os.path.join(RAIZ, "dados", "migrations")
CAMINHO_DB = os.path.join(RAIZ, "dados", "acompanhamento.db")


def migrations_disponiveis(pasta):
    """Lista (versao, nome_arquivo) de cada migration em `pasta`, na
    ordem numerica do prefixo (NNN_descricao.sql)."""
    arquivos = sorted(f for f in os.listdir(pasta) if f.endswith(".sql"))
    resultado = []
    for nome in arquivos:
        m = re.match(r"^(\d+)_", nome)
        if m:
            resultado.append((int(m.group(1)), nome))
    return resultado


def main():
    os.makedirs(os.path.dirname(CAMINHO_DB), exist_ok=True)
    conn = sqlite3.connect(CAMINHO_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS esquema_versao (
            versao INTEGER NOT NULL,
            aplicado_em TEXT NOT NULL
        )
    """)

    aplicadas = {row[0] for row in conn.execute("SELECT versao FROM esquema_versao")}
    pendentes = [(v, n) for v, n in migrations_disponiveis(PASTA_MIGRATIONS) if v not in aplicadas]

    if not pendentes:
        print("[OK] Nenhuma migration pendente.")
        conn.close()
        return

    for versao, nome in pendentes:
        caminho = os.path.join(PASTA_MIGRATIONS, nome)
        with open(caminho, encoding="utf-8") as f:
            sql = f.read()
        print(f"[..] Aplicando {nome}...")
        try:
            with conn:
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO esquema_versao (versao, aplicado_em) VALUES (?, ?)",
                    (versao, datetime.now(timezone.utc).isoformat()),
                )
            print(f"[OK] {nome} aplicada.")
        except sqlite3.Error as e:
            print(f"[FALHA] {nome}: {e}")
            conn.close()
            sys.exit(1)

    conn.close()
    print(f"[OK] {len(pendentes)} migration(ns) aplicada(s).")


if __name__ == "__main__":
    main()
