# Integrações — estado real

Regras gerais de como integrar estão em `prompts/tarefas/integracoes.txt` e
`prompts/tarefas/notificacoes.txt`. Este arquivo registra o **estado real**
de cada integração: o que já existe, o que é planejado, e detalhes
concretos (endpoint, formato) assim que forem implementados.

## Zabbix — ATIVA (única integração implementada hoje)

- Ver `contexto/infraestrutura.md` (endpoint/rede) e `contexto/api.md`
  (detalhes de uso da API).
- Autenticação: token de API do usuário `Admin` (Super admin) — ver
  `AI_MEMORY.md`, seção Dívidas técnicas, item 1.

## E-mail (SMTP) — PLANEJADA, não implementada

- Infraestrutura disponível: domínio `gruporanchoalegre.com.br` na
  Locaweb, SMTP já validado manualmente via Thunderbird em outro
  contexto do Grupo Rancho. Há histórico de erro intermitente
  "queue file write error" no envio observado nesse ambiente Locaweb —
  vale considerar retry (ver `prompts/tarefas/notificacoes.txt`) quando esta
  integração for implementada aqui.
- Nada implementado neste projeto ainda. Quando for, preencher aqui:
  host/porta SMTP, se usa STARTTLS, nome da variável de ambiente da
  senha.

## GLPI — NÃO INTEGRADA, candidata de roadmap

- GLPI 10 já em uso pelo Grupo Rancho para inventário de ativos, com
  inventário nativo via dyndns, entidade raiz "Grupo Rancho".
- Ideia de integração (não implementada): cruzar `host.get` do Zabbix
  com o inventário do GLPI para achar (a) hosts monitorados sem ativo
  cadastrado, (b) ativos cadastrados sem monitoramento.
- Quando isso avançar, documentar aqui: como a API do GLPI é acessada
  (REST, App-Token/User-Token), e mover a regra de acesso para
  `prompts/tarefas/integracoes.txt`.

## Telegram / Teams / WhatsApp — NÃO INTEGRADAS

- Nenhuma decisão tomada sobre qual canal usar primeiro. Ver
  `prompts/tarefas/notificacoes.txt` para o padrão a seguir quando uma dessas
  for implementada.

## Proxmox — NÃO INTEGRADA, relacionada indiretamente

- O servidor `srvprojrancho` (192.168.11.84) já roda um relatório de
  backup Proxmox via cron, fora deste projeto. Se este projeto vier a
  cruzar dados (ex.: saúde de VM no Zabbix x status de backup Proxmox),
  registrar aqui a forma de acesso quando decidido.
