# Regras de negócio

Definições que não estão em nenhum lugar do Zabbix, mas que este projeto
usa para transformar dados brutos em informação útil. Se uma dessas
definições mudar, os relatórios existentes mudam de significado — por
isso ficam registradas aqui, não só implícitas no código.

## Recorrência de problema

**Definição adotada:** recorrência = número de vezes que uma trigger
entrou em estado de **PROBLEMA** (evento com `value=1`, fonte trigger) em
uma janela de tempo. Eventos de recuperação (`value=0`, "OK") não contam.

Motivo: o objetivo é medir "quantas vezes algo deu errado", não "quanto
tempo ficou no estado de erro" (isso seria uma métrica diferente, de
duração/MTTR, não implementada ainda).

## Agrupamento por "problema"

Eventos são agrupados pelo **nome do problema** (`event.name`), não pelo
`triggerid`. Consequência conhecida e aceita: quando o nome de uma
trigger muda (ex.: o Zabbix cria uma trigger nova por versão de serviço,
como aconteceu com o GoogleUpdater), cada nome vira uma linha separada no
ranking, mesmo representando "o mesmo tipo de problema" na prática. Isso
é aceitável para o caso de uso de identificar ruído (ver
`docs/adr/002-correcao-ruido-googleupdater.md`), mas quem ler o relatório
deve saber disso.

## Janelas de tempo padrão dos relatórios

- **Hoje**: desde 00:00 do dia corrente.
- **Últimos 7 dias**: últimas 168 horas a partir do momento de geração.
- **Últimos 30 dias**: últimos 30 dias corridos.
- **Últimos 365 dias**: último ano corrido.

Essas janelas foram escolhidas para responder três perguntas diferentes:
"o que está acontecendo agora" (hoje/7 dias), "o que é um padrão do mês"
(30 dias) e "o que é estrutural" (365 dias, geralmente aponta ruído
crônico como o caso GoogleUpdater).

## Severidade

A severidade de um "problema agrupado" no relatório é a **severidade
máxima** observada entre todas as ocorrências daquele nome no período —
não a média, não a mais recente. Motivo: um problema que já foi
"Desastre" uma vez merece destaque mesmo que a maioria das ocorrências
tenha sido "Média".

## Ruído vs. problema real (heurística, não regra formal do Zabbix)

Um padrão de evento é tratado como candidato a "ruído" (falso positivo
recorrente) quando: (a) tem volume desproporcional no ranking; (b)
representa um serviço/processo transitório por natureza (ex.: updater de
terceiros); (c) não corresponde a uma indisponibilidade real percebida
pelo usuário do sistema monitorado. Essa avaliação é sempre feita por uma
pessoa lendo o relatório — o script não decide sozinho o que é ruído (ver
`prompts/workflow/missao.txt`, objetivo 1).

## Escopo de "escrita" no Zabbix permitida por este projeto

Este projeto só escreve no Zabbix em **configuração** (macros, filtros de
descoberta), nunca em dados de monitoramento (não fecha problemas
manualmente, não cria/edita triggers de negócio, não altera hosts). Se
esse escopo precisar mudar, é uma decisão a registrar como um ADR novo em
`docs/adr/`, com aprovação do usuário.
