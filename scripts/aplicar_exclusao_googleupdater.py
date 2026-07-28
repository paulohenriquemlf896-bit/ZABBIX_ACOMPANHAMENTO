#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplica a exclusao do GoogleUpdater na descoberta de servicos do Windows.

Acrescenta '|GoogleUpdater.*' na macro {$SERVICE.NAME.NOT_MATCHES} dos
templates 'Windows by Zabbix agent' e 'Windows by Zabbix agent active',
preservando todo o valor de exclusao que ja existe.

Idempotente: se o GoogleUpdater ja estiver na macro, nao mexe.
Mostra o valor ANTES e DEPOIS de cada template.

Uso:
  python scripts/aplicar_exclusao_googleupdater.py

Dependencia: apenas a biblioteca padrao do Python (urllib), via
src/zbx_api.py — o cliente unico de acesso a API deste projeto (ver
prompts/politicas/arquitetura.txt).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from zbx_api import call_ou_falhar  # noqa: E402 — import apos sys.path

TEMPLATES = ["Windows by Zabbix agent", "Windows by Zabbix agent active"]
MACRO = "{$SERVICE.NAME.NOT_MATCHES}"
EXCLUSAO = "GoogleUpdater.*"


def novo_valor(atual):
    if EXCLUSAO in atual or "GoogleUpdater" in atual:
        return None  # ja tem
    if atual.endswith(")$"):
        return atual[:-2] + "|" + EXCLUSAO + ")$"
    return atual + "|" + EXCLUSAO


def main():
    print("Aplicando exclusao do GoogleUpdater na macro", MACRO)
    print("=" * 70)

    tpls = call_ou_falhar("template.get", {
        "output": ["templateid", "host"],
        "filter": {"host": TEMPLATES},
        "selectMacros": "extend",
    })
    if not tpls:
        print("[FALHA] Nenhum template encontrado com esses nomes.")
        sys.exit(1)

    alterados = 0
    for t in tpls:
        macro = next((m for m in t.get("macros", []) if m.get("macro") == MACRO), None)
        print(f"\nTemplate: {t['host']}")
        if not macro:
            print(f"  [PULADO] macro {MACRO} nao existe neste template.")
            continue
        atual = macro.get("value", "")
        novo = novo_valor(atual)
        print(f"  ANTES : {atual}")
        if novo is None:
            print("  [OK] Ja contem GoogleUpdater. Nada a fazer.")
            continue
        call_ou_falhar("usermacro.update", {"hostmacroid": macro["hostmacroid"], "value": novo})
        print(f"  DEPOIS: {novo}")
        print("  [APLICADO]")
        alterados += 1

    print("\n" + "=" * 70)
    print(f"Concluido. Templates alterados: {alterados}")
    print("A descoberta roda ~1x/hora; as triggers do GoogleUpdater serao")
    print("removidas na proxima execucao (conforme retencao de recurso perdido).")


if __name__ == "__main__":
    main()
