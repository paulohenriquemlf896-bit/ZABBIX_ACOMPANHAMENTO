#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desativa um usuario do painel web (revoga o acesso sem apagar o
registro — ver docs/adr/006-autenticacao-usuarios-individuais.md e
specs/autenticacao_painel.md).

Uso:
  python scripts/desativar_usuario.py <nome_usuario>

Dependencia: apenas a biblioteca padrao do Python (sqlite3).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from db import conectar  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print("Uso: python scripts/desativar_usuario.py <nome_usuario>")
        sys.exit(1)

    nome_usuario = sys.argv[1].strip()

    with conectar() as conn:
        cur = conn.execute("UPDATE usuario SET ativo = 0 WHERE nome_usuario = ?", (nome_usuario,))
        if cur.rowcount == 0:
            print(f"[FALHA] Usuario '{nome_usuario}' nao encontrado.")
            sys.exit(1)

    print(f"[OK] Usuario '{nome_usuario}' desativado.")


if __name__ == "__main__":
    main()
