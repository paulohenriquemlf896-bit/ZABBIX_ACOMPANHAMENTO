# ADR 001 — Adotar estrutura de conhecimento orientada por IA (prompts/ + contexto/)

**Data:** 2026-07-27
**Status:** Superado parcialmente por [ADR 003](003-evolucao-arquitetura-ai-driven-v2.md) (a organização interna de `prompts/` mudou; a existência de `prompts/` e `contexto/` como conceitos permanece válida).

## Contexto

O projeto começou como 4 scripts Python soltos na raiz, sem nenhuma
regra de desenvolvimento registrada — cada sessão de IA reconstruía o
entendimento do zero a partir da conversa. O projeto tinha planos claros
de crescer (painel web, notificações, banco próprio) e precisava de uma
forma de qualquer IA retomar o trabalho com consistência entre sessões.

## Problema

Como garantir que decisões de estilo, arquitetura e conhecimento sobre o
projeto (infraestrutura, regras de negócio, peculiaridades da API do
Zabbix) sobrevivam ao fim de uma conversa e sejam aplicadas de forma
consistente em sessões futuras, por qualquer IA?

## Alternativas avaliadas

1. **Depender só da memória de longo prazo do assistente** — descartado:
   memória de assistente é específica de uma ferramenta/sessão, não é
   parte do repositório, não é auditável nem versionável junto com o
   código.
2. **Um único `CLAUDE.md` com tudo** — descartado: cresceria sem limite e
   misturaria regra permanente com conhecimento factual do projeto,
   dificultando manutenção.
3. **`prompts/` (regras executáveis) + `contexto/` (conhecimento factual)
   + `CLAUDE.md` (porta de entrada)** — escolhida.

## Decisão tomada

Criar `prompts/` com 22 arquivos numerados (00 a 21), cada um com
responsabilidade única, e `contexto/` com 8 arquivos de conhecimento
permanente sobre como o projeto funciona. `CLAUDE.md` na raiz como porta
de entrada obrigatória, com tabela de ordem de leitura e regras de
precedência.

## Justificativa

Separar "como desenvolver" (`prompts/`) de "como o projeto é"
(`contexto/`) mantém cada arquivo pequeno, focado e fácil de atualizar
independentemente. Numeração ordenava por prioridade de leitura.

## Consequências

- Scripts existentes movidos de raiz para `src/` (posteriormente para
  `scripts/`, ver ADR 003).
- Toda tarefa futura passou a consultar `CLAUDE.md` primeiro.
- A numeração plana (00-21) funcionou até o projeto pedir uma
  categorização mais explícita — ver ADR 003 para a evolução.
