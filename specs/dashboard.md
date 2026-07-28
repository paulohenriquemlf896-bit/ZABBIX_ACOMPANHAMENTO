# Spec: Painel web (Flask)

**Status:** planejado, não implementado. Escopo inicial proposto — a
implementar em etapas, cada etapa podendo virar sua própria spec mais
detalhada se a complexidade justificar.

## Objetivo

Consolidar as visões hoje geradas como arquivos HTML estáticos
(`scripts/relatorio_problemas.py`) em um painel navegável, sempre
atualizado, acessível pela rede interna, sem precisar rodar script
manualmente para ver o estado atual.

## Regras de negócio

Reaproveita integralmente as regras de `contexto/regras_negocio.md` — o
painel não redefine o que é recorrência, severidade ou janela de tempo,
apenas apresenta os mesmos dados de forma interativa.

## Fluxo (escopo inicial)

1. Usuário acessa `http://<host-do-painel>/` na rede interna.
2. Tela inicial mostra o equivalente ao relatório de recorrência, com
   seletor de janela (`hoje|7d|30d|365d`) via querystring
   (`?periodo=7d`), permitindo link direto compartilhável.
3. Dados vêm de `src/web/services/`, que reaproveita a mesma lógica de
   agregação hoje em `scripts/relatorio_problemas.py` (extraída para um
   módulo comum — ver `docs/adr/003-evolucao-arquitetura-ai-driven-v2.md`
   sobre `src/` vs `scripts/`).
4. Cache em memória de 60s por combinação de parâmetros, para não
   reconsultar a API a cada acesso (`prompts/politicas/performance.txt`).
5. Rota `/health` expõe status de conectividade com o Zabbix
   (`prompts/politicas/monitoramento.txt`).

## Entradas

| Nome | Origem | Obrigatório |
|---|---|---|
| `periodo` | querystring | não (default `7d`) |
| `ZBX_URL`, `ZBX_TOKEN` | `.env` | sim |
| `FLASK_SECRET_KEY` | `.env` | sim (quando houver sessão/CSRF) |

## Saídas

- HTML renderizado (Jinja2, `src/web/templates/`).
- Endpoints JSON internos seguindo `padroes/padrao_respostas_api.md`.

## Validações

- `periodo` validado contra whitelist fixa — qualquer valor fora dela
  cai no default, nunca em erro 500 (`prompts/politicas/seguranca.txt`).
- Bind apenas em IP da rede interna, nunca `0.0.0.0` exposto
  (`prompts/politicas/seguranca.txt`, item 10).

## Casos extremos

- Zabbix inacessível no momento do acesso → página mostra estado de erro
  amigável, não stacktrace; `/health` reporta `zabbix_alcancavel: false`.
- Cache expirado durante pico de acesso → aceitável reconsultar a API
  (TTL curto, volume de usuários baixo — ver
  `prompts/politicas/performance.txt`).

## Fora de escopo desta primeira versão

- Autenticação de usuário (painel é só de rede interna por ora).
- Edição de configuração do Zabbix pela interface (correções de
  configuração continuam sendo scripts dedicados e confirmados, ver
  `prompts/tarefas/backend.txt`).
- Ranking por host (spec própria futura).
