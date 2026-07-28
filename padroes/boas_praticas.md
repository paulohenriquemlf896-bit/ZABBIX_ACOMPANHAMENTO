# Boas práticas — resumo consultável

Este arquivo não substitui `prompts/politicas/*` — é um resumo de
consulta rápida das praticas mais importantes, com pointer para o prompt
completo. Em caso de dúvida ou aparente conflito, o prompt completo é
quem vale.

## Antes de escrever qualquer código novo

1. Verificar se já existe implementação semelhante em `src/`, `scripts/`
   ou `templates/` (ver `prompts/politicas/principios.txt`, item 2, e a
   regra equivalente em `CLAUDE.md`).
2. Verificar se `padroes/` já define como isso deve ser feito.
3. Se for uma funcionalidade nova e não trivial, verificar se já existe
   uma especificação em `specs/` — se não existir e a funcionalidade for
   complexa, criar a spec antes de implementar (ver
   `prompts/workflow/missao.txt` e a pasta `specs/`).

## Ao escrever

- Biblioteca padrão do Python primeiro; dependência externa só com
  necessidade real e aprovação (`prompts/politicas/dependencias.txt`).
- Função curta, uma responsabilidade (`prompts/politicas/codigo.txt`).
- Nunca `except` silencioso; sempre 3 camadas de erro em chamada de rede
  (`padroes/convencoes.md`, `prompts/tarefas/backend.txt`).
- Nunca credencial hardcoded em código novo
  (`prompts/politicas/seguranca.txt`).
- HTML sempre com `html.escape()` em dado externo
  (`prompts/tarefas/frontend.txt`).
- SQL sempre parametrizado, nunca concatenado
  (`prompts/tarefas/banco_de_dados.txt`).

## Ao terminar

- Rodar as perguntas de `prompts/workflow/evolucao.txt` (duplicação,
  acoplamento, oportunidade de template).
- Atualizar `docs/README.md`, `docs/CHANGELOG.md` e `AI_MEMORY.md`
  conforme o que mudou (`prompts/politicas/documentacao.txt`).
- Rodar o checklist completo de `prompts/workflow/checklist.txt`.

## Sinais de alerta (parar e reconsiderar)

- Copiando e colando um bloco de código pela segunda vez → deveria ser
  função/módulo comum ou um template em `/templates`.
- Escrevendo uma chamada de escrita à API do Zabbix sem ter pedido
  confirmação ao usuário → parar, confirmar antes.
- Um arquivo passando de ~300-400 linhas → candidato a dividir
  (ver `prompts/workflow/evolucao.txt`).
- Uma decisão que, se estivesse errada, seria cara de reverter depois →
  documentar em ADR antes de seguir (`docs/adr/`), não só implementar.
- Uma tentativa de "resolver rápido" que pula teste, documentação ou
  tratamento de erro → contraria a ordem de prioridades do projeto
  (segurança > estabilidade > manutenibilidade > escalabilidade >
  performance > funcionalidade nova — ver `prompts/workflow/missao.txt`).
