#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cria um usuario do painel web (autenticacao por usuario individual — ver
docs/adr/006-autenticacao-usuarios-individuais.md e
specs/autenticacao_painel.md).

Nao ha autocadastro no painel: usuarios so sao criados por quem tem
acesso a este script.

Uso:
  python scripts/criar_usuario.py <nome_usuario>
  (a senha e pedida de forma oculta, via getpass; nunca passar a senha
  como argumento de linha de comando — ficaria no historico do shell)

Pre-requisito: rodar scripts/aplicar_migrations.py antes, pelo menos uma
vez, para o banco e a tabela usuario existirem.

Dependencia: biblioteca padrao (sqlite3, getpass) + werkzeug.security
(ja vem com o Flask — ver requirements.txt e docs/adr/006).
"""

import getpass
import os
import sqlite3
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from db import conectar  # noqa: E402

from werkzeug.security import generate_password_hash

SENHA_MIN_CARACTERES = 8


def main():
    if len(sys.argv) != 2:
        print("Uso: python scripts/criar_usuario.py <nome_usuario>")
        sys.exit(1)

    nome_usuario = sys.argv[1].strip()
    if not nome_usuario:
        print("[FALHA] Nome de usuario nao pode ser vazio.")
        sys.exit(1)

    senha = getpass.getpass("Senha: ")
    confirmacao = getpass.getpass("Confirme a senha: ")
    if senha != confirmacao:
        print("[FALHA] As senhas nao coincidem.")
        sys.exit(1)
    if len(senha) < SENHA_MIN_CARACTERES:
        print(f"[FALHA] Senha precisa ter pelo menos {SENHA_MIN_CARACTERES} caracteres.")
        sys.exit(1)

    senha_hash = generate_password_hash(senha)
    agora = datetime.now(timezone.utc).isoformat()

    try:
        with conectar() as conn:
            conn.execute(
                "INSERT INTO usuario (nome_usuario, senha_hash, ativo, criado_em) VALUES (?, ?, 1, ?)",
                (nome_usuario, senha_hash, agora),
            )
        print(f"[OK] Usuario '{nome_usuario}' criado.")
    except sqlite3.IntegrityError:
        print(f"[FALHA] Ja existe um usuario com o nome '{nome_usuario}'.")
        sys.exit(1)
    except sqlite3.OperationalError as e:
        print(f"[FALHA] {e}. Rode 'python scripts/aplicar_migrations.py' primeiro.")
        sys.exit(1)


if __name__ == "__main__":
    main()
