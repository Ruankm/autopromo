# AutoPromo - Start All Services (PowerShell)
# Executa: .\start_all.ps1

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "AutoPromo - Starting All Services" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker is running
Write-Host "[1/4] Checking Docker..." -ForegroundColor Yellow
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker Desktop is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host "✓ Docker is running" -ForegroundColor Green
Write-Host ""

# Start PostgreSQL + Redis
Write-Host "[2/4] Starting PostgreSQL + Redis..." -ForegroundColor Yellow
docker-compose up -d postgres redis

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Database services started" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start database services" -ForegroundColor Red
    pause
    exit 1
}
Write-Host ""

# Wait for services to be ready
Write-Host "[3/4] Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
Write-Host "✓ Services should be ready" -ForegroundColor Green
Write-Host ""

# Instructions for next steps
Write-Host "[4/4] Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Open 2 new PowerShell terminals and run:" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 2 (Backend):" -ForegroundColor Cyan
Write-Host "  cd C:\Users\Ruan\Desktop\autopromo" -ForegroundColor White
Write-Host "  .\start_backend.bat" -ForegroundColor Green
Write-Host ""
Write-Host "Terminal 3 (Worker):" -ForegroundColor Cyan
Write-Host "  cd C:\Users\Ruan\Desktop\autopromo" -ForegroundColor White
Write-Host "  .\start_worker.bat" -ForegroundColor Green
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Services Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
