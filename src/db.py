#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Acesso ao banco proprio do projeto (SQLite) — ver
prompts/tarefas/banco_de_dados.txt.

Hoje guarda so a tabela de usuarios do painel web (autenticacao — ver
docs/adr/006-autenticacao-usuarios-individuais.md). Esquema criado/
atualizado por scripts/aplicar_migrations.py, nunca por este modulo.
"""

import os
import sqlite3

CAMINHO_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dados", "acompanhamento.db")


def conectar(caminho: str = None) -> sqlite3.Connection:
    """Abre conexao com o banco, com foreign_keys ligado e
    row_factory=sqlite3.Row (prompts/tarefas/banco_de_dados.txt, item 5).

    `caminho` sobrescreve CAMINHO_DB — usado pelos testes para apontar
    para um banco isolado (ex.: ":memory:").
    """
    conn = sqlite3.connect(caminho or CAMINHO_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn
