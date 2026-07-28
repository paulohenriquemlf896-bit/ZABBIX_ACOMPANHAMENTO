# Spec: Envio automático de relatório por e-mail

**Status:** planejado, não implementado. Escrita antes da implementação
conforme `prompts/politicas/principios.txt` (funcionalidade não trivial
merece spec prévia). Atualizar esta spec se o comportamento real, quando
implementado, divergir do planejado aqui.

## Objetivo

Enviar automaticamente, por e-mail, um resumo do relatório de problemas
recorrentes (ver `specs/relatorios.md`) em periodicidade fixa (ex.:
semanal, segunda de manhã), para que a equipe de TI e a gestão não
precisem lembrar de rodar o script manualmente.

## Regras de negócio

- Preferir resumo periódico (digest) a alerta unitário — ver
  `prompts/tarefas/notificacoes.txt`, item 14.
- Assunto do e-mail sempre datado:
  `[Zabbix] Relatório semanal de problemas — dd/mm/aaaa`.
- Corpo reaproveita a lógica de dados de `relatorio_problemas.py`
  (camada de domínio), nunca duplica a agregação — só troca a
  apresentação para o formato de `templates/email.html`.
- Anexar ou linkar o relatório HTML/CSV completo; o corpo do e-mail traz
  só o Top 5 (não o relatório inteiro colado).

## Fluxo proposto

1. Um agendador (Task Scheduler do Windows) dispara o script em
   periodicidade fixa.
2. O script roda a mesma lógica de `relatorio_problemas.py` para a
   janela "7 dias" (a mais relevante para um resumo semanal).
3. Monta o e-mail a partir de `templates/email.html`.
4. Envia via SMTP (credenciais em `.env` — ver
   `contexto/integracoes.md`, seção E-mail).
5. Loga o resultado do envio (sucesso/falha, destinatários) — ver
   `prompts/politicas/logs.txt`, item 9 (auditoria).
6. Falha de envio não apaga nem invalida o relatório já salvo em
   `scripts/saidas/`.

## Entradas

| Nome | Origem | Obrigatório |
|---|---|---|
| `SMTP_HOST`, `SMTP_PORT` | `.env` | sim |
| `SMTP_USUARIO`, `SMTP_SENHA` | `.env` | sim |
| Lista de destinatários | `.env` ou arquivo de configuração simples | sim |
| Janela do relatório (padrão: 7 dias) | constante/parâmetro | não |

## Saídas

- E-mail HTML enviado aos destinatários configurados.
- Log de envio em `/logs`.
- Nenhum arquivo novo em `scripts/saidas/` (reaproveita o já gerado pelo
  relatório).

## Validações

- Antes de habilitar em produção: enviar um teste controlado e confirmar
  com o usuário formato/destinatários (`prompts/workflow/release.txt`,
  item 9).
- Endereços de destinatário validados quanto a formato antes do envio.

## Casos extremos

- Falha de SMTP (ex.: "queue file write error", já observado em outro
  contexto do Grupo Rancho na Locaweb — ver `contexto/integracoes.md`) →
  retry finito com backoff (`prompts/tarefas/notificacoes.txt`, item 11),
  depois log em nível ERROR, sem derrubar o processo principal.
- Relatório da janela sem nenhum problema → e-mail ainda é enviado,
  com mensagem clara de "nenhum problema recorrente nesta semana" (não
  suprimir o envio silenciosamente — ausência de e-mail não deve ser
  interpretada como "o job não rodou").
- Lista de destinatários vazia → não enviar, logar `[FALHA]`
  explicitamente (evita erro silencioso de configuração).
