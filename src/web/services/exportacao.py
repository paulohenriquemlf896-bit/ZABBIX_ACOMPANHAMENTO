#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camada de servico do painel web para a exportacao de relatorio
(Excel/PDF) — ver docs/CHANGELOG.md e specs/exportacao_relatorio.md.

Reaproveita a mesma logica de dominio do ranking "por problema"
(src/relatorios_service.py) — so acrescenta o filtro por host antes de
agregar. Nao usa cache: exportacao e sob demanda, nao a visao principal
do painel (mesma decisao ja tomada para o historico de ocorrencias).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from relatorios_service import (  # noqa: E402
    buscar_eventos, filtrar_por_hosts, agregar, desde_periodo, PERIODOS, TITULOS_PERIODO,
)
from zbx_api import call, ZBX_TOKEN  # noqa: E402


def listar_hosts() -> list[str]:
    """Lista os nomes de todos os hosts monitorados, em ordem alfabetica
    — usado para popular a tela de selecao (ver specs/exportacao_relatorio.md).
    Levanta RuntimeError em falha de comunicacao com o Zabbix.
    """
    r = call("host.get", {"output": ["host"]}, token=ZBX_TOKEN)
    if "error" in r:
        raise RuntimeError(r["error"].get("data") or r["error"].get("message"))
    if "__error__" in r:
        raise RuntimeError(r["__error__"])
    return sorted(h["host"] for h in r.get("result", []))


def dados_exportacao(periodos: list[str], hosts: list[str] | None) -> dict:
    """Para cada periodo em `periodos`, busca eventos, filtra por
    `hosts` (None/vazio = todos) e agrega por problema.

    Devolve {periodo: {"titulo":..., "ranking":..., "total":...,
    "por_severidade":...}}. Levanta ValueError se `periodos` estiver
    vazio ou tiver algo fora da whitelist; RuntimeError em falha de
    comunicacao com o Zabbix (aborta a exportacao inteira, ver
    specs/exportacao_relatorio.md, casos extremos).
    """
    if not periodos or any(p not in PERIODOS for p in periodos):
        raise ValueError(f"periodos invalidos: {periodos!r}")

    hosts_set = set(hosts) if hosts else None
    resultado = {}
    for periodo in periodos:
        desde = desde_periodo(periodo)
        desde_ts = int(desde.timestamp())
        eventos, erro = buscar_eventos(desde_ts, ZBX_TOKEN)
        if erro:
            raise RuntimeError(erro)
        eventos_filtrados = filtrar_por_hosts(eventos, hosts_set)
        ranking, total, por_sev = agregar(eventos_filtrados, desde_ts)
        resultado[periodo] = {
            "titulo": TITULOS_PERIODO[periodo],
            "desde": desde,
            "ranking": ranking,
            "total": total,
            "por_severidade": por_sev,
        }
    return resultado
