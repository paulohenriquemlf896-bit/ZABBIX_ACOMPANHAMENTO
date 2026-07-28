#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de novo_valor() em scripts/aplicar_exclusao_googleupdater.py.
Fecha a divida tecnica registrada em AI_MEMORY.md (cobertura de teste
parcial, item 4).

100% offline: novo_valor() e uma funcao pura de string, sem rede nem
escrita real no Zabbix (ver prompts/politicas/testes.txt, item 5).

Uso:
  python -m unittest discover src/tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
import aplicar_exclusao_googleupdater as aeg  # noqa: E402 — import apos sys.path


class TestNovoValor(unittest.TestCase):

    def test_acrescenta_antes_do_fechamento_quando_termina_em_parenteses_dolar(self):
        atual = "^(?:RemoteRegistry|MMCSS)$"
        novo = aeg.novo_valor(atual)
        self.assertEqual(novo, "^(?:RemoteRegistry|MMCSS|GoogleUpdater.*)$")

    def test_concatena_com_pipe_quando_nao_termina_em_parenteses_dolar(self):
        atual = "RemoteRegistry"
        novo = aeg.novo_valor(atual)
        self.assertEqual(novo, "RemoteRegistry|GoogleUpdater.*")

    def test_preserva_o_valor_original(self):
        atual = "^(?:A|B|C)$"
        novo = aeg.novo_valor(atual)
        self.assertIn("A|B|C", novo)

    def test_idempotente_quando_ja_contem_o_padrao_exato(self):
        atual = "^(?:RemoteRegistry|GoogleUpdater.*)$"
        self.assertIsNone(aeg.novo_valor(atual))

    def test_idempotente_quando_ja_contem_qualquer_forma_de_googleupdater(self):
        # mesmo uma exclusao manual antiga, mais restrita, e reconhecida
        # como "ja tratada" (ver docs/adr/002-correcao-ruido-googleupdater.md,
        # que documenta exatamente esse caso em 3 hosts).
        atual = "^(?:RemoteRegistry|GoogleUpdaterService.*)$"
        self.assertIsNone(aeg.novo_valor(atual))

    def test_valor_vazio_nao_quebra(self):
        novo = aeg.novo_valor("")
        self.assertEqual(novo, "|GoogleUpdater.*")


if __name__ == "__main__":
    unittest.main()
