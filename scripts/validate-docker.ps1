# scripts/validate-docker.ps1
# Validate Docker configuration without building

Write-Host "Validating Docker configuration..." -ForegroundColor Blue

# Check if Docker is available
try {
    $dockerVersion = docker --version
    Write-Host "Docker available: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "Docker is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
try {
    $composeVersion = docker-compose --version
    Write-Host "Docker Compose available: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "Docker Compose is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Validate docker-compose files
Write-Host "Validating docker-compose.yml..." -ForegroundColor Blue
try {
    docker-compose -f docker-compose.yml config | Out-Null
    Write-Host "docker-compose.yml is valid" -ForegroundColor Green
} catch {
    Write-Host "docker-compose.yml has errors" -ForegroundColor Red
    docker-compose -f docker-compose.yml config
    exit 1
}

Write-Host "Validating docker-compose.prod.yml..." -ForegroundColor Blue
try {
    docker-compose -f docker-compose.prod.yml config | Out-Null
    Write-Host "docker-compose.prod.yml is valid" -ForegroundColor Green
} catch {
    Write-Host "docker-compose.prod.yml has errors" -ForegroundColor Red
    docker-compose -f docker-compose.prod.yml config
    exit 1
}

# Check for .dockerignore files
Write-Host "Checking .dockerignore files..." -ForegroundColor Blue
if (Test-Path "backend\.dockerignore") {
    Write-Host "Backend .dockerignore exists" -ForegroundColor Green
} else {
    Write-Host "Backend .dockerignore missing" -ForegroundColor Yellow
}

if (Test-Path "frontend\.dockerignore") {
    Write-Host "Frontend .dockerignore exists" -ForegroundColor Green
} else {
    Write-Host "Frontend .dockerignore missing" -ForegroundColor Yellow
}

# Check critical files exist
Write-Host "Checking critical files..." -ForegroundColor Blue
$criticalFiles = @(
    "backend\Dockerfile",
    "frontend\Dockerfile",
    "docker-compose.yml",
    "docker-compose.prod.yml",
    "backend\pyproject.toml",
    "backend\requirements.txt",
    "frontend\package.json",
    "frontend\next.config.js"
)

foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Write-Host "$file exists" -ForegroundColor Green
    } else {
        Write-Host "$file missing" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "All Docker configuration validations passed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Blue
Write-Host "  1. Build images: .\scripts\docker-dev.ps1 build"
Write-Host "  2. Start development: .\scripts\docker-dev.ps1 up"
Write-Host "  3. Run tests: .\scripts\docker-dev.ps1 test"
Write-Host ""
Write-Host "Ready for containerized deployment!" -ForegroundColor Green