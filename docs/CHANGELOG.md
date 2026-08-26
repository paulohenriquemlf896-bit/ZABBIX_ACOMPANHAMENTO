# Changelog

Formato: data (aaaa-mm-dd), o que mudou e por quê. Ordem cronológica
inversa (mais recente primeiro). Mudanças de configuração aplicadas
diretamente no Zabbix também entram aqui — ver
[`prompts/politicas/documentacao.txt`](../prompts/politicas/documentacao.txt).

## 2026-08-26 (2) — Painel sobe sozinho ao logar no Windows (tarefa agendada)

- **Pedido do usuário**: não querer ter que abrir terminal e rodar o
  painel manualmente toda vez que liga o PC.
- **`scripts/iniciar_painel.ps1` criado**: carrega o `.env` e sobe o
  painel via `pythonw.exe` (sem janela de console). Testado
  manualmente antes de instruir o registro da tarefa.
- **Correção pequena em `src/web/app.py`**: a falha de
  `PAINEL_SECRET_KEY` ausente só ia para `print()`, que não aparece em
  nada quando o processo roda sem console (exatamente o caso de uma
  tarefa agendada). Agora também vai para `log.error()` — confirmado
  útil na prática: foi assim que descobri, ao testar o script pela
  primeira vez, que a `.env` real do usuário ainda não tinha
  `PAINEL_SECRET_KEY` preenchida (só existia no `.env.example`).
- **`PAINEL_SECRET_KEY` gerada e salva no `.env` real** (valor
  aleatório local, não é credencial de sistema externo).
- **Instruções passadas ao usuário** (não registradas por mim — pedido
  explícito de ser instruído, não de eu executar) para criar a tarefa
  agendada via `Register-ScheduledTask` (gatilho "ao logar", até 3
  tentativas de reinício automático se cair). Usuário registrou e
  testou (`Start-ScheduledTask` + `GET /health`) com sucesso.
- Documentado em `docs/README.md` (seção "Rodar o painel ao ligar o
  PC") e `AI_MEMORY.md`. **Não é** o deploy definitivo (serviço
  Linux/systemd) — isso continua sendo fase futura, no servidor
  definitivo, por decisão já registrada do usuário.

## 2026-08-26 (1) — Autenticação do painel por usuário individual

- **Pedido do usuário**: o painel passou a ser acessado por outra pessoa
  da equipe pela rede interna, o que tornou a falta de autenticação um
  problema real (antes era só uso local). Escolhida a opção de usuários
  individuais (rastreabilidade) em vez de senha única compartilhada —
  decisão registrada em
  [`docs/adr/006-autenticacao-usuarios-individuais.md`](../docs/adr/006-autenticacao-usuarios-individuais.md),
  spec em [`specs/autenticacao_painel.md`](../specs/autenticacao_painel.md).
- **Primeiro banco de dados próprio do projeto**: SQLite em
  `dados/acompanhamento.db`, schema versionado por migrations numeradas
  em `dados/migrations/` (`001_criacao_inicial.sql` — tabela `usuario`),
  aplicadas por `scripts/aplicar_migrations.py` (novo). `src/db.py`
  criado como ponto único de acesso (`conectar()`, `PRAGMA
  foreign_keys=ON`, `row_factory=sqlite3.Row`).
- **`.gitignore` ajustado**: a linha genérica `/dados` foi trocada — o
  `.db` continua ignorado (`*.db` já cobria isso), mas
  `dados/migrations/*.sql` agora é versionado (é código de schema, não
  dado).
- **Gestão de usuário sem autocadastro**: `scripts/criar_usuario.py`
  (senha oculta via `getpass`, hash `werkzeug.security` antes de
  gravar — já vinha com o Flask, não é dependência nova, só passou a
  ser importada diretamente e por isso entrou em `requirements.txt`) e
  `scripts/desativar_usuario.py` (revoga sem apagar o registro).
- **`src/web/auth.py` criado**: `verificar_credenciais()` (mensagem
  sempre genérica, não revela se o usuário existe — nem se está
  desativado), `login_required` (rotas de página, redireciona para
  `/login?proximo=...`) e `api_login_required` (rotas `/api/...`,
  devolve `401` JSON em vez de redirecionar).
- **Rotas novas**: `GET/POST /login`, `POST /logout`. Todas as rotas
  existentes (`/`, `/historico`, `/api/relatorios/dados`,
  `/api/relatorios/historico`) passaram a exigir sessão. `/health`
  continua aberto (uso por ferramentas de monitoramento externas, não
  expõe dado sensível).
- **`PAINEL_SECRET_KEY` obrigatória**: painel recusa subir (mensagem
  `[FALHA]` clara) se a variável de ambiente não estiver definida —
  nunca roda com sessão insegura por omissão.
- Indicador de sessão no cabeçalho (`base.html`): nome do usuário logado
  + botão "sair". Template novo `login.html`.
- Todos os testes de rota existentes em `src/tests/test_web_app.py`
  foram atualizados para autenticar a sessão do cliente de teste antes
  de exercitar as rotas protegidas (helper `_autenticar()`, via
  `session_transaction()` do Flask — sem precisar de banco real).
  Testes novos: `src/tests/test_db.py`, `src/tests/test_auth.py`,
  `TestLogin` e `TestProtecaoDeRotas` em `test_web_app.py` (login
  válido/inválido, logout, cada rota protegida sem sessão, `/health`
  continua acessível).
- Suite completa: **129 testes**, 100% offline. Validado manualmente
  contra o painel real: usuário de teste criado direto no banco (o
  `getpass` do script não funciona bem com stdin via pipe neste
  ambiente de validação — o script em si continua interativo,
  normalmente), login inválido, login válido, cookie de sessão
  liberando `/` e a API, `/health` sem sessão, logout limpando a sessão.
  Usuário de teste removido ao final.
- `docs/README.md`, `src/README.md` e `AI_MEMORY.md` atualizados
  (passo a passo de primeira instalação, "sem banco de dados próprio"
  deixou de ser uma limitação — agora é só para usuários, dados de
  monitoramento continuam sempre vindos do Zabbix ao vivo).

## 2026-07-28 (10) — Histórico de ocorrências (drill-down) no painel

- **Motivado por uma investigação real do usuário**: ao ver a linha
  "Acesso Nutrane está fora do ar — 47 ocorrências" no painel, o usuário
  perguntou quando cada uma caiu e quando foi resolvida. Investigação ao
  vivo contra a API do Zabbix revelou um achado real: **169 ocorrências
  em 30 dias, 100% resolvidas sozinhas em segundos (média 44s, máxima
  ~1h16min)** — não é indisponibilidade sustentada, é flapping. Achado
  registrado em `contexto/servidores.md`.
- **Descoberta de API registrada em `contexto/api.md`**: `event.get` não
  devolve o horário de resolução direto (`r_clock` não é um campo de
  `output` válido, dá erro `Invalid params`) — só o `r_eventid`, exigindo
  uma segunda chamada `event.get` pelos `eventids` dos eventos de
  recuperação para obter o `clock` de resolução.
- **Funcionalidade nova**: spec escrita antes de implementar
  ([`specs/historico_ocorrencias.md`](../specs/historico_ocorrencias.md)).
  Cada linha do ranking (tabela e gráfico) agora é um link para
  `GET /historico?periodo=...&visao=...&chave=...`: lista cada
  ocorrência (quando caiu, quando voltou, duração), resumo (total,
  quantas ainda abertas, duração média/mínima/máxima) e um mini-gráfico
  de frequência por dia (achar dias de pico — exatamente o que motivou o
  pedido). Endpoint JSON equivalente em `GET /api/relatorios/historico`.
- **Camada de domínio** (`src/relatorios_service.py`): `eventos_do_grupo()`
  filtra os eventos já buscados pela mesma chave de agrupamento do
  ranking (nome do problema ou host — garante que o total do histórico
  bate com o total da linha clicada); `buscar_resolucoes()` busca os
  horários de resolução; `historico()` combina os dois;
  `fmt_duracao()` formata segundos de forma humana (`44s`, `1h16m`).
  `buscar_eventos()` passou a pedir também `r_eventid` no `output`.
- **Camada de serviço web** (`src/web/services/relatorios.py`):
  `historico_grupo()` — sem cache (é consulta sob demanda, não a visão
  principal), valida `visao` e limita `chave` a 500 caracteres
  (`prompts/politicas/seguranca.txt`, item 9).
- **Rotas**: `/historico` (página) e `/api/relatorios/historico` (JSON),
  ambas com log de falha/lentidão (`src/logging_util.py`), mesmo padrão
  das rotas existentes.
- **Template novo**: `src/web/templates/historico.html`, reaproveitando
  os componentes e a paleta já estabelecidos (`_componentes.html`,
  `.grafico-ranking` para o gráfico por dia).
- 21 testes novos (domínio, serviço, rotas). Suite completa: **114
  testes, 100% offline**. Validado manualmente contra o Zabbix real: o
  histórico de "Acesso Nutrane está fora do ar" bateu exatamente com os
  números apurados na investigação ao vivo que originou o pedido (169
  ocorrências/30 dias, 47/7 dias, média 44s).
- `docs/README.md`, `AI_MEMORY.md`, `contexto/api.md` e
  `contexto/servidores.md` atualizados.

## 2026-07-28 (9) — Auditoria de conformidade contra prompts/ e correção de 3 gaps

- **Pedido do usuário**: auditoria explícita do que já foi construído
  contra `prompts/politicas/`, `prompts/tarefas/` e `prompts/workflow/`.
  Encontrados 3 gaps reais, não sinalizados antes:
  1. **`prompts/politicas/logs.txt`, item 3** — o painel web (processo
     de longa duração) só usava `print()`, sem logging estruturado em
     arquivo. Corrigido: `src/logging_util.py` criado (graduação de
     `templates/logging.py` para código real, mesmo padrão de
     `zbx_api.py`); `src/web/app.py` e `src/web/api.py` passam a logar
     em `logs/painel_web.log` (INFO no início; WARNING em falha de
     comunicação com o Zabbix e em consultas lentas; ERROR em exceção
     inesperada). De quebra, fecha também
     `prompts/politicas/monitoramento.txt`, item 7 (log de rotas lentas
     > 5s), que também estava pendente sem estar formalmente registrado
     como dívida.
  2. **`prompts/politicas/codigo.txt`, item 8** — funções de domínio
     novas desta sessão (`agregar_por_host()`, `dados_periodo()`,
     `montar_grafico_ranking()`) sem type hints. Adicionados. Escopo
     limitado às funções realmente novas — não uma varredura retroativa
     do arquivo inteiro (fora do que foi pedido).
  3. **`prompts/politicas/configuracao.txt`** — `.env.example` não
     listava `PAINEL_HOST`/`PAINEL_PORT`. Adicionados como comentário
     (são opcionais, já têm default seguro).
- Suite completa validada após as mudanças: 79 testes, sem alteração de
  contagem (os gaps eram de conformidade de política, não de lógica sem
  cobertura). Painel reiniciado manualmente e log de arquivo confirmado
  funcionando (`logs/painel_web.log`).

## 2026-07-28 (7) — Repositório git inicializado e publicado

- `git init`, `.claude/` (config local da ferramenta de IA) adicionado
  ao `.gitignore` — decisão do usuário, não é parte do projeto Zabbix.
  Nenhuma credencial no primeiro commit (confirmado: o token real só
  existe em `.env`, fora do git).
- Remoto adicionado e publicado em
  `https://github.com/paulohenriquemlf896-bit/ZABBIX_ACOMPANHAMENTO`.
