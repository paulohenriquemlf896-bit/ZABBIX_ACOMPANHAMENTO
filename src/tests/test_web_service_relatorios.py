#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes do servico web de relatorios (src/web/services/relatorios.py),
com foco no cache de 60s. 100% offline: relatorios_service.buscar_eventos
e sempre mockado (ver prompts/politicas/testes.txt, item 5).

Uso:
  python -m unittest discover src/tests
"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "services"))
import relatorios as web_relatorios  # noqa: E402


class TestDadosPeriodo(unittest.TestCase):

    def setUp(self):
        web_relatorios._cache.clear()

    @patch("relatorios.buscar_eventos")
    def test_periodo_valido_devolve_estrutura_esperada(self, mock_buscar):
        mock_buscar.return_value = ([
            {"clock": 9999999999, "name": "X", "severity": 3, "hosts": [{"name": "Host A"}]},
        ], None)
        dados = web_relatorios.dados_periodo("hoje")
        self.assertEqual(dados["total"], 1)
        self.assertEqual(dados["ranking"][0]["nome"], "X")
        self.assertEqual(dados["ranking"][0]["hosts"], ["Host A"])

    @patch("relatorios.buscar_eventos")
    def test_erro_de_comunicacao_levanta_runtimeerror_e_nao_cacheia(self, mock_buscar):
        mock_buscar.return_value = ([], "Conexao: timed out")
        with self.assertRaises(RuntimeError):
            web_relatorios.dados_periodo("hoje")
        self.assertNotIn(("hoje", "problema"), web_relatorios._cache)

    def test_visao_invalida_levanta_valueerror(self):
        with self.assertRaises(ValueError):
            web_relatorios.dados_periodo("hoje", visao="por_departamento")

    @patch("relatorios.buscar_eventos")
    def test_segunda_chamada_dentro_do_ttl_usa_cache(self, mock_buscar):
        mock_buscar.return_value = ([], None)
        web_relatorios.dados_periodo("7d")
        web_relatorios.dados_periodo("7d")
        self.assertEqual(mock_buscar.call_count, 1)

    @patch("relatorios.buscar_eventos")
    def test_periodos_diferentes_nao_compartilham_cache(self, mock_buscar):
        mock_buscar.return_value = ([], None)
        web_relatorios.dados_periodo("hoje")
        web_relatorios.dados_periodo("30d")
        self.assertEqual(mock_buscar.call_count, 2)

    @patch("relatorios.buscar_eventos")
    def test_cache_expirado_consulta_de_novo(self, mock_buscar):
        mock_buscar.return_value = ([], None)
        web_relatorios.dados_periodo("365d")
        # simula expiracao do TTL sem esperar 60s de verdade
        chave = ("365d", "problema")
        resultado = web_relatorios._cache[chave]
        web_relatorios._cache[chave] = (resultado[0] - web_relatorios.TTL_SEGUNDOS - 1, resultado[1])
        web_relatorios.dados_periodo("365d")
        self.assertEqual(mock_buscar.call_count, 2)


class TestVisaoHost(unittest.TestCase):

    def setUp(self):
        web_relatorios._cache.clear()

    @patch("relatorios.buscar_eventos")
    def test_visao_host_devolve_estrutura_esperada(self, mock_buscar):
        mock_buscar.return_value = ([
            {"clock": 9999999999, "name": "Problema X", "severity": 3, "hosts": [{"name": "Host A"}]},
        ], None)
        dados = web_relatorios.dados_periodo("hoje", visao="host")
        self.assertEqual(dados["visao"], "host")
        self.assertEqual(dados["ranking"][0]["host"], "Host A")
        self.assertEqual(dados["ranking"][0]["problemas"], ["Problema X"])

    @patch("relatorios.buscar_eventos")
    def test_visoes_diferentes_do_mesmo_periodo_nao_compartilham_cache(self, mock_buscar):
        mock_buscar.return_value = ([], None)
        web_relatorios.dados_periodo("7d", visao="problema")
        web_relatorios.dados_periodo("7d", visao="host")
        self.assertEqual(mock_buscar.call_count, 2)

    @patch("relatorios.buscar_eventos")
    def test_mesma_visao_e_periodo_usa_cache(self, mock_buscar):
        mock_buscar.return_value = ([], None)
        web_relatorios.dados_periodo("7d", visao="host")
        web_relatorios.dados_periodo("7d", visao="host")
        self.assertEqual(mock_buscar.call_count, 1)


if __name__ == "__main__":
    unittest.main()
