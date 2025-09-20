#!/bin/bash
# scripts/validate-docker.sh
# Validate Docker configuration without building

echo "🔍 Validating Docker configuration..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed or not in PATH"
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Validate Dockerfile syntax
echo "🔍 Validating backend Dockerfile..."
if docker build --dry-run backend/ 2>/dev/null; then
    echo "✅ Backend Dockerfile syntax is valid"
else
    echo "❌ Backend Dockerfile has syntax errors"
    exit 1
fi

echo "🔍 Validating frontend Dockerfile..."
if docker build --dry-run frontend/ 2>/dev/null; then
    echo "✅ Frontend Dockerfile syntax is valid"
else
    echo "❌ Frontend Dockerfile has syntax errors"
    exit 1
fi

# Validate docker-compose files
echo "🔍 Validating docker-compose.yml..."
if docker-compose -f docker-compose.yml config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml is valid"
else
    echo "❌ docker-compose.yml has errors"
    docker-compose -f docker-compose.yml config
    exit 1
fi

echo "🔍 Validating docker-compose.prod.yml..."
if docker-compose -f docker-compose.prod.yml config > /dev/null 2>&1; then
    echo "✅ docker-compose.prod.yml is valid"
else
    echo "❌ docker-compose.prod.yml has errors"
    docker-compose -f docker-compose.prod.yml config
    exit 1
fi

# Check for .dockerignore files
echo "🔍 Checking .dockerignore files..."
if [ -f "backend/.dockerignore" ]; then
    echo "✅ Backend .dockerignore exists"
else
    echo "⚠️ Backend .dockerignore missing"
fi

if [ -f "frontend/.dockerignore" ]; then
    echo "✅ Frontend .dockerignore exists"
else
    echo "⚠️ Frontend .dockerignore missing"
fi

# Check critical files exist
echo "🔍 Checking critical files..."
critical_files=(
    "backend/Dockerfile"
    "frontend/Dockerfile"
    "docker-compose.yml"
    "docker-compose.prod.yml"
    "backend/pyproject.toml"
    "backend/requirements.txt"
    "frontend/package.json"
    "frontend/next.config.js"
)

for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

echo ""
echo "🎉 All Docker configuration validations passed!"
echo ""
echo "📋 Next steps:"
echo "  1. Build images: ./scripts/docker-dev.sh build"
echo "  2. Start development: ./scripts/docker-dev.sh up"
echo "  3. Run tests: ./scripts/docker-dev.sh test"
echo ""
echo "🚀 Ready for containerized deployment!"