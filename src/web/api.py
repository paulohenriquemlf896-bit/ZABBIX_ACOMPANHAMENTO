#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Endpoints JSON internos do painel (/api/...), seguindo o envelope de
padroes/padrao_respostas_api.md.

Rotas finas: so validam entrada e chamam a camada de servico
(src/web/services/relatorios.py) — nenhuma logica de negocio nem chamada
a API do Zabbix diretamente aqui (ver prompts/tarefas/backend.txt, item 10).
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.relatorios import dados_periodo, VISOES  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from logging_util import configurar_logging  # noqa: E402

from flask import Blueprint, jsonify, request

PERIODOS_VALIDOS = {"hoje", "7d", "30d", "365d"}  # whitelist — nunca aceitar livre (prompts/politicas/seguranca.txt, item 9)
LIMIAR_LENTIDAO_SEGUNDOS = 5  # acima disso, loga WARNING (prompts/politicas/monitoramento.txt, item 7)

log = configurar_logging("painel_web")

bp_api = Blueprint("api", __name__, url_prefix="/api")


@bp_api.route("/relatorios/dados", methods=["GET"])
def relatorios_dados():
    """Dados agregados de um periodo/visao (para uso futuro de
    atualizacao via JS, ou consumo programatico). A pagina principal ja
    renderiza os mesmos dados no servidor — ver src/web/app.py.
    `visao=problema` (default) ou `visao=host` — ver
    specs/ranking_por_host.md."""
    periodo = request.args.get("periodo", "7d")
    if periodo not in PERIODOS_VALIDOS:
        return jsonify({"ok": False, "dados": None,
                         "erro": "Parametro 'periodo' invalido."}), 400

    visao = request.args.get("visao", "problema")
    if visao not in VISOES:
        return jsonify({"ok": False, "dados": None,
                         "erro": "Parametro 'visao' invalido."}), 400

    inicio = time.monotonic()
    try:
        dados = dados_periodo(periodo, visao)
        duracao = time.monotonic() - inicio
        if duracao > LIMIAR_LENTIDAO_SEGUNDOS:
            log.warning("Consulta lenta: periodo=%s visao=%s levou %.1fs", periodo, visao, duracao)
        return jsonify({"ok": True, "dados": dados, "erro": None})
    except RuntimeError as e:
        # Falha esperada de comunicacao com o Zabbix: 200 com ok=false
        # (padroes/padrao_respostas_api.md — erro de negocio, nao 5xx).
        log.warning("Falha ao obter dados do Zabbix (periodo=%s, visao=%s): %s", periodo, visao, e)
        return jsonify({"ok": False, "dados": None, "erro": str(e)}), 200
    except Exception:  # noqa: BLE001 — borda HTTP: nunca vaza stacktrace
        log.error("Erro inesperado em /api/relatorios/dados (periodo=%s, visao=%s)", periodo, visao, exc_info=True)
        return jsonify({"ok": False, "dados": None,
                         "erro": "Nao foi possivel obter os dados. Tente novamente."}), 500
