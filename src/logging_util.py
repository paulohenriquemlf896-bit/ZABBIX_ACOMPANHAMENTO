#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuracao de logging padrao do projeto para processos de longa
duracao (ex.: o painel web) — ver prompts/politicas/logs.txt.

Scripts CLI interativos continuam usando so print() com os prefixos
padrao ([OK]/[FALHA]/...) — este modulo e para o outro caso: servico que
fica de pe respondendo requisicoes, onde so console nao basta.

Graduado de templates/logging.py (o template generico) para codigo real
assim que o painel web precisou de logging estruturado pela primeira vez
(ver docs/CHANGELOG.md).
"""

import logging
import os
from logging.handlers import RotatingFileHandler

PASTA_LOGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")


def configurar_logging(nome_script: str, nivel_console: int = logging.INFO,
                        nivel_arquivo: int = logging.INFO) -> logging.Logger:
    """Configura logger com saida em console e em arquivo rotacionado.

    Arquivo: /logs/<nome_script>.log, ate 1MB x 5 backups (padrao do
    projeto — ver prompts/politicas/logs.txt). Idempotente: chamar de
    novo com o mesmo nome so reconfigura os mesmos handlers, nunca
    duplica.
    """
    os.makedirs(PASTA_LOGS, exist_ok=True)
    caminho_log = os.path.join(PASTA_LOGS, f"{nome_script}.log")

    logger = logging.getLogger(nome_script)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    formato = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    handler_arquivo = RotatingFileHandler(
        caminho_log, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    handler_arquivo.setLevel(nivel_arquivo)
    handler_arquivo.setFormatter(formato)
    logger.addHandler(handler_arquivo)

    handler_console = logging.StreamHandler()
    handler_console.setLevel(nivel_console)
    handler_console.setFormatter(formato)
    logger.addHandler(handler_console)

    return logger
