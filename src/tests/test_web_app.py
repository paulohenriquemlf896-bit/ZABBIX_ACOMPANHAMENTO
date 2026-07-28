#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes do painel web (src/web/app.py e src/web/api.py) via Flask test
client. 100% offline: zbx_api.call e services.relatorios.dados_periodo
sempre mockados (ver prompts/politicas/testes.txt, item 5).

Uso:
  python -m unittest discover src/tests
"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web"))
import app as painel  # noqa: E402


class TestPaginaRelatorios(unittest.TestCase):

    def setUp(self):
        self.client = painel.app.test_client()

    @patch("app.dados_periodo")
    @patch("app.call")
    def test_pagina_inicial_usa_periodo_default_7d(self, mock_call, mock_dados):
        mock_call.return_value = {"result": "7.4.4"}
        mock_dados.return_value = {"total": 0, "por_severidade": {}, "ranking": []}
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        mock_dados.assert_called_once_with("7d")

    @patch("app.dados_periodo")
    @patch("app.call")
    def test_periodo_invalido_cai_no_default(self, mock_call, mock_dados):
        mock_call.return_value = {"result": "7.4.4"}
        mock_dados.return_value = {"total": 0, "por_severidade": {}, "ranking": []}
        resp = self.client.get("/?periodo=nao_existe")
        self.assertEqual(resp.status_code, 200)
        mock_dados.assert_called_once_with("7d")

    @patch("app.dados_periodo")
    @patch("app.call")
    def test_periodo_valido_e_repassado_ao_servico(self, mock_call, mock_dados):
        mock_call.return_value = {"result": "7.4.4"}
        mock_dados.return_value = {"total": 0, "por_severidade": {}, "ranking": []}
        resp = self.client.get("/?periodo=365d")
        self.assertEqual(resp.status_code, 200)
        mock_dados.assert_called_once_with("365d")

    @patch("app.dados_periodo")
    @patch("app.call")
    def test_erro_de_comunicacao_mostra_mensagem_amigavel_sem_500(self, mock_call, mock_dados):
        mock_call.return_value = {"result": "7.4.4"}
        mock_dados.side_effect = RuntimeError("Conexao: timed out")
        resp = self.client.get("/?periodo=hoje")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Conexao: timed out", resp.data)


class TestHealth(unittest.TestCase):

    def setUp(self):
        self.client = painel.app.test_client()

    @patch("app.call")
    def test_health_zabbix_alcancavel(self, mock_call):
        mock_call.return_value = {"result": "7.4.4"}
        resp = self.client.get("/health")
        body = resp.get_json()
        self.assertTrue(body["ok"])
        self.assertTrue(body["zabbix_alcancavel"])
        self.assertEqual(body["versao_api"], "7.4.4")

    @patch("app.call")
    def test_health_zabbix_inalcancavel(self, mock_call):
        mock_call.return_value = {"__error__": "Conexao: timed out"}
        resp = self.client.get("/health")
        body = resp.get_json()
        self.assertFalse(body["ok"])
        self.assertFalse(body["zabbix_alcancavel"])


class TestApiRelatoriosDados(unittest.TestCase):

    def setUp(self):
        self.client = painel.app.test_client()

    @patch("api.dados_periodo")
    def test_periodo_valido_devolve_envelope_ok(self, mock_dados):
        mock_dados.return_value = {"total": 3, "por_severidade": {}, "ranking": []}
        resp = self.client.get("/api/relatorios/dados?periodo=30d")
        body = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["dados"]["total"], 3)
        self.assertIsNone(body["erro"])

    def test_periodo_invalido_devolve_400(self):
        resp = self.client.get("/api/relatorios/dados?periodo=nao_existe")
        body = resp.get_json()
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(body["ok"])

    @patch("api.dados_periodo")
    def test_erro_de_comunicacao_devolve_200_com_ok_false(self, mock_dados):
        mock_dados.side_effect = RuntimeError("Conexao: timed out")
        resp = self.client.get("/api/relatorios/dados?periodo=hoje")
        body = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(body["ok"])
        self.assertEqual(body["erro"], "Conexao: timed out")


if __name__ == "__main__":
    unittest.main()
