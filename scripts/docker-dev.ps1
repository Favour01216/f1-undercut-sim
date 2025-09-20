# scripts/docker-dev.ps1
# Development Docker management script for Windows

param(
    [Parameter(Position=0)]
    [ValidateSet("build", "up", "down", "restart", "logs", "logs-be", "logs-fe", "shell-be", "shell-fe", "test", "clean", "prod-up", "prod-down", "status", "help")]
    [string]$Command = "help"
)

$COMPOSE_FILE = "docker-compose.yml"
$PROD_COMPOSE_FILE = "docker-compose.prod.yml"

function Show-Help {
    Write-Host @"
F1 Undercut Simulator - Docker Development Script

Usage: .\scripts\docker-dev.ps1 [COMMAND]

Commands:
    build       Build all Docker images
    up          Start development environment
    down        Stop and remove containers
    restart     Restart all services
    logs        Show logs for all services
    logs-be     Show backend logs only
    logs-fe     Show frontend logs only
    shell-be    Open shell in backend container
    shell-fe    Open shell in frontend container
    test        Run smoke tests on containers
    clean       Clean up Docker resources
    prod-up     Start production environment
    prod-down   Stop production environment
    status      Show container status
    help        Show this help message

Examples:
    .\scripts\docker-dev.ps1 build          # Build all images
    .\scripts\docker-dev.ps1 up             # Start development stack
    .\scripts\docker-dev.ps1 logs-be        # View backend logs
    .\scripts\docker-dev.ps1 test           # Run container tests
    .\scripts\docker-dev.ps1 prod-up        # Start production stack

"@ -ForegroundColor Green
}

function Build-Images {
    Write-Host "Building Docker images..." -ForegroundColor Blue
    docker-compose -f $COMPOSE_FILE build --parallel
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Build complete!" -ForegroundColor Green
    } else {
        Write-Host "Build failed!" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

function Start-Dev {
    Write-Host "Starting development environment..." -ForegroundColor Blue
    docker-compose -f $COMPOSE_FILE up -d
    Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
    docker-compose -f $COMPOSE_FILE ps
    Write-Host ""
    Write-Host "Services available at:" -ForegroundColor Green
    Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  Backend Docs: http://localhost:8000/docs" -ForegroundColor Cyan
}

function Stop-Dev {
    Write-Host "Stopping development environment..." -ForegroundColor Blue
    docker-compose -f $COMPOSE_FILE down
    Write-Host "Environment stopped!" -ForegroundColor Green
}

function Restart-Services {
    Write-Host "Restarting services..." -ForegroundColor Blue
    docker-compose -f $COMPOSE_FILE restart
    Write-Host "Services restarted!" -ForegroundColor Green
}

function Show-Logs {
    docker-compose -f $COMPOSE_FILE logs -f
}

function Show-BackendLogs {
    docker-compose -f $COMPOSE_FILE logs -f backend
}

function Show-FrontendLogs {
    docker-compose -f $COMPOSE_FILE logs -f frontend
}

function Backend-Shell {
    Write-Host "Opening backend shell..." -ForegroundColor Blue
    docker-compose -f $COMPOSE_FILE exec backend /bin/bash
}

function Frontend-Shell {
    Write-Host "Opening frontend shell..." -ForegroundColor Blue
    docker-compose -f $COMPOSE_FILE exec frontend /bin/sh
}

function Run-Tests {
    Write-Host "Running container smoke tests..." -ForegroundColor Blue
    
    # Test backend health
    Write-Host "Testing backend health..."
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "Backend health check passed!" -ForegroundColor Green
        }
    } catch {
        Write-Host "Backend health check failed" -ForegroundColor Red
        docker-compose -f $COMPOSE_FILE logs backend
        exit 1
    }
    
    # Test frontend health
    Write-Host "Testing frontend health..."
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "Frontend health check passed!" -ForegroundColor Green
        }
    } catch {
        Write-Host "Frontend health check failed" -ForegroundColor Red
        docker-compose -f $COMPOSE_FILE logs frontend
        exit 1
    }
    
    Write-Host "All smoke tests passed!" -ForegroundColor Green
}

function Clean-Docker {
    Write-Host "Cleaning up Docker resources..." -ForegroundColor Blue
    docker-compose -f $COMPOSE_FILE down -v --rmi local
    docker system prune -f
    Write-Host "Cleanup complete!" -ForegroundColor Green
}

function Start-Prod {
    Write-Host "Starting production environment..." -ForegroundColor Blue
    docker-compose -f $PROD_COMPOSE_FILE up -d
    Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
    docker-compose -f $PROD_COMPOSE_FILE ps
    Write-Host ""
    Write-Host "Production services available at:" -ForegroundColor Green
    Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Cyan
}

function Stop-Prod {
    Write-Host "Stopping production environment..." -ForegroundColor Blue
    docker-compose -f $PROD_COMPOSE_FILE down
    Write-Host "Production environment stopped!" -ForegroundColor Green
}

function Show-Status {
    Write-Host "Container Status:" -ForegroundColor Blue
    docker-compose -f $COMPOSE_FILE ps
    Write-Host ""
    Write-Host "Health Status:" -ForegroundColor Blue
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

switch ($Command) {
    "build" { Build-Images }
    "up" { Start-Dev }
    "down" { Stop-Dev }
    "restart" { Restart-Services }
    "logs" { Show-Logs }
    "logs-be" { Show-BackendLogs }
    "logs-fe" { Show-FrontendLogs }
    "shell-be" { Backend-Shell }
    "shell-fe" { Frontend-Shell }
    "test" { Run-Tests }
    "clean" { Clean-Docker }
    "prod-up" { Start-Prod }
    "prod-down" { Stop-Prod }
    "status" { Show-Status }
    "help" { Show-Help }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
        exit 1
    }
}