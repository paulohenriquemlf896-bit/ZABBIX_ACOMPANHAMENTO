#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relatorio de problemas mais recorrentes do Zabbix (7.4).

Puxa os eventos de PROBLEMA (source=trigger) do ultimo ano via API e gera:
  - um relatorio HTML (imprimivel como PDF) com o ranking dos problemas
    mais recorrentes em 4 janelas: Hoje, 7 dias, 30 dias e 365 dias;
  - um CSV consolidado com todas as janelas.

Recorrencia = quantas vezes cada problema (trigger) DISPAROU no periodo.

Uso:
  python scripts/relatorio_problemas.py
  (ou defina as variaveis de ambiente ZBX_URL e ZBX_TOKEN)

Dependencia: apenas a biblioteca padrao do Python, via src/zbx_api.py e
src/relatorios_service.py (logica de agregacao compartilhada com o
painel web — ver docs/adr/005-painel-web-flask.md). Nada para instalar.
"""

import csv
import os
import sys
from datetime import datetime
from html import escape

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from zbx_api import call, ZBX_URL, ZBX_TOKEN  # noqa: E402 — import apos sys.path
from relatorios_service import (  # noqa: E402
    buscar_eventos, agregar, fmt_ts, janelas, MAX_EVENTOS, SEV_NOME, SEV_COR,
)

# =========================================================================
# CONFIGURACAO ESPECIFICA DESTE RELATORIO
# =========================================================================
TOP_N = 20                 # quantos problemas listar no ranking de cada janela
PASTA_SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saidas")
# =========================================================================


def tabela_html(ranking, total):
    if not ranking:
        return "<p class='vazio'>Nenhum problema registrado neste periodo.</p>"
    linhas = []
    for i, g in enumerate(ranking[:TOP_N], 1):
        pct = (g["count"] / total * 100) if total else 0
        cor = SEV_COR.get(g["sev"], "#97AAB3")
        sev = SEV_NOME.get(g["sev"], "?")
        hosts = ", ".join(sorted(g["hosts"]))
        linhas.append(f"""<tr>
          <td class="rank">{i}</td>
          <td class="nome">{escape(g['nome'])}</td>
          <td class="num">{g['count']}</td>
          <td class="num">{pct:.1f}%</td>
          <td><span class="badge" style="background:{cor}">{sev}</span></td>
          <td class="hosts">{escape(hosts)}</td>
          <td class="data">{fmt_ts(g['ultimo'])}</td>
        </tr>""")
    return f"""<table>
      <thead><tr>
        <th>#</th><th>Problema</th><th>Ocorr.</th><th>%</th>
        <th>Gravidade</th><th>Hosts afetados</th><th>Ultima vez</th>
      </tr></thead>
      <tbody>{''.join(linhas)}</tbody>
    </table>"""


def barra_sev(por_sev, total):
    partes = []
    for s in [5, 4, 3, 2, 1, 0]:
        n = por_sev.get(s, 0)
        if n == 0:
            continue
        partes.append(f'<span class="pill" style="background:{SEV_COR[s]}">'
                      f'{SEV_NOME[s]}: {n}</span>')
    return f'<div class="sevrow"><b>Total: {total}</b> &nbsp; {" ".join(partes)}</div>'


def main():
    print("Relatorio de problemas recorrentes - Zabbix")
    print(f"Endpoint: {ZBX_URL}\n")

    # valida conexao/versao
    v = call("apiinfo.version")
    if "result" not in v:
        print(f"[FALHA] Nao conectou: {v}")
        sys.exit(1)
    print(f"[OK] Conectado. API {v['result']}")

    agora = datetime.now()
    janelas_lista = janelas(agora)
    ano_ts = int(janelas_lista[-1][1].timestamp())

    print("[..] Buscando eventos do ultimo ano...")
    eventos, erro = buscar_eventos(ano_ts, ZBX_TOKEN)
    if erro:
        print(f"[FALHA] {erro}")
        sys.exit(1)
    print(f"[OK] {len(eventos)} eventos de problema recebidos.")
    if len(eventos) >= MAX_EVENTOS:
        print(f"     (atingiu o teto de {MAX_EVENTOS}; aumente MAX_EVENTOS se precisar de mais)")

    # monta HTML + coleta linhas do CSV
    secoes = []
    csv_linhas = []
    console = []
    for titulo, dt in janelas_lista:
        desde = int(dt.timestamp())
        ranking, total, por_sev = agregar(eventos, desde)
        secoes.append(f"""<section>
          <h2>{escape(titulo)} <small>(desde {dt.strftime('%d/%m/%Y %H:%M')})</small></h2>
          {barra_sev(por_sev, total)}
          {tabela_html(ranking, total)}
        </section>""")
        for g in ranking:
            csv_linhas.append({
                "periodo": titulo,
                "problema": g["nome"],
                "ocorrencias": g["count"],
                "gravidade": SEV_NOME.get(g["sev"], "?"),
                "hosts": ", ".join(sorted(g["hosts"])),
                "primeira_vez": fmt_ts(g["primeiro"]),
                "ultima_vez": fmt_ts(g["ultimo"]),
            })
        console.append((titulo, total, ranking[:5]))

    gerado = agora.strftime("%d/%m/%Y %H:%M:%S")
    html = f"""<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<title>Relatorio de problemas recorrentes - Zabbix</title>
