# API do Zabbix — conhecimento acumulado

O que já foi aprendido na prática sobre a API JSON-RPC deste servidor
Zabbix 7.4.4, além do que está na documentação oficial. Atualizar quando
uma nova peculiaridade for descoberta.

## Autenticação

- Zabbix 7.x usa header `Authorization: Bearer <token>`. O campo `auth`
  no corpo da requisição **não deve** ser enviado — misturar os dois
  quebra a chamada.
- `user.login` e outros métodos de autenticação por usuário/senha não são
  usados neste projeto; o fluxo é 100% via API token pré-gerado na
  interface (**Usuários → Tokens de API**).

## Métodos usados até agora

| Método | Uso neste projeto |
|---|---|
| `apiinfo.version` | Validar conectividade e versão, sem precisar de token |
| `event.get` | Buscar eventos de PROBLEMA (`source=0, object=0, value=1`) para relatório de recorrência |
| `host.get` | Listar hosts, inventário, interfaces |
| `user.get` | Identificar o usuário dono do token (`validar_token.py`) |
| `discoveryrule.get` | Inspecionar regras de descoberta (LLD) de serviços |
| `template.get` / `host.get` com `selectMacros` | Ler macros de template/host |
| `usermacro.update` | Escrever valor de macro (uso controlado — ver `prompts/politicas/seguranca.txt`) |
| `trigger.get` | Localizar triggers por nome (ex.: busca por "GoogleUpdater") |

## Peculiaridades e armadilhas já encontradas

- **`history.get`** exige o parâmetro `history` com o tipo certo do item
  (0 float, 1 char, 2 log, 3 uint, 4 text) — sem isso o resultado vem
  vazio silenciosamente. Descobrir o tipo via `item.get` (`value_type`)
  antes de consultar.
- **Regex de exclusão em macros de LLD** (`{$SERVICE.NAME.NOT_MATCHES}`)
  usa sintaxe POSIX ERE. Um padrão como `^GoogleUpdaterService.*` não
  cobre `GoogleUpdaterInternalService...` — é preciso um padrão mais
  amplo (`GoogleUpdater.*`, sem member `^...Service` fixo) para pegar
  todas as variações de serviço criadas pelo instalador do Chrome.
- **Volume de eventos**: em uma janela de 365 dias, este ambiente retorna
  ~23 mil eventos de problema. Consultas sem `limit` explícito arriscam
  respostas muito grandes — sempre paginar/limitar (ver
  `prompts/politicas/performance.txt`).
- **Precedência de exclusões manuais vs. macro de template**: quando um
  host tem uma condição de filtro adicionada diretamente na regra de
  descoberta (fora da macro do template), ela convive com a macro, mas é
  fácil ficar inconsistente entre hosts (foi o que causou o problema do
  GoogleUpdater — ver `docs/adr/002-correcao-ruido-googleupdater.md`).

## Estrutura de resposta padrão

- Sucesso: `{"jsonrpc": "2.0", "result": [...], "id": 1}`
- Erro: `{"jsonrpc": "2.0", "error": {"code": ..., "message": ...,
  "data": ...}, "id": 1}` — o campo `data` costuma ter a mensagem mais
  específica e é o que deve ser mostrado ao usuário.
