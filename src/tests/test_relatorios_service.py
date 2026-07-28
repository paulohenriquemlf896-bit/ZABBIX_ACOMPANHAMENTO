#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes da camada de dominio/servico do relatorio de problemas recorrentes
(src/relatorios_service.py). Casos obrigatorios de
prompts/politicas/testes.txt, item 6.

100% offline: buscar_eventos() e testado com relatorios_service.call
mockado, nunca com rede real (ver prompts/politicas/testes.txt, item 5).

Uso:
  python -m unittest discover src/tests
"""

import os
import sys
import unittest
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import relatorios_service as rs  # noqa: E402 — import apos sys.path


class TestAgregar(unittest.TestCase):

    def test_lista_vazia_retorna_ranking_vazio(self):
        ranking, total, por_sev = rs.agregar([], desde_ts=0)
        self.assertEqual(ranking, [])
        self.assertEqual(total, 0)
        self.assertTrue(all(n == 0 for n in por_sev.values()))

    def test_evento_sem_host_nao_quebra(self):
        eventos = [{"clock": 100, "name": "X", "severity": 2, "hosts": []}]
        ranking, total, _ = rs.agregar(eventos, desde_ts=0)
        self.assertEqual(total, 1)
        self.assertEqual(ranking[0]["hosts"], set())

    def test_evento_fora_da_janela_e_ignorado(self):
        eventos = [
            {"clock": 50, "name": "Antigo", "severity": 2, "hosts": []},
            {"clock": 150, "name": "Recente", "severity": 2, "hosts": []},
        ]
        ranking, total, _ = rs.agregar(eventos, desde_ts=100)
        self.assertEqual(total, 1)
        self.assertEqual(ranking[0]["nome"], "Recente")

    def test_nome_com_caractere_html_e_preservado_cru(self):
        # Escape e responsabilidade da camada de apresentacao (tabela_html
        # em scripts/relatorio_problemas.py), nao desta camada de dominio.
        eventos = [{"clock": 100, "name": "<script>alert(1)</script>", "severity": 1, "hosts": []}]
        ranking, _, _ = rs.agregar(eventos, desde_ts=0)
        self.assertEqual(ranking[0]["nome"], "<script>alert(1)</script>")

    def test_empate_de_contagem_mantem_ambos(self):
        eventos = [
            {"clock": 100, "name": "A", "severity": 1, "hosts": []},
            {"clock": 101, "name": "B", "severity": 1, "hosts": []},
        ]
        ranking, total, _ = rs.agregar(eventos, desde_ts=0)
        self.assertEqual(total, 2)
        nomes = {g["nome"] for g in ranking}
        self.assertEqual(nomes, {"A", "B"})
        self.assertTrue(all(g["count"] == 1 for g in ranking))

    def test_severidade_agregada_e_a_maxima_do_grupo(self):
        eventos = [
            {"clock": 100, "name": "X", "severity": 2, "hosts": []},
            {"clock": 101, "name": "X", "severity": 4, "hosts": []},
            {"clock": 102, "name": "X", "severity": 1, "hosts": []},
        ]
        ranking, _, _ = rs.agregar(eventos, desde_ts=0)
        self.assertEqual(ranking[0]["sev"], 4)

    def test_hosts_de_multiplos_eventos_sao_unificados(self):
        eventos = [
            {"clock": 100, "name": "X", "severity": 1, "hosts": [{"name": "Host A"}]},
            {"clock": 101, "name": "X", "severity": 1, "hosts": [{"name": "Host B"}]},
        ]
        ranking, _, _ = rs.agregar(eventos, desde_ts=0)
        self.assertEqual(ranking[0]["hosts"], {"Host A", "Host B"})


class TestAgregarPorHost(unittest.TestCase):
    """Ver specs/ranking_por_host.md para as regras de negocio."""

    def test_lista_vazia_retorna_ranking_vazio(self):
        ranking, total, por_sev = rs.agregar_por_host([], desde_ts=0)
        self.assertEqual(ranking, [])
        self.assertEqual(total, 0)
        self.assertTrue(all(n == 0 for n in por_sev.values()))

    def test_evento_sem_host_nao_entra_no_ranking_mas_conta_no_total(self):
        eventos = [{"clock": 100, "name": "X", "severity": 2, "hosts": []}]
        ranking, total, _ = rs.agregar_por_host(eventos, desde_ts=0)
        self.assertEqual(ranking, [])
        self.assertEqual(total, 1)

    def test_evento_com_host_unico_conta_uma_vez(self):
        eventos = [{"clock": 100, "name": "X", "severity": 2, "hosts": [{"name": "Host A"}]}]
        ranking, total, _ = rs.agregar_por_host(eventos, desde_ts=0)
        self.assertEqual(total, 1)
        self.assertEqual(ranking[0]["host"], "Host A")
        self.assertEqual(ranking[0]["count"], 1)

    def test_evento_com_multiplos_hosts_conta_para_cada_host(self):
        eventos = [{"clock": 100, "name": "X", "severity": 2,
                    "hosts": [{"name": "Host A"}, {"name": "Host B"}]}]
        ranking, total, _ = rs.agregar_por_host(eventos, desde_ts=0)
        self.assertEqual(total, 1)
        hosts = {g["host"]: g["count"] for g in ranking}
        self.assertEqual(hosts, {"Host A": 1, "Host B": 1})

    def test_evento_fora_da_janela_e_ignorado(self):
        eventos = [
            {"clock": 50, "name": "Antigo", "severity": 2, "hosts": [{"name": "Host A"}]},
            {"clock": 150, "name": "Recente", "severity": 2, "hosts": [{"name": "Host A"}]},
        ]
        ranking, total, _ = rs.agregar_por_host(eventos, desde_ts=100)
        self.assertEqual(total, 1)
        self.assertEqual(ranking[0]["count"], 1)

    def test_empate_de_contagem_mantem_ambos_hosts(self):
        eventos = [
            {"clock": 100, "name": "A", "severity": 1, "hosts": [{"name": "Host A"}]},
            {"clock": 101, "name": "B", "severity": 1, "hosts": [{"name": "Host B"}]},
        ]
        ranking, total, _ = rs.agregar_por_host(eventos, desde_ts=0)
        self.assertEqual(total, 2)
        hosts = {g["host"] for g in ranking}
        self.assertEqual(hosts, {"Host A", "Host B"})

    def test_severidade_agregada_e_a_maxima_do_host(self):
        eventos = [
            {"clock": 100, "name": "X", "severity": 2, "hosts": [{"name": "Host A"}]},
            {"clock": 101, "name": "Y", "severity": 4, "hosts": [{"name": "Host A"}]},
        ]
        ranking, _, _ = rs.agregar_por_host(eventos, desde_ts=0)
        self.assertEqual(ranking[0]["sev"], 4)

    def test_problemas_distintos_do_host_sao_unificados(self):
        eventos = [
            {"clock": 100, "name": "Problema A", "severity": 1, "hosts": [{"name": "Host A"}]},
            {"clock": 101, "name": "Problema B", "severity": 1, "hosts": [{"name": "Host A"}]},
            {"clock": 102, "name": "Problema A", "severity": 1, "hosts": [{"name": "Host A"}]},
        ]
        ranking, _, _ = rs.agregar_por_host(eventos, desde_ts=0)
        self.assertEqual(ranking[0]["count"], 3)
        self.assertEqual(ranking[0]["problemas"], {"Problema A", "Problema B"})


class TestBuscarEventos(unittest.TestCase):

    @patch("relatorios_service.call")
    def test_sucesso_devolve_eventos_sem_erro(self, mock_call):
        mock_call.return_value = {"result": [{"eventid": "1"}]}
        eventos, erro = rs.buscar_eventos(0, token="abc")
        self.assertEqual(eventos, [{"eventid": "1"}])
        self.assertIsNone(erro)

    @patch("relatorios_service.call")
    def test_erro_de_aplicacao_devolve_lista_vazia_e_mensagem(self, mock_call):
        mock_call.return_value = {"error": {"data": "Session terminated"}}
        eventos, erro = rs.buscar_eventos(0, token="abc")
        self.assertEqual(eventos, [])
        self.assertIn("Session terminated", erro)

    @patch("relatorios_service.call")
    def test_erro_de_conexao_devolve_lista_vazia_e_mensagem(self, mock_call):
        mock_call.return_value = {"__error__": "Conexao: timed out"}
        eventos, erro = rs.buscar_eventos(0, token="abc")
        self.assertEqual(eventos, [])
        self.assertEqual(erro, "Conexao: timed out")

    @patch("relatorios_service.call")
    def test_teto_maximo_e_respeitado_por_padrao(self, mock_call):
        mock_call.return_value = {"result": []}
        rs.buscar_eventos(0, token="abc")
        params = mock_call.call_args[0][1]
        self.assertEqual(params["limit"], rs.MAX_EVENTOS)

    @patch("relatorios_service.call")
    def test_limite_customizado_sobrescreve_max_eventos(self, mock_call):
        mock_call.return_value = {"result": []}
        rs.buscar_eventos(0, token="abc", limite=10)
        params = mock_call.call_args[0][1]
        self.assertEqual(params["limit"], 10)


class TestPeriodos(unittest.TestCase):

    def test_desde_periodo_hoje_e_meia_noite(self):
        agora = datetime(2026, 7, 28, 15, 30)
        d = rs.desde_periodo("hoje", agora)
        self.assertEqual(d, datetime(2026, 7, 28, 0, 0))

    def test_desde_periodo_invalido_levanta_valueerror(self):
        with self.assertRaises(ValueError):
            rs.desde_periodo("2anos")

    def test_janelas_devolve_4_periodos_na_ordem(self):
        agora = datetime(2026, 7, 28, 12, 0)
        j = rs.janelas(agora)
        titulos = [t for t, _ in j]
        self.assertEqual(titulos, ["Hoje", "Ultimos 7 dias", "Ultimos 30 dias", "Ultimos 365 dias"])


if __name__ == "__main__":
    unittest.main()
