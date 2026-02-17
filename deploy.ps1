# Deployment Script for Equifax AI MCP Screening Platform
# Usage: .\deploy.ps1 [-Environment <env>] [-Action <action>]

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('local', 'dev', 'staging', 'prod')]
    [string]$Environment = 'local',
    
    [Parameter(Mandatory=$false)]
    [ValidateSet('build', 'up', 'down', 'restart', 'logs', 'test', 'clean')]
    [string]$Action = 'up'
)

$ErrorActionPreference = "Stop"

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host "  Equifax AI MCP Screening Platform - Deployment" -ForegroundColor White
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host ""

# Configuration
$ProjectName = "equifax-screening"
$ComposeFile = "docker-compose.yml"
$ComposeFilesDev = @("docker-compose.yml", "docker-compose.dev.yml")

function Show-Status {
    Write-Host "Environment: " -NoNewline -ForegroundColor Yellow
    Write-Host $Environment -ForegroundColor Green
    Write-Host "Action: " -NoNewline -ForegroundColor Yellow
    Write-Host $Action -ForegroundColor Green
    Write-Host ""
}

function Build-Images {
    Write-Host "🔨 Building Docker images..." -ForegroundColor Cyan
    
    if ($Environment -eq 'local') {
        docker-compose -f $ComposeFile -p $ProjectName build
    } else {
        docker-compose -f $ComposeFile -f "docker-compose.$Environment.yml" -p "$ProjectName-$Environment" build
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Build completed successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Build failed" -ForegroundColor Red
        exit 1
    }
}

function Start-Services {
    Write-Host "🚀 Starting services..." -ForegroundColor Cyan
    
    # Check if .env file exists
    if (!(Test-Path ".env")) {
        Write-Host "⚠️  .env file not found. Creating from .env.example..." -ForegroundColor Yellow
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Host "⚠️  Please update .env with your API keys before proceeding!" -ForegroundColor Yellow
            $continue = Read-Host "Continue anyway? (y/n)"
            if ($continue -ne 'y') {
                exit 0
            }
        }
    }
    
    if ($Environment -eq 'local') {
        docker-compose -f $ComposeFile -p $ProjectName up -d
    } else {
        docker-compose -f $ComposeFile -f "docker-compose.$Environment.yml" -p "$ProjectName-$Environment" up -d
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Services started successfully" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Service URLs:" -ForegroundColor Cyan
        Write-Host "   API:      http://localhost:8000" -ForegroundColor White
        Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
        Write-Host "   Health:   http://localhost:8000/health" -ForegroundColor White
        
        if ($Environment -eq 'dev') {
            Write-Host "   pgAdmin:  http://localhost:5050" -ForegroundColor White
        }
        
        Write-Host ""
        Write-Host "📝 View logs: docker-compose -p $ProjectName logs -f" -ForegroundColor Gray
    } else {
        Write-Host "❌ Failed to start services" -ForegroundColor Red
        exit 1
    }
}

function Stop-Services {
    Write-Host "🛑 Stopping services..." -ForegroundColor Cyan
    
    if ($Environment -eq 'local') {
        docker-compose -f $ComposeFile -p $ProjectName down
    } else {
        docker-compose -f $ComposeFile -f "docker-compose.$Environment.yml" -p "$ProjectName-$Environment" down
    }
    
    Write-Host "✅ Services stopped" -ForegroundColor Green
}

function Restart-Services {
    Write-Host "🔄 Restarting services..." -ForegroundColor Cyan
    Stop-Services
    Start-Sleep -Seconds 2
    Start-Services
}

function Show-Logs {
    Write-Host "📋 Showing logs (Ctrl+C to exit)..." -ForegroundColor Cyan
    
    if ($Environment -eq 'local') {
        docker-compose -f $ComposeFile -p $ProjectName logs -f
    } else {
        docker-compose -f $ComposeFile -f "docker-compose.$Environment.yml" -p "$ProjectName-$Environment" logs -f
    }
}

function Test-Deployment {
    Write-Host "🧪 Testing deployment..." -ForegroundColor Cyan
    
    # Wait for services to be ready
    Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Test health endpoint
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 10
        Write-Host "✅ Health check: " -NoNewline -ForegroundColor Green
        Write-Host ($response | ConvertTo-Json -Compress)
    } catch {
        Write-Host "❌ Health check failed: $_" -ForegroundColor Red
        exit 1
    }
    
    # Test root endpoint
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get -TimeoutSec 10
        Write-Host "✅ Root endpoint: " -NoNewline -ForegroundColor Green
        Write-Host ($response.version)
    } catch {
        Write-Host "❌ Root endpoint failed: $_" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "✅ All tests passed!" -ForegroundColor Green
    Write-Host "🌐 Visit http://localhost:8000/docs for API documentation" -ForegroundColor Cyan
}

function Clean-Environment {
    Write-Host "🧹 Cleaning environment..." -ForegroundColor Cyan
    
    $confirm = Read-Host "This will remove all containers, volumes, and images. Continue? (y/n)"
    if ($confirm -eq 'y') {
        if ($Environment -eq 'local') {
            docker-compose -f $ComposeFile -p $ProjectName down -v --rmi all
        } else {
            docker-compose -f $ComposeFile -f "docker-compose.$Environment.yml" -p "$ProjectName-$Environment" down -v --rmi all
        }
        Write-Host "✅ Environment cleaned" -ForegroundColor Green
    } else {
        Write-Host "❌ Cancelled" -ForegroundColor Yellow
    }
}

# Main execution
Show-Status

switch ($Action) {
    'build' { Build-Images }
    'up' { Start-Services }
    'down' { Stop-Services }
    'restart' { Restart-Services }
    'logs' { Show-Logs }
    'test' { Test-Deployment }
    'clean' { Clean-Environment }
}

Write-Host ""
Write-Host "✨ Done!" -ForegroundColor Green