<style>
  body{{font-family:Segoe UI,Arial,sans-serif;color:#222;margin:24px;background:#f7f8fa}}
  h1{{margin:0 0 4px}} .sub{{color:#666;margin-bottom:24px;font-size:14px}}
  section{{background:#fff;border:1px solid #e3e6ea;border-radius:8px;padding:16px 20px;margin-bottom:22px}}
  h2{{margin:0 0 10px;font-size:18px;border-bottom:2px solid #eee;padding-bottom:6px}}
  h2 small{{color:#888;font-weight:normal;font-size:13px}}
  table{{width:100%;border-collapse:collapse;font-size:13px}}
  th,td{{padding:7px 9px;text-align:left;border-bottom:1px solid #eee;vertical-align:top}}
  th{{background:#f0f2f5;font-size:12px;text-transform:uppercase;letter-spacing:.3px}}
  td.rank{{font-weight:bold;color:#888;width:28px}}
  td.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
  td.nome{{font-weight:600;max-width:420px}}
  td.hosts{{color:#555;font-size:12px}} td.data{{white-space:nowrap;color:#555}}
  .badge{{color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;white-space:nowrap}}
  .sevrow{{margin:6px 0 12px;font-size:13px}}
  .pill{{color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;margin-right:4px;display:inline-block}}
  .vazio{{color:#888;font-style:italic}}
  tr:nth-child(even) td{{background:#fafbfc}}
  @media print{{body{{background:#fff;margin:0}} section{{break-inside:avoid;border:none}}}}
</style></head><body>
<h1>Relatorio de problemas mais recorrentes</h1>
<div class="sub">Zabbix {v['result']} &middot; {escape(ZBX_URL)} &middot; gerado em {gerado}</div>
{''.join(secoes)}
<div class="sub">Recorrencia = numero de vezes que cada trigger entrou em estado de PROBLEMA no periodo.
Base: ultimos {len(eventos)} eventos.</div>
</body></html>"""

    stamp = agora.strftime("%Y%m%d_%H%M")
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    html_path = os.path.join(PASTA_SAIDA, f"relatorio_problemas_{stamp}.html")
    csv_path = os.path.join(PASTA_SAIDA, f"relatorio_problemas_{stamp}.csv")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["periodo", "problema", "ocorrencias",
                                          "gravidade", "hosts", "primeira_vez", "ultima_vez"])
        w.writeheader()
        w.writerows(csv_linhas)

    # resumo no console
    print("\n" + "=" * 60)
    for titulo, total, top5 in console:
        print(f"\n{titulo} - {total} ocorrencias")
        if not top5:
            print("   (sem problemas)")
        for i, g in enumerate(top5, 1):
            print(f"   {i}. [{g['count']:>4}x] {g['nome'][:70]}")
    print("\n" + "=" * 60)
    print(f"Relatorio HTML: {html_path}")
    print(f"CSV:            {csv_path}")
    print("Abra o HTML no navegador e use Ctrl+P > 'Salvar como PDF' se quiser PDF.")


if __name__ == "__main__":
    main()
