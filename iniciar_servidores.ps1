# Script PowerShell para iniciar os dois servidores SICFAAE

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Iniciando Servidores SICFAAE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/2] Iniciando DRH na porta 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\sicfaae-drh'; python manage.py runserver 8000" -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host "[2/2] Iniciando DEFC na porta 8001..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\sicfaae-defc'; python manage.py runserver 8001" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Servidores Iniciados!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "DRH:  " -NoNewline
Write-Host "http://localhost:8000" -ForegroundColor Blue
Write-Host "DEFC: " -NoNewline
Write-Host "http://localhost:8001" -ForegroundColor Blue
Write-Host ""
Write-Host "Pressione qualquer tecla para abrir os navegadores..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Start-Process "http://localhost:8000"
Start-Process "http://localhost:8001"

Write-Host ""
Write-Host "Para parar os servidores, feche as janelas do PowerShell." -ForegroundColor Gray
Write-Host ""
