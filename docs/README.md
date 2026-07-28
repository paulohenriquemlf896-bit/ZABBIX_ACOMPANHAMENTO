# Acompanhamento Zabbix — Grupo Rancho

Scripts Python que consomem a API do Zabbix 7.4 para gerar relatórios de
disponibilidade e recorrência de problemas, inspecionar configuração e
aplicar correções controladas na infraestrutura monitorada do Grupo
Rancho.

Este projeto segue uma arquitetura orientada por IA (AI-Driven
Development). Se for a primeira vez trabalhando aqui, **comece por
[`/AI_BOOTSTRAP.md`](../AI_BOOTSTRAP.md)** — ele define a ordem correta
de leitura de todo o projeto (bootstrap → `CLAUDE.md` → prompts →
contexto → docs → `AI_MEMORY.md` → roadmap → código-fonte).

## Pré-requisitos

- Python 3.10 ou superior.
- Acesso de rede a `192.168.11.12` (rede interna do Grupo Rancho).
- Um token de API do Zabbix (gerado em **Usuários → Tokens de API** na
  interface web do Zabbix).
- Para o painel web (`/src/web`): dependências em
  [`requirements.txt`](../requirements.txt) —
  `pip install -r requirements.txt`. Os scripts em `/scripts` não
  precisam disso (só biblioteca padrão).

## Configuração

Defina as variáveis de ambiente antes de rodar qualquer script (ver
também [`.env.example`](../.env.example)):

```bash
export ZBX_URL="http://192.168.11.12/zabbix/api_jsonrpc.php"
export ZBX_TOKEN="SEU_TOKEN_AQUI"
```

No PowerShell:

```powershell
$env:ZBX_URL="http://192.168.11.12/zabbix/api_jsonrpc.php"
$env:ZBX_TOKEN="SEU_TOKEN_AQUI"
```

> Nunca coloque o token real em código versionado ou documentação — ver
> [`prompts/politicas/seguranca.txt`](../prompts/politicas/seguranca.txt).

## Cliente da API (`/src`)

### `zbx_api.py`
Cliente único de acesso à API JSON-RPC do Zabbix — nenhum outro módulo
deste projeto monta requisição HTTP diretamente. Expõe `call()` (nunca
encerra o processo, token explícito por chamada) e `call_ou_falhar()`
(encerra com `[FALHA]` em qualquer erro, usa `ZBX_TOKEN` automaticamente).
Usado pelos 4 scripts abaixo. Testes em `src/tests/test_zbx_api.py`
(`python -m unittest discover src/tests`). Ver
[`docs/adr/004-centralizacao-cliente-api-zabbix.md`](adr/004-centralizacao-cliente-api-zabbix.md).

### `relatorios_service.py`
Camada de domínio/serviço do relatório de problemas recorrentes (busca de
eventos, agregação, janelas de tempo, mapas de severidade) — extraída de
`scripts/relatorio_problemas.py` para ser reaproveitada também pelo
painel web, sem duplicar a lógica. Testes em
`src/tests/test_relatorios_service.py`. Ver
[`docs/adr/005-painel-web-flask.md`](adr/005-painel-web-flask.md).

`/src` é reservado para código que roda como aplicação contínua (este
cliente, a camada de domínio compartilhada, e o painel web) — ver
`padroes/estrutura_pastas.md`.

## Painel web (`/src/web`)

Painel Flask que consolida a visão de problemas recorrentes numa tela
navegável, com seletor de período (`?periodo=hoje|7d|30d|365d`) e de
visão (`?visao=problema|host` — ranking por nome do problema ou por host
afetado, ver [`specs/ranking_por_host.md`](../specs/ranking_por_host.md)),
cache de 60s, e auto-atualização periódica (meta refresh, mesmo
intervalo do cache). Cada visão tem um gráfico de barras (ranking) e uma
barra de mix de severidade, além da tabela detalhada. Escopo inicial
(sem autenticação, sem escrita no Zabbix) definido em
[`specs/dashboard.md`](../specs/dashboard.md); decisão arquitetural em
[`docs/adr/005-painel-web-flask.md`](adr/005-painel-web-flask.md).

