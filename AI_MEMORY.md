# AI_MEMORY.md — memória permanente da IA neste projeto

Este arquivo é o registro vivo do estado do projeto: o que já existe, o
que está em andamento, o que é planejado, o que é dívida técnica, o que é
risco conhecido. **Sempre manter atualizado** — toda tarefa que muda um
desses aspectos atualiza a seção correspondente na mesma tarefa (ver
`prompts/politicas/documentacao.txt` e `prompts/workflow/checklist.txt`).

Diferença para `docs/adr/`: ADR registra **por que** uma decisão foi
tomada, de forma imutável (histórico). Este arquivo registra **o que é
verdade agora** — muda com frequência, sem preservar histórico de versões
anteriores (o histórico de mudança de estado vive no
`docs/CHANGELOG.md`).

---

## Funcionalidades implementadas

- **Validação de token/conectividade** — `scripts/validar_token.py`.
- **Relatório de problemas recorrentes** (Hoje/7d/30d/365d, HTML+CSV) —
  `scripts/relatorio_problemas.py`. Spec: `specs/relatorios.md`.
- **Inspeção de descoberta de serviços Windows** (somente leitura) —
  `scripts/inspecionar_servicos.py`.
- **Correção da macro de exclusão de serviços** (GoogleUpdater) —
  `scripts/aplicar_exclusao_googleupdater.py`. Ver
  `docs/adr/002-correcao-ruido-googleupdater.md`.
- **Estrutura de conhecimento orientada por IA** — `prompts/`
  (politicas/tarefas/workflow), `contexto/`, `padroes/`, `templates/`,
  `specs/`, `examples/`, `docs/adr/`, `AI_MEMORY.md`, `AI_BOOTSTRAP.md`.
  Ver `docs/adr/003-evolucao-arquitetura-ai-driven-v2.md`.
- **Cliente único da API do Zabbix** — `src/zbx_api.py` (`call()` e
  `call_ou_falhar()`), usado pelos scripts em `scripts/` e pelo painel
  web. Cobertura de teste em `src/tests/test_zbx_api.py` (11 casos,
  offline). Ver `docs/adr/004-centralizacao-cliente-api-zabbix.md`.
- **Camada de domínio do relatório de problemas recorrentes** —
  `src/relatorios_service.py` (busca de eventos, agregação, janelas de
  tempo, mapas de severidade), extraída de
  `scripts/relatorio_problemas.py` para ser compartilhada com o painel
  web. Testes em `src/tests/test_relatorios_service.py` (16 casos,
  offline). Ver `docs/adr/005-painel-web-flask.md`.
- **Painel web (Flask)** — `src/web/` (`app.py`, `api.py`,
  `services/relatorios.py`). Duas visões — recorrência por **problema**
  ou por **host** (`?visao=problema|host`, ver
  `specs/ranking_por_host.md`) — combinadas com seletor de período
  (`?periodo=hoje|7d|30d|365d`), cache em memória de 60s (chaveado por
  período+visão), rota `GET /health`, endpoint JSON
  `GET /api/relatorios/dados`. Servido via `waitress`
  (`python src/web/app.py`). Logging estruturado em `logs/painel_web.log`
  (`src/logging_util.py` — inicio, falha de comunicacao com o Zabbix,
  consultas > 5s como WARNING). Sem autenticação (fora de escopo desta
  primeira versão, ver `specs/dashboard.md`). Testes em
  `src/tests/test_web_app.py` e `src/tests/test_web_service_relatorios.py`
  (29 casos, offline). Ver `docs/adr/005-painel-web-flask.md`.
- **Auto-atualização do painel** — a página se atualiza sozinha a cada
  60s (`<meta http-equiv="refresh">`, mesmo intervalo do cache),
  preservando período e visão selecionados na querystring; indicador
  visível "atualiza automaticamente a cada 60s" no cabeçalho. Padrão de
  "painel de TV" já previsto em `prompts/tarefas/frontend.txt`, item 18
  — sem dependência nova, sem processo em segundo plano. Real-time via
  WebSocket foi avaliado e descartado por ora: exigiria dependência nova
  e processo extra sem ganho real, já que o cache é de 60s (ver decisão
  registrada no CHANGELOG de 2026-07-28).
- **Gráficos no painel** — barra proporcional de mix de severidade
  (part-to-whole) e gráfico de barras horizontais do ranking (top 10,
  comprimento = ocorrências, cor = severidade da linha), em cada uma das
  duas visões. SVG/CSS puro (sem dependência nova, sem CDN), cor sempre
  a paleta oficial de severidade do Zabbix já usada nas badges/pills —
  nunca uma paleta genérica inventada. Testes em
  `src/tests/test_web_app.py` (`TestMontarGraficoRanking`).
  Validado manualmente contra o Zabbix real em 2026-07-28.
- **Histórico de ocorrências (drill-down)** — cada linha do ranking (e do
  gráfico de barras) é clicável e leva a `GET /historico?periodo=...&visao=...&chave=...`:
  quando cada ocorrência começou, quando terminou e quanto durou, com
  gráfico de frequência por dia (ajuda a achar dias de pico). Endpoint
  JSON equivalente em `GET /api/relatorios/historico`. Motivado por uma
  investigação real do usuário (trigger "Acesso Nutrane está fora do ar",
  ver `contexto/servidores.md`) que descobriu, ao vivo contra a API, que
  a API do Zabbix não devolve o horário de resolução direto em
  `event.get` (só o `r_eventid` — achado registrado em `contexto/api.md`).
  Spec: `specs/historico_ocorrencias.md`. Testes: 21 casos novos entre
  `src/tests/test_relatorios_service.py`,
  `src/tests/test_web_service_relatorios.py` e `src/tests/test_web_app.py`.
  Suite completa do projeto: 114 testes. Validado manualmente contra o
  Zabbix real em 2026-07-28 (o total do histórico bateu exatamente com o
  total mostrado na linha do ranking que originou o clique).

## Funcionalidades em andamento

- Nenhuma no momento (última tarefa concluída: histórico de ocorrências
  no painel, 2026-07-28).

## Funcionalidades futuras (planejadas, com spec já escrita)

- **Painel web — próximas etapas** (fora do escopo inicial, ver
  `specs/dashboard.md`, seção "Fora de escopo desta primeira versão"):
  autenticação, edição de configuração pela interface.
- **Envio automático de relatório por e-mail** — spec em
  `specs/notificacoes.md`. Não iniciado. Infra SMTP do domínio
  `gruporanchoalegre.com.br` (Locaweb) já validada em outro contexto do
  Grupo Rancho (ver `contexto/integracoes.md`).

## Ideias no roadmap (sem spec ainda)

Ver `prompts/workflow/roadmap.txt` para o processo. Itens atuais:

- Cruzamento Zabbix x GLPI (hosts monitorados sem ativo cadastrado e
  vice-versa).
- Ajuste de `StartPollersUnreachable` no `zabbix_server.conf` (fora do
  escopo de acesso via API deste projeto — exige acesso ao SO do
  servidor Zabbix).
- Investigação de capacidade do host `SRV-FORTES` (memória/disco/CPU
  recorrentemente no limite — ver `contexto/servidores.md`).
- Investigação de estabilidade da aplicação/rede do host `Siagri
  Nutrane` (alertas de indisponibilidade em tendência de piora) —
  **parcialmente avançada em 2026-07-28**: dados de padrão (flapping,
  duração, dias de pico) já levantados, ver `contexto/servidores.md`;
  falta a causa raiz (correlacionar com rotina/job da aplicação ou da
  rede), que exige acesso fora deste projeto.

## Dívidas técnicas

1. ~~Token do Zabbix com privilégio Super admin embutido como default
   nos scripts.~~ **Parcialmente resolvido em 2026-07-28** — o valor
   hardcoded foi removido de `src/zbx_api.py` (default passou a ser
   `""`; scripts agora falham com `[FALHA]` se `ZBX_TOKEN` não estiver
   configurado). Continua pendente: o token em uso ainda pertence ao
   usuário `Admin` (Super admin) — criar um usuário dedicado
   `svc_relatorios` read-only permanece recomendação ativa (ver
   `prompts/politicas/seguranca.txt`, item 5). Como esse token esteve
   exposto em código-fonte, recomenda-se revogá-lo no Zabbix
   (Usuários → Tokens de API) e gerar um novo antes de considerar este
   item totalmente resolvido.
2. **Exclusões manuais redundantes de GoogleUpdater** em 3 hosts (Siagri
   Nutrane, Siagri Rancho, TERMINAL CAIXA02-GUS BR) — a macro do template
   já cobre tudo; as condições manuais na regra de descoberta desses
   hosts ficaram inofensivas mas redundantes. Limpar quando algum desses
   hosts for tocado por outro motivo.
3. ~~Função `call()` de acesso à API duplicada nos 4 scripts.~~
   **Resolvido em 2026-07-28** — extraída para `src/zbx_api.py`. Ver
   `docs/adr/004-centralizacao-cliente-api-zabbix.md`.
