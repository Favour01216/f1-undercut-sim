#!/bin/bash
# scripts/docker-dev.sh
# Development Docker management script

set -e

COMPOSE_FILE="docker-compose.yml"
PROD_COMPOSE_FILE="docker-compose.prod.yml"

show_help() {
    cat << EOF
F1 Undercut Simulator - Docker Development Script

Usage: $0 [COMMAND]

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
    $0 build          # Build all images
    $0 up             # Start development stack
    $0 logs-be        # View backend logs
    $0 test           # Run container tests
    $0 prod-up        # Start production stack

EOF
}

build_images() {
    echo "🔨 Building Docker images..."
    docker-compose -f $COMPOSE_FILE build --parallel
    echo "✅ Build complete!"
}

start_dev() {
    echo "🚀 Starting development environment..."
    docker-compose -f $COMPOSE_FILE up -d
    echo "⏳ Waiting for services to be healthy..."
    docker-compose -f $COMPOSE_FILE ps
    echo ""
    echo "🌐 Services available at:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:8000"
    echo "  Backend Docs: http://localhost:8000/docs"
}

stop_dev() {
    echo "🛑 Stopping development environment..."
    docker-compose -f $COMPOSE_FILE down
    echo "✅ Environment stopped!"
}

restart_services() {
    echo "🔄 Restarting services..."
    docker-compose -f $COMPOSE_FILE restart
    echo "✅ Services restarted!"
}

show_logs() {
    docker-compose -f $COMPOSE_FILE logs -f
}

show_backend_logs() {
    docker-compose -f $COMPOSE_FILE logs -f backend
}

show_frontend_logs() {
    docker-compose -f $COMPOSE_FILE logs -f frontend
}

backend_shell() {
    echo "🐚 Opening backend shell..."
    docker-compose -f $COMPOSE_FILE exec backend /bin/bash
}

frontend_shell() {
    echo "🐚 Opening frontend shell..."
    docker-compose -f $COMPOSE_FILE exec frontend /bin/sh
}

run_tests() {
    echo "🧪 Running container smoke tests..."
    
    # Test backend health
    echo "Testing backend health..."
    curl -f http://localhost:8000/ || {
        echo "❌ Backend health check failed"
        docker-compose -f $COMPOSE_FILE logs backend
        exit 1
    }
    
    # Test frontend health
    echo "Testing frontend health..."
    curl -f http://localhost:3000/api/health || {
        echo "❌ Frontend health check failed"
        docker-compose -f $COMPOSE_FILE logs frontend
        exit 1
    }
    
    echo "✅ All smoke tests passed!"
}

clean_docker() {
    echo "🧹 Cleaning up Docker resources..."
    docker-compose -f $COMPOSE_FILE down -v --rmi local
    docker system prune -f
    echo "✅ Cleanup complete!"
}

start_prod() {
    echo "🚀 Starting production environment..."
    docker-compose -f $PROD_COMPOSE_FILE up -d
    echo "⏳ Waiting for services to be healthy..."
    docker-compose -f $PROD_COMPOSE_FILE ps
    echo ""
    echo "🌐 Production services available at:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:8000"
}

stop_prod() {
    echo "🛑 Stopping production environment..."
    docker-compose -f $PROD_COMPOSE_FILE down
    echo "✅ Production environment stopped!"
}

show_status() {
    echo "📊 Container Status:"
    docker-compose -f $COMPOSE_FILE ps
    echo ""
    echo "🏥 Health Status:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

case "$1" in
    build)
        build_images
        ;;
    up)
        start_dev
        ;;
    down)
        stop_dev
        ;;
    restart)
        restart_services
        ;;
    logs)
        show_logs
        ;;
    logs-be)
        show_backend_logs
        ;;
    logs-fe)
        show_frontend_logs
        ;;
    shell-be)
        backend_shell
        ;;
    shell-fe)
        frontend_shell
        ;;
    test)
        run_tests
        ;;
    clean)
        clean_docker
        ;;
    prod-up)
        start_prod
        ;;
    prod-down)
        stop_prod
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac