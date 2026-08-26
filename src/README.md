# src/ — a aplicação

Esta pasta contém **apenas a aplicação** do projeto: código pensado para
ser importado/rodar continuamente, não scripts pontuais (esses ficam em
[`/scripts`](../scripts) — ver `padroes/estrutura_pastas.md` para a regra
completa de separação).

## O que existe hoje

```
src/
├── zbx_api.py             — cliente único de acesso à API do Zabbix
│                            (call, call_ou_falhar — ver docs/adr/004)
├── relatorios_service.py   — camada de dominio/servico do relatorio de
│                            problemas recorrentes (busca, agregacao,
│                            janelas, severidade) — compartilhada entre
│                            scripts/relatorio_problemas.py e o painel
│                            web (ver docs/adr/005)
├── logging_util.py          — configuracao de logging padrao do projeto
│                            para processos de longa duracao (ver
│                            prompts/politicas/logs.txt)
├── db.py                     — acesso ao banco proprio (SQLite, so
│                            usuarios do painel hoje — ver docs/adr/006)
├── web/                     — painel Flask (ver docs/adr/005 e
│   ├── app.py               specs/dashboard.md)
│   ├── api.py
│   ├── auth.py                — login/sessao (ver docs/adr/006)
│   ├── services/relatorios.py  — cache de 60s sobre relatorios_service.py
│   └── templates/
└── tests/
    ├── test_zbx_api.py
    ├── test_relatorios_service.py
    ├── test_web_service_relatorios.py
    ├── test_web_app.py
    ├── test_relatorio_problemas_apresentacao.py
    ├── test_aplicar_exclusao_googleupdater.py
    ├── test_db.py
    └── test_auth.py
```

`zbx_api.py` e `relatorios_service.py` são importados pelos scripts de
`/scripts` e pelo painel web via `sys.path.insert`. Rodar os testes:

```bash
python -m unittest discover src/tests
```

Rodar o painel (primeira vez, cria banco e usuário — ver
`docs/README.md` para o passo a passo completo):

```bash
pip install -r requirements.txt
python scripts/aplicar_migrations.py
python scripts/criar_usuario.py SEU_NOME
python src/web/app.py
```
