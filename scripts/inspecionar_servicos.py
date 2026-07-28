#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inspeciona (somente leitura) a descoberta de servicos do Windows no Zabbix,
para descobrir QUAL macro/regex usar para excluir o ruido do Google Updater.

Mostra:
  - as regras de descoberta (LLD) de servicos e o filtro atual;
  - as macros relacionadas a servico no template e o valor de cada uma;
  - quais hosts/templates tem triggers do GoogleUpdater.

NAO altera nada. So le.

Uso:
  python scripts/inspecionar_servicos.py

Dependencia: apenas a biblioteca padrao do Python (urllib), via
src/zbx_api.py — o cliente unico de acesso a API deste projeto (ver
prompts/politicas/arquitetura.txt).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from zbx_api import call_ou_falhar  # noqa: E402 — import apos sys.path


def main():
    print("=" * 70)
    print("  Inspecao da descoberta de servicos (Windows) - Zabbix")
    print("=" * 70)

    # 1) Regras de descoberta (LLD) relacionadas a servicos
    print("\n>>> Regras de descoberta (LLD) de servicos:\n")
    rules = call_ou_falhar("discoveryrule.get", {
        "output": ["itemid", "name", "key_", "status"],
        "selectFilter": "extend",
        "selectHosts": ["hostid", "host", "status"],
        "search": {"key_": "service"},
        "searchWildcardsEnabled": True,
    })
    if not rules:
        rules = call_ou_falhar("discoveryrule.get", {
            "output": ["itemid", "name", "key_", "status"],
            "selectFilter": "extend",
            "selectHosts": ["hostid", "host", "status"],
            "search": {"name": "service"},
        })

    for r in rules:
        onde = ", ".join(f"{h['host']}{' [TEMPLATE]' if h.get('status') == '3' else ''}"
                         for h in r.get("hosts", []))
        st = "ATIVA" if r.get("status") == "0" else "DESABILITADA"
        print(f"  - Regra: {r['name']}  ({st})")
        print(f"    key: {r['key_']}")
        print(f"    em : {onde}")
        flt = r.get("filter", {})
        conds = flt.get("conditions", [])
        if conds:
            print(f"    filtro (avaliacao: {flt.get('evaltype')}):")
            for c in conds:
                macro = c.get("macro", "")
                val = c.get("value", "")
                op = c.get("operator", "")
                print(f"        {macro}  op={op}  valor={val!r}")
        else:
            print("    (sem filtro configurado)")
        print()

    # 2) Macros de SERVICE nos templates/hosts que tem essas regras
    host_ids = sorted({h["hostid"] for r in rules for h in r.get("hosts", [])})
    if host_ids:
        print(">>> Macros relacionadas a 'SERVICE' nesses templates/hosts:\n")
        tpls = call_ou_falhar("template.get", {
            "output": ["host"], "templateids": host_ids, "selectMacros": "extend",
        })
        hsts = call_ou_falhar("host.get", {
            "output": ["host"], "hostids": host_ids, "selectMacros": "extend",
        })
        for obj in (tpls + hsts):
            svc_macros = [m for m in obj.get("macros", []) if "SERVICE" in m.get("macro", "")]
            if svc_macros:
                print(f"  {obj['host']}:")
                for m in svc_macros:
                    print(f"      {m['macro']} = {m.get('value', '')!r}")
                print()

        # macros globais
        gm = call_ou_falhar("usermacro.get", {"globalmacro": True, "output": "extend"})
        svc_g = [m for m in gm if "SERVICE" in m.get("macro", "")]
        if svc_g:
            print("  [Macros GLOBAIS]:")
            for m in svc_g:
                print(f"      {m['macro']} = {m.get('value', '')!r}")
            print()

    # 3) Onde estao as triggers do GoogleUpdater
    print(">>> Triggers do 'GoogleUpdater' (amostra) e onde estao:\n")
    hosts_afetados = call_ou_falhar("trigger.get", {
        "output": ["triggerid"],
        "selectHosts": ["host"],
        "search": {"description": "GoogleUpdater"},
    })
    distintos = sorted({h["host"] for t in hosts_afetados for h in t.get("hosts", [])})
    print(f"  Total de triggers GoogleUpdater: {len(hosts_afetados)}")
    print(f"  Hosts afetados: {', '.join(distintos) or '(nenhum)'}\n")

    print("=" * 70)
    print("COMO EXCLUIR (use a macro de NOT_MATCHES mostrada acima):")
    print("  No template, defina a macro de exclusao de NOME de servico para:")
    print("      GoogleUpdater.*")
    print("  Isso remove todas as versoes de uma vez na proxima descoberta.")
    print("=" * 70)


if __name__ == "__main__":
    main()
