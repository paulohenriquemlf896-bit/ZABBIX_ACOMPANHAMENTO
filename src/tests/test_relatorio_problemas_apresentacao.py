#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes da camada de apresentacao do relatorio de problemas recorrentes
(tabela_html, barra_sev em scripts/relatorio_problemas.py). Fecha a
divida tecnica registrada em AI_MEMORY.md (cobertura de teste parcial,
item 4) — casos obrigatorios de prompts/politicas/testes.txt, item 6.

100% offline: tabela_html/barra_sev sao funcoes puras de formatacao,
recebem dados ja agregados (nenhuma chamada de rede).

Uso:
  python -m unittest discover src/tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
import relatorio_problemas as rp  # noqa: E402 — import apos sys.path


def _grupo(nome="Problema X", count=1, sev=3, hosts=None, ultimo=1785000000):
    return {"nome": nome, "count": count, "sev": sev, "hosts": hosts or set(),
            "primeiro": ultimo, "ultimo": ultimo}


class TestTabelaHtml(unittest.TestCase):

    def test_ranking_vazio_mostra_mensagem_de_vazio(self):
        html = rp.tabela_html([], total=0)
        self.assertIn("Nenhum problema registrado neste periodo.", html)
        self.assertNotIn("<table>", html)

    def test_nome_com_caractere_html_e_escapado(self):
        g = _grupo(nome='<script>alert("x")</script>')
        html = rp.tabela_html([g], total=1)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_hosts_com_caractere_html_sao_escapados(self):
        g = _grupo(hosts={"<Host A>"})
        html = rp.tabela_html([g], total=1)
        self.assertNotIn("<Host A>", html)
        self.assertIn("&lt;Host A&gt;", html)

    def test_percentual_calculado_sobre_o_total(self):
        g = _grupo(count=25)
        html = rp.tabela_html([g], total=100)
        self.assertIn("25.0%", html)

    def test_total_zero_nao_quebra_e_percentual_e_zero(self):
        g = _grupo(count=0)
        html = rp.tabela_html([g], total=0)
        self.assertIn("0.0%", html)

    def test_severidade_desconhecida_usa_cor_e_rotulo_padrao(self):
        g = _grupo(sev=99)
        html = rp.tabela_html([g], total=1)
        self.assertIn("#97AAB3", html)
        self.assertIn(">?<", html)

    def test_ranking_maior_que_top_n_e_truncado(self):
        ranking = [_grupo(nome=f"P{i}", count=1) for i in range(rp.TOP_N + 5)]
        html = rp.tabela_html(ranking, total=len(ranking))
        self.assertEqual(html.count('class="rank"'), rp.TOP_N)


class TestBarraSev(unittest.TestCase):

    def test_todas_severidades_zeradas_nao_gera_pill(self):
        por_sev = {s: 0 for s in rp.SEV_NOME}
        html = rp.barra_sev(por_sev, total=0)
        self.assertIn("Total: 0", html)
        self.assertNotIn("pill", html)

    def test_pills_aparecem_da_mais_grave_para_a_menos_grave(self):
        por_sev = {0: 0, 1: 0, 2: 0, 3: 5, 4: 2, 5: 1}
        html = rp.barra_sev(por_sev, total=8)
        pos_desastre = html.index("Desastre: 1")
        pos_alta = html.index("Alta: 2")
        pos_media = html.index("Media: 5")
        self.assertLess(pos_desastre, pos_alta)
        self.assertLess(pos_alta, pos_media)

    def test_total_aparece_no_resultado(self):
        por_sev = {s: 0 for s in rp.SEV_NOME}
        html = rp.barra_sev(por_sev, total=42)
        self.assertIn("Total: 42", html)


if __name__ == "__main__":
    unittest.main()
