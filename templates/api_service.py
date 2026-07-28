#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEMPLATE: cliente de acesso a uma API JSON-RPC/REST externa.

Como usar este template:
  1. Copie para src/ (se for parte da aplicacao) ou scripts/ (se for uso
     pontual) com um nome descritivo (ex.: zbx_api.py).
  2. Troque NOME_SERVICO / SERVICO_URL / SERVICO_TOKEN pelo nome real.
  3. Ajuste call() para o protocolo real (este exemplo segue o padrao
     JSON-RPC 2.0 usado pela API do Zabbix — ver contexto/api.md).
  4. Apague os comentarios "TEMPLATE:" depois de adaptar.

Ver padroes/convencoes.md (bloco de configuracao, docstring, 3 camadas de
erro) e prompts/tarefas/backend.txt.
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
SERVICO_URL = os.environ.get("SERVICO_URL", "")   # TEMPLATE: renomear
SERVICO_TOKEN = os.environ.get("SERVICO_TOKEN", "")  # TEMPLATE: renomear
VERIFY_SSL = True
TIMEOUT_PADRAO = 30
# =========================================================================


def _context():
    """Contexto SSL. Deixe None (verificacao normal) a menos que o
    servidor use certificado autoassinado em rede confiavel."""
    if VERIFY_SSL:
        return None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def call(method: str, params: dict | None = None, token: str | None = None,
         timeout: int = TIMEOUT_PADRAO) -> dict:
    """Chama a API e devolve o corpo decodificado como dict.

    Nunca levanta excecao para erro de rede/HTTP/aplicacao — sempre
    retorna um dict; o chamador verifica as chaves "error"/"__error__".
    """
    payload = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1}
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json-rpc"}
    if token:
        headers["Authorization"] = "Bearer " + token

    req = urllib.request.Request(SERVICO_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_context()) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # Camada 2: servidor respondeu com status de erro.
        return {"__error__": f"HTTP {e.code} {e.reason}: {e.read().decode('utf-8', 'ignore')}"}
    except urllib.error.URLError as e:
        # Camada 1: falha de conexao/timeout.
        return {"__error__": f"Conexao: {e.reason}"}
    except Exception as e:  # noqa: BLE001 — borda externa: converte tudo em mensagem
        return {"__error__": str(e)}


def call_ou_falhar(method: str, params: dict | None = None,
                    token: str | None = None) -> list | dict:
    """Wrapper para scripts CLI: chama a API e encerra o processo com
    [FALHA] se algo deu errado. Camada 3: erro de aplicacao
    ({"error": ...} no corpo)."""
    r = call(method, params, token)
    if "__error__" in r:
        print(f"[FALHA] {method}: {r['__error__']}")
        sys.exit(1)
    if "error" in r:
        msg = r["error"].get("data") or r["error"].get("message")
        print(f"[FALHA] {method}: {msg}")
        sys.exit(1)
    return r.get("result", [])


# TEMPLATE: exemplo de uso
if __name__ == "__main__":
    resultado = call_ou_falhar("apiinfo.version")
    print(f"[OK] Versao: {resultado}")
