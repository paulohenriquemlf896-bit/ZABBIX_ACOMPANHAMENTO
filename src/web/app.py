#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Painel web (Flask) — visao de problemas recorrentes do Zabbix.

Consolida o que hoje e gerado como HTML estatico por
scripts/relatorio_problemas.py em uma tela navegavel, sempre atualizada
(cache de 60s — ver src/web/services/relatorios.py). A pagina se
autoatualiza no mesmo intervalo do cache (meta refresh — ver
prompts/tarefas/frontend.txt, item 18, "painel de TV"), preservando
periodo e visao selecionados na querystring. Duas visoes de ranking (por
problema ou por host — ver specs/ranking_por_host.md), cada uma com um
grafico de barras alem da tabela detalhada. Sem autenticacao (ver
specs/dashboard.md e docs/adr/005-painel-web-flask.md).

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
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from flask import Flask, render_template, request  # noqa: E402

from api import bp_api  # noqa: E402
from logging_util import configurar_logging  # noqa: E402
from relatorios_service import (  # noqa: E402
    PERIODOS, TITULOS_PERIODO, SEV_NOME, SEV_COR, fmt_ts, fmt_duracao,
)
from services.relatorios import (  # noqa: E402
    dados_periodo, historico_grupo, TTL_SEGUNDOS, VISOES, CHAVE_MAX_CARACTERES,
)
from zbx_api import call  # noqa: E402

# =========================================================================
# CONFIGURACAO
# =========================================================================
PAINEL_HOST = os.environ.get("PAINEL_HOST", "127.0.0.1")
PAINEL_PORT = int(os.environ.get("PAINEL_PORT", "8080"))
TOP_N = 20            # quantas linhas a tabela mostra
TOP_N_GRAFICO = 10    # quantas barras o grafico de ranking mostra (ver specs/ranking_por_host.md)
LIMIAR_LENTIDAO_SEGUNDOS = 5  # acima disso, loga WARNING (prompts/politicas/monitoramento.txt, item 7)
# =========================================================================

TITULOS_VISAO = {"problema": "Por problema", "host": "Por host"}

log = configurar_logging("painel_web")

app = Flask(__name__)
app.register_blueprint(bp_api)


def montar_grafico_ranking(ranking: list[dict], visao: str) -> list[dict]:
    """Converte o ranking (ja formatado por dados_periodo) em itens prontos
    para o grafico de barras: rotulo (nome do problema ou host, conforme a
    visao) e largura_pct relativa ao MAIOR valor exibido — nao ao total
    geral do periodo, para o grafico usar toda a largura disponivel em
    vez de barras minusculas quando o total for grande (ver
    prompts/tarefas/frontend.txt e a skill de visualizacao de dados).
    """
    subset = ranking[:TOP_N_GRAFICO]
    if not subset:
        return []
    maior = max(g["ocorrencias"] for g in subset)
    chave_rotulo = "host" if visao == "host" else "nome"
    return [
        {
            "rotulo": g[chave_rotulo],
            "ocorrencias": g["ocorrencias"],
            "severidade": g["severidade"],
            "largura_pct": (g["ocorrencias"] / maior * 100) if maior else 0,
        }
        for g in subset
    ]


def montar_grafico_dias(itens: list[dict]) -> list[dict]:
    """Agrupa o historico de ocorrencias por dia (dd/mm) para o
    mini-grafico de frequencia do drill-down — ajuda a identificar dias
    de pico (foi exatamente essa pergunta que motivou a funcionalidade,
    ver docs/CHANGELOG.md e specs/historico_ocorrencias.md).
    """
    if not itens:
        return []
    contagem = {}
    ordem = []
    for it in reversed(itens):  # itens vem do mais recente pro mais antigo; queremos ordem cronologica
        dia = datetime.fromtimestamp(it["inicio"]).strftime("%d/%m")
        if dia not in contagem:
            ordem.append(dia)
        contagem[dia] = contagem.get(dia, 0) + 1
    maior = max(contagem.values())
    return [
        {"dia": d, "ocorrencias": contagem[d], "largura_pct": contagem[d] / maior * 100}
        for d in ordem
    ]


def resumo_historico(itens: list[dict]) -> dict:
    """Resumo estatistico do historico de ocorrencias: total, quantas
    ainda estao abertas, duracao media/minima/maxima das resolvidas (ja
    formatadas para exibicao) — pronto para o template."""
    total = len(itens)
    duracoes = [it["duracao_segundos"] for it in itens if it["duracao_segundos"] is not None]
    resumo = {"total": total, "abertas": total - len(duracoes), "resolvidas": len(duracoes),
              "duracao_media": None, "duracao_min": None, "duracao_max": None}
    if duracoes:
        resumo["duracao_media"] = fmt_duracao(round(sum(duracoes) / len(duracoes)))
        resumo["duracao_min"] = fmt_duracao(min(duracoes))
        resumo["duracao_max"] = fmt_duracao(max(duracoes))
    return resumo