- Resolve o risco "sem repositório git inicializado" registrado em
  `AI_MEMORY.md`.

## 2026-07-28 (8) — Ranking por host + gráficos no painel

- **Pedido do usuário**: ranking de problemas por host e "um dashboard
  com gráficos". Spec escrita antes de implementar:
  [`specs/ranking_por_host.md`](../specs/ranking_por_host.md).
- **`agregar_por_host()` criada** em `src/relatorios_service.py`,
  espelhando `agregar()` com a chave de agrupamento trocada. Regra de
  negócio nova e não óbvia, registrada na spec: evento com múltiplos
  hosts conta para cada host envolvido; evento sem host é excluído do
  ranking mas continua contando no total geral. 8 testes novos.
- **`dados_periodo()`** (painel) ganhou o parâmetro `visao`
  (`problema`/`host`), cache agora chaveado por `(periodo, visao)`. 4
  testes novos.
- **Rotas** (`/` e `/api/relatorios/dados`) ganharam `visao` na
  querystring, validada contra whitelist (nunca 500 em valor inválido,
  mesma regra de `periodo`). 6 testes novos.
- **Gráficos**: antes de desenhar, consultada a skill de visualização de
  dados do projeto (forma → cor → validação → marcas → interação →
  acessibilidade). Decisões tomadas:
  - Forma: ranking/magnitude → barra horizontal (rótulos longos não
    cabem em coluna vertical). Part-to-whole da severidade → barra
    única proporcional (≤6 segmentos, dentro do limite recomendado).
  - Cor: a paleta de severidade já fixada pelo projeto
    (`padroes/convencoes.md`) é tratada como o "status palette" da
    skill — cor da barra = severidade da linha (um status real, não
    identity nem magnitude), comprimento da barra = ocorrências
    (magnitude). Dois canais distintos, não sobrepostos. A paleta NÃO
    foi rodada pelo validador da skill: são as cores oficiais do
    Zabbix, já mandatórias pelo projeto antes desta tarefa
    (`prompts/tarefas/frontend.txt`, item 5) — fora de discricionariedade
    desta implementação.
  - Marcas: barra ≤24px (16px usada), ponta arredondada só do lado do
    dado (`border-radius: 0 4px 4px 0`), base quadrada; gap de 2px cor
    de superfície entre segmentos do mix de severidade; valor sempre na
    ponta da barra (nunca dentro, nunca cortado); rótulo truncado com
    reticências + `title` (nunca clipado sem indicação).
    Comprimento relativo ao MAIOR item exibido (não ao total do
    período), para o gráfico usar a largura disponível.
  - Interação: `title` nativo (tooltip sem JS) em cada barra/segmento —
    reforça, nunca substitui, já que todo valor também está na tabela
    detalhada logo abaixo (o "table view" exigido pela skill já existia).
  - Sem dependência nova: tudo é HTML/CSS/Jinja server-side, mesma
    filosofia do resto do painel.
  - `montar_grafico_ranking()` criada em `src/web/app.py` (camada de
    apresentação). 5 testes novos.
- Suite completa: **79 testes**, 100% offline. Validado manualmente
  contra o Zabbix real nas duas visões e nas 4 janelas de tempo.
- `docs/README.md` e `AI_MEMORY.md` atualizados; item "ranking por host"
  removido do roadmap (implementado).

## 2026-07-28 (6) — Auto-atualização do painel ("dashboard em tempo real")

