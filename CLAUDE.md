# Acompanhamento Zabbix — Grupo Rancho

Sistema orientado por IA (AI-Driven Development) que consome a API do
Zabbix 7.4 para relatórios, inspeção e correção de configuração da
infraestrutura monitorada do Grupo Rancho.

**Antes de ler este arquivo, confirme que já passou por
[`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md)** — ele define a ordem de leitura
completa do projeto. Este arquivo (`CLAUDE.md`) é o segundo passo dessa
ordem: visão geral, regras de precedência, convenções e checklist.

## Visão geral do sistema

- **O que é:** um conjunto de scripts Python (evoluindo para um painel
  Flask) que fala com o Zabbix via API JSON-RPC para gerar relatórios de
  disponibilidade e recorrência de problemas, inspecionar configuração e
  aplicar correções controladas.
- **Para quem:** equipe de TI do Grupo Rancho (uso técnico) e gestão
  (relatórios executivos).
- **Onde roda:** rede interna, endpoint
  `http://192.168.11.12/zabbix/api_jsonrpc.php`. Sem exposição à internet.
- **Estado atual:** ver [`AI_MEMORY.md`](AI_MEMORY.md) — é a fonte viva
  de "o que existe hoje, o que está em andamento, o que é dívida".

## Prioridades do projeto (nesta ordem, sem exceção)

1. **Segurança**
2. **Estabilidade**
3. **Manutenibilidade**
4. **Escalabilidade**
5. **Performance**
6. **Novas funcionalidades**

A IA nunca deve sacrificar arquitetura ou qualidade só para entregar uma
funcionalidade mais rápido. Se uma tarefa pedir isso, sinalizar o
trade-off ao usuário antes de agir.

## Estrutura do projeto

```
/
├── AI_BOOTSTRAP.md   ← ordem de leitura obrigatória (ler primeiro)
├── AI_MEMORY.md       ← memória viva: features, dívidas, riscos, roadmap
├── CLAUDE.md           ← este arquivo
├── prompts/             ← regras permanentes de desenvolvimento
│   ├── politicas/         ← regra que vale sempre, qualquer tarefa
│   ├── tarefas/            ← regra específica por área
│   └── workflow/            ← regra de processo/ciclo de vida
├── padroes/               ← decisões permanentes de convenção (não é código)
├── templates/              ← modelos reutilizáveis de código
├── specs/                   ← especificação de cada funcionalidade
├── examples/                  ← exemplos reais (payloads, HTML, CSV)
├── contexto/                  ← conhecimento sobre como o projeto funciona
├── docs/                       ← README, CHANGELOG
│   └── adr/                     ← uma decisão arquitetural por arquivo
├── logs/                        ← logs de execução
├── scripts/                      ← utilitários: relatórios, manutenção,
│                                  migração, automação pontual
└── src/                           ← SOMENTE a aplicação (hoje vazio;
                                    painel Flask nascerá aqui)
```

Detalhe de cada pasta e a distinção `src/` x `scripts/`:
[`padroes/estrutura_pastas.md`](padroes/estrutura_pastas.md).

## REGRA OBRIGATÓRIA: reutilizar antes de criar

**Antes de criar qualquer código novo, verificar se já existe uma
implementação semelhante no projeto.** Nesta ordem:

1. Existe um **template** em [`/templates`](templates) que já cobre esse
   padrão? → copiar e adaptar, não escrever do zero.
2. Existe um **padrão documentado** em [`/padroes`](padroes) que define
   como isso deve ser feito? → seguir, não inventar uma forma nova.
3. Existe uma **função, classe, serviço ou utilitário** já implementado
   em `src/` ou `scripts/` que resolve o mesmo problema? → reutilizar
   (importar/chamar), não duplicar.
4. Só depois de checar os três itens acima, se nada existir, escrever
   código novo — e considerar se ele deveria já nascer como um template
   reutilizável (ver `prompts/workflow/evolucao.txt`).

Evitar criar implementações paralelas para resolver o mesmo problema é
prioridade alta — ver `prompts/politicas/principios.txt`, itens 1 e 2.

## Ordem de leitura dos prompts (por categoria)

Antes de implementar qualquer funcionalidade, ler os prompts relevantes
ao tema da tarefa. `politicas/` sempre; `tarefas/` conforme a área;
`workflow/` conforme a fase do trabalho.

### `prompts/politicas/` — vale sempre, qualquer tarefa

| Arquivo | Ler quando |
|---|---|
| `principios.txt` | **SEMPRE, junto com seguranca.txt** — princípios que têm prioridade sobre qualquer decisão de implementação |
| `seguranca.txt` | **SEMPRE que tocar em credencial, escrita no Zabbix, entrada externa ou web** — prioridade máxima |
| `regras_gerais.txt` | SEMPRE, em qualquer tarefa |
| `arquitetura.txt` | Qualquer mudança estrutural, novo módulo, decisão de design |
| `codigo.txt` | Todo código Python novo |
| `testes.txt` | Qualquer lógica nova ou alterada |
| `logs.txt` | Qualquer script/serviço que produz saída operacional |
| `monitoramento.txt` | Health checks, métricas, observabilidade do próprio sistema |
| `documentacao.txt` | Ao criar/alterar scripts ou config do Zabbix |
| `git.txt` | Ao versionar, commitar, ramificar |
| `performance.txt` | Consultas pesadas, relatórios lentos, cache |
| `configuracao.txt` | Variáveis de ambiente, `.env`, parâmetros |
| `dependencias.txt` | Adicionar/atualizar/remover dependência |

### `prompts/tarefas/` — conforme a área da tarefa

| Arquivo | Ler quando |
|---|---|
| `backend.txt` | Scripts, serviços, API Zabbix, regras de negócio |
| `frontend.txt` | Relatórios HTML, painel, componentes, UX/UI |
| `banco_de_dados.txt` | Persistência, SQLite, migrations |
| `integracoes.txt` | Zabbix, GLPI, Proxmox — qualquer sistema externo |
| `notificacoes.txt` | E-mail, Telegram, Teams, WhatsApp, retries |

### `prompts/workflow/` — conforme a fase do trabalho

| Arquivo | Ler quando |
|---|---|
| `missao.txt` | **SEMPRE, primeiro de todos** — missão, prioridades, regras inquebráveis |
| `evolucao.txt` | Ao final de qualquer tarefa não trivial, antes do checklist |
| `refatoracao.txt` | Antes de refatorar código existente |
| `release.txt` | Antes de publicar/entregar uma versão |
| `roadmap.txt` | Ao planejar ou registrar ideias futuras |
| `checklist.txt` | **SEMPRE, ao concluir qualquer tarefa** |

## Precedência entre regras

Quando dois prompts conflitarem:

1. **`prompts/politicas/seguranca.txt`** vence qualquer outro prompt, sem
   exceção.
2. **`prompts/politicas/principios.txt`** vence em qualquer questão de
   trade-off de implementação (duplicação, reutilização, simplicidade,
   retrocompatibilidade).
3. **`prompts/workflow/missao.txt`** vence em questões de prioridade/
   filosofia do projeto (ex.: "vale sacrificar estabilidade por essa
   funcionalidade?" → não).
4. O prompt mais específico ao tema da tarefa vence o mais genérico
   (ex.: `prompts/tarefas/banco_de_dados.txt` vence
   `prompts/politicas/regras_gerais.txt` em modelagem de tabela).
5. Na dúvida, ou se dois prompts parecerem se contradizer sem que a
   hierarquia acima resolva, perguntar ao usuário em vez de decidir
   sozinho.

## Convenções gerais (resumo — detalhe em `padroes/`)

- Python 3.10+, biblioteca padrão como primeira escolha.
- Nomes de arquivos/variáveis/funções: português sem acentos, snake_case;
  não misturar com inglês no mesmo arquivo (`padroes/nomenclatura.md`).
- Mensagens ao usuário (console, HTML, e-mail): português.
- Console usa prefixos padronizados: `[OK]` `[FALHA]` `[info]` `[..]`
  `[PULADO]` `[APLICADO]`.
- Credenciais **sempre** via variável de ambiente/`.env`, nunca
  hardcoded em código novo (`prompts/politicas/seguranca.txt`).
- Autenticação Zabbix 7.x: header `Authorization: Bearer <token>`; nunca
  campo `auth` no corpo.
- Saídas geradas (`relatorio_*.html/csv`) levam timestamp e vão para
  `scripts/saidas/`.
- Respostas JSON internas (painel, quando existir) seguem
  `padroes/padrao_respostas_api.md`.

## Fluxo de desenvolvimento

1. Seguir `AI_BOOTSTRAP.md` (bootstrap completo) se for a primeira vez
   nesta sessão trabalhando no projeto.
2. Identificar o tema da tarefa e ler os prompts relevantes nas tabelas
   acima (`politicas/principios.txt`, `politicas/seguranca.txt` e
   `workflow/missao.txt` sempre).
3. Verificar reutilização (seção "Regra obrigatória" acima) antes de
   escrever código novo.
4. Verificar se há conhecimento já registrado em `contexto/` sobre o
   assunto — não redescobrir o que já está documentado.
5. Se a funcionalidade for nova e não trivial, verificar/criar spec em
   `specs/` antes de implementar.
6. Implementar seguindo as regras dos prompts aplicáveis.
7. Atualizar `docs/`, `contexto/` e `AI_MEMORY.md` na mesma tarefa se
   algo relevante mudou.
8. Escrever/atualizar testes (`prompts/politicas/testes.txt`).
9. Rodar a autoavaliação de `prompts/workflow/evolucao.txt`.
10. Rodar o checklist de `prompts/workflow/checklist.txt` antes de
    considerar a tarefa concluída.
11. Se identificar um novo domínio de conhecimento ou categoria de regra
    sem prompt correspondente, **propor a criação de um novo arquivo**
    antes de implementá-la (exceto quando o usuário já forneceu a
    especificação completa e aprovada) — ver `prompts/workflow/evolucao.txt`.

## Checklist obrigatório antes de concluir qualquer tarefa

(Versão resumida — a completa está em
`prompts/workflow/checklist.txt`, que deve ser consultada integralmente.)

- [ ] Verifiquei reutilização (`/templates`, `/padroes`, código existente)
      antes de criar algo novo.
- [ ] Código roda sem erro de sintaxe/import.
- [ ] Nenhuma duplicação desnecessária introduzida.
- [ ] Tratamento de erros presente (sem `except` silencioso).
- [ ] Logs adequados implementados.
- [ ] Documentação (`docs/`, `contexto/`, `AI_MEMORY.md`, docstrings)
      atualizada.
- [ ] Testes existentes continuam passando; testes novos cobrem a lógica
      nova.
- [ ] Nenhuma credencial exposta em código, log ou documentação.
- [ ] Configuração via `.env`/variável de ambiente, não hardcoded.
- [ ] Arquitetura permanece consistente com `prompts/politicas/arquitetura.txt`.
- [ ] Decisão arquitetural relevante registrada em `docs/adr/`.
- [ ] Mudança respeita todos os prompts aplicáveis ao tema.

Nenhuma tarefa é considerada concluída sem passar por este checklist.

## Evolução contínua

Esta estrutura é um sistema vivo — ver `prompts/workflow/evolucao.txt`
para a rotina de autoavaliação contínua (duplicação, acoplamento,
oportunidade de reutilização, tamanho de módulo). Sempre que surgir uma
nova categoria de regra ou de conhecimento, **propor** ao usuário a
criação do arquivo correspondente (`prompts/<categoria>/nome.txt`,
`contexto/nome.md`, `padroes/nome.md`, `specs/nome.md`) antes de
implementar — exceto quando o usuário já entregou a especificação
completa e aprovada, caso em que se implementa e se registra a decisão
em `docs/adr/`.
