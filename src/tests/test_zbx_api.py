#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes do cliente unico de acesso a API do Zabbix (src/zbx_api.py).

100% offline: urllib.request.urlopen e sempre mockado, nenhuma chamada
de rede real acontece (ver prompts/politicas/testes.txt, item 5 —
proibido teste automatizado que fala com o Zabbix de verdade).

Uso:
  python -m unittest discover src/tests
"""

import io
import json
import os
import sys
import unittest
import urllib.error
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import zbx_api  # noqa: E402 — import apos sys.path


def _resposta_ok(corpo: dict):
    """Fabrica um objeto com o mesmo shape do retorno de urlopen() (context
    manager cujo .read() devolve bytes)."""
    m = io.BytesIO(json.dumps(corpo).encode("utf-8"))
    m.__enter__ = lambda *_: m
    m.__exit__ = lambda *_: None
    return m


class TestCall(unittest.TestCase):
    """call() nunca levanta excecao nem encerra o processo."""

    @patch("zbx_api.urllib.request.urlopen")
    def test_sucesso_devolve_corpo_decodificado(self, mock_urlopen):
        mock_urlopen.return_value = _resposta_ok(
            {"jsonrpc": "2.0", "result": "7.4.4", "id": 1}
        )
        r = zbx_api.call("apiinfo.version")
        self.assertEqual(r["result"], "7.4.4")

    @patch("zbx_api.urllib.request.urlopen")
    def test_erro_de_conexao_vira_dict_com_erro(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("timed out")
        r = zbx_api.call("apiinfo.version")
        self.assertIn("__error__", r)
        self.assertIn("Conexao", r["__error__"])

    @patch("zbx_api.urllib.request.urlopen")
    def test_erro_http_vira_dict_com_erro(self, mock_urlopen):
        corpo_erro = io.BytesIO(b"Internal Server Error")
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url=zbx_api.ZBX_URL, code=500, msg="Internal Server Error",
            hdrs=None, fp=corpo_erro,
        )
        r = zbx_api.call("apiinfo.version")
        self.assertIn("__error__", r)
        self.assertIn("500", r["__error__"])

    @patch("zbx_api.urllib.request.urlopen")
    def test_erro_de_aplicacao_zabbix_preserva_formato_nativo(self, mock_urlopen):
        mock_urlopen.return_value = _resposta_ok({
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": "Invalid params.", "data": "Session terminated"},
            "id": 1,
        })
        r = zbx_api.call("host.get", token="qualquer")
        self.assertIn("error", r)
        self.assertEqual(r["error"]["data"], "Session terminated")

    @patch("zbx_api.urllib.request.urlopen")
    def test_sem_token_nao_envia_header_authorization(self, mock_urlopen):
        mock_urlopen.return_value = _resposta_ok({"jsonrpc": "2.0", "result": "7.4.4", "id": 1})
        zbx_api.call("apiinfo.version")  # sem token=
        req = mock_urlopen.call_args[0][0]
        self.assertNotIn("Authorization", req.headers)

    @patch("zbx_api.urllib.request.urlopen")
    def test_com_token_envia_header_bearer(self, mock_urlopen):
        mock_urlopen.return_value = _resposta_ok({"jsonrpc": "2.0", "result": [], "id": 1})
        zbx_api.call("host.get", token="abc123")
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.headers.get("Authorization"), "Bearer abc123")

    @patch("zbx_api.urllib.request.urlopen")
    def test_excecao_inesperada_tambem_vira_dict_com_erro(self, mock_urlopen):
        mock_urlopen.side_effect = ValueError("algo bizarro")
        r = zbx_api.call("apiinfo.version")
        self.assertIn("__error__", r)
        self.assertIn("algo bizarro", r["__error__"])


class TestCallOuFalhar(unittest.TestCase):
    """call_ou_falhar() encerra o processo em qualquer falha e devolve
    so o 'result' em sucesso."""

    @patch("zbx_api.urllib.request.urlopen")
    def test_sucesso_devolve_apenas_o_result(self, mock_urlopen):
        mock_urlopen.return_value = _resposta_ok(
            {"jsonrpc": "2.0", "result": [{"hostid": "1"}], "id": 1}
        )
        r = zbx_api.call_ou_falhar("host.get")
        self.assertEqual(r, [{"hostid": "1"}])

    @patch("zbx_api.urllib.request.urlopen")
    def test_erro_de_conexao_encerra_processo(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("timed out")
        with self.assertRaises(SystemExit) as ctx:
            zbx_api.call_ou_falhar("discoveryrule.get")
        self.assertEqual(ctx.exception.code, 1)

    @patch("zbx_api.urllib.request.urlopen")
    def test_erro_de_aplicacao_encerra_processo(self, mock_urlopen):
        mock_urlopen.return_value = _resposta_ok({
            "jsonrpc": "2.0",
            "error": {"code": -32500, "message": "Application error.", "data": "No permissions"},
            "id": 1,
        })
        with self.assertRaises(SystemExit) as ctx:
            zbx_api.call_ou_falhar("template.get")
        self.assertEqual(ctx.exception.code, 1)

    @patch("zbx_api.urllib.request.urlopen")
    def test_usa_zbx_token_global_por_padrao(self, mock_urlopen):
        mock_urlopen.return_value = _resposta_ok({"jsonrpc": "2.0", "result": [], "id": 1})
        with patch.object(zbx_api, "ZBX_TOKEN", "token-de-teste"):
            zbx_api.call_ou_falhar("host.get")  # sem token= explicito
            req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.headers.get("Authorization"), "Bearer token-de-teste")


if __name__ == "__main__":
    unittest.main()
