#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de src/db.py. 100% offline: usa SQLite em memoria
(prompts/politicas/testes.txt).

Uso:
  python -m unittest discover src/tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import db  # noqa: E402


class TestConectar(unittest.TestCase):

    def test_devolve_conexao_utilizavel(self):
        conn = db.conectar(":memory:")
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO t DEFAULT VALUES")
        linha = conn.execute("SELECT id FROM t").fetchone()
        self.assertEqual(linha["id"], 1)  # row_factory=sqlite3.Row permite acesso por nome
        conn.close()

    def test_foreign_keys_ligado(self):
        conn = db.conectar(":memory:")
        valor = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        self.assertEqual(valor, 1)
        conn.close()


if __name__ == "__main__":
    unittest.main()