```bash
pip install -r requirements.txt
export ZBX_URL="http://192.168.11.12/zabbix/api_jsonrpc.php"
export ZBX_TOKEN="SEU_TOKEN_AQUI"
python src/web/app.py
```

Sobe em `http://127.0.0.1:8080` via `waitress` (nunca o servidor de debug
do Flask — ver `prompts/tarefas/backend.txt`, item 13). Ajustável com as
variáveis `PAINEL_HOST`/`PAINEL_PORT`. Rota `GET /health` expõe status de
conectividade com o Zabbix; rota `GET /api/relatorios/dados?periodo=...`
expõe os mesmos dados em JSON (`padroes/padrao_respostas_api.md`).
Testes em `src/tests/test_web_app.py` e
`src/tests/test_web_service_relatorios.py`.

## Inventário de scripts (`/scripts`)

Utilitários pontuais — relatórios, inspeção e correções de configuração.
Todos importam `src/zbx_api.py` para falar com o Zabbix.

### `validar_token.py`
Valida conectividade com a API do Zabbix e confere se o token configurado
autentica corretamente, mostrando o usuário e a permissão associados.

```bash
python scripts/validar_token.py
```

### `relatorio_problemas.py`
Gera o relatório de problemas mais recorrentes em 4 janelas de tempo
(Hoje, 7 dias, 30 dias, 365 dias), com ranking, severidade e hosts
afetados. Spec: [`specs/relatorios.md`](../specs/relatorios.md).

```bash
python scripts/relatorio_problemas.py
```

Saída: `scripts/saidas/relatorio_problemas_AAAAMMDD_HHMM.html` (visual,
imprimível como PDF) e `.csv` (dados brutos).

### `inspecionar_servicos.py`
Inspeciona (somente leitura) a descoberta de serviços do Windows: regras
de LLD, filtros/macros atuais e onde estão as triggers de um serviço
específico. Útil para investigar ruído de alertas.

```bash
python scripts/inspecionar_servicos.py
```

### `aplicar_exclusao_googleupdater.py`
Script de correção pontual que adiciona `GoogleUpdater.*` à macro de
exclusão de serviços nos templates Windows, preservando o valor anterior.
Idempotente. Ver
[`docs/adr/002-correcao-ruido-googleupdater.md`](adr/002-correcao-ruido-googleupdater.md).

```bash
python scripts/aplicar_exclusao_googleupdater.py
```

## Estrutura do projeto

```
/
├── AI_BOOTSTRAP.md   — ordem de leitura obrigatória (comece aqui)
├── AI_MEMORY.md       — memória viva: features, dívidas, riscos, roadmap
├── CLAUDE.md           — porta de entrada: visão geral, regras, checklist
├── prompts/             — regras permanentes (politicas/tarefas/workflow)
├── padroes/               — convenções permanentes (não é código)
├── templates/              — modelos reutilizáveis de código
├── specs/                   — especificação de cada funcionalidade
├── examples/                  — exemplos reais (payloads, HTML, CSV)
├── contexto/                  — conhecimento sobre como o projeto funciona
├── docs/                       — este README, CHANGELOG
│   └── adr/                      — uma decisão arquitetural por arquivo
├── logs/                          — logs de execução
├── requirements.txt                — dependências externas (flask, waitress)
├── scripts/                        — os 4 utilitários listados acima
└── src/                             — zbx_api.py, relatorios_service.py,
                                      painel web (src/web/) + testes
```

Detalhe completo de cada pasta:
[`padroes/estrutura_pastas.md`](../padroes/estrutura_pastas.md).

## Documentação relacionada

- [`docs/CHANGELOG.md`](CHANGELOG.md) — histórico de mudanças, incluindo
  mudanças de configuração aplicadas diretamente no Zabbix.
- [`docs/adr/`](adr) — decisões arquiteturais, uma por arquivo.
- [`contexto/dashboard.md`](../contexto/dashboard.md) — o que cada
  relatório responde e quando usar qual.
- [`AI_MEMORY.md`](../AI_MEMORY.md) — estado corrente do projeto.