- **Pedido do usuário**: dashboard em tempo real. Avaliadas duas
  abordagens — WebSocket (push instantâneo, exigiria dependência nova
  como `flask-socketio` e um processo extra verificando o Zabbix
  continuamente) vs. auto-atualização periódica (meta refresh, já
  prevista em `prompts/tarefas/frontend.txt`, item 18, para "painel de
  TV"). Escolhida a segunda: sem dependência nova, sem processo extra, e
  sem perda real de atualidade — o cache do painel já é de 60s, então
  nada mais rápido que isso apareceria de qualquer forma.
- `src/web/app.py`: contexto do template passa a incluir
  `auto_refresh_segundos` (reaproveita `TTL_SEGUNDOS` de
  `src/web/services/relatorios.py` — um único número controla cache e
  intervalo de atualização, não dois valores que poderiam divergir).
- `src/web/templates/base.html`: `<meta http-equiv="refresh">`
  condicional (só quando o valor é passado, evitando refresh acidental
  em `content=""` caso algum template futuro use `base.html` sem
  fornecer o contexto).
- `src/web/templates/index.html`: indicador visível "atualiza
  automaticamente a cada 60s" ao lado do horário de atualização — nunca
  refresh silencioso sem o usuário saber por que a tela mudou.
- O período selecionado (`?periodo=...`) é preservado no refresh (meta
  refresh sem URL recarrega a própria URL atual).
- 2 testes novos em `src/tests/test_web_app.py` (tag presente na página
  normal e também na página de erro, para que o painel se recupere
  sozinho quando o Zabbix voltar). Suite completa: 58 testes.
- Validado manualmente contra o Zabbix real.

## 2026-07-28 (5) — Fechamento da dívida técnica de cobertura de teste

- **`src/tests/test_relatorio_problemas_apresentacao.py` criado** (10
  casos) — cobre `tabela_html()` e `barra_sev()` de
  `scripts/relatorio_problemas.py`: ranking vazio, escape de caracteres
  HTML em nome de problema e em host, cálculo de percentual (incluindo
  total zero), severidade desconhecida (fallback de cor/rótulo), truncamento
  no `TOP_N`, ordem das pills de severidade (mais grave → menos grave).
- **`src/tests/test_aplicar_exclusao_googleupdater.py` criado** (6 casos)
  — cobre `novo_valor()`: inserção antes de `)$`, concatenação simples,
  preservação do valor original, idempotência (padrão exato já presente
  e qualquer variação de "GoogleUpdater" já presente — caso real
  documentado em `docs/adr/002-correcao-ruido-googleupdater.md`), valor
  vazio.
- Fecha a dívida técnica "cobertura de teste parcial" registrada em
  `AI_MEMORY.md` desde a criação da estrutura de conhecimento do
  projeto. Suite completa: 56 testes, 100% offline
  (`python -m unittest discover src/tests`).

## 2026-07-28 (4) — Painel web (Flask), escopo inicial

- **Primeira versão do painel web** implementada — ver
  [`docs/adr/005-painel-web-flask.md`](adr/005-painel-web-flask.md) para
  o registro completo da decisão. Escopo definido em
  [`specs/dashboard.md`](../specs/dashboard.md): uma visão (recorrência
  de problemas), seletor de período via querystring
  (`?periodo=hoje|7d|30d|365d`, validado contra whitelist), cache em
  memória de 60s, rota `GET /health`, endpoint JSON interno
  `GET /api/relatorios/dados` (envelope `ok/dados/erro` conforme
  `padroes/padrao_respostas_api.md`). Sem autenticação — uso interno,
  bind em `127.0.0.1` por padrão.
- **`requirements.txt` criado** — primeira dependência externa do
  projeto (`flask`, `waitress`). Servido em produção via `waitress`
  (`python src/web/app.py`), nunca o servidor de debug do Flask.
- **Refatoração pré-requisito**: lógica de domínio de
  `scripts/relatorio_problemas.py` (`buscar_eventos`, `agregar`, mapas
  de severidade, janelas de tempo) extraída para
  `src/relatorios_service.py`, compartilhada agora entre o script CLI e
  o painel — elimina a duplicação que existiria ao construir o painel do
  zero. `scripts/relatorio_problemas.py` validado após a mudança:
  mesma saída HTML/CSV/console, testado contra o Zabbix real.
  Efeito colateral positivo: uma variável local morta (`hosts =
  ", ".join(...)`, nunca lida) encontrada e removida durante a extração.
- **Testes novos**: `src/tests/test_relatorios_service.py` (16 casos —
  cobre a dívida técnica de `agregar()` sem teste, registrada em
  `AI_MEMORY.md`), `src/tests/test_web_service_relatorios.py` (cache),
  `src/tests/test_web_app.py` (rotas via Flask test client). Suite
  completa: 40 testes, 100% offline.
- Validado manualmente contra o Zabbix real: as 4 janelas de período,
  `/health` (`zabbix_alcancavel: true`), endpoint JSON, e fallback de
  período inválido — todos responderam como esperado.
- Documentação atualizada: `docs/README.md` (seção do painel,
  pré-requisitos), `src/README.md` (nova estrutura), `AI_MEMORY.md`
  (painel movido de "futuras" para "implementadas — escopo inicial").

## 2026-07-28 (3) — Remoção de token hardcoded em `src/zbx_api.py`

- **Problema identificado** (durante leitura completa do projeto, a
  pedido do usuário): `src/zbx_api.py` tinha um token real do Zabbix
  (usuário `Admin`, Super admin) como valor default de `ZBX_TOKEN =
  os.environ.get("ZBX_TOKEN", "<token>")`. Já era dívida técnica
  registrada em `AI_MEMORY.md`, mas o valor real seguia em código-fonte
  sem repositório git inicializado ainda.
- **Correção**: default alterado para `""` — os 4 scripts agora exigem
  `ZBX_TOKEN` via variável de ambiente/`.env` e falham com `[FALHA]`
  quando ausente (`validar_token.py` já tinha checagem explícita; os
  demais falham através das 3 camadas de tratamento de erro já
  existentes em `zbx_api.call()`).
- **Bug relacionado corrigido**: `call_ou_falhar(token=ZBX_TOKEN)` tinha
  o valor de `ZBX_TOKEN` vinculado como default de argumento no momento
  da definição da função (comportamento padrão do Python — default de
  argumento é avaliado uma única vez, na definição), então uma mudança
  posterior no valor do módulo não era refletida nas chamadas sem
  `token=` explícito. Corrigido para `token=None` com fallback lido em
  tempo de chamada (`if token is None: token = ZBX_TOKEN`) —
  comportamento observável idêntico para os 4 scripts existentes
  (nenhum passa `token=` para `call_ou_falhar`), porém corretamente
  dinâmico agora. Teste `test_usa_zbx_token_global_por_padrao` ajustado
  para não depender mais do valor real do token (antes comparava contra
  o próprio valor hardcoded).
- **`.env` local criado** (não versionado, fora do git) com o valor que
  estava hardcoded, para não interromper o uso imediato dos scripts.
- **Pendência sinalizada ao usuário**: como esse token esteve em
  código-fonte, recomenda-se revogá-lo no Zabbix (Usuários → Tokens de
  API) e gerar um novo, substituindo o valor em `.env`. Ver
  `AI_MEMORY.md`, Dívidas técnicas, item 1.
- Suite `src/tests/test_zbx_api.py` (11 casos) validada após a mudança —
  todos passando.

## 2026-07-28 (2) — Servidor Zabbix recuperado; validação end-to-end concluída

- O erro `Internal error: No such file or directory` na API (registrado
  como risco mais cedo hoje) se resolveu — os próprios dados monitorados
  mostram o motivo: evento `Linux: Zabbix server has been restarted`.
- `scripts/relatorio_problemas.py` rodado contra o Zabbix real com
  sucesso: 23.563 eventos processados, HTML+CSV gerados corretamente.
  Confirma que `src/zbx_api.py` funciona de ponta a ponta, não só nos
  testes com mock.
- Ranking "Hoje" não mostra mais nenhum evento GoogleUpdater no top 5 —
  indício de que a correção de `docs/adr/002` está efetiva. Janelas de
  7/30/365 dias ainda mostram volume alto por conterem eventos anteriores
  à correção (comportamento esperado, não falha).

## 2026-07-28 (1) — Auditoria de arquitetura + centralização do cliente da API do Zabbix

- **Auditoria de arquitetura**: encontrada e corrigida uma violação
  sistêmica de fonte única de verdade — ~20 arquivos em `prompts/` e
  `contexto/` ainda instruíam registrar decisões novas em
  `contexto/decisoes.md` (que desde a ADR 003 é só um índice). Todos
  corrigidos para apontar `docs/adr/` (decisão nova) ou `AI_MEMORY.md`
  (estado/dívida/roadmap), conforme o caso. Também corrigida prosa
  contraditória em `prompts/politicas/regras_gerais.txt` (item 4, ainda
  descrevia `/src` como "todo código-fonte: scripts, e futuramente app
  Flask", desatualizado desde a separação `src/`/`scripts/`) e
  referências obsoletas ao esquema plano `prompts/NN_nome.txt` em
  `prompts/workflow/roadmap.txt` e `contexto/fluxos.md`.
- **`src/zbx_api.py` criado** — cliente único de acesso à API JSON-RPC do
  Zabbix (`call()` e `call_ou_falhar()`), eliminando a duplicação da
  função `call()` nos 4 scripts de `scripts/`. Um bug real foi corrigido
  no processo: `aplicar_exclusao_googleupdater.py` não tinha
  `try/except` em volta do `urlopen()` e quebraria com traceback cru em
  falha de rede; agora usa o tratamento de erro comum. Código morto
  removido de `inspecionar_servicos.py` (variáveis não utilizadas).
- **`src/tests/test_zbx_api.py` criado** — 11 testes, 100% offline (mock
  de `urlopen`), primeira suíte de testes automatizados do projeto.
- Ver [`docs/adr/004-centralizacao-cliente-api-zabbix.md`](adr/004-centralizacao-cliente-api-zabbix.md)
  para o registro completo, incluindo as diferenças de comportamento
  encontradas entre os 4 scripts antes da centralização.
- **Risco identificado (não corrigido, fora do escopo deste projeto)**:
  a API do Zabbix (`192.168.11.12`) está retornando
  `Internal error: No such file or directory` desde antes desta
  refatoração — confirmado com `curl` puro, sem código deste projeto
  envolvido. Interface web responde normalmente; problema é específico
  do endpoint da API, provável causa no servidor (PHP-FPM ou sessão).
  Registrado em `AI_MEMORY.md`.

## 2026-07-27 (2) — Evolução para ecossistema de desenvolvimento orientado por IA (v2)

- **`prompts/` reorganizado em `politicas/`, `tarefas/` e `workflow/`**
  (24 arquivos: os 22 originais recategorizados e renomeados sem prefixo
  numérico, mais `politicas/principios.txt` e `workflow/evolucao.txt`
  novos). Todas as referências cruzadas entre prompts, `contexto/` e
  `docs/` atualizadas para os novos caminhos.
- **`src/` e `scripts/` separados**: os 4 scripts utilitários
  (`validar_token.py`, `relatorio_problemas.py`, `inspecionar_servicos.py`,
  `aplicar_exclusao_googleupdater.py`) movidos para `scripts/`; `src/`
  fica reservado para a futura aplicação (painel Flask). Nenhuma mudança
  de comportamento nos scripts — caminho de saída é relativo ao próprio
  arquivo.
- **`padroes/` criado** — 5 documentos de convenção (nomenclatura,
  estrutura de pastas, padrão de resposta de API, convenções gerais,
  boas práticas), consultáveis antes de gerar código novo.
- **`templates/` criado** — 6 modelos reutilizáveis (`api_service.py`,
  `flask_blueprint.py`, `email.html`, `dashboard.html`, `logging.py`,
  `teste_unitario.py`).
- **`docs/adr/` criado** — decisões arquiteturais migradas de
  `contexto/decisoes.md` (agora um índice curto) para ADRs individuais.
- **`specs/` criado** — especificações de `relatorios.md` (retrofit),
  `notificacoes.md` e `dashboard.md` (planejadas).
- **`examples/` criado** — payloads e saídas reais (resposta de
  `event.get`, erro JSON-RPC, payload de `usermacro.update`, trecho de
  HTML/CSV gerado, `.env` de exemplo fictício).
- **`AI_MEMORY.md` e `AI_BOOTSTRAP.md` criados** na raiz — memória viva
  do projeto e ordem de leitura obrigatória para qualquer IA.
- **`CLAUDE.md` reescrito**: nova tabela de prompts por categoria, regra
  obrigatória de verificar reutilização antes de criar código, nova
  ordem de precedência (`principios.txt` ao lado de `seguranca.txt` no
  topo da hierarquia).
- Ver [`docs/adr/003-evolucao-arquitetura-ai-driven-v2.md`](adr/003-evolucao-arquitetura-ai-driven-v2.md)
  para o registro completo (contexto, alternativas avaliadas,
  justificativa e consequências).

## 2026-07-27 (1) — Estrutura inicial de conhecimento orientada por IA

- **Estrutura de conhecimento orientada por IA criada.** Adicionadas as
  pastas `prompts/` (22 arquivos de regras permanentes, 00 a 21),
  `contexto/` (8 arquivos de conhecimento do projeto), `docs/` e `logs/`.
  `CLAUDE.md` reescrito como porta de entrada obrigatória. Scripts
  movidos de raiz para `src/`. Ver
  [`docs/adr/001-estrutura-conhecimento-orientada-por-ia.md`](adr/001-estrutura-conhecimento-orientada-por-ia.md)
  (superado parcialmente pela entrada acima).
- **Correção de configuração no Zabbix: ruído do GoogleUpdater
  eliminado.** Macro `{$SERVICE.NAME.NOT_MATCHES}` nos templates
  `Windows by Zabbix agent` e `Windows by Zabbix agent active` alterada
  via API (`usermacro.update`) para incluir `GoogleUpdater.*`.
  - **Antes:** `^(?:RemoteRegistry|MMCSS|gupdate|SysmonLog|clr_optimization_v.+|sppsvc|gpsvc|Pml Driver HPZ12|Net Driver HPZ12|MapsBroker|IntelAudioService|Intel\(R\) TPM Provisioning Service|dbupdate|DoSvc|CDPUserSvc_.+|WpnUserService_.+|OneSyncSvc_.+|WbioSrvc|BITS|tiledatamodelsvc|GISvc|ShellHWDetection|TrustedInstaller|TabletInputService|CDPSvc|wuauserv|edgeupdate|cbdhsvc_.+)$`
  - **Depois:** o mesmo valor com `|GoogleUpdater.*` acrescentado antes
    de `)$`.
  - **Motivo:** o relatório de problemas recorrentes mostrou que
    triggers `GoogleUpdaterInternalService...`/`GoogleUpdaterService...`
    (uma por versão do Chrome) representavam ~50% de todos os eventos de
    problema do último ano. Uma correção manual anterior em 3 hosts
    (`^GoogleUpdaterService.*`) não cobria a variante "Internal".
  - Ver [`docs/adr/002-correcao-ruido-googleupdater.md`](adr/002-correcao-ruido-googleupdater.md) para o registro completo.
- **`scripts/relatorio_problemas.py` criado.** Relatório de problemas mais
  recorrentes em 4 janelas (Hoje, 7 dias, 30 dias, 365 dias), com saída
  HTML + CSV em `scripts/saidas/`.
- **`scripts/inspecionar_servicos.py` criado.** Ferramenta somente leitura
  para inspecionar regras de descoberta de serviços Windows e localizar
  a macro/filtro relevante para investigação de ruído.
- **`scripts/aplicar_exclusao_googleupdater.py` criado.** Script idempotente
  de correção de configuração via API, com impressão de estado
  antes/depois.
- **`scripts/validar_token.py` criado.** Validação de conectividade e
  autenticação com a API do Zabbix.
