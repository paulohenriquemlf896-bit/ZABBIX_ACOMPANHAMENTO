# Convenções gerais

Convenções práticas de formato e comportamento que não se encaixam em
nomenclatura, estrutura de pastas ou resposta de API — mas que todo
código novo deve seguir por padrão. Origem das regras: prompts
correspondentes citados em cada seção; este arquivo é a referência
rápida e consultável.

## Formato de data e hora

- Exibição ao usuário: `dd/mm/aaaa hh:mm` (ex.: `27/07/2026 16:54`).
- Persistência (banco, quando existir): ISO 8601 UTC.
- Timestamp em nome de arquivo gerado: `AAAAMMDD_HHMM`.
- Timestamp bruto do Zabbix (`clock`, unix epoch): sempre convertido no
  ponto de entrada, nunca propagado cru para a camada de apresentação.

## Formato numérico

- Separador de milhar em números grandes exibidos ao usuário.
- Percentual com 1 casa decimal (`70.8%`).
- Números em tabela: alinhados à direita, `tabular-nums`.

## Cores de severidade (fixas, nunca redefinir)

| Severidade | Cor |
|---|---|
| Desastre | `#E45959` |
| Alta | `#E97659` |
| Média | `#FFA059` |
| Aviso | `#FFC859` |
| Informação | `#7499FF` |
| Não classificado | `#97AAB3` |

Ver `prompts/tarefas/frontend.txt`.

## Prefixos de console (fixos, vocabulário único do projeto)

`[OK]` `[FALHA]` `[info]` `[..]` `[PULADO]` `[APLICADO]` — ver
`prompts/politicas/logs.txt`.

## Configuração de script (bloco padrão no topo do arquivo)

```python
# =========================================================================
# CONFIGURACAO
# =========================================================================
ZBX_URL = os.environ.get("ZBX_URL", "")
ZBX_TOKEN = os.environ.get("ZBX_TOKEN", "")
VERIFY_SSL = True
# =========================================================================
```

Ver `prompts/politicas/configuracao.txt` e `templates/api_service.py`.

## Docstring de módulo (todo script executável)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
<O que o script faz em uma frase>.

Uso:
  python scripts/nome.py

Saidas:
  <o que gera e onde>

Dependencia: apenas a biblioteca padrao do Python.
"""
```

## Tratamento de erro de chamada de rede (3 camadas, sempre as mesmas)

1. Erro de conexão (`urllib.error.URLError`) — problema de rede/timeout.
2. Erro HTTP (`urllib.error.HTTPError`) — servidor respondeu com status
   de erro.
3. Erro de aplicação (corpo com `{"error": ...}`) — servidor respondeu
   200 mas a operação falhou.

Ver `prompts/tarefas/backend.txt` e `templates/api_service.py`.

## Idempotência de scripts de escrita

Todo script que altera configuração no Zabbix: lê o estado atual,
compara com o estado desejado, só escreve se for diferente, e informa
`[PULADO]` quando já está no estado esperado. Ver
`prompts/politicas/seguranca.txt` e o exemplo real em
`scripts/aplicar_exclusao_googleupdater.py`.
