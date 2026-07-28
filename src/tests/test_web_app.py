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
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web"))
import app as painel  # noqa: E402


class TestPaginaRelatorios(unittest.TestCase):

    def setUp(self):
        self.client = painel.app.test_client()

    @patch("app.dados_periodo")
    @patch("app.call")
    def test_pagina_inicial_usa_periodo_e_visao_default(self, mock_call, mock_dados):
        mock_call.return_value = {"result": "7.4.4"}
        mock_dados.return_value = {"total": 0, "por_severidade": {}, "ranking": []}
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        mock_dados.assert_called_once_with("7d", "problema")

    @patch("app.dados_periodo")
    @patch("app.call")
    def test_periodo_invalido_cai_no_default(self, mock_call, mock_dados):
        mock_call.return_value = {"result": "7.4.4"}
        mock_dados.return_value = {"total": 0, "por_severidade": {}, "ranking": []}
        resp = self.client.get("/?periodo=nao_existe")
        self.assertEqual(resp.status_code, 200)
        mock_dados.assert_called_once_with("7d", "problema")

    @patch("app.dados_periodo")
    @patch("app.call")
    def test_periodo_valido_e_repassado_ao_servico(self, mock_call, mock_dados):
        mock_call.return_value = {"result": "7.4.4"}
        mock_dados.return_value = {"total": 0, "por_severidade": {}, "ranking": []}
        resp = self.client.get("/?periodo=365d")
        self.assertEqual(resp.status_code, 200)
        mock_dados.assert_called_once_with("365d", "problema")

    @patch("app.dados_periodo")
    @patch("app.call")
    def test_visao_host_e_repassada_ao_servico(self, mock_call, mock_dados):
        mock_call.return_value = {"result": "7.4.4"}
        mock_dados.return_value = {"total": 0, "por_severidade": {}, "ranking": []}
        resp = self.client.get("/?visao=host")
        self.assertEqual(resp.status_code, 200)
        mock_dados.assert_called_once_with("7d", "host")

    @patch("app.dados_periodo")
    @patch("app.call")
    def test_visao_invalida_cai_no_default(self, mock_call, mock_dados):
        mock_call.return_value = {"result": "7.4.4"}
        mock_dados.return_value = {"total": 0, "por_severidade": {}, "ranking": []}
        resp = self.client.get("/?visao=departamento")
        self.assertEqual(resp.status_code, 200)
        mock_dados.assert_called_once_with("7d", "problema")

    @patch("app.dados_periodo")
    @patch("app.call")
    def test_erro_de_comunicacao_mostra_mensagem_amigavel_sem_500(self, mock_call, mock_dados):
        mock_call.return_value = {"result": "7.4.4"}
        mock_dados.side_effect = RuntimeError("Conexao: timed out")
        resp = self.client.get("/?periodo=hoje")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Conexao: timed out", resp.data)

    @patch("app.dados_periodo")
    @patch("app.call")
    def test_pagina_tem_meta_refresh_no_intervalo_do_cache(self, mock_call, mock_dados):
        mock_call.return_value = {"result": "7.4.4"}
        mock_dados.return_value = {"total": 0, "por_severidade": {}, "ranking": []}
        resp = self.client.get("/")
        esperado = f'<meta http-equiv="refresh" content="{painel.TTL_SEGUNDOS}">'.encode("utf-8")
        self.assertIn(esperado, resp.data)

    @patch("app.dados_periodo")
    @patch("app.call")
    def test_pagina_de_erro_tambem_tem_meta_refresh(self, mock_call, mock_dados):
        # mesmo em falha de comunicacao, a pagina deve se recuperar sozinha
        # quando o Zabbix voltar, sem exigir F5 manual.
        mock_call.return_value = {"result": "7.4.4"}
        mock_dados.side_effect = RuntimeError("Conexao: timed out")
        resp = self.client.get("/")
        esperado = f'<meta http-equiv="refresh" content="{painel.TTL_SEGUNDOS}">'.encode("utf-8")
        self.assertIn(esperado, resp.data)


