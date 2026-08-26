# Spec: Autenticação do painel web (usuários individuais)

**Status:** implementado. Decisão registrada em
[`docs/adr/006-autenticacao-usuarios-individuais.md`](../docs/adr/006-autenticacao-usuarios-individuais.md).

## Objetivo

Impedir que qualquer pessoa na rede interna acesse o painel — só quem
tem usuário e senha cadastrados. Cada pessoa com sua própria conta
(rastreabilidade), não uma senha única compartilhada.

## Regras de negócio

- Usuário tem `nome_usuario` (único), `senha_hash` (nunca senha em
  texto puro), `ativo` (permite revogar acesso sem apagar o histórico
  de quem existiu) e `criado_em`.
- Não existe autocadastro. Usuários só são criados por quem tem acesso
  ao servidor, via `scripts/criar_usuario.py`.
- Login errado (usuário inexistente, senha errada, ou usuário inativo)
  sempre devolve a mesma mensagem genérica ("Usuário ou senha
  inválidos") — nunca revelar se o usuário existe ou não.
- Sessão via cookie assinado do Flask; não há "lembrar-me" nem
  renovação automática além do padrão do framework.
- `GET /health` **não** exige login (uso por ferramentas de
  monitoramento externas; não expõe dado sensível).
- Todas as demais rotas do painel (`/`, `/historico`,
  `/api/relatorios/dados`, `/api/relatorios/historico`) exigem sessão
  ativa.

## Fluxo

1. Usuário sem sessão acessa `/` (ou qualquer rota protegida) →
   redirecionado para `/login?proximo=<rota original>`.
2. Preenche usuário/senha, `POST /login`. Credencial válida → sessão
   criada, redireciona para `proximo` (ou `/` se não houver). Credencial
   inválida → mesma página com mensagem de erro genérica, tentativa
   registrada em log (WARNING, sem a senha).
3. Botão "sair" no cabeçalho → `POST /logout` → limpa a sessão,
   redireciona para `/login`.
4. Rotas `/api/relatorios/...` sem sessão devolvem `401` com o envelope
   `{"ok": false, "dados": null, "erro": "Nao autenticado."}` — nunca
   redirecionam (consumidor programático, não navegador).

## Entradas

| Nome | Origem | Obrigatório |
|---|---|---|
| `nome_usuario`, `senha` | formulário `POST /login` | sim |
| `PAINEL_SECRET_KEY` | variável de ambiente | sim — painel recusa subir sem ela |

## Saídas

- Cookie de sessão Flask (`usuario` = nome do usuário logado).
- `dados/acompanhamento.db` — tabela `usuario`.

## Validações

- `PAINEL_SECRET_KEY` ausente → painel não sobe, mensagem `[FALHA]`
  clara no console/log, não um erro genérico do Flask.
- Senha nova (via `scripts/criar_usuario.py`) exige no mínimo 8
  caracteres e confirmação digitada duas vezes.
- `nome_usuario` duplicado → script de criação falha com mensagem
  clara, não deixa dois usuários com o mesmo nome.

## Casos extremos

- Usuário desativado tenta logar → mesma mensagem genérica de "usuário
  ou senha inválidos" (não "sua conta foi desativada" — evita confirmar
  a um possível ex-funcionário que a conta existe/existiu).
- Sessão expira ou cookie é limpo enquanto o usuário está no meio de uma
  navegação → próxima rota protegida redireciona para `/login`
  normalmente, sem erro 500.
- Banco (`dados/acompanhamento.db`) ainda não existe (primeira
  instalação) → `scripts/aplicar_migrations.py` cria o arquivo e a
  tabela; painel não tenta criar schema sozinho.

## Fora de escopo desta versão

- Autocadastro e recuperação de senha por e-mail (sem infraestrutura de
  e-mail neste projeto ainda — ver `specs/notificacoes.md`).
- Papéis/permissões diferenciadas por usuário (hoje todo usuário
  autenticado tem o mesmo acesso — o painel inteiro é somente leitura).
- CSRF token explícito (avaliado e adiado — ver ADR 006, justificativa).
- "Lembrar-me" / sessão de longa duração.
