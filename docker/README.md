# Docker Setup for F1 Undercut Simulator

This directory contains Docker configurations for running the F1 Undercut Simulator in containerized environments.

## 🐳 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB+ available RAM
- 2GB+ available disk space

### Development Environment

```bash
# Build and start development stack
./scripts/docker-dev.sh build
./scripts/docker-dev.sh up

# Or on Windows
.\scripts\docker-dev.ps1 build
.\scripts\docker-dev.ps1 up
```

Services will be available at:

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Production Environment

```bash
# Start production stack
./scripts/docker-dev.sh prod-up

# Or manually
docker-compose -f docker-compose.prod.yml up -d
```

## 📁 Docker Files

### Backend Dockerfile (`backend/Dockerfile`)

- **Base Image**: `python:3.11-slim`
- **Package Manager**: `uv` for fast dependency resolution
- **Port**: 8000
- **Health Check**: HTTP GET to `/`
- **Optimizations**: Multi-stage build, minimal dependencies

### Frontend Dockerfile (`frontend/Dockerfile`)

- **Base Image**: `node:20-alpine`
- **Package Manager**: `pnpm`
- **Build**: Next.js standalone output
- **Port**: 3000
- **Health Check**: HTTP GET to `/api/health`
- **Optimizations**: Multi-stage build, non-root user

### Docker Compose Files

#### `docker-compose.yml` (Development)

- **Environment**: `ENV=development`
- **Features**: Hot reload, volume mounts, debug logging
- **Networks**: Shared `f1-network`
- **Dependencies**: Frontend waits for backend health

#### `docker-compose.prod.yml` (Production)

- **Environment**: `ENV=production`
- **Features**: Resource limits, restart policies, persistent volumes
- **Security**: Non-root containers, health checks
- **Monitoring**: Sentry integration enabled

## 🔧 Configuration

### Environment Variables

#### Backend

```bash
ENV=production                    # Environment mode
OFFLINE=0                        # Enable/disable external APIs
CORS_ORIGINS=https://yourapp.com # Allowed CORS origins
SENTRY_DSN=your_sentry_dsn      # Error monitoring
RNG_SEED=42                     # Reproducible randomness
WORKERS=4                       # Uvicorn worker processes
```

#### Frontend

```bash
NODE_ENV=production                           # Node environment
NEXT_PUBLIC_API_URL=http://backend:8000      # Backend URL
NEXT_PUBLIC_ENABLE_SENTRY=true              # Enable error tracking
NEXT_PUBLIC_SENTRY_DSN=your_frontend_dsn    # Frontend Sentry DSN
```

### Health Checks

Both services include comprehensive health checks:

- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3 attempts
- **Start Period**: 40 seconds

### Resource Limits (Production)

#### Backend

- **CPU**: 2.0 cores max, 0.5 cores reserved
- **Memory**: 2GB max, 512MB reserved

#### Frontend

- **CPU**: 1.0 core max, 0.25 cores reserved
- **Memory**: 1GB max, 256MB reserved

## 🚀 Common Commands

### Development Workflow

```bash
# Build images
./scripts/docker-dev.sh build

# Start development environment
./scripts/docker-dev.sh up

# View logs
./scripts/docker-dev.sh logs
./scripts/docker-dev.sh logs-be  # Backend only
./scripts/docker-dev.sh logs-fe  # Frontend only

# Access containers
./scripts/docker-dev.sh shell-be  # Backend shell
./scripts/docker-dev.sh shell-fe  # Frontend shell

# Run tests
./scripts/docker-dev.sh test

# Stop environment
./scripts/docker-dev.sh down
```

### Manual Docker Commands

```bash
# Build specific service
docker-compose build backend
docker-compose build frontend

# Start specific service
docker-compose up -d backend
docker-compose up -d frontend

# Scale services
docker-compose up -d --scale backend=2

# View container stats
docker stats

# Inspect containers
docker-compose ps
docker-compose logs backend
```

## 🧪 Testing

### Smoke Tests

The CI pipeline includes comprehensive smoke tests:

1. **Container Build**: Verify images build successfully
2. **Service Health**: Test health endpoints
3. **Stack Integration**: Verify service communication
4. **Security Scan**: Trivy vulnerability scanning

### Manual Testing

```bash
# Test backend API
curl -f http://localhost:8000/

# Test frontend health
curl -f http://localhost:3000/api/health

# Run full simulation test
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "circuit": "BAHRAIN",
    "year": 2024,
    "lap_now": 20,
    "driver_a": "VER",
    "driver_b": "LEC",
    "compound": "MEDIUM",
    "gap_seconds": 15.0,
    "samples": 1000
  }'
```

## 🔒 Security

### Container Security

- **Non-root users** for both services
- **Minimal base images** (slim/alpine)
- **Security scanning** with Trivy in CI
- **Resource limits** to prevent resource exhaustion
- **Read-only file systems** where possible

### Network Security

- **Isolated networks** for container communication
- **CORS configuration** for cross-origin requests
- **Health check endpoints** for monitoring
- **No exposed secrets** in environment variables

## 📊 Monitoring

### Health Monitoring

- **Container health checks** every 30 seconds
- **Service dependency** management
- **Graceful startup** with start periods
- **Automatic restarts** on failure

### Logging

- **Structured logging** with JSON format
- **Log aggregation** via Docker logging drivers
- **Error tracking** with Sentry integration
- **Performance metrics** collection

## 🚀 Deployment

### Container Registry

Images are automatically built and pushed to GitHub Container Registry:

- `ghcr.io/favour01216/f1-undercut-sim-backend`
- `ghcr.io/favour01216/f1-undercut-sim-frontend`

### Production Deployment

1. **Pull images** from registry
2. **Set environment variables** in `.env` file
3. **Start production stack** with docker-compose
4. **Verify health checks** are passing
5. **Monitor logs** for any issues

### Scaling

```bash
# Scale backend for higher load
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Use load balancer (nginx/traefik) for multiple frontends
docker-compose -f docker-compose.prod.yml up -d --scale frontend=2
```

## 🐛 Troubleshooting

### Common Issues

**Build failures:**

```bash
# Clean Docker cache
docker system prune -a
docker-compose build --no-cache
```

**Container won't start:**

```bash
# Check logs
docker-compose logs [service]

# Check resource usage
docker stats

# Verify health checks
docker inspect [container]
```

**Network issues:**

```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

**Permission issues:**

```bash
# Fix file permissions
chmod +x scripts/docker-dev.sh
```

### Performance Tuning

- **Increase memory** for better caching
- **Use SSD storage** for better I/O
- **Enable BuildKit** for faster builds
- **Use multi-stage builds** for smaller images

## 📈 Best Practices

1. **Always use health checks** for service dependencies
2. **Set resource limits** to prevent resource exhaustion
3. **Use .dockerignore** to reduce build context
4. **Pin base image versions** for reproducible builds
5. **Run containers as non-root** for security
6. **Use multi-stage builds** for smaller production images
7. **Enable BuildKit** for faster, more efficient builds
8. **Monitor container logs** for application health
