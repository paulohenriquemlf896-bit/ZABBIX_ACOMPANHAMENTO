# Padrão de nomenclatura

Referência única de como nomear coisas neste projeto. Consultar **antes**
de criar arquivo, função, variável, classe ou tabela nova. Regra de origem
em `prompts/politicas/regras_gerais.txt` e `prompts/politicas/codigo.txt`
— este documento é a referência prática e consultável, não a política em
si.

## Idioma

| O quê | Idioma | Exemplo |
|---|---|---|
| Nome de arquivo, variável, função, classe | Português sem acentos | `validar_token.py`, `buscar_eventos`, `novo_valor` |
| Mensagem ao usuário (console, HTML, e-mail) | Português | `"[FALHA] Token rejeitado"` |
| Comentário no código | Português | `# recorrencia = numero de vezes que entrou em PROBLEM` |

Nunca misturar português e inglês de nomenclatura no mesmo arquivo.

## Arquivos

- Scripts executáveis (`/scripts`): `verbo_substantivo.py` —
  `validar_token.py`, `relatorio_problemas.py`,
  `aplicar_exclusao_googleupdater.py`.
- Módulos de biblioteca (`/src`): `substantivo.py` — `zbx_api.py`.
- Prompts (`/prompts/<categoria>`): `substantivo.txt`, sem prefixo
  numérico (a categoria já organiza) — `seguranca.txt`, `backend.txt`.
- Contexto (`/contexto`): `substantivo.md` — `infraestrutura.md`.
- ADR (`/docs/adr`): `NNN-titulo-curto-em-kebab-case.md` — numeração
  sequencial de 3 dígitos, nunca reaproveitada mesmo se um ADR for
  superado (marcar como "Superado por NNN", não apagar nem renumerar).
- Templates (`/templates`): nome do padrão que representa —
  `api_service.py`, `flask_blueprint.py`, `email.html`.
- Specs (`/specs`): `substantivo.md` nomeado pela funcionalidade —
  `relatorios.md`, `notificacoes.md`.
- Saídas geradas: `nome_AAAAMMDD_HHMM.ext` — timestamp sempre presente.

## Variáveis e constantes

- Constantes de configuração: `MAIUSCULAS_COM_UNDERSCORE` no topo do
  arquivo — `ZBX_URL`, `MAX_EVENTOS`, `TOP_N`.
- Variáveis normais: `snake_case` — `eventos`, `ranking`, `total`.
- Booleanos: prefixo que deixa claro que é sim/não quando o nome sozinho
  não é óbvio — `VERIFY_SSL`, não `verify`.

## Funções

- `verbo_substantivo`, uma responsabilidade — `buscar_eventos`,
  `agregar`, `tabela_html`, `novo_valor`.
- Função que só formata/apresenta termina descrevendo a saída:
  `tabela_html`, `barra_sev`.

## Classes (quando existirem — usar só com estado real a encapsular)

- `PascalCase`, substantivo — `ClienteZabbix`, não `GerenciadorDeCliente`
  (evitar sufixos genéricos tipo Manager/Handler sem necessidade).

## Banco de dados (quando existir — ver `prompts/tarefas/banco_de_dados.txt`)

- Tabelas e colunas: `snake_case`, português sem acentos, singular —
  `evento`, `problema`, `host`, `snapshot_diario`.
- Índices: `idx_tabela_coluna`.
- Migrations: `NNN_descricao_curta.sql`, numeração sequencial de 3
  dígitos.

## Variáveis de ambiente

- Prefixo do sistema/integração em maiúsculas + nome —
  `ZBX_URL`, `ZBX_TOKEN`, `SMTP_HOST`, `TELEGRAM_BOT_TOKEN`.

## Console (prefixos fixos, não inventar variação)

`[OK]` `[FALHA]` `[info]` `[..]` `[PULADO]` `[APLICADO]` — ver
`prompts/politicas/logs.txt` para o significado de cada um.
