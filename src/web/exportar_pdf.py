#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera o relatorio de exportacao em PDF — ver specs/exportacao_relatorio.md.

Documento unico (PDF nao tem "aba"), uma secao por periodo selecionado,
mesma paleta oficial de severidade do Zabbix (src/relatorios_service.py).

Dependencia: fpdf2 (ver requirements.txt e specs/exportacao_relatorio.md
para a justificativa — biblioteca padrao nao gera PDF).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from relatorios_service import SEV_NOME, SEV_COR, fmt_ts  # noqa: E402

from fpdf import FPDF
from fpdf.fonts import FontFace

LARGURAS_COLUNA = (8, 85, 18, 14, 22, 55, 28)
COLUNAS = ["#", "Problema", "Ocorr.", "%", "Gravidade", "Hosts afetados", "Ultima vez"]


def _cor_rgb(hex_cor: str) -> tuple:
    hex_cor = hex_cor.lstrip("#")
    return tuple(int(hex_cor[i:i + 2], 16) for i in (0, 2, 4))


def _escrever_periodo(pdf, dados):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, dados["titulo"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)

    if not dados["ranking"]:
        pdf.cell(0, 6, "Nenhum problema registrado neste periodo.", new_x="LMARGIN", new_y="NEXT")
        return

    total = dados["total"]
    cabecalho_estilo = FontFace(emphasis="BOLD", fill_color=(240, 242, 245))
    with pdf.table(col_widths=LARGURAS_COLUNA, text_align="LEFT",
                   headings_style=cabecalho_estilo, line_height=6) as table:
        linha = table.row()
        for coluna in COLUNAS:
            linha.cell(coluna)
        for i, g in enumerate(dados["ranking"], 1):
            pct = (g["count"] / total * 100) if total else 0
            linha = table.row()
            linha.cell(str(i))
            linha.cell(g["nome"])
            linha.cell(str(g["count"]))
            linha.cell(f"{pct:.1f}%")
            linha.cell(SEV_NOME.get(g["sev"], "?"),
                       style=FontFace(fill_color=_cor_rgb(SEV_COR.get(g["sev"], "#97AAB3"))))
            linha.cell(", ".join(sorted(g["hosts"])))
            linha.cell(fmt_ts(g["ultimo"]))


def gerar_pdf(dados_por_periodo: dict, hosts_selecionados: list, gerado_em: str) -> bytes:
    """dados_por_periodo: mesmo shape de
    src/web/services/exportacao.py:dados_exportacao(). Devolve os bytes
    do arquivo .pdf pronto para download."""
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Relatorio de problemas recorrentes - Acompanhamento Zabbix",
              new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    titulos = ", ".join(d["titulo"] for d in dados_por_periodo.values())
    hosts_txt = ", ".join(hosts_selecionados) if hosts_selecionados else "Todos"
    pdf.multi_cell(0, 6, f"Gerado em {gerado_em}\nPeriodos: {titulos}\nHosts: {hosts_txt}")

    for dados in dados_por_periodo.values():
        _escrever_periodo(pdf, dados)

    return bytes(pdf.output())
