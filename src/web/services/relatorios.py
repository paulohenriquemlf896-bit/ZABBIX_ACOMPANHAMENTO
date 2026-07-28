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
from relatorios_service import buscar_eventos, agregar, desde_periodo  # noqa: E402
from zbx_api import ZBX_TOKEN  # noqa: E402

# =========================================================================
# CONFIGURACAO
# =========================================================================
TTL_SEGUNDOS = 60  # cache por periodo (prompts/politicas/performance.txt, item 7)
# =========================================================================

_cache = {}  # periodo -> (timestamp_cache, resultado)


def dados_periodo(periodo):
    """Devolve os dados agregados de um periodo valido, usando cache de 60s.

    Devolve um dict serializavel (ranking, total, por_severidade) em
    sucesso. Levanta RuntimeError com mensagem amigavel em falha de
    comunicacao com o Zabbix — nunca cacheia falha, para nao esconder uma
    indisponibilidade temporaria por 60s (prompts/politicas/performance.txt,
    item 7).
    """
    agora = time.time()
    cacheado = _cache.get(periodo)
    if cacheado and (agora - cacheado[0]) < TTL_SEGUNDOS:
        return cacheado[1]

    desde = desde_periodo(periodo)
    desde_ts = int(desde.timestamp())
    eventos, erro = buscar_eventos(desde_ts, ZBX_TOKEN)
    if erro:
        raise RuntimeError(erro)

    ranking, total, por_sev = agregar(eventos, desde_ts)
    resultado = {
        "periodo": periodo,
        "desde": desde.isoformat(),
        "total": total,
        "por_severidade": por_sev,
        "ranking": [
            {
                "nome": g["nome"],
                "ocorrencias": g["count"],
                "severidade": g["sev"],
                "hosts": sorted(g["hosts"]),
                "primeira_vez": g["primeiro"],
                "ultima_vez": g["ultimo"],
            }
            for g in ranking
        ],
    }
    _cache[periodo] = (agora, resultado)
    return resultado
