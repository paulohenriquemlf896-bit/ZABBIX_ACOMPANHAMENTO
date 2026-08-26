# Sobe o painel web carregando as variaveis do .env, sem precisar de
# terminal aberto manualmente. Pensado para ser chamado pelo Agendador
# de Tarefas do Windows (Task Scheduler) — ver docs/README.md, secao
# "Rodar o painel ao ligar o PC".
#
# Uso manual (fora do Agendador, so pra testar):
#   powershell -ExecutionPolicy Bypass -File scripts\iniciar_painel.ps1

$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

if (-not (Test-Path ".env")) {
    Write-Error "[FALHA] .env nao encontrado em $raiz. Copie .env.example para .env e preencha antes de usar este script."
    exit 1
}

Get-Content ".env" | Where-Object { $_ -match '^\w+=' } | ForEach-Object {
    $nome, $valor = $_.Split('=', 2)
    Set-Item "Env:$nome" $valor
}

& pythonw.exe "src\web\app.py"
