#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Painel web (Flask) — visao de problemas recorrentes do Zabbix.

Consolida o que hoje e gerado como HTML estatico por
scripts/relatorio_problemas.py em uma tela navegavel, sempre atualizada
(cache de 60s — ver src/web/services/relatorios.py). Escopo inicial: uma
unica visao, sem autenticacao (ver specs/dashboard.md e
docs/adr/005-painel-web-flask.md).

Uso:
  python src/web/app.py
  (sobe via waitress, o mesmo modo usado em producao — nunca o servidor
  de debug do Flask, ver prompts/tarefas/backend.txt item 13)

Configuracao via variavel de ambiente (ver prompts/politicas/configuracao.txt):
  ZBX_URL, ZBX_TOKEN — obrigatorias, lidas por src/zbx_api.py
  PAINEL_HOST — default 127.0.0.1 (rede interna; nunca 0.0.0.0 sem decisao
                deliberada, ver prompts/politicas/seguranca.txt item 10)
  PAINEL_PORT — default 8080

Dependencia: flask, waitress (ver requirements.txt e
docs/adr/005-painel-web-flask.md).
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from flask import Flask, render_template, request  # noqa: E402

from api import bp_api  # noqa: E402
from relatorios_service import PERIODOS, TITULOS_PERIODO, SEV_NOME, SEV_COR, fmt_ts  # noqa: E402
from services.relatorios import dados_periodo  # noqa: E402
from zbx_api import call  # noqa: E402

# =========================================================================
# CONFIGURACAO
# =========================================================================
PAINEL_HOST = os.environ.get("PAINEL_HOST", "127.0.0.1")
PAINEL_PORT = int(os.environ.get("PAINEL_PORT", "8080"))
TOP_N = 20
# =========================================================================

app = Flask(__name__)
app.register_blueprint(bp_api)


@app.route("/", methods=["GET"])
def pagina_relatorios():
    periodo = request.args.get("periodo", "7d")
    if periodo not in PERIODOS:
        periodo = "7d"

    v = call("apiinfo.version")

    contexto = {
        "periodos": PERIODOS,
        "titulos_periodo": TITULOS_PERIODO,
        "periodo_atual": periodo,
        "sev_nome": SEV_NOME,
        "sev_cor": SEV_COR,
        "top_n": TOP_N,
        "versao_api": v.get("result", "?"),
        "gerado": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "dados": None,
        "erro": None,
    }

    try:
        dados = dados_periodo(periodo)
    except RuntimeError as e:
        contexto["erro"] = str(e)
        return render_template("index.html", **contexto)

    for g in dados["ranking"]:
        g["ultima_vez_fmt"] = fmt_ts(g["ultima_vez"])
    contexto["dados"] = dados
    return render_template("index.html", **contexto)


@app.route("/health", methods=["GET"])
def health():
    """Ver prompts/politicas/monitoramento.txt item 5-6 e
    padroes/padrao_respostas_api.md — checa conectividade real com o
    Zabbix, nao so se o processo Flask esta de pe."""
    v = call("apiinfo.version")
    alcancavel = "result" in v
    return {
        "ok": alcancavel,
        "zabbix_alcancavel": alcancavel,
        "versao_api": v.get("result", ""),
        "hora_servidor": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    from waitress import serve
    print(f"[OK] Painel disponivel em http://{PAINEL_HOST}:{PAINEL_PORT}")
    serve(app, host=PAINEL_HOST, port=PAINEL_PORT)
