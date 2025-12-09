# Aktivace virtuálního prostředí na Windows
# Spusťte: .\scripts\activate.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath
$venvPath = Join-Path $rootPath ".venv"

if (-not (Test-Path $venvPath)) {
    Write-Host "Chyba: Virtuální prostředí neexistuje!" -ForegroundColor Red
    Write-Host "Nejdřív spusťte: .\scripts\setup.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Aktivace virtuálního prostředí..." -ForegroundColor Green
& "$venvPath\Scripts\Activate.ps1"
Write-Host "Prostředí aktivováno!" -ForegroundColor Green
