#!/bin/bash
# Deployment Script for Equifax AI MCP Screening Platform (Linux/Mac)
# Usage: ./deploy.sh [environment] [action]

set -e

# Configuration
ENVIRONMENT=${1:-local}
ACTION=${2:-up}
PROJECT_NAME="equifax-screening"
COMPOSE_FILE="docker-compose.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}============================================================================${NC}"
echo -e "${CYAN}  Equifax AI MCP Screening Platform - Deployment${NC}"
echo -e "${CYAN}============================================================================${NC}"
echo ""

# Show status
echo -e "${YELLOW}Environment:${NC} ${GREEN}$ENVIRONMENT${NC}"
echo -e "${YELLOW}Action:${NC} ${GREEN}$ACTION${NC}"
echo ""

build_images() {
    echo -e "${CYAN}🔨 Building Docker images...${NC}"
    
    if [ "$ENVIRONMENT" = "local" ]; then
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME build
    else
        docker-compose -f $COMPOSE_FILE -f "docker-compose.$ENVIRONMENT.yml" -p "$PROJECT_NAME-$ENVIRONMENT" build
    fi
    
    echo -e "${GREEN}✅ Build completed successfully${NC}"
}

start_services() {
    echo -e "${CYAN}🚀 Starting services...${NC}"
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
        if [ -f .env.example ]; then
            cp .env.example .env
            echo -e "${YELLOW}⚠️  Please update .env with your API keys!${NC}"
            read -p "Continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 0
            fi
        fi
    fi
    
    if [ "$ENVIRONMENT" = "local" ]; then
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d
    else
        docker-compose -f $COMPOSE_FILE -f "docker-compose.$ENVIRONMENT.yml" -p "$PROJECT_NAME-$ENVIRONMENT" up -d
    fi
    
    echo -e "${GREEN}✅ Services started successfully${NC}"
    echo ""
    echo -e "${CYAN}📊 Service URLs:${NC}"
    echo -e "   API:      http://localhost:8000"
    echo -e "   API Docs: http://localhost:8000/docs"
    echo -e "   Health:   http://localhost:8000/health"
    
    if [ "$ENVIRONMENT" = "dev" ]; then
        echo -e "   pgAdmin:  http://localhost:5050"
    fi
    
    echo ""
    echo -e "${NC}📝 View logs: docker-compose -p $PROJECT_NAME logs -f${NC}"
}

stop_services() {
    echo -e "${CYAN}🛑 Stopping services...${NC}"
    
    if [ "$ENVIRONMENT" = "local" ]; then
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down
    else
        docker-compose -f $COMPOSE_FILE -f "docker-compose.$ENVIRONMENT.yml" -p "$PROJECT_NAME-$ENVIRONMENT" down
    fi
    
    echo -e "${GREEN}✅ Services stopped${NC}"
}

restart_services() {
    echo -e "${CYAN}🔄 Restarting services...${NC}"
    stop_services
    sleep 2
    start_services
}

tail_logs() {
    echo -e "${CYAN}📋 Showing logs (Ctrl+C to exit)...${NC}"
    
    if [ "$ENVIRONMENT" = "local" ]; then
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f
    else
        docker-compose -f $COMPOSE_FILE -f "docker-compose.$ENVIRONMENT.yml" -p "$PROJECT_NAME-$ENVIRONMENT" logs -f
    fi
}

test_deployment() {
    echo -e "${CYAN}🧪 Testing deployment...${NC}"
    
    # Wait for services
    echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
    sleep 5
    
    # Test health endpoint
    if curl -f -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${RED}❌ Health check failed${NC}"
        exit 1
    fi
    
    # Test root endpoint
    if curl -f -s http://localhost:8000/ > /dev/null; then
        echo -e "${GREEN}✅ Root endpoint passed${NC}"
    else
        echo -e "${RED}❌ Root endpoint failed${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo -e "${CYAN}🌐 Visit http://localhost:8000/docs for API documentation${NC}"
}

clean_env() {
    echo -e "${CYAN}🧹 Cleaning environment...${NC}"
    
    read -p "This will remove all containers, volumes, and images. Continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ "$ENVIRONMENT" = "local" ]; then
            docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down -v --rmi all
        else
            docker-compose -f $COMPOSE_FILE -f "docker-compose.$ENVIRONMENT.yml" -p "$PROJECT_NAME-$ENVIRONMENT" down -v --rmi all
        fi
        echo -e "${GREEN}✅ Environment cleaned${NC}"
    else
        echo -e "${YELLOW}❌ Cancelled${NC}"
    fi
}

# Main execution
case $ACTION in
    build)
        build_images
        ;;
    up|start)
        start_services
        ;;
    down|stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        tail_logs
        ;;
    test)
        test_deployment
        ;;
    clean)
        clean_env
        ;;
    *)
        echo -e "${RED}Unknown action: $ACTION${NC}"
        echo "Usage: ./deploy.sh [environment] [action]"
        echo "Environments: local, dev, staging, prod"
        echo "Actions: build, up, down, restart, logs, test, clean"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✨ Done!${NC}"
