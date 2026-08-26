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
        "output": ["eventid", "clock", "name", "severity", "r_eventid"],
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


def filtrar_por_hosts(eventos: list[dict], hosts: set[str] | None) -> list[dict]:
    """Filtra eventos pelos hosts informados (por nome do host).

    `hosts` None ou vazio significa nao filtrar (todos os hosts — ver
    specs/exportacao_relatorio.md). Um evento entra se PELO MENOS UM dos
    hosts que ele afeta estiver em `hosts` (mesma semantica de "afeta o
    host", nao "afeta so o host").
    """
    if not hosts:
        return eventos
    return [ev for ev in eventos
            if any(h.get("name") in hosts for h in ev.get("hosts", []))]


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


def eventos_do_grupo(eventos: list[dict], visao: str, chave: str, desde_ts: int) -> list[dict]:
    """Filtra os eventos ja buscados para os que pertencem a um grupo
    especifico do ranking — mesma chave de agrupamento que agregar()
    (visao "problema", chave = nome) ou agregar_por_host() (visao
    "host", chave = host) usam, para o total do historico bater com o
    total mostrado na linha do ranking (ver specs/historico_ocorrencias.md).

    Nao busca nada novo na API — so filtra a lista ja fornecida.
    Devolve ordenado do mais recente para o mais antigo.
    """
    resultado = []
    for ev in eventos:
        clock = int(ev["clock"])
        if clock < desde_ts:
            continue
        if visao == "host":
            pertence = chave in {h.get("name", "?") for h in ev.get("hosts", [])}
        else:
            pertence = (ev.get("name") or "(sem nome)") == chave
        if pertence:
            resultado.append(ev)
    resultado.sort(key=lambda e: int(e["clock"]), reverse=True)
    return resultado


def buscar_resolucoes(r_eventids: list[str], token: str) -> dict[str, int]:
    """Busca o horario (clock) de cada evento de recuperacao (OK) dado o
    seu eventid (campo "r_eventid" do evento de problema original).

    A API do Zabbix nao devolve o horario de resolucao direto no
    event.get do evento de problema (so o eventid da recuperacao, em
    "r_eventid") — por isso uma segunda chamada busca esses eventos de
    recuperacao pelo proprio eventid (ver contexto/api.md). Nunca
    levanta excecao: falha na chamada devolve dict vazio, e o chamador
    mostra as ocorrencias sem duracao em vez de falhar a pagina inteira
    (ver specs/historico_ocorrencias.md, casos extremos).
    """
    ids = sorted({r for r in r_eventids if r and r != "0"})
    if not ids:
        return {}
    r = call("event.get", {"output": ["eventid", "clock"], "eventids": ids}, token=token)
    if "error" in r or "__error__" in r:
        return {}
    return {e["eventid"]: int(e["clock"]) for e in r.get("result", [])}


def historico(eventos: list[dict], visao: str, chave: str, desde_ts: int, token: str) -> list[dict]:
    """Monta o historico de ocorrencias de um grupo (ver specs/historico_ocorrencias.md):
    cada item tem "inicio" (clock), "fim" (clock da resolucao, ou None
    se ainda aberta), "duracao_segundos" (ou None) e "severidade".
    """
    grupo = eventos_do_grupo(eventos, visao, chave, desde_ts)
    resolucoes = buscar_resolucoes([ev.get("r_eventid", "0") for ev in grupo], token)
    itens = []
    for ev in grupo:
        inicio = int(ev["clock"])
        reid = ev.get("r_eventid", "0")
        fim = resolucoes.get(reid) if reid and reid != "0" else None
        itens.append({
            "inicio": inicio,
            "fim": fim,
            "duracao_segundos": (fim - inicio) if fim is not None else None,
            "severidade": int(ev.get("severity", 0)),
        })
    return itens


def fmt_ts(ts):
    """Formata timestamp unix para dd/mm/aaaa hh:mm (padroes/convencoes.md)."""
    return datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")


def fmt_duracao(segundos: int) -> str:
    """Formata uma duracao em segundos de forma humana (ex.: 44s, 5m07s, 1h16m)."""
    if segundos < 60:
        return f"{segundos}s"
    minutos, seg = divmod(segundos, 60)
    if minutos < 60:
        return f"{minutos}m{seg:02d}s"
    horas, minutos = divmod(minutos, 60)
    return f"{horas}h{minutos:02d}m"
