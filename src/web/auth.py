#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autenticacao do painel web por usuario individual — ver
docs/adr/006-autenticacao-usuarios-individuais.md e
specs/autenticacao_painel.md.

Senha nunca fica em texto puro: hash via werkzeug.security (ja vem com
o Flask, nao e dependencia nova). Sessao via cookie assinado do Flask
(PAINEL_SECRET_KEY obrigatoria — ver src/web/app.py).

Duas variantes de protecao de rota:
  - login_required: para paginas HTML, redireciona para /login.
  - api_login_required: para rotas /api/..., devolve 401 JSON (nunca
    redireciona um consumidor programatico).
"""

import functools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from db import conectar  # noqa: E402

from flask import jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash


def verificar_credenciais(nome_usuario: str, senha: str) -> bool:
    """Confere usuario/senha contra o banco. Usuario inexistente ou
    inativo sempre falha, sem distinguir a mensagem (nao vazar quais
    usuarios existem — ver specs/autenticacao_painel.md, casos extremos).
    """
    with conectar() as conn:
        linha = conn.execute(
            "SELECT senha_hash, ativo FROM usuario WHERE nome_usuario = ?",
            (nome_usuario,),
        ).fetchone()
    if linha is None or not linha["ativo"]:
        return False
    return check_password_hash(linha["senha_hash"], senha)


def login_required(view):
    """Decorator para rotas de pagina: redireciona para /login (com
    ?proximo=<rota original>) se nao houver sessao ativa."""
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login", proximo=request.path))
        return view(*args, **kwargs)
    return wrapped


def api_login_required(view):
    """Decorator para rotas /api/...: devolve 401 com o envelope padrao
    (padroes/padrao_respostas_api.md) em vez de redirecionar."""
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if "usuario" not in session:
            return jsonify({"ok": False, "dados": None, "erro": "Nao autenticado."}), 401
        return view(*args, **kwargs)
    return wrapped
