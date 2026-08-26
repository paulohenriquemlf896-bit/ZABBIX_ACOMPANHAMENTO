-- Migration 001: cria a tabela de usuarios do painel web.
-- Ver docs/adr/006-autenticacao-usuarios-individuais.md e
-- specs/autenticacao_painel.md.
--
-- NUNCA editar esta migration depois de aplicada em algum ambiente;
-- criar a proxima migration com a correcao (prompts/tarefas/banco_de_dados.txt).

CREATE TABLE usuario (
    id INTEGER PRIMARY KEY,
    nome_usuario TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL
);
