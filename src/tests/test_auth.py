#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de autenticacao do painel (src/web/auth.py). Ver
docs/adr/006-autenticacao-usuarios-individuais.md e
specs/autenticacao_painel.md.

100% offline: usa um banco SQLite em memoria no lugar do arquivo real
(prompts/politicas/testes.txt).

Uso:
  python -m unittest discover src/tests
"""

import os
import sqlite3
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web"))
import auth  # noqa: E402

from werkzeug.security import generate_password_hash


def _banco_com_usuario(nome_usuario="paulo", senha="senha-forte-123", ativo=1):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE usuario (
            id INTEGER PRIMARY KEY,
            nome_usuario TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TEXT NOT NULL
        )
    """)
    conn.execute(
        "INSERT INTO usuario (nome_usuario, senha_hash, ativo, criado_em) VALUES (?, ?, ?, ?)",
        (nome_usuario, generate_password_hash(senha), ativo, "2026-08-07T00:00:00+00:00"),
    )
    conn.commit()
    return conn


class TestVerificarCredenciais(unittest.TestCase):

    @patch("auth.conectar")
    def test_senha_correta_autentica(self, mock_conectar):
        mock_conectar.return_value = _banco_com_usuario()
        self.assertTrue(auth.verificar_credenciais("paulo", "senha-forte-123"))

    @patch("auth.conectar")
    def test_senha_errada_nao_autentica(self, mock_conectar):
        mock_conectar.return_value = _banco_com_usuario()
        self.assertFalse(auth.verificar_credenciais("paulo", "senha-errada"))

    @patch("auth.conectar")
    def test_usuario_inexistente_nao_autentica(self, mock_conectar):
        mock_conectar.return_value = _banco_com_usuario()
        self.assertFalse(auth.verificar_credenciais("ninguem", "qualquer"))

    @patch("auth.conectar")
    def test_usuario_inativo_nao_autentica(self, mock_conectar):
        mock_conectar.return_value = _banco_com_usuario(ativo=0)
        self.assertFalse(auth.verificar_credenciais("paulo", "senha-forte-123"))


if __name__ == "__main__":
    unittest.main()
