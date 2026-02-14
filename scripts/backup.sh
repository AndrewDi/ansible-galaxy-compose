#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

BACKUP_DIR="${BACKUP_DIR:-${PROJECT_DIR}/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="galaxy_backup_${TIMESTAMP}"

source "${PROJECT_DIR}/.env" 2>/dev/null || true

echo "=========================================="
echo "Galaxy Backup Script"
echo "=========================================="
echo "Backup directory: ${BACKUP_DIR}"
echo "Retention days: ${RETENTION_DAYS}"
echo ""

mkdir -p "${BACKUP_DIR}"

echo "[1/3] Backing up PostgreSQL database..."
docker exec galaxy-postgres pg_dump -U ${POSTGRESQL_USER:-galaxy} ${POSTGRESQL_DATABASE:-galaxy} > "${BACKUP_DIR}/${BACKUP_NAME}_db.sql"
echo "      Database backup completed: ${BACKUP_NAME}_db.sql"

echo "[2/3] Backing up Galaxy data..."
docker run --rm \
  --network ansible-galaxy_galaxy-network \
  -v "${PROJECT_DIR}/config:/data" \
  alpine:latest \
  tar czf - -C /data . 2>/dev/null | tar xzf - -C "${BACKUP_DIR}/${BACKUP_NAME}_data" 2>/dev/null || true

docker cp galaxy-api:/var/lib/pulp "${BACKUP_DIR}/${BACKUP_NAME}_pulp" 2>/dev/null || true
echo "      Data backup completed: ${BACKUP_NAME}_pulp"

echo "[3/3] Creating archive..."
cd "${BACKUP_DIR}"
tar czf "${BACKUP_NAME}.tar.gz" \
  "${BACKUP_NAME}_db.sql" \
  "${BACKUP_NAME}_pulp" 2>/dev/null || true

rm -rf "${BACKUP_NAME}_db.sql" "${BACKUP_NAME}_pulp" 2>/dev/null || true

echo ""
echo "Backup created: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

echo ""
echo "Cleaning up old backups (keeping last ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "galaxy_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete
OLD_COUNT=$(find "${BACKUP_DIR}" -name "galaxy_backup_*.tar.gz" | wc -l)
echo "      Remaining backups: ${OLD_COUNT}"

echo ""
echo "=========================================="
echo "Backup completed successfully!"
echo "=========================================="
