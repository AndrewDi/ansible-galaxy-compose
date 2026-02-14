#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

source "${PROJECT_DIR}/.env" 2>/dev/null || true

AUTO_BACKUP_ENABLED="${AUTO_BACKUP_ENABLED:-false}"
BACKUP_SCHEDULE="${BACKUP_SCHEDULE:-0 2 * * *}"

show_help() {
  cat << EOF
Galaxy Auto Backup Scheduler

Usage:
  $0 start   - Start the backup scheduler
  $0 stop    - Stop the backup scheduler
  $0 status  - Show scheduler status
  $0 run     - Run backup immediately

Environment variables:
  AUTO_BACKUP_ENABLED   - Enable auto backup (default: false)
  BACKUP_SCHEDULE       - Cron schedule (default: "0 2 * * *" - daily at 2 AM)
  BACKUP_RETENTION_DAYS - Days to keep backups (default: 7)

EOF
}

start_scheduler() {
  if [ "$AUTO_BACKUP_ENABLED" != "true" ]; then
    echo "Auto backup is disabled. Set AUTO_BACKUP_ENABLED=true in .env to enable."
    return 1
  fi

  echo "Starting Galaxy backup scheduler..."
  echo "Schedule: ${BACKUP_SCHEDULE}"
  
  (crontab -l 2>/dev/null | grep -v "galaxy-backup.sh"; echo "${BACKUP_SCHEDULE} ${SCRIPT_DIR}/backup.sh >> ${PROJECT_DIR}/logs/backup.log 2>&1") | crontab -
  
  crontab -l | grep "galaxy-backup.sh" && echo "Scheduler started successfully!" || echo "Failed to start scheduler"
}

stop_scheduler() {
  echo "Stopping Galaxy backup scheduler..."
  crontab -l 2>/dev/null | grep -v "galaxy-backup.sh" | crontab -
  echo "Scheduler stopped"
}

show_status() {
  echo "Galaxy Backup Scheduler Status"
  echo "==============================="
  echo "Auto backup enabled: ${AUTO_BACKUP_ENABLED}"
  echo "Schedule: ${BACKUP_SCHEDULE}"
  echo ""
  echo "Current crontab:"
  crontab -l 2>/dev/null | grep "galaxy-backup.sh" || echo "  (no backup jobs)"
}

run_backup() {
  echo "Running backup now..."
  "${SCRIPT_DIR}/backup.sh"
}

case "$1" in
  start)
    start_scheduler
    ;;
  stop)
    stop_scheduler
    ;;
  status)
    show_status
    ;;
  run)
    run_backup
    ;;
  *)
    show_help
    ;;
esac
