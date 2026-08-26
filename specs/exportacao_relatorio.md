# Spec: Exportação de relatório (Excel/PDF) com seleção de hosts e período

**Status:** implementado. Pedido do usuário em 2026-08-26.

## Objetivo

Gerar um relatório de problemas recorrentes para download (Excel ou
PDF), com o usuário escolhendo **quais hosts** incluir e **quais
períodos**, em vez de sempre gerar o relatório completo fixo que
`scripts/relatorio_problemas.py` já produz.

## Regras de negócio

- Reaproveita `contexto/regras_negocio.md` integralmente (recorrência,
  agrupamento por nome do problema, severidade máxima) — a exportação
  não redefine nada, só filtra por host antes de agregar.
- **Filtro de host**: se nenhum host for selecionado, ou a opção
  "Todos" for marcada, nenhum filtro é aplicado (comportamento igual ao
  relatório CLI). Se hosts específicos forem selecionados, um evento só
  entra na agregação se pelo menos um dos hosts afetados por ele estiver
  na lista escolhida (mesma semântica de "afeta o host", não "afeta
  só o host").
- **Períodos**: um ou mais entre `hoje`, `7d`, `30d`, `365d` (mesma
  whitelist do painel). Cada período selecionado gera sua própria
  agregação independente (nunca soma ocorrências de períodos
  diferentes).
- **Excel**: cada período selecionado vira uma aba própria, nomeada com
  o título do período (ex.: "Hoje", "Ultimos 7 dias"). Uma aba de capa
  ("Resumo") lista os hosts/período selecionados e a data de geração.
- **PDF**: documento único, uma seção por período selecionado, no mesmo
  estilo visual (paleta de severidade, badges) do relatório HTML/painel
  já existentes — não inventa uma identidade visual nova.
- Lista de hosts oferecida na tela de seleção vem de `host.get` (todos
  os hosts monitorados, não só os que têm problema no período) —
  ordenados alfabeticamente.

## Fluxo

1. Usuário acessa `GET /exportar` (rota protegida, exige login).
2. Marca hosts (ou "Selecionar todos"), períodos (ou "Selecionar
   todos") e o formato (Excel ou PDF).
3. `POST /exportar` — para cada período selecionado: busca eventos
   (`buscar_eventos`), filtra por host (`filtrar_por_hosts`, novo em
   `src/relatorios_service.py`), agrega (`agregar`, já existente).
4. Gera o arquivo em memória (`src/web/exportar_excel.py` ou
   `src/web/exportar_pdf.py`) e devolve como download
   (`Content-Disposition: attachment`), nome
   `relatorio_problemas_AAAAMMDD_HHMM.xlsx` (ou `.pdf`).
5. Nenhum arquivo fica salvo no servidor — gerado sob demanda e
   descartado após o download (diferente de
   `scripts/relatorio_problemas.py`, que salva em `scripts/saidas/`).

## Entradas

| Nome | Origem | Obrigatório | Observação |
|---|---|---|---|
| `hosts` | formulário `POST /exportar` | não | lista de nomes de host; ausente/vazio = todos |
| `periodos` | formulário `POST /exportar` | sim | pelo menos um de `hoje,7d,30d,365d` |
| `formato` | formulário `POST /exportar` | sim | `excel` ou `pdf` |

## Saídas

- Arquivo `.xlsx` (via `openpyxl`) ou `.pdf` (via `fpdf2`) — ambas
  dependências novas, avaliadas e justificadas: biblioteca padrão não
  tem gerador de planilha nem de PDF; as duas são puro Python, sem
  compilação nativa no Windows (`prompts/politicas/dependencias.txt`,
  item 11).

## Validações

- `periodos` vazio ou só valores fora da whitelist → erro amigável na
  tela do formulário, nunca 500.
- `formato` fora de `{excel, pdf}` → mesma coisa.
- Host informado que não existe mais no Zabbix (removido entre a
  listagem e o envio do formulário) → simplesmente não aparece em
  nenhum evento, relatório sai sem ele, sem erro.

## Casos extremos

- Nenhum evento no período+hosts selecionados → aba/seção mostra
  "Nenhum problema registrado", igual ao padrão já usado no
  painel/CLI — nunca aba/seção vazia muda.
- Todos os hosts selecionados individualmente (equivalente a "todos")
  → funciona igual a marcar "Todos", só mais lento de montar o filtro
  (sem problema de performance real nessa escala, ~25 hosts).
- Falha de comunicação com o Zabbix no meio da geração (após já ter
  processado algum período) → aborta a exportação inteira com erro
  amigável, não devolve arquivo parcial.

## Fora de escopo desta versão

- Agendamento/envio automático do relatório por e-mail (ver
  `specs/notificacoes.md` — feature separada, ainda não retomada).
- Filtro por severidade mínima — ideia sugerida, não implementada
  agora (ver `AI_MEMORY.md`, roadmap).
- Gráficos embutidos no Excel/PDF (o painel web já mostra gráficos;
  exportação por ora é só tabular).
