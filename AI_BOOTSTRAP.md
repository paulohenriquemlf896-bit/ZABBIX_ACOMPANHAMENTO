# AI_BOOTSTRAP.md — ordem de leitura obrigatória

Este arquivo orienta qualquer IA (ou pessoa) sobre a sequência correta
para entender este projeto antes de modificar qualquer coisa. **É o
primeiro arquivo a abrir**, antes até do `CLAUDE.md`.

## Fluxo de bootstrap

```
1. AI_BOOTSTRAP.md   ← você está aqui
2. CLAUDE.md          ← visão geral, regras de precedência, checklist
3. prompts/            ← regras de desenvolvimento (ordem: workflow/missao.txt
                         e politicas/principios.txt primeiro, depois o que
                         for relevante ao tema da tarefa — tabela completa
                         em CLAUDE.md)
4. contexto/            ← como o projeto funciona hoje (infra, API, regras
                         de negócio, servidores, integrações)
5. docs/                ← README (inventário), CHANGELOG (histórico),
                         adr/ (decisões arquiteturais)
6. AI_MEMORY.md          ← estado corrente: features prontas/em andamento/
                         futuras, dívidas técnicas, riscos, limitações
7. roadmap               ← prompts/workflow/roadmap.txt (ideias futuras
                         ainda sem spec)
8. código-fonte           ← só agora, com todo o contexto acima, abrir
                         scripts/ e src/
```

## Por que essa ordem

Abrir o código antes do contexto leva a redescobrir (ou pior, contradizer
sem perceber) decisões já tomadas — como aconteceu com a correção manual
incompleta do GoogleUpdater antes deste projeto existir (ver
`docs/adr/002-correcao-ruido-googleupdater.md`). Ler `AI_MEMORY.md` antes
do código evita retrabalho em algo que já é dívida técnica conhecida ou
já está no roadmap.

## Checklist rápido antes de tocar em qualquer arquivo

- [ ] Li `CLAUDE.md` e sei qual(is) prompt(s) de `prompts/politicas`,
      `prompts/tarefas` e `prompts/workflow` se aplicam à tarefa.
- [ ] Chequei `contexto/` para não redescobrir algo já documentado.
- [ ] Chequei `AI_MEMORY.md` para saber se isso já é uma dívida conhecida,
      um risco listado, ou algo já planejado com spec própria.
- [ ] Se a funcionalidade é nova e não trivial, chequei se existe (ou se
      preciso criar) uma spec em `specs/` antes de implementar.
- [ ] Verifiquei se existe um template em `/templates` ou um padrão em
      `/padroes` que já resolve parte do problema, em vez de reimplementar
      (regra obrigatória — ver `CLAUDE.md` e
      `prompts/politicas/principios.txt`, item 2).

## Ponteiro rápido por tipo de pergunta

| Pergunta | Onde olhar primeiro |
|---|---|
| "Como devo nomear isso?" | `padroes/nomenclatura.md` |
| "Onde esse arquivo deveria ficar?" | `padroes/estrutura_pastas.md` |
| "Já existe algo assim no projeto?" | `templates/`, `src/`, `scripts/` |
| "Por que foi feito assim?" | `docs/adr/` |
| "Qual é o estado real disso hoje?" | `AI_MEMORY.md`, `contexto/` |
| "Como essa funcionalidade deveria se comportar?" | `specs/` |
| "Isso é permitido/seguro fazer?" | `prompts/politicas/seguranca.txt`, `prompts/politicas/principios.txt` |
