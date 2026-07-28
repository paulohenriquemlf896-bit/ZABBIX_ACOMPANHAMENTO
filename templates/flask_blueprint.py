#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEMPLATE: blueprint Flask para uma area do painel (ex.: relatorios,
hosts, notificacoes).

Como usar este template:
  1. Copie para src/web/blueprints/nome_da_area.py
  2. Troque NOME_AREA pelo nome real (ex.: "relatorios").
  3. A rota chama SOMENTE a camada de servico (src/web/services/) —
     nunca a API do Zabbix diretamente daqui.
  4. Toda resposta JSON segue o envelope de padroes/padrao_respostas_api.md.
  5. Registre o blueprint em src/web/app.py:
       from web.blueprints.nome_da_area import bp_nome_area
       app.register_blueprint(bp_nome_area)

Ver prompts/tarefas/backend.txt e prompts/tarefas/frontend.txt.
"""

from flask import Blueprint, jsonify, render_template, request

# from web.services.nome_area_service import buscar_dados  # TEMPLATE

bp_nome_area = Blueprint("nome_area", __name__, url_prefix="/nome-area")

PERIODOS_VALIDOS = {"hoje", "7d", "30d", "365d"}  # whitelist — nunca aceitar livre


@bp_nome_area.route("/", methods=["GET"])
def pagina():
    """Renderiza a tela principal (HTML)."""
    periodo = request.args.get("periodo", "7d")
    if periodo not in PERIODOS_VALIDOS:
        periodo = "7d"
    return render_template("nome_area/index.html", periodo=periodo)


@bp_nome_area.route("/api/dados", methods=["GET"])
def api_dados():
    """Endpoint JSON interno consumido pelo front-end da pagina."""
    periodo = request.args.get("periodo", "7d")
    if periodo not in PERIODOS_VALIDOS:
        return jsonify({"ok": False, "dados": None,
                         "erro": "Parametro 'periodo' invalido."}), 400

    try:
        # dados = buscar_dados(periodo)  # TEMPLATE: chamar a camada de servico
        dados = {}
        return jsonify({"ok": True, "dados": dados, "erro": None})
    except Exception as e:  # noqa: BLE001 — borda HTTP: nunca vaza stacktrace
        # TODO(logging): registrar e.args em logger.error antes de responder
        return jsonify({"ok": False, "dados": None,
                         "erro": "Nao foi possivel obter os dados. Tente novamente."}), 500
