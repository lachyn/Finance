# Setup virtuálního prostředí na Windows
# Spusťte: .\scripts\setup.ps1

Write-Host "Setup Python prostředí - Finance" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath

# Ověř Python
Write-Host "`nKontrola Python..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Chyba: Python není nainstalován nebo není v PATH" -ForegroundColor Red
    Write-Host "Stáhněte Python z https://www.python.org/" -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Host "Nalezen: $pythonVersion" -ForegroundColor Green

# Vytvoř virtuální prostředí
$venvPath = Join-Path $rootPath ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "`nVytváření virtuálního prostředí..." -ForegroundColor Yellow
    python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Chyba při vytváření virtuálního prostředí" -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtuální prostředí vytvořeno: $venvPath" -ForegroundColor Green
} else {
    Write-Host "`nVirtualní prostředí již existuje" -ForegroundColor Cyan
}

# Aktivuj virtuální prostředí
Write-Host "`nAktivace virtuálního prostředí..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"

# Upgraduj pip
Write-Host "`nUpgrade pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Instaluj závislosti
$requirementsPath = Join-Path $rootPath "requirements.txt"
if (Test-Path $requirementsPath) {
    Write-Host "`nInstalace závislostí z requirements.txt..." -ForegroundColor Yellow
    pip install -r $requirementsPath --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Všechny závislosti nainstalovány" -ForegroundColor Green
    } else {
        Write-Host "Chyba při instalaci závislostí" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Soubor requirements.txt nenalezen" -ForegroundColor Yellow
}

Write-Host "`n=================================" -ForegroundColor Green
Write-Host "Setup dokončen!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "`nAktivace prostředí:" -ForegroundColor Cyan
Write-Host ".\scripts\activate.ps1" -ForegroundColor White
Write-Host "`nSpuštění skriptu:" -ForegroundColor Cyan
Write-Host "python src\qqq_gap_analysis.py" -ForegroundColor White