class TestMontarGraficoRanking(unittest.TestCase):

    def test_ranking_vazio_devolve_lista_vazia(self):
        self.assertEqual(painel.montar_grafico_ranking([], "problema"), [])

    def test_largura_relativa_ao_maior_item_exibido(self):
        ranking = [
            {"nome": "A", "ocorrencias": 40, "severidade": 3},
            {"nome": "B", "ocorrencias": 10, "severidade": 2},
        ]
        grafico = painel.montar_grafico_ranking(ranking, "problema")
        self.assertEqual(grafico[0]["largura_pct"], 100.0)
        self.assertEqual(grafico[1]["largura_pct"], 25.0)

    def test_visao_host_usa_campo_host_como_rotulo(self):
        ranking = [{"host": "SRV-FORTES", "ocorrencias": 5, "severidade": 4}]
        grafico = painel.montar_grafico_ranking(ranking, "host")
        self.assertEqual(grafico[0]["rotulo"], "SRV-FORTES")

    def test_visao_problema_usa_campo_nome_como_rotulo(self):
        ranking = [{"nome": "ICMP Ping: Unavailable", "ocorrencias": 5, "severidade": 4}]
        grafico = painel.montar_grafico_ranking(ranking, "problema")
        self.assertEqual(grafico[0]["rotulo"], "ICMP Ping: Unavailable")

    def test_limita_ao_top_n_grafico(self):
        ranking = [{"nome": f"P{i}", "ocorrencias": 1, "severidade": 1}
                   for i in range(painel.TOP_N_GRAFICO + 5)]
        grafico = painel.montar_grafico_ranking(ranking, "problema")
        self.assertEqual(len(grafico), painel.TOP_N_GRAFICO)


class TestPaginaHistorico(unittest.TestCase):

    def setUp(self):
        self.client = painel.app.test_client()

    def test_sem_chave_mostra_mensagem_amigavel(self):
        resp = self.client.get("/historico?periodo=7d&visao=problema")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Nenhum problema/host valido selecionado".encode("utf-8"), resp.data)

    @patch("app.historico_grupo")
    def test_chave_valida_repassada_ao_servico(self, mock_hist):
        mock_hist.return_value = []
        resp = self.client.get("/historico?periodo=30d&visao=host&chave=SRV-FORTES")
        self.assertEqual(resp.status_code, 200)
        mock_hist.assert_called_once_with("30d", "host", "SRV-FORTES")

    @patch("app.historico_grupo")
    def test_ocorrencia_resolvida_mostra_duracao_formatada(self, mock_hist):
        mock_hist.return_value = [
            {"inicio": 1000, "fim": 1044, "duracao_segundos": 44, "severidade": 2},
        ]
        resp = self.client.get("/historico?chave=X")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"44s", resp.data)

    @patch("app.historico_grupo")
    def test_ocorrencia_aberta_mostra_ainda_aberta(self, mock_hist):
        mock_hist.return_value = [
            {"inicio": 1000, "fim": None, "duracao_segundos": None, "severidade": 2},
        ]
        resp = self.client.get("/historico?chave=X")
        self.assertIn("ainda aberta".encode("utf-8"), resp.data)

    @patch("app.historico_grupo")
    def test_erro_de_comunicacao_mostra_mensagem_amigavel(self, mock_hist):
        mock_hist.side_effect = RuntimeError("Conexao: timed out")
        resp = self.client.get("/historico?chave=X")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Conexao: timed out", resp.data)

    def test_chave_maior_que_limite_mostra_mensagem_amigavel(self):
        resp = self.client.get("/historico?chave=" + "x" * 600)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Nenhum problema/host valido selecionado".encode("utf-8"), resp.data)


