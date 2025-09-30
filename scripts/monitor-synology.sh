#!/bin/bash

# D&D Story Telling - Synology Monitoring and Maintenance Script
# Automated monitoring, backup, and maintenance for Synology deployment

set -e

# Configuration
APP_NAME="dndstorytelling"
BASE_DIR="/volume1/docker/${APP_NAME}"
BACKUP_DIR="/volume1/backups/${APP_NAME}"
LOG_DIR="${BASE_DIR}/logs"
COMPOSE_FILE="docker-compose.synology.yml"
RETENTION_DAYS=30
ALERT_EMAIL=""  # Set this to receive alerts

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"; }

# Create monitoring log
MONITOR_LOG="${LOG_DIR}/monitor.log"
mkdir -p "$LOG_DIR"

log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$MONITOR_LOG"
}

# Health monitoring functions
check_docker_health() {
    log_info "Checking Docker service health..."

    if ! systemctl is-active --quiet docker; then
        log_error "Docker service is not running"
        log_to_file "ERROR: Docker service down"
        return 1
    fi

    cd "$BASE_DIR"

    # Check containers
    local containers=$(docker-compose -f "$COMPOSE_FILE" ps -q)
    if [ -z "$containers" ]; then
        log_error "No containers are running"
        log_to_file "ERROR: No containers running"
        return 1
    fi

    # Check individual container health
    local failed_containers=()
    for container in $containers; do
        local container_name=$(docker inspect --format='{{.Name}}' "$container" | sed 's/^.//')
        local container_status=$(docker inspect --format='{{.State.Status}}' "$container")

        if [ "$container_status" != "running" ]; then
            failed_containers+=("$container_name")
            log_error "Container $container_name is $container_status"
            log_to_file "ERROR: Container $container_name status: $container_status"
        else
            log_success "Container $container_name is healthy"
        fi
    done

    if [ ${#failed_containers[@]} -gt 0 ]; then
        log_error "Failed containers: ${failed_containers[*]}"
        return 1
    fi

    log_success "All containers are healthy"
    return 0
}

check_application_health() {
    log_info "Checking application endpoints..."

    # Health endpoint
    if curl -f -s "http://localhost:8000/health" > /dev/null; then
        log_success "Health endpoint is responding"
        log_to_file "INFO: Health endpoint OK"
    else
        log_error "Health endpoint is not responding"
        log_to_file "ERROR: Health endpoint failed"
        return 1
    fi

    # Main application
    if curl -f -s "http://localhost:8000/" > /dev/null; then
        log_success "Main application is responding"
        log_to_file "INFO: Main application OK"
    else
        log_warning "Main application may have issues"
        log_to_file "WARNING: Main application response issue"
    fi

    return 0
}

check_database_health() {
    log_info "Checking database health..."

    cd "$BASE_DIR"

    # Check database connectivity
    if docker-compose -f "$COMPOSE_FILE" exec -T db pg_isready -U user -d dndstory > /dev/null 2>&1; then
        log_success "Database is accepting connections"
        log_to_file "INFO: Database connectivity OK"
    else
        log_error "Database is not accepting connections"
        log_to_file "ERROR: Database connectivity failed"
        return 1
    fi

    # Check database size
    local db_size=$(docker-compose -f "$COMPOSE_FILE" exec -T db psql -U user -d dndstory -t -c "SELECT pg_size_pretty(pg_database_size('dndstory'));" | xargs)
    log_info "Database size: $db_size"
    log_to_file "INFO: Database size: $db_size"

    return 0
}

check_resource_usage() {
    log_info "Checking resource usage..."

    # Memory usage
    local mem_info=$(free -m | awk 'NR==2{printf "Used: %sMB (%.1f%%), Available: %sMB", $3, $3*100/$2, $7}')
    log_info "Memory: $mem_info"
    log_to_file "INFO: Memory usage: $mem_info"

    # Check if memory usage is high
    local mem_percent=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$mem_percent" -gt 90 ]; then
        log_warning "High memory usage: ${mem_percent}%"
        log_to_file "WARNING: High memory usage: ${mem_percent}%"
    fi

    # Disk usage
    local disk_info=$(df -h /volume1 | awk 'NR==2{printf "Used: %s (%s), Available: %s", $3, $5, $4}')
    log_info "Disk: $disk_info"
    log_to_file "INFO: Disk usage: $disk_info"

    # Check if disk usage is high
    local disk_percent=$(df /volume1 | awk 'NR==2{print $5}' | sed 's/%//')
    if [ "$disk_percent" -gt 85 ]; then
        log_warning "High disk usage: ${disk_percent}%"
        log_to_file "WARNING: High disk usage: ${disk_percent}%"
    fi

    # Container resource usage
    cd "$BASE_DIR"
    log_info "Container resource usage:"
    docker-compose -f "$COMPOSE_FILE" exec web sh -c "ps aux | head -5" 2>/dev/null || true

    return 0
}

backup_data() {
    log_info "Creating backup..."

    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_path="${BACKUP_DIR}/${backup_timestamp}"

    mkdir -p "$backup_path"

    cd "$BASE_DIR"

    # Backup database
    log_info "Backing up database..."
    docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump -U user -d dndstory > "${backup_path}/database.sql"

    if [ $? -eq 0 ]; then
        log_success "Database backup completed"
        log_to_file "INFO: Database backup completed: ${backup_path}/database.sql"
    else
        log_error "Database backup failed"
        log_to_file "ERROR: Database backup failed"
        return 1
    fi

    # Backup uploads and configuration
    log_info "Backing up application data..."
    cp -r uploads "${backup_path}/" 2>/dev/null || mkdir -p "${backup_path}/uploads"
    cp .env "${backup_path}/" 2>/dev/null || true
    cp docker-compose.synology.yml "${backup_path}/" 2>/dev/null || true

    # Compress backup
    cd "$BACKUP_DIR"
    tar -czf "${backup_timestamp}.tar.gz" "$backup_timestamp"
    rm -rf "$backup_timestamp"

    log_success "Backup completed: ${BACKUP_DIR}/${backup_timestamp}.tar.gz"
    log_to_file "INFO: Full backup completed: ${backup_timestamp}.tar.gz"

    return 0
}

cleanup_old_backups() {
    log_info "Cleaning up old backups (older than $RETENTION_DAYS days)..."

    if [ -d "$BACKUP_DIR" ]; then
        local deleted_count=$(find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -exec rm {} \; -print | wc -l)
        if [ "$deleted_count" -gt 0 ]; then
            log_info "Deleted $deleted_count old backup files"
            log_to_file "INFO: Cleaned up $deleted_count old backups"
        else
            log_info "No old backups to clean up"
        fi
    fi
}

cleanup_old_logs() {
    log_info "Cleaning up old logs..."

    # Rotate monitoring log
    if [ -f "$MONITOR_LOG" ] && [ $(stat -f%z "$MONITOR_LOG" 2>/dev/null || stat -c%s "$MONITOR_LOG") -gt 10485760 ]; then  # 10MB
        mv "$MONITOR_LOG" "${MONITOR_LOG}.old"
        log_to_file "INFO: Rotated monitoring log"
    fi

    # Clean Docker logs
    cd "$BASE_DIR"
    docker-compose -f "$COMPOSE_FILE" logs --no-color | tail -1000 > "${LOG_DIR}/application.log" 2>/dev/null || true

    # Clean old Docker logs
    docker system prune -f --filter "until=72h" > /dev/null 2>&1 || true
}

restart_if_needed() {
    log_info "Checking if restart is needed..."

    # Check if containers have been running for more than 7 days
    cd "$BASE_DIR"
    local containers=$(docker-compose -f "$COMPOSE_FILE" ps -q)

    for container in $containers; do
        local started=$(docker inspect --format='{{.State.StartedAt}}' "$container")
        local started_timestamp=$(date -d "$started" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S" "$started" +%s 2>/dev/null || echo 0)
        local current_timestamp=$(date +%s)
        local uptime_days=$(( (current_timestamp - started_timestamp) / 86400 ))

        if [ "$uptime_days" -gt 7 ]; then
            log_info "Container has been running for $uptime_days days, considering restart..."

            # Check if memory usage is high
            local mem_percent=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
            if [ "$mem_percent" -gt 80 ]; then
                log_warning "High memory usage detected, restarting containers..."
                docker-compose -f "$COMPOSE_FILE" restart
                log_to_file "INFO: Containers restarted due to high memory usage"
                sleep 30
                return 0
            fi
        fi
    done
}

send_alert() {
    local subject="$1"
    local message="$2"

    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL" 2>/dev/null || true
    fi

    # Log to system log
    logger -t "dndstorytelling" "$subject: $message"
}

run_health_check() {
    log_info "Starting comprehensive health check..."

    local issues=0

    if ! check_docker_health; then
        issues=$((issues + 1))
        send_alert "D&D Story Telling - Docker Health Issue" "Docker containers are not healthy. Check the logs for details."
    fi

    if ! check_application_health; then
        issues=$((issues + 1))
        send_alert "D&D Story Telling - Application Health Issue" "Application endpoints are not responding properly."
    fi

    if ! check_database_health; then
        issues=$((issues + 1))
        send_alert "D&D Story Telling - Database Health Issue" "Database is not accepting connections."
    fi

    check_resource_usage

    if [ $issues -eq 0 ]; then
        log_success "All health checks passed"
        log_to_file "INFO: Health check completed successfully"
    else
        log_error "$issues health check(s) failed"
        log_to_file "ERROR: Health check completed with $issues issues"
    fi

    return $issues
}

run_maintenance() {
    log_info "Starting maintenance tasks..."

    cleanup_old_logs
    cleanup_old_backups
    restart_if_needed

    log_success "Maintenance tasks completed"
    log_to_file "INFO: Maintenance completed"
}

# Main execution
case "${1:-health}" in
    "health")
        run_health_check
        ;;

    "backup")
        backup_data
        ;;

    "maintenance")
        run_maintenance
        ;;

    "monitor")
        # Continuous monitoring mode
        log_info "Starting continuous monitoring mode..."
        while true; do
            run_health_check
            sleep 300  # Check every 5 minutes
        done
        ;;

    "full")
        # Full maintenance cycle
        run_health_check
        backup_data
        run_maintenance
        ;;

    *)
        echo "Usage: $0 {health|backup|maintenance|monitor|full}"
        echo ""
        echo "Commands:"
        echo "  health      - Run health checks"
        echo "  backup      - Create backup"
        echo "  maintenance - Run maintenance tasks"
        echo "  monitor     - Continuous monitoring (runs every 5 minutes)"
        echo "  full        - Run all tasks (health + backup + maintenance)"
        exit 1
        ;;
esac