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


class TestEventosDoGrupo(unittest.TestCase):
    """Ver specs/historico_ocorrencias.md."""

    def test_visao_problema_filtra_pelo_nome_exato(self):
        eventos = [
            {"clock": 100, "name": "A", "severity": 1, "hosts": []},
            {"clock": 101, "name": "B", "severity": 1, "hosts": []},
        ]
        r = rs.eventos_do_grupo(eventos, "problema", "A", desde_ts=0)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["name"], "A")

    def test_visao_host_filtra_por_host_presente_na_lista(self):
        eventos = [
            {"clock": 100, "name": "X", "severity": 1, "hosts": [{"name": "Host A"}, {"name": "Host B"}]},
            {"clock": 101, "name": "Y", "severity": 1, "hosts": [{"name": "Host B"}]},
        ]
        r = rs.eventos_do_grupo(eventos, "host", "Host A", desde_ts=0)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["name"], "X")

    def test_evento_fora_da_janela_e_ignorado(self):
        eventos = [{"clock": 50, "name": "A", "severity": 1, "hosts": []}]
        r = rs.eventos_do_grupo(eventos, "problema", "A", desde_ts=100)
        self.assertEqual(r, [])

    def test_ordenado_do_mais_recente_para_o_mais_antigo(self):
        eventos = [
            {"clock": 100, "name": "A", "severity": 1, "hosts": []},
            {"clock": 300, "name": "A", "severity": 1, "hosts": []},
            {"clock": 200, "name": "A", "severity": 1, "hosts": []},
        ]
        r = rs.eventos_do_grupo(eventos, "problema", "A", desde_ts=0)
        self.assertEqual([int(e["clock"]) for e in r], [300, 200, 100])


class TestBuscarResolucoes(unittest.TestCase):

    def test_lista_vazia_nao_chama_api(self):
        with patch("relatorios_service.call") as mock_call:
            r = rs.buscar_resolucoes([], token="abc")
            self.assertEqual(r, {})
            mock_call.assert_not_called()

    def test_ignora_eventids_zero(self):
        with patch("relatorios_service.call") as mock_call:
            r = rs.buscar_resolucoes(["0", "0"], token="abc")
            self.assertEqual(r, {})
            mock_call.assert_not_called()

    @patch("relatorios_service.call")
    def test_sucesso_devolve_dict_eventid_para_clock(self, mock_call):
        mock_call.return_value = {"result": [{"eventid": "55", "clock": "1000"}]}
        r = rs.buscar_resolucoes(["55"], token="abc")
        self.assertEqual(r, {"55": 1000})

    @patch("relatorios_service.call")
    def test_erro_na_chamada_devolve_dict_vazio(self, mock_call):
        mock_call.return_value = {"__error__": "Conexao: timed out"}
        r = rs.buscar_resolucoes(["55"], token="abc")
        self.assertEqual(r, {})


class TestHistorico(unittest.TestCase):

    @patch("relatorios_service.call")
    def test_ocorrencia_resolvida_tem_duracao(self, mock_call):
        mock_call.return_value = {"result": [{"eventid": "99", "clock": "1044"}]}
        eventos = [{"clock": "1000", "name": "A", "severity": 2, "hosts": [], "r_eventid": "99"}]
        itens = rs.historico(eventos, "problema", "A", desde_ts=0, token="abc")
        self.assertEqual(itens[0]["inicio"], 1000)
        self.assertEqual(itens[0]["fim"], 1044)
        self.assertEqual(itens[0]["duracao_segundos"], 44)

    def test_ocorrencia_ainda_aberta_nao_tem_fim_nem_duracao(self):
        eventos = [{"clock": "1000", "name": "A", "severity": 2, "hosts": [], "r_eventid": "0"}]
        itens = rs.historico(eventos, "problema", "A", desde_ts=0, token="abc")
        self.assertIsNone(itens[0]["fim"])
        self.assertIsNone(itens[0]["duracao_segundos"])

    def test_chave_sem_correspondencia_devolve_lista_vazia(self):
        eventos = [{"clock": "1000", "name": "A", "severity": 2, "hosts": [], "r_eventid": "0"}]
        itens = rs.historico(eventos, "problema", "Nao existe", desde_ts=0, token="abc")
        self.assertEqual(itens, [])


class TestFmtDuracao(unittest.TestCase):

    def test_menos_de_um_minuto(self):
        self.assertEqual(rs.fmt_duracao(44), "44s")

    def test_minutos_e_segundos(self):
        self.assertEqual(rs.fmt_duracao(367), "6m07s")

    def test_horas_e_minutos(self):
        self.assertEqual(rs.fmt_duracao(4573), "1h16m")


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
