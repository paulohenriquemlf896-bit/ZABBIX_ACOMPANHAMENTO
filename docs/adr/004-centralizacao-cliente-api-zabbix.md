# ADR 004 — Centralizar a comunicação com a API do Zabbix em `src/zbx_api.py`

**Data:** 2026-07-28
**Status:** Aceito e aplicado.

## Contexto

Os 4 scripts em `scripts/` (`validar_token.py`, `relatorio_problemas.py`,
`inspecionar_servicos.py`, `aplicar_exclusao_googleupdater.py`) cada um
definia sua própria função `call()` de acesso à API JSON-RPC do Zabbix,
com `_context()` (SSL) e as constantes `ZBX_URL`/`ZBX_TOKEN`/`VERIFY_SSL`
duplicadas. Essa duplicação já estava registrada como dívida técnica em
`AI_MEMORY.md` desde a criação da estrutura de conhecimento do projeto, e
como regra explícita em `prompts/politicas/arquitetura.txt` ("extrair
para módulo comum assim que tocar em um desses scripts de novo").

Uma auditoria de arquitetura anterior a este ADR (mesma sessão) também
encontrou ~20 referências, em `prompts/` e `contexto/`, apontando
decisões novas para `contexto/decisoes.md` em vez de `docs/adr/` —
inconsistência corrigida antes desta refatoração, para que o registro
desta decisão já nascesse no lugar certo.

## Problema

Ao ler as 4 implementações lado a lado para extrair o módulo comum,
ficou claro que elas **não eram idênticas**:

- `validar_token.py` e `relatorio_problemas.py`: `call()` nunca encerra
  o processo — devolve sempre um dict; o chamador decide o que fazer.
  Token é parâmetro explícito por chamada (permite chamada
  propositalmente não autenticada, como `apiinfo.version` sem token, e
  chamada autenticada na mesma sessão de script).
- `inspecionar_servicos.py` e `aplicar_exclusao_googleupdater.py`:
  `call()` encerra o processo direto (`sys.exit(1)`) em qualquer falha,
  injeta `ZBX_TOKEN` automaticamente sem parâmetro explícito, e devolve
  só o conteúdo de `"result"`.
- **Bug encontrado**: `aplicar_exclusao_googleupdater.py` não tinha
  `try/except` em volta do `urlopen()` — uma falha de rede real (timeout,
  conexão recusada) quebraria o script com traceback cru em vez de
  `[FALHA]` limpo, ao contrário dos outros 3 scripts.
- **Código morto encontrado em `inspecionar_servicos.py`**: uma variável
  `trg` recebia o resultado de uma consulta `trigger.get` (limit 5) nunca
  usada depois, e `macros_ref = set()` era declarada e nunca lida.

## Alternativas avaliadas

1. **Extrair só a assinatura mais comum e forçar os 4 scripts a se
   adequarem a ela** — descartado: perderia a distinção intencional de
   `validar_token.py` entre chamada autenticada e não autenticada, que é
   o propósito central desse script (testar as duas situações).
2. **Duas funções no módulo comum** — `call()` (nunca encerra, token
   explícito) e `call_ou_falhar()` (encerra em falha, token
   automático) — cada script usa a que já usava, sem mudar de
   comportamento observável — escolhida.
3. **Não centralizar agora, só remover o código morto e corrigir o bug
   pontualmente em cada script** — descartado: não resolve a duplicação
   em si, que é a dívida técnica original a ser paga.

## Decisão tomada

Criado `src/zbx_api.py` com:
- `call(method, params, token, timeout)` — nunca levanta exceção nem
  encerra o processo; erros de conexão/HTTP/inesperados viram
  `{"__error__": "..."}`; erros de aplicação do Zabbix mantêm o formato
  nativo `{"error": {...}}`. Não injeta `ZBX_TOKEN` automaticamente.
- `call_ou_falhar(method, params, token=ZBX_TOKEN, timeout)` — chama
  `call()`, imprime `[FALHA] <método>: <mensagem>` e `sys.exit(1)` em
  qualquer falha; em sucesso devolve direto `result`. Usa `ZBX_TOKEN`
  automaticamente quando `token` não é passado.

`validar_token.py` e `relatorio_problemas.py` passaram a importar e usar
`call()` diretamente, preservando seu tratamento de erro específico linha
por linha. `inspecionar_servicos.py` e `aplicar_exclusao_googleupdater.py`
passaram a usar `call_ou_falhar()` em todos os pontos de chamada.

Cada script adiciona `sys.path.insert(0, ".../src")` antes do import —
sem instalar nada, sem `PYTHONPATH`, funciona independente do diretório
de onde o script é chamado (testado).

O código morto identificado foi removido; o bug do `try/except` ausente
foi corrigido como efeito direto de passar a usar `call_ou_falhar()`
(que sempre passa por `call()`, que sempre tem os 3 níveis de tratamento
de erro).

## Justificativa

Preservar duas funções em vez de uma só evita forçar uma falsa unificação
de comportamento onde os scripts tinham necessidades genuinamente
diferentes (teste de conectividade não autenticada vs. utilitário que só
quer o resultado ou falhar). Isso respeita
`prompts/politicas/principios.txt` (retrocompatibilidade, simplicidade —
duas funções pequenas e claras, não uma função com flags para simular
dois comportamentos). A correção do bug e a remoção de código morto são
consequência natural de centralizar (agora só existe um lugar para esse
tipo de erro escapar), não um esforço à parte.

## Consequências

- Duplicação de ~30 linhas por script (120 linhas totais) eliminada;
  qualquer mudança futura no protocolo de comunicação com o Zabbix
  (ex.: novo header, novo timeout padrão) muda em um lugar só.
- `aplicar_exclusao_googleupdater.py` ganhou tratamento de erro de rede
  que não tinha antes — comportamento mais seguro, não só mais limpo.
- Testes automatizados cobrindo `src/zbx_api.py` criados em
  `src/tests/test_zbx_api.py` (11 casos, 100% offline via mock de
  `urlopen`) — primeira suíte de testes do projeto, resolvendo
  parcialmente a dívida técnica "sem testes automatizados" registrada em
  `AI_MEMORY.md`. Os 4 scripts continuam sem cobertura de teste própria
  (sua lógica de domínio, como `agregar()`, permanece candidata futura).
- Validação end-to-end contra o Zabbix real ficou **incompleta** nesta
  sessão: o servidor (`192.168.11.12`) está retornando
  `Internal error: No such file or directory` na API (`api_jsonrpc.php`)
  desde antes desta refatoração — confirmado com `curl` puro, sem
  qualquer código deste projeto envolvido, então não é uma regressão
  desta mudança. A interface web do Zabbix responde normalmente (HTTP
  200); o problema é específico do endpoint da API, provavelmente
  PHP-FPM ou um caminho de sessão ausente no servidor. Os 4 scripts foram
  validados por falharem de forma limpa e idêntica diante desse erro
  (prova de que a camada de erro funciona), mas o caminho de sucesso não
  pôde ser confirmado contra dados reais nesta sessão. Registrado como
  risco em `AI_MEMORY.md`.
