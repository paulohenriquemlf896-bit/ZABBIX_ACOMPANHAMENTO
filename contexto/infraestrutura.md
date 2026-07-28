# Infraestrutura

Conhecimento permanente sobre onde este projeto roda e com o que ele
conversa. Atualizar sempre que algo aqui mudar de fato (não é
especulação — é o estado real observado).

## Zabbix (sistema monitorado por este projeto)

- **Servidor:** `192.168.11.12` (rede interna do Grupo Rancho).
- **Versão:** Zabbix 7.4.4 (server e frontend).
- **Interface web:** `http://192.168.11.12/zabbix/`
- **API JSON-RPC:** `http://192.168.11.12/zabbix/api_jsonrpc.php`
- **Protocolo:** HTTP puro (sem TLS) — aceito por ser rede interna. Se
  isso mudar, registrar como um ADR novo em `docs/adr/`.
- **Autenticação:** header `Authorization: Bearer <token>` (padrão 7.x,
  sem campo `auth` no corpo).
- Escopo monitorado: ~23 hosts — servidores Windows (SRV-FORTES, Siagri
  Nutrane, Siagri Rancho, RanchoAD, Servidor de Arquivo), terminais de
  caixa em várias lojas, catracas de acesso (C.Alves, Carpina, Pesqueira,
  Teresina), dispositivos de rede (link WAN, dispositivos SNMP em postos).

## Onde este projeto roda

- Máquina de desenvolvimento/operação: Windows (ambiente principal dos
  scripts atuais).
- Scripts são executados manualmente hoje; agendamento via Task Scheduler
  do Windows é o candidato natural quando a automação evoluir (ver
  `prompts/workflow/roadmap.txt`).

## Outros servidores do Grupo Rancho relevantes ao contexto (não integrados
a este projeto ainda)

- **srvprojrancho** — `192.168.11.84`: roda o relatório de backup Proxmox
  via cron e dois serviços Flask soltos no home do usuário. Possível
  ponto de integração futura (ver `contexto/integracoes.md`).
- **VPS Hostinger** — hospeda as aplicações StoCount (`stocount.com:5000`)
  e Inventário Delaval (porta 8000), via systemd + MariaDB. Sem relação
  direta com o Zabbix hoje.
- **GLPI** — inventário de ativos do Grupo Rancho (GLPI 10, inventário
  nativo via dyndns, entidade raiz "Grupo Rancho"). Candidato a
  cruzamento com o inventário do Zabbix (host x ativo cadastrado) — ver
  roadmap.
- **E-mail Locaweb** — domínio `gruporanchoalegre.com.br`, SMTP validado
  via Thunderbird. Candidato a canal de envio de relatórios quando
  `prompts/tarefas/notificacoes.txt` for implementado.

## Limitações conhecidas do ambiente

- Sem ambiente de homologação separado para o Zabbix — todo teste de
  leitura roda contra produção (aceitável, pois leitura é livre); testes
  de escrita são sempre confirmados manualmente (ver
  `prompts/politicas/seguranca.txt`).
- Sem VPN configurada para acesso externo ao Zabbix — uso é 100% rede
  interna por enquanto.