class TestMontarGraficoDias(unittest.TestCase):

    def test_lista_vazia_devolve_lista_vazia(self):
        self.assertEqual(painel.montar_grafico_dias([]), [])

    def test_agrupa_por_dia_em_ordem_cronologica(self):
        # itens vem do mais recente para o mais antigo (como historico() devolve)
        itens = [
            {"inicio": datetime(2026, 7, 27, 10, 0).timestamp()},
            {"inicio": datetime(2026, 7, 26, 10, 0).timestamp()},
            {"inicio": datetime(2026, 7, 26, 11, 0).timestamp()},
        ]
        grafico = painel.montar_grafico_dias(itens)
        dias = [g["dia"] for g in grafico]
        self.assertEqual(dias, ["26/07", "27/07"])
        self.assertEqual(grafico[0]["ocorrencias"], 2)
        self.assertEqual(grafico[1]["ocorrencias"], 1)


class TestResumoHistorico(unittest.TestCase):

    def test_lista_vazia(self):
        r = painel.resumo_historico([])
        self.assertEqual(r["total"], 0)
        self.assertIsNone(r["duracao_media"])

    def test_mistura_resolvidas_e_abertas(self):
        itens = [
            {"duracao_segundos": 10},
            {"duracao_segundos": 30},
            {"duracao_segundos": None},
        ]
        r = painel.resumo_historico(itens)
        self.assertEqual(r["total"], 3)
        self.assertEqual(r["abertas"], 1)
        self.assertEqual(r["resolvidas"], 2)
        self.assertEqual(r["duracao_media"], "20s")
        self.assertEqual(r["duracao_min"], "10s")
        self.assertEqual(r["duracao_max"], "30s")


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
        mock_dados.assert_called_once_with("30d", "problema")

    def test_periodo_invalido_devolve_400(self):
        resp = self.client.get("/api/relatorios/dados?periodo=nao_existe")
        body = resp.get_json()
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(body["ok"])

    @patch("api.dados_periodo")
    def test_visao_host_e_repassada(self, mock_dados):
        mock_dados.return_value = {"total": 0, "por_severidade": {}, "ranking": []}
        resp = self.client.get("/api/relatorios/dados?periodo=7d&visao=host")
        self.assertEqual(resp.status_code, 200)
        mock_dados.assert_called_once_with("7d", "host")

    def test_visao_invalida_devolve_400(self):
        resp = self.client.get("/api/relatorios/dados?visao=departamento")
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


class TestApiRelatoriosHistorico(unittest.TestCase):

    def setUp(self):
        self.client = painel.app.test_client()

    @patch("api.historico_grupo")
    def test_chave_valida_devolve_envelope_ok(self, mock_hist):
        mock_hist.return_value = [{"inicio": 1000, "fim": None, "duracao_segundos": None, "severidade": 2}]
        resp = self.client.get("/api/relatorios/historico?periodo=7d&visao=problema&chave=X")
        body = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(len(body["dados"]["itens"]), 1)
        mock_hist.assert_called_once_with("7d", "problema", "X")

    def test_chave_ausente_devolve_400(self):
        resp = self.client.get("/api/relatorios/historico?periodo=7d")
        body = resp.get_json()
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(body["ok"])

    def test_periodo_invalido_devolve_400(self):
        resp = self.client.get("/api/relatorios/historico?periodo=nao_existe&chave=X")
        self.assertEqual(resp.status_code, 400)

    def test_visao_invalida_devolve_400(self):
        resp = self.client.get("/api/relatorios/historico?visao=departamento&chave=X")
        self.assertEqual(resp.status_code, 400)

    @patch("api.historico_grupo")
    def test_erro_de_comunicacao_devolve_200_com_ok_false(self, mock_hist):
        mock_hist.side_effect = RuntimeError("Conexao: timed out")
        resp = self.client.get("/api/relatorios/historico?chave=X")
        body = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(body["ok"])


if __name__ == "__main__":
    unittest.main()
