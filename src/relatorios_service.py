#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camada de dominio/servico do relatorio de problemas recorrentes.

Reune a logica de busca e agregacao de eventos usada tanto por
scripts/relatorio_problemas.py (CLI) quanto pelo painel web
(src/web/services/relatorios.py) — extraida para nao duplicar entre os
dois (ver docs/adr/005-painel-web-flask.md e specs/dashboard.md, item 3).

Nao conhece HTTP nem formato de tela (ver prompts/politicas/arquitetura.txt,
camada de dominio/servico): recebe parametros, devolve dados, nunca
imprime nem encerra o processo. Regras de negocio formais (o que e
recorrencia, agrupamento, janelas, severidade) documentadas em
contexto/regras_negocio.md — este modulo e a implementacao delas.

Dependencia: apenas a biblioteca padrao do Python, via src/zbx_api.py.
"""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zbx_api import call  # noqa: E402 — import apos sys.path

# =========================================================================
# CONFIGURACAO
# =========================================================================
MAX_EVENTOS = 100000  # teto de eventos puxados por consulta (protege contra respostas gigantes)
# =========================================================================

SEV_NOME = {0: "Nao classif.", 1: "Informacao", 2: "Aviso", 3: "Media", 4: "Alta", 5: "Desastre"}
SEV_COR = {0: "#97AAB3", 1: "#7499FF", 2: "#FFC859", 3: "#FFA059", 4: "#E97659", 5: "#E45959"}

# Periodos padrao do projeto (ver contexto/regras_negocio.md, "Janelas de
# tempo padrao"). PERIODOS e a whitelist usada tambem para validar
# querystring no painel web (prompts/politicas/seguranca.txt, item 9).
PERIODOS = ["hoje", "7d", "30d", "365d"]
TITULOS_PERIODO = {
    "hoje": "Hoje",
    "7d": "Ultimos 7 dias",
    "30d": "Ultimos 30 dias",
    "365d": "Ultimos 365 dias",
}


def desde_periodo(periodo, agora=None):
    """Devolve o datetime de inicio (>=) para um periodo valido (ver PERIODOS).

    Levanta ValueError para periodo fora da whitelist — o chamador decide
    como tratar (CLI: nao deveria acontecer, e uso interno; web: cair no
    default antes de chegar aqui, nunca propagar o erro para o usuario).
    """
    agora = agora or datetime.now()
    if periodo == "hoje":
        return datetime(agora.year, agora.month, agora.day)
    if periodo == "7d":
        return agora - timedelta(days=7)
    if periodo == "30d":
        return agora - timedelta(days=30)
    if periodo == "365d":
        return agora - timedelta(days=365)
    raise ValueError(f"periodo invalido: {periodo!r}")


def janelas(agora=None):
    """Devolve as 4 janelas padrao do projeto como [(titulo, desde), ...],
    da mais recente para a mais ampla — usado pelo relatorio CLI, que
    mostra todas de uma vez."""
    agora = agora or datetime.now()
    return [(TITULOS_PERIODO[p], desde_periodo(p, agora)) for p in PERIODOS]


def buscar_eventos(desde_ts, token, limite=None):
    """Busca eventos de PROBLEMA (value=1) desde o timestamp dado.

    `limite` sobrescreve MAX_EVENTOS para esta chamada (ver
    prompts/politicas/arquitetura.txt item 6 — extensivel por parametro,
    sem duplicar a funcao). Nunca levanta excecao nem encerra o processo
    (camada de dominio nao decide isso). Devolve sempre uma tupla
    (eventos, erro): erro e None em sucesso, ou uma mensagem pronta para
    exibir (com prefixo "event.get: " quando for erro de aplicacao do
    Zabbix, para manter a mensagem historica dos scripts).
    """
    r = call("event.get", {
        "output": ["eventid", "clock", "name", "severity"],
        "source": 0,          # triggers
        "object": 0,          # trigger
        "value": 1,           # 1 = PROBLEM (ignora as recuperacoes/OK)
        "time_from": desde_ts,
        "selectHosts": ["hostid", "name"],
        "sortfield": "clock",
        "sortorder": "DESC",
        "limit": limite or MAX_EVENTOS,
    }, token=token)
    if "error" in r:
        msg = r["error"].get("data") or r["error"].get("message")
        return [], f"event.get: {msg}"
    if "__error__" in r:
        return [], r["__error__"]
    return r.get("result", []), None


def agregar(eventos, desde_ts):
    """Agrupa por nome do problema, contando ocorrencias no periodo (>= desde_ts).

    Devolve (ranking, total, por_sev): ranking ordenado do mais frequente
    para o menos frequente; por_sev e um dict severidade -> contagem.
    """
    grupos = {}
    total = 0
    por_sev = {s: 0 for s in SEV_NOME}
    for ev in eventos:
        clock = int(ev["clock"])
        if clock < desde_ts:
            continue
        total += 1
        sev = int(ev.get("severity", 0))
        por_sev[sev] = por_sev.get(sev, 0) + 1
        nome = ev.get("name") or "(sem nome)"
        g = grupos.get(nome)
        if g is None:
            g = grupos[nome] = {"nome": nome, "count": 0, "sev": sev,
                                "hosts": set(), "primeiro": clock, "ultimo": clock}
        g["count"] += 1
        g["sev"] = max(g["sev"], sev)
        for h in ev.get("hosts", []):
            g["hosts"].add(h.get("name", "?"))
        g["primeiro"] = min(g["primeiro"], clock)
        g["ultimo"] = max(g["ultimo"], clock)
    ranking = sorted(grupos.values(), key=lambda x: x["count"], reverse=True)
    return ranking, total, por_sev


def agregar_por_host(eventos: list[dict], desde_ts: int) -> tuple[list[dict], int, dict[int, int]]:
    """Agrupa por host afetado, contando ocorrencias no periodo (>= desde_ts).

    Ver specs/ranking_por_host.md para as regras de negocio completas.
    Resumo: evento com multiplos hosts conta para cada host envolvido;
    evento sem host associado nao entra no ranking (mas ainda soma no
    `total` devolvido, igual a agregar()). Devolve (ranking, total,
    por_sev) — mesmo shape de agregar(), trocando "nome"/"hosts" por
    "host"/"problemas".
    """
    grupos = {}
    total = 0
    por_sev = {s: 0 for s in SEV_NOME}
    for ev in eventos:
        clock = int(ev["clock"])
        if clock < desde_ts:
            continue
        total += 1
        sev = int(ev.get("severity", 0))
        por_sev[sev] = por_sev.get(sev, 0) + 1
        nome_problema = ev.get("name") or "(sem nome)"
        for h in ev.get("hosts", []):
            host = h.get("name", "?")
            g = grupos.get(host)
            if g is None:
                g = grupos[host] = {"host": host, "count": 0, "sev": sev,
                                     "problemas": set(), "primeiro": clock, "ultimo": clock}
            g["count"] += 1
            g["sev"] = max(g["sev"], sev)
            g["problemas"].add(nome_problema)
            g["primeiro"] = min(g["primeiro"], clock)
            g["ultimo"] = max(g["ultimo"], clock)
    ranking = sorted(grupos.values(), key=lambda x: x["count"], reverse=True)
    return ranking, total, por_sev


def fmt_ts(ts):
    """Formata timestamp unix para dd/mm/aaaa hh:mm (padroes/convencoes.md)."""
    return datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
