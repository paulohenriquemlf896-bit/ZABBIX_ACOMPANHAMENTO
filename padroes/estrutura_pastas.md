# Padrão de estrutura de pastas

O que vai em cada pasta da raiz do projeto e a regra que separa uma da
outra. Consultar antes de decidir onde colocar um arquivo novo.

```
/
├── AI_BOOTSTRAP.md   — ordem de leitura obrigatória para qualquer IA
├── AI_MEMORY.md       — memória viva: decisões, features, dívidas, riscos
├── CLAUDE.md           — porta de entrada: visão geral, regras, precedência
├── .env / .env.example — credenciais e configuração (não versionar .env)
├── prompts/            — regras permanentes de desenvolvimento (executáveis)
│   ├── politicas/       — regras que valem sempre, independente da tarefa
│   ├── tarefas/          — regras específicas por área (backend, frontend...)
│   └── workflow/         — processo: missão, checklist, release, roadmap
├── padroes/             — decisões permanentes de "como fazer" (não é código)
├── templates/            — modelos de código reutilizáveis (é código, mas
│                           nunca executado diretamente — é ponto de partida)
├── specs/                — especificação de cada funcionalidade antes de
│                           implementar
├── examples/              — exemplos reais (payloads, respostas, HTML/CSV)
├── contexto/              — conhecimento permanente sobre COMO o projeto
│                           funciona hoje (infra, API, regras de negócio)
├── docs/                  — documentação viva
│   └── adr/                — uma decisão arquitetural por arquivo
├── logs/                   — logs de execução (não versionado)
├── scripts/                — utilitários: relatórios, manutenção, migração,
│                            importação/exportação, automações pontuais
└── src/                    — SOMENTE a aplicação (hoje: zbx_api.py, o
                             cliente de API compartilhado; nascerá aqui
                             tambem o painel Flask)
```

## A distinção mais importante: `src/` x `scripts/`

- **`src/`** é a aplicação: código que roda como um serviço/produto
  contínuo (o futuro painel Flask, o módulo `zbx_api.py` compartilhado
  que a aplicação e os scripts vão importar). Tem ciclo de vida de
  produto: versionado, testado, documentado como uma unidade.
- **`scripts/`** é ferramenta: algo que roda pontualmente ou por
  agendamento, produz uma saída e termina (`relatorio_problemas.py`,
  `validar_token.py`, `inspecionar_servicos.py`,
  `aplicar_exclusao_googleupdater.py`). Cada script é independente; não
  faz parte de um todo maior.
- Regra prática: se a pergunta "isso precisa estar rodando o tempo todo
  para o sistema funcionar?" for sim, é `src/`; se a resposta for
  "roda quando alguém manda ou quando o agendador dispara, e depois
  termina", é `scripts/`.
- Código comum aos dois (ex.: cliente da API Zabbix) vive em `src/` e é
  importado por `scripts/` — nunca duplicado entre os dois.

## `prompts/` — três categorias, sem exceção

- **`politicas/`** — regra que vale para QUALQUER tarefa, independente do
  que está sendo construído (segurança, arquitetura, estilo de código,
  testes, princípios, git, dependências, documentação, logs,
  configuração, performance, monitoramento).
- **`tarefas/`** — regra que só se aplica quando se está trabalhando
  naquela área específica (backend, frontend, banco de dados,
  integrações, notificações).
- **`workflow/`** — regra sobre o PROCESSO de desenvolver (missão,
  checklist de conclusão, release, roadmap, refatoração, revisão de
  evolução contínua).

Um prompt novo sempre entra em uma dessas três categorias. Se parecer não
caber em nenhuma, é sinal de que talvez precise de uma quarta categoria —
propor ao usuário antes de criar (ver
`prompts/workflow/evolucao.txt`).

## `padroes/` x `contexto/` x `docs/adr/` — não confundir

- **`padroes/`**: "como sempre fazemos X neste projeto" — atemporal,
  muda raramente, é referência de estilo/convenção.
- **`contexto/`**: "como o projeto está montado hoje" — factual sobre a
  infraestrutura, API, regras de negócio, servidores reais.
- **`docs/adr/`**: "por que decidimos fazer X desta forma, em vez de Y" —
  um registro histórico, imutável depois de escrito (se a decisão mudar,
  cria-se um ADR novo que supera o anterior, não se edita o antigo).

## `templates/` x `examples/` — não confundir

- **`templates/`**: ponto de partida para escrever código novo (esqueleto
  genérico, com placeholders).
- **`examples/`**: coisa real que o projeto já produziu ou recebeu
  (payload de resposta real da API, HTML real gerado) — serve para
  entender o formato, não para copiar como esqueleto.

## Regra de não-crescimento desordenado

Antes de criar uma pasta nova na raiz, verificar se o conteúdo não cabe
em uma das pastas já existentes. Pasta nova na raiz é uma decisão
arquitetural — registrar em `docs/adr/` (ver
`prompts/politicas/arquitetura.txt`).
