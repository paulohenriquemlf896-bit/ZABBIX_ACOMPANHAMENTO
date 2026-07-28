#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente unico de acesso a API JSON-RPC do Zabbix.

Camada de integracao (ver prompts/politicas/arquitetura.txt, item 1):
nenhum outro modulo deste projeto monta requisicao HTTP para o Zabbix
diretamente — scripts e a futura aplicacao importam este modulo.

Duas formas de uso:
  - call(method, params, token, timeout) -> nunca encerra o processo;
    devolve sempre um dict. Em falha, o dict tem a chave "__error__"
    (erro de conexao/HTTP/inesperado) ou "error" (erro de aplicacao do
    proprio Zabbix). Use quando o chamador precisa decidir sozinho o que
    fazer com a falha (ex.: testar conectividade sem/com token).
  - call_ou_falhar(method, params, token, timeout) -> chama call() e,
    se algo deu errado, imprime "[FALHA] <metodo>: <mensagem>" e encerra
    o processo com sys.exit(1). Em sucesso, devolve direto o conteudo de
    "result". Use em scripts CLI que so querem o resultado ou morrer
    tentando.

Autenticacao: header "Authorization: Bearer <token>" (padrao Zabbix 7.x).
NUNCA usar o campo "auth" no corpo da requisicao.

Configuracao via variavel de ambiente (ver prompts/politicas/configuracao.txt
e .env.example): ZBX_URL, ZBX_TOKEN.
"""

import json
import os
import ssl
import sys
import urllib.request
import urllib.error

# =========================================================================
# CONFIGURACAO
# =========================================================================
ZBX_URL = os.environ.get("ZBX_URL", "http://192.168.11.12/zabbix/api_jsonrpc.php")
ZBX_TOKEN = os.environ.get("ZBX_TOKEN", "")

VERIFY_SSL = True  # http nao usa; deixe True. Em https autoassinado use False.
TIMEOUT_PADRAO = 60
# =========================================================================


def _context():
    """Contexto SSL. None = verificacao normal. So desliga com VERIFY_SSL=False,
    em rede interna confiavel com certificado autoassinado."""
    if VERIFY_SSL:
        return None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def call(method, params=None, token=None, timeout=TIMEOUT_PADRAO):
    """Chama a API JSON-RPC do Zabbix e devolve o corpo decodificado.

    Nao injeta ZBX_TOKEN automaticamente — token e explicito por chamada,
    para permitir chamadas propositalmente nao autenticadas (ex.:
    apiinfo.version) coexistirem com chamadas autenticadas no mesmo
    script. Nunca levanta excecao: falhas de conexao, HTTP ou inesperadas
    viram {"__error__": "..."}; falhas de aplicacao do Zabbix continuam
    no formato nativo {"error": {...}}.
    """
    payload = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1}
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json-rpc"}
    if token:
        headers["Authorization"] = "Bearer " + token

    req = urllib.request.Request(ZBX_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_context()) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"__error__": f"HTTP {e.code} {e.reason}: {e.read().decode('utf-8', 'ignore')}"}
    except urllib.error.URLError as e:
        return {"__error__": f"Conexao: {e.reason}"}
    except Exception as e:  # noqa: BLE001 — borda externa: converte tudo em mensagem
        return {"__error__": str(e)}


def call_ou_falhar(method, params=None, token=None, timeout=TIMEOUT_PADRAO):
    """Chama a API autenticada com ZBX_TOKEN por padrao; em qualquer falha
    (conexao ou aplicacao), imprime [FALHA] e encerra o processo. Em
    sucesso, devolve direto o conteudo de "result" (lista ou dict)."""
    if token is None:
        token = ZBX_TOKEN
    r = call(method, params, token, timeout)
    if "__error__" in r:
        print(f"[FALHA] {method}: {r['__error__']}")
        sys.exit(1)
    if "error" in r:
        msg = r["error"].get("data") or r["error"].get("message")
        print(f"[FALHA] {method}: {msg}")
        sys.exit(1)
    return r.get("result", [])
