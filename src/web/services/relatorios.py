#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camada de servico do painel web para a visao de problemas recorrentes.

Fina de proposito: so adiciona cache em memoria (TTL 60s) sobre a logica
de dominio compartilhada em src/relatorios_service.py — nao duplica busca
nem agregacao de eventos (ver docs/adr/005-painel-web-flask.md e
specs/dashboard.md, item 3).

Dependencia: apenas a biblioteca padrao do Python, via
src/relatorios_service.py e src/zbx_api.py.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from relatorios_service import buscar_eventos, agregar, agregar_por_host, desde_periodo  # noqa: E402
from zbx_api import ZBX_TOKEN  # noqa: E402

# =========================================================================
# CONFIGURACAO
# =========================================================================
TTL_SEGUNDOS = 60  # cache por periodo (prompts/politicas/performance.txt, item 7)
VISOES = ("problema", "host")
# =========================================================================

_cache = {}  # (periodo, visao) -> (timestamp_cache, resultado)


def dados_periodo(periodo: str, visao: str = "problema") -> dict:
    """Devolve os dados agregados de um periodo/visao validos, usando
    cache de 60s (ver specs/ranking_por_host.md para a visao "host").

    Devolve um dict serializavel (ranking, total, por_severidade) em
    sucesso. Item do ranking tem "nome"/"hosts" na visao "problema" ou
    "host"/"problemas" na visao "host" (ver
    src/relatorios_service.py: agregar() vs agregar_por_host()).
    Levanta RuntimeError com mensagem amigavel em falha de comunicacao
    com o Zabbix, ou ValueError se `visao` nao estiver em VISOES — nunca
    cacheia falha, para nao esconder uma indisponibilidade temporaria por
    60s (prompts/politicas/performance.txt, item 7).
    """
    if visao not in VISOES:
        raise ValueError(f"visao invalida: {visao!r}")

    chave = (periodo, visao)
    agora = time.time()
    cacheado = _cache.get(chave)
    if cacheado and (agora - cacheado[0]) < TTL_SEGUNDOS:
        return cacheado[1]

    desde = desde_periodo(periodo)
    desde_ts = int(desde.timestamp())
    eventos, erro = buscar_eventos(desde_ts, ZBX_TOKEN)
    if erro:
        raise RuntimeError(erro)

    if visao == "host":
        ranking_bruto, total, por_sev = agregar_por_host(eventos, desde_ts)
        ranking = [
            {
                "host": g["host"],
                "ocorrencias": g["count"],
                "severidade": g["sev"],
                "problemas": sorted(g["problemas"]),
                "primeira_vez": g["primeiro"],
                "ultima_vez": g["ultimo"],
            }
            for g in ranking_bruto
        ]
    else:
        ranking_bruto, total, por_sev = agregar(eventos, desde_ts)
        ranking = [
            {
                "nome": g["nome"],
                "ocorrencias": g["count"],
                "severidade": g["sev"],
                "hosts": sorted(g["hosts"]),
                "primeira_vez": g["primeiro"],
                "ultima_vez": g["ultimo"],
            }
            for g in ranking_bruto
        ]

    resultado = {
        "periodo": periodo,
        "visao": visao,
        "desde": desde.isoformat(),
        "total": total,
        "por_severidade": por_sev,
        "ranking": ranking,
    }
    _cache[chave] = (agora, resultado)
    return resultado
