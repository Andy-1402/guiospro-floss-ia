# Subir GUIOSPRO_FLOSS a GitHub — ejecutar en PowerShell:
#   cd C:\Users\Jeff\Desktop\GUIOSPRO_FLOSS-main
#   .\subir_github.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== GUIOSPRO — preparar Git ===" -ForegroundColor Cyan

git --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Instale Git: https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path .git)) {
    git init
    Write-Host "Repositorio git inicializado." -ForegroundColor Green
}

# Rama principal
$branch = git branch --show-current 2>$null
if (-not $branch) {
    git checkout -b main 2>$null
    if ($LASTEXITCODE -ne 0) { git checkout -b master }
}

git add -A
Write-Host "`nArchivos que se subiran:" -ForegroundColor Yellow
git status --short

if (git status --porcelain | Select-String "^\?\? \.env$|^A  \.env$|^M  \.env$") {
    Write-Host "AVISO: .env no deberia subirse. Revise .gitignore" -ForegroundColor Red
}

$hasCommit = git rev-parse HEAD 2>$null
if (-not $hasCommit) {
    git commit -m "Initial commit: GUIOSPRO Streamlit app (SQLite)"
    Write-Host "Commit creado." -ForegroundColor Green
} else {
    $pending = git status --porcelain
    if ($pending) {
        git commit -m "Update: GUIOSPRO app"
        Write-Host "Commit de cambios creado." -ForegroundColor Green
    }
}

Write-Host "`n=== GitHub ===" -ForegroundColor Cyan
$ghOk = $false
try {
    gh auth status 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $ghOk = $true }
} catch {}

if ($ghOk) {
    Write-Host "GitHub CLI detectado. Creando repo publico GUIOSPRO_FLOSS ..." -ForegroundColor Green
    gh repo create GUIOSPRO_FLOSS --public --source=. --remote=origin --push
    if ($LASTEXITCODE -eq 0) {
        git remote get-url origin
        Write-Host "`nListo. Abra la URL anterior en el navegador." -ForegroundColor Green
        exit 0
    }
}

Write-Host @"

GitHub CLI no disponible o no ha iniciado sesion.

Pasos manuales:
1. Abra https://github.com/new
2. Nombre del repositorio: GUIOSPRO_FLOSS
3. Publico -> Create repository (sin README ni .gitignore)
4. Ejecute (cambie TU_USUARIO por su usuario de GitHub):

   git remote add origin https://github.com/TU_USUARIO/GUIOSPRO_FLOSS.git
   git push -u origin main

   Si su rama se llama master:
   git push -u origin master

Para usar gh despues: gh auth login
"@ -ForegroundColor Yellow
