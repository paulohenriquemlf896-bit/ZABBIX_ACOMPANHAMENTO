#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes do servico web de exportacao (src/web/services/exportacao.py).
100% offline (prompts/politicas/testes.txt).

Uso:
  python -m unittest discover src/tests
"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "services"))
import exportacao  # noqa: E402


class TestListarHosts(unittest.TestCase):

    @patch("exportacao.call")
    def test_devolve_nomes_ordenados(self, mock_call):
        mock_call.return_value = {"result": [{"host": "Zabbix server"}, {"host": "Siagri Nutrane"}]}
        r = exportacao.listar_hosts()
        self.assertEqual(r, ["Siagri Nutrane", "Zabbix server"])

    @patch("exportacao.call")
    def test_erro_levanta_runtimeerror(self, mock_call):
        mock_call.return_value = {"__error__": "Conexao: timed out"}
        with self.assertRaises(RuntimeError):
            exportacao.listar_hosts()


class TestDadosExportacao(unittest.TestCase):

    def test_periodos_vazio_levanta_valueerror(self):
        with self.assertRaises(ValueError):
            exportacao.dados_exportacao([], None)

    def test_periodo_invalido_levanta_valueerror(self):
        with self.assertRaises(ValueError):
            exportacao.dados_exportacao(["2anos"], None)

    @patch("exportacao.buscar_eventos")
    def test_um_periodo_sem_filtro_de_host(self, mock_buscar):
        mock_buscar.return_value = ([
            {"clock": "9999999999", "name": "X", "severity": 2, "hosts": [{"name": "Host A"}]},
        ], None)
        r = exportacao.dados_exportacao(["hoje"], None)
        self.assertEqual(set(r.keys()), {"hoje"})
        self.assertEqual(r["hoje"]["total"], 1)
        self.assertEqual(r["hoje"]["titulo"], "Hoje")

    @patch("exportacao.buscar_eventos")
    def test_filtro_de_host_e_aplicado(self, mock_buscar):
        mock_buscar.return_value = ([
            {"clock": "9999999999", "name": "X", "severity": 2, "hosts": [{"name": "Host A"}]},
            {"clock": "9999999999", "name": "Y", "severity": 2, "hosts": [{"name": "Host B"}]},
        ], None)
        r = exportacao.dados_exportacao(["hoje"], ["Host A"])
        self.assertEqual(r["hoje"]["total"], 1)
        self.assertEqual(r["hoje"]["ranking"][0]["nome"], "X")

    @patch("exportacao.buscar_eventos")
    def test_multiplos_periodos_geram_entradas_independentes(self, mock_buscar):
        mock_buscar.return_value = ([], None)
        r = exportacao.dados_exportacao(["hoje", "7d"], None)
        self.assertEqual(set(r.keys()), {"hoje", "7d"})
        self.assertEqual(mock_buscar.call_count, 2)

    @patch("exportacao.buscar_eventos")
    def test_erro_de_comunicacao_levanta_runtimeerror(self, mock_buscar):
        mock_buscar.return_value = ([], "Conexao: timed out")
        with self.assertRaises(RuntimeError):
            exportacao.dados_exportacao(["hoje"], None)


if __name__ == "__main__":
    unittest.main()