@app.route("/", methods=["GET"])
def pagina_relatorios():
    periodo = request.args.get("periodo", "7d")
    if periodo not in PERIODOS:
        periodo = "7d"

    visao = request.args.get("visao", "problema")
    if visao not in VISOES:
        visao = "problema"

    v = call("apiinfo.version")

    contexto = {
        "periodos": PERIODOS,
        "titulos_periodo": TITULOS_PERIODO,
        "periodo_atual": periodo,
        "visoes": VISOES,
        "titulos_visao": TITULOS_VISAO,
        "visao_atual": visao,
        "sev_nome": SEV_NOME,
        "sev_cor": SEV_COR,
        "top_n": TOP_N,
        "versao_api": v.get("result", "?"),
        "gerado": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "auto_refresh_segundos": TTL_SEGUNDOS,
        "dados": None,
        "erro": None,
        "grafico_ranking": [],
    }

    inicio = time.monotonic()
    try:
        dados = dados_periodo(periodo, visao)
    except RuntimeError as e:
        log.warning("Falha ao obter dados do Zabbix (periodo=%s, visao=%s): %s", periodo, visao, e)
        contexto["erro"] = str(e)
        return render_template("index.html", **contexto)
    duracao = time.monotonic() - inicio
    if duracao > LIMIAR_LENTIDAO_SEGUNDOS:
        log.warning("Consulta lenta: periodo=%s visao=%s levou %.1fs", periodo, visao, duracao)

    for g in dados["ranking"]:
        g["ultima_vez_fmt"] = fmt_ts(g["ultima_vez"])
    contexto["dados"] = dados
    contexto["grafico_ranking"] = montar_grafico_ranking(dados["ranking"], visao)
    return render_template("index.html", **contexto)


@app.route("/historico", methods=["GET"])
def pagina_historico():
    """Drill-down de uma linha do ranking: quando cada ocorrencia comecou,
    quando terminou e quanto durou — ver specs/historico_ocorrencias.md."""
    periodo = request.args.get("periodo", "7d")
    if periodo not in PERIODOS:
        periodo = "7d"

    visao = request.args.get("visao", "problema")
    if visao not in VISOES:
        visao = "problema"

    chave = request.args.get("chave", "")

    contexto = {
        "periodos": PERIODOS,
        "titulos_periodo": TITULOS_PERIODO,
        "periodo_atual": periodo,
        "visoes": VISOES,
        "titulos_visao": TITULOS_VISAO,
        "visao_atual": visao,
        "chave": chave,
        "sev_nome": SEV_NOME,
        "sev_cor": SEV_COR,
        "auto_refresh_segundos": TTL_SEGUNDOS,
        "itens": [],
        "erro": None,
        "grafico_dias": [],
        "resumo": None,
    }

    if not chave or len(chave) > CHAVE_MAX_CARACTERES:
        contexto["erro"] = "Nenhum problema/host valido selecionado."
        return render_template("historico.html", **contexto)

    inicio = time.monotonic()
    try:
        itens = historico_grupo(periodo, visao, chave)
    except RuntimeError as e:
        log.warning("Falha ao obter historico (periodo=%s, visao=%s, chave=%s): %s", periodo, visao, chave, e)
        contexto["erro"] = str(e)
        return render_template("historico.html", **contexto)
    duracao = time.monotonic() - inicio
    if duracao > LIMIAR_LENTIDAO_SEGUNDOS:
        log.warning("Historico lento: periodo=%s visao=%s chave=%s levou %.1fs", periodo, visao, chave, duracao)

    for it in itens:
        it["inicio_fmt"] = fmt_ts(it["inicio"])
        it["fim_fmt"] = fmt_ts(it["fim"]) if it["fim"] is not None else None
        it["duracao_fmt"] = fmt_duracao(it["duracao_segundos"]) if it["duracao_segundos"] is not None else None

    contexto["itens"] = itens
    contexto["grafico_dias"] = montar_grafico_dias(itens)
    contexto["resumo"] = resumo_historico(itens)
    return render_template("historico.html", **contexto)


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
    log.info("Painel disponivel em http://%s:%s", PAINEL_HOST, PAINEL_PORT)
    serve(app, host=PAINEL_HOST, port=PAINEL_PORT)
