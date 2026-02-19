# Quick Setup Script for MySQL Database-Driven Screening
# Run this after MySQL is installed and configured

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  Equifax Agentic AI Screening - Quick Setup" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Step 1: Check Python
Write-Host "Step 1: Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Step 2: Check virtual environment
Write-Host "`nStep 2: Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "  ✓ Virtual environment exists" -ForegroundColor Green
    
    # Activate virtual environment
    Write-Host "  → Activating virtual environment..." -ForegroundColor Cyan
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "  ✗ Virtual environment not found" -ForegroundColor Red
    Write-Host "  → Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    & .\venv\Scripts\Activate.ps1
    Write-Host "  ✓ Virtual environment created and activated" -ForegroundColor Green
}

# Step 3: Install dependencies
Write-Host "`nStep 3: Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "  → This may take a few minutes..." -ForegroundColor Cyan
pip install --upgrade pip -q
pip install -r requirements.txt -q
Write-Host "  ✓ Dependencies installed" -ForegroundColor Green

# Step 4: Check MySQL
Write-Host "`nStep 4: Checking MySQL..." -ForegroundColor Yellow
try {
    $mysqlVersion = mysql --version 2>&1
    Write-Host "  ✓ MySQL installed: $mysqlVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ MySQL not found. Please install MySQL 8.0+" -ForegroundColor Red
    Write-Host "    Download from: https://dev.mysql.com/downloads/installer/" -ForegroundColor Yellow
    exit 1
}

# Check MySQL service
$mysqlService = Get-Service -Name "MySQL*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($mysqlService) {
    if ($mysqlService.Status -eq "Running") {
        Write-Host "  ✓ MySQL service is running" -ForegroundColor Green
    } else {
        Write-Host "  ! MySQL service is not running. Starting..." -ForegroundColor Yellow
        Start-Service $mysqlService.Name
        Write-Host "  ✓ MySQL service started" -ForegroundColor Green
    }
} else {
    Write-Host "  ! MySQL service not found, but MySQL CLI is available" -ForegroundColor Yellow
}

# Step 5: Check .env file
Write-Host "`nStep 5: Checking configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  ✓ .env file exists" -ForegroundColor Green
} else {
    Write-Host "  ! .env file not found. Creating from example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "  ✓ .env file created" -ForegroundColor Green
    Write-Host "  ⚠  Please update DATABASE_URL and API keys in .env file!" -ForegroundColor Yellow
    
    # Open .env in notepad
    $response = Read-Host "  → Open .env file now? (Y/n)"
    if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
        notepad .env
        Write-Host "  → Waiting for you to update .env file. Press Enter when done..." -ForegroundColor Cyan
        Read-Host
    }
}

# Step 6: Database initialization
Write-Host "`nStep 6: Database initialization..." -ForegroundColor Yellow
Write-Host "  ⚠  WARNING: This will DROP and recreate the database!" -ForegroundColor Yellow
$response = Read-Host "  → Continue with database initialization? (y/N)"

if ($response -eq "y" -or $response -eq "Y") {
    Write-Host "`n  → Initializing database with 10 sample applicants..." -ForegroundColor Cyan
    Write-Host "    - 2 approved" -ForegroundColor Gray
    Write-Host "    - 2 rejected" -ForegroundColor Gray
    Write-Host "    - 6 pending (to be processed)" -ForegroundColor Gray
    Write-Host ""
    
    # Update DB credentials in init script
    Write-Host "  → Please ensure database credentials are set in database\init_db.py" -ForegroundColor Yellow
    $response2 = Read-Host "  → Credentials updated? (Y/n)"
    
    if ($response2 -eq "" -or $response2 -eq "Y" -or $response2 -eq "y") {
        python database\init_db.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n  ✓ Database initialized successfully!" -ForegroundColor Green
        } else {
            Write-Host "`n  ✗ Database initialization failed" -ForegroundColor Red
            Write-Host "    Check error messages above and fix database credentials" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "  → Skipped database initialization" -ForegroundColor Yellow
    }
} else {
    Write-Host "  → Skipped database initialization" -ForegroundColor Yellow
}

# Summary and next steps
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Start the API server:" -ForegroundColor White
Write-Host "   uvicorn api.main:app --reload`n" -ForegroundColor Cyan

Write-Host "2. In another terminal, run the test script:" -ForegroundColor White
Write-Host "   python test_mysql_system.py`n" -ForegroundColor Cyan

Write-Host "3. Process pending applications:" -ForegroundColor White
Write-Host "   Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/process-pending?limit=10' -Method POST`n" -ForegroundColor Cyan

Write-Host "4. View API documentation:" -ForegroundColor White
Write-Host "   http://localhost:8000/docs`n" -ForegroundColor Cyan

Write-Host "5. Check statistics:" -ForegroundColor White
Write-Host "   Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/statistics' -Method GET | ConvertTo-Json`n" -ForegroundColor Cyan

Write-Host "============================================================`n" -ForegroundColor Cyan

# Offer to start server
$response = Read-Host "Start the API server now? (Y/n)"
if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
    Write-Host "`nStarting API server..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Yellow
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
}
