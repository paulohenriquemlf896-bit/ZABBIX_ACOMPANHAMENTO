#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEMPLATE: configuracao de logging padrao do projeto.

Como usar este template:
  1. Copie o conteudo (ou importe esta funcao) em qualquer script
     agendado / de longa duracao que precise registrar em arquivo,
     alem do console (scripts CLI interativos podem continuar usando so
     print() com os prefixos padrao — ver padroes/convencoes.md).
  2. Chame configurar_logging("nome_do_script") no inicio do main().

Ver prompts/politicas/logs.txt para os niveis e a politica de rotacao.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

PASTA_LOGS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


def configurar_logging(nome_script: str, nivel_console: int = logging.INFO,
                        nivel_arquivo: int = logging.INFO) -> logging.Logger:
    """Configura logger com saida em console e em arquivo rotacionado.

    Arquivo: /logs/<nome_script>.log, ate 1MB x 5 backups (padrao do
    projeto — ver prompts/politicas/logs.txt).
    """
    os.makedirs(PASTA_LOGS, exist_ok=True)
    caminho_log = os.path.join(PASTA_LOGS, f"{nome_script}.log")

    logger = logging.getLogger(nome_script)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()  # evita handler duplicado se chamado 2x

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


# TEMPLATE: exemplo de uso
if __name__ == "__main__":
    log = configurar_logging("exemplo")
    log.info("Script iniciado")
    log.warning("Situacao anormal, mas nao fatal")
    log.error("Falha ao processar um item especifico")
    # NUNCA: log.debug(f"token={TOKEN}") — segredo nunca vai para log
    # (ver prompts/politicas/seguranca.txt, item 13)
