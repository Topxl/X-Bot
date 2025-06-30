#!/bin/bash
set -e

echo "🚀 Twitter Bot - Production Deployment"
echo "======================================"

# Configuration
CONTAINER_NAME="twitter-bot"
IMAGE_NAME="twitter-bot:latest"
BACKUP_DIR="./backups"
LOG_FILE="./logs/deploy.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Pre-deployment checks
pre_deploy_checks() {
    echo -e "${BLUE}Running pre-deployment checks...${NC}"
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running${NC}"
        exit 1
    fi
    
    # Check if required files exist
    required_files=(".env" "config.json" "docker-compose.yml")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            echo -e "${RED}❌ Required file missing: $file${NC}"
            exit 1
        fi
    done
    
    # Check environment variables
    if ! grep -q "X_API_KEY" .env; then
        echo -e "${RED}❌ X_API_KEY not configured in .env${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Pre-deployment checks passed${NC}"
    log "Pre-deployment checks passed"
}

# Backup current deployment
backup_current() {
    echo -e "${BLUE}Creating backup...${NC}"
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    mkdir -p "$BACKUP_PATH"
    
    # Backup configuration
    cp config.json "$BACKUP_PATH/"
    cp .env "$BACKUP_PATH/"
    
    # Backup data if exists
    if [[ -d "data" ]]; then
        cp -r data "$BACKUP_PATH/"
    fi
    
    # Export current container if running
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        docker export "$CONTAINER_NAME" > "$BACKUP_PATH/container.tar"
    fi
    
    echo -e "${GREEN}✅ Backup created: $BACKUP_PATH${NC}"
    log "Backup created: $BACKUP_PATH"
}

# Build new image
build_image() {
    echo -e "${BLUE}Building new image...${NC}"
    
    # Build with timestamp tag
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    docker build -t "$IMAGE_NAME" -t "twitter-bot:$TIMESTAMP" .
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Image built successfully${NC}"
        log "Image built successfully: twitter-bot:$TIMESTAMP"
    else
        echo -e "${RED}❌ Image build failed${NC}"
        log "ERROR: Image build failed"
        exit 1
    fi
}

# Deploy new version
deploy() {
    echo -e "${BLUE}Deploying new version...${NC}"
    
    # Stop current container gracefully
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        echo "Stopping current container..."
        docker-compose down --timeout 30
        sleep 5
    fi
    
    # Start new version
    docker-compose up -d
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ New version deployed${NC}"
        log "New version deployed successfully"
    else
        echo -e "${RED}❌ Deployment failed${NC}"
        log "ERROR: Deployment failed"
        rollback
        exit 1
    fi
}

# Health check
health_check() {
    echo -e "${BLUE}Running health checks...${NC}"
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker ps | grep -q "$CONTAINER_NAME"; then
            # Check if container is healthy
            health_status=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")
            
            if [[ "$health_status" == "healthy" ]]; then
                echo -e "${GREEN}✅ Health check passed${NC}"
                log "Health check passed"
                return 0
            elif [[ "$health_status" == "unhealthy" ]]; then
                echo -e "${RED}❌ Health check failed${NC}"
                log "ERROR: Health check failed"
                return 1
            fi
        fi
        
        echo "Waiting for health check... ($attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    echo -e "${RED}❌ Health check timeout${NC}"
    log "ERROR: Health check timeout"
    return 1
}

# Rollback function
rollback() {
    echo -e "${YELLOW}🔄 Rolling back to previous version...${NC}"
    
    # Stop current container
    docker-compose down --timeout 30
    
    # Find latest backup
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR" | head -n1)
    
    if [[ -n "$LATEST_BACKUP" ]]; then
        echo "Restoring from backup: $LATEST_BACKUP"
        
        # Restore configuration
        cp "$BACKUP_DIR/$LATEST_BACKUP/config.json" ./
        cp "$BACKUP_DIR/$LATEST_BACKUP/.env" ./
        
        # Restore data if exists
        if [[ -d "$BACKUP_DIR/$LATEST_BACKUP/data" ]]; then
            rm -rf data
            cp -r "$BACKUP_DIR/$LATEST_BACKUP/data" ./
        fi
        
        # Start with previous configuration
        docker-compose up -d
        
        echo -e "${GREEN}✅ Rollback completed${NC}"
        log "Rollback completed using backup: $LATEST_BACKUP"
    else
        echo -e "${RED}❌ No backup found for rollback${NC}"
        log "ERROR: No backup found for rollback"
    fi
}

# Clean old backups (keep last 5)
cleanup_backups() {
    echo -e "${BLUE}Cleaning old backups...${NC}"
    
    if [[ -d "$BACKUP_DIR" ]]; then
        # Keep only last 5 backups
        ls -t "$BACKUP_DIR" | tail -n +6 | xargs -I {} rm -rf "$BACKUP_DIR/{}"
        echo -e "${GREEN}✅ Old backups cleaned${NC}"
        log "Old backups cleaned"
    fi
}

# Show deployment status
show_status() {
    echo -e "\n${BLUE}Deployment Status:${NC}"
    echo "==================="
    
    # Container status
    if docker ps | grep -q "$CONTAINER_NAME"; then
        echo -e "Container: ${GREEN}Running${NC}"
        
        # Health status
        health_status=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")
        case $health_status in
            "healthy")
                echo -e "Health: ${GREEN}Healthy${NC}"
                ;;
            "unhealthy")
                echo -e "Health: ${RED}Unhealthy${NC}"
                ;;
            *)
                echo -e "Health: ${YELLOW}Unknown${NC}"
                ;;
        esac
        
        # Show logs
        echo -e "\nRecent logs:"
        docker logs --tail=10 "$CONTAINER_NAME"
    else
        echo -e "Container: ${RED}Not Running${NC}"
    fi
}

# Main deployment process
main() {
    echo -e "${BLUE}Starting deployment process...${NC}\n"
    
    # Create log directory
    mkdir -p logs
    
    log "Deployment started"
    
    pre_deploy_checks
    backup_current
    build_image
    deploy
    
    if health_check; then
        cleanup_backups
        echo -e "\n${GREEN}🎉 Deployment completed successfully!${NC}"
        log "Deployment completed successfully"
    else
        echo -e "\n${RED}❌ Deployment failed health checks${NC}"
        echo -e "${YELLOW}Rolling back...${NC}"
        rollback
        log "Deployment failed, rollback initiated"
        exit 1
    fi
    
    show_status
}

# Handle script arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    rollback)
        rollback
        ;;
    status)
        show_status
        ;;
    logs)
        docker logs -f "$CONTAINER_NAME"
        ;;
    stop)
        echo -e "${YELLOW}Stopping Twitter Bot...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ Stopped${NC}"
        ;;
    restart)
        echo -e "${YELLOW}Restarting Twitter Bot...${NC}"
        docker-compose restart
        echo -e "${GREEN}✅ Restarted${NC}"
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|status|logs|stop|restart}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy new version (default)"
        echo "  rollback - Rollback to previous version"
        echo "  status   - Show deployment status"
        echo "  logs     - Show live logs"
        echo "  stop     - Stop the bot"
        echo "  restart  - Restart the bot"
        exit 1
        ;;
esac 