4. ~~Cobertura de teste parcial~~ **Resolvido em 2026-07-28** —
   `src/zbx_api.py`, `src/relatorios_service.py` (`agregar()`,
   `buscar_eventos()`), a camada de apresentação de
   `scripts/relatorio_problemas.py` (`tabela_html()`, `barra_sev()` —
   `src/tests/test_relatorio_problemas_apresentacao.py`) e `novo_valor()`
   de `aplicar_exclusao_googleupdater.py`
   (`src/tests/test_aplicar_exclusao_googleupdater.py`) agora têm suites
   próprias. Suite completa do projeto: 56 testes, 100% offline. O único
   ponto ainda sem teste automatizado é `main()` de cada script (camada
   de entrada/orquestração) — aceitável, é I/O e orquestração, não lógica
   de domínio (ver `prompts/politicas/testes.txt`, item 7).
5. ~~Sem `.env` real criado~~ **Resolvido em 2026-07-28** — `.env` local
   criado (não versionado) com `ZBX_URL`/`ZBX_TOKEN`; `src/zbx_api.py`
   agora exige a variável de ambiente em vez de valor hardcoded (ver
   item 1).

## Riscos conhecidos

- ~~API do Zabbix retornando erro interno~~ **Resolvido em 2026-07-28**
  — o servidor reiniciou (confirmado pelos próprios dados monitorados:
  evento `Linux: Zabbix server has been restarted`) e a API voltou a
  responder normalmente. Validação end-to-end de `src/zbx_api.py`
  concluída com sucesso contra dados reais (23.563 eventos,
  `scripts/relatorio_problemas.py` gerou HTML+CSV corretamente) — ver
  `docs/adr/004-centralizacao-cliente-api-zabbix.md`.
- ~~Sem repositório git inicializado~~ **Resolvido em 2026-07-28** —
  repositório criado e enviado para
  `https://github.com/paulohenriquemlf896-bit/ZABBIX_ACOMPANHAMENTO`.
  `.claude/` (config local da ferramenta de IA, não do projeto)
  adicionado ao `.gitignore`, junto com o que já era ignorado.
- **Rede interna sem VPN** — o painel Flask futuro não pode ser exposto
  além da rede local sem essa decisão ser tomada deliberadamente (ver
  `prompts/politicas/seguranca.txt`, item 10).
- **Volume de eventos do Zabbix é alto** (~23 mil/ano) — consultas mal
  filtradas podem ficar lentas; mitigado hoje por `MAX_EVENTOS`, mas
  ainda não há paginação real implementada.

## Limitações atuais

- Nenhuma automação agendada ainda — todos os scripts rodam manualmente.
- Nenhuma integração além do Zabbix está implementada (GLPI, e-mail,
  Telegram, Teams, WhatsApp, Proxmox — todas planejadas, ver
  `contexto/integracoes.md`).
- Sem banco de dados próprio — toda saída é arquivo (HTML/CSV).

## Observações importantes

- O projeto já produziu um resultado real de valor antes de qualquer
  "infraestrutura de projeto" existir: a correção do ruído GoogleUpdater
  reduziu por si só uma fração muito grande do volume de eventos do
  ambiente. A estrutura de `prompts/`/`contexto/`/etc. existe para que
  achados como esse continuem acontecendo de forma consistente, não para
  ser um fim em si mesma (ver `prompts/politicas/principios.txt`, item 8,
  simplicidade).
- Toda a base de `contexto/` foi escrita a partir de investigação real
  (API do Zabbix consultada de fato), não de suposição. Reconfirmado
  contra o Zabbix real em 2026-07-28 (ver validação end-to-end acima) —
  ainda assim, é uma fotografia; reconferir antes de decisão importante
  baseada só na leitura destes arquivos.
- A correção do GoogleUpdater (`docs/adr/002`) parece efetiva: no
  ranking "Hoje" de 2026-07-28 nenhum evento GoogleUpdater aparece mais
  no top 5. As janelas de 7/30/365 dias ainda mostram volume alto porque
  contam eventos anteriores à correção (2026-07-27) — comportamento
  esperado da métrica de recorrência (contexto/regras_negocio.md), não
  falha da correção. Confirmar de novo daqui a ~7-30 dias, quando essas
  janelas não tiverem mais dados de antes do fix.
- Uma auditoria de arquitetura em 2026-07-28 encontrou e corrigiu ~20
  referências, em `prompts/` e `contexto/`, que apontavam decisões novas
  para `contexto/decisoes.md` (que desde a ADR 003 é só um índice) em vez
  de `docs/adr/`. Se, ao trabalhar em qualquer prompt antigo por outro
  motivo, aparecer uma instrução para "registrar em contexto/decisoes.md"
  como destino de conteúdo novo, é sinal de mais uma dessas referências
  que escapou — corrigir para `docs/adr/` (decisão) ou `AI_MEMORY.md`
  (estado/dívida/roadmap).
