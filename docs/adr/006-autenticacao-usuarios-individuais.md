# ADR 006 — Autenticação do painel web por usuários individuais (SQLite)

**Data:** 2026-08-26
**Status:** Aceito e em implementação.

## Contexto

O painel web (ADR 005) nasceu sem autenticação, escopo explicitamente
aceito para a primeira versão (`specs/dashboard.md`, "Fora de escopo
desta primeira versão"). Naquele momento o painel só era acessado da
própria máquina (`127.0.0.1`). Desde então o painel passou a ser exposto
na rede interna (`PAINEL_HOST` configurável, regra de liberar Firewall
documentada) para outra pessoa da equipe acessar — o que tornou a falta
de autenticação um problema real, não mais hipotético.

## Problema

Como controlar quem acessa o painel, sem contrariar os princípios do
projeto (simplicidade, sem dependência desnecessária, sem banco de
dados sem necessidade real — `prompts/tarefas/banco_de_dados.txt`)?

## Alternativas avaliadas

1. **Senha única compartilhada** (variável de ambiente, igual ao token
   do Zabbix) — mais simples, sem banco de dados novo. Rejeitada: o
   usuário decidiu explicitamente que queria usuários individuais
   (rastreabilidade de quem acessa).
2. **Integração com login do Windows/AD ou do próprio Zabbix** — não
   avaliada a fundo (usuário não pediu), ficaria como alternativa futura
   se a lista de usuários crescer o suficiente para justificar não
   duplicar cadastro.
3. **Usuários individuais com senha própria, armazenados em SQLite** —
   escolhida. É a primeira necessidade real de banco de dados próprio do
   projeto (`prompts/tarefas/banco_de_dados.txt`, item 2: "só criar
   banco próprio quando houver necessidade real que a API não atende
   bem" — login de usuário não é dado do Zabbix, não tem onde mais
   guardar).

## Decisão tomada

- **Banco**: SQLite em `dados/acompanhamento.db` (padrão já definido em
  `prompts/tarefas/banco_de_dados.txt`), criado/atualizado por
  `scripts/aplicar_migrations.py` a partir de arquivos SQL numerados em
  `dados/migrations/`. Primeira migration: tabela `usuario`
  (`nome_usuario`, `senha_hash`, `ativo`, `criado_em`).
- **Hash de senha**: `werkzeug.security` (`generate_password_hash`/
  `check_password_hash`, PBKDF2) — já é dependência transitiva do Flask,
  não é dependência nova no projeto; só passou a ser importada
  diretamente, por isso listada explicitamente em `requirements.txt`
  agora.
- **Sessão**: cookie de sessão assinado do próprio Flask
  (`PAINEL_SECRET_KEY` obrigatória via variável de ambiente, nunca
  hardcoded — `prompts/politicas/seguranca.txt`). Sem "lembrar-me"
  persistente nem refresh token — sessão dura o que o Flask define por
  padrão.
- **Gestão de usuário sem autocadastro**: `scripts/criar_usuario.py`
  (pede senha oculta via `getpass`, hash antes de gravar) e
  `scripts/desativar_usuario.py` — mesmo padrão dos outros scripts do
  projeto (CLI, prefixos `[OK]`/`[FALHA]`).
- **Rotas protegidas**: `/` e `/historico` (página) redirecionam para
  `/login` se não houver sessão; `/api/relatorios/...` devolve `401`
  JSON (não faz sentido redirecionar um consumidor programático).
  `/health` continua sem exigir login — é usado por ferramentas de
  monitoramento externas e não expõe dado sensível (só
  ok/alcançável/versão/hora).
- **Sem CSRF token explícito nesta versão**: o único formulário
  introduzido é o de login (e um botão de logout via POST). O risco de
  CSRF aqui é login CSRF (atacante loga a vítima na conta do atacante),
  severidade baixa para este caso de uso interno — decisão consciente
  de não adicionar Flask-WTF (dependência nova) só para isso agora;
  registrado aqui para não ser esquecido se o escopo de autenticação
  crescer (ex.: se um dia houver ação destrutiva atrás de login).

## Justificativa

SQLite é o motor já padronizado pelo projeto para esse cenário
(processo único, zero administração). Reaproveitar `werkzeug.security`
em vez de adicionar uma biblioteca de hash de senha respeita
`prompts/politicas/dependencias.txt` (evitar dependência nova quando já
existe uma disponível). Separar `login_required` (web, redireciona) de
uma variante para API (401 JSON) respeita o formato de resposta já
padronizado (`padroes/padrao_respostas_api.md`) em vez de forçar todo
consumidor a lidar com redirecionamento HTML.

## Consequências

- `dados/` deixa de ser só um placeholder no `.gitignore` — passa a
  existir de verdade. Ajuste no `.gitignore`: o arquivo `.db` continua
  ignorado (já coberto por `*.db`), mas `dados/migrations/*.sql` agora é
  versionado (é código de schema, não dado).
- Todas as rotas existentes do painel (`/`, `/historico`,
  `/api/relatorios/dados`, `/api/relatorios/historico`) passam a exigir
  login — os testes existentes precisaram ser atualizados para
  autenticar a sessão do cliente de teste antes de exercitar essas
  rotas.
- Primeiro uso exige rodar `scripts/aplicar_migrations.py` e depois
  `scripts/criar_usuario.py` manualmente — documentado em
  `docs/README.md`.
- `PAINEL_SECRET_KEY` passa a ser obrigatória para o painel subir; sem
  ela, o processo falha cedo com mensagem clara em vez de rodar com
  sessão insegura.
