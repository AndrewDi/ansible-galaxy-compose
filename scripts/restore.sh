#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

BACKUP_DIR="${BACKUP_DIR:-${PROJECT_DIR}/backups}"

source "${PROJECT_DIR}/.env" 2>/dev/null || true

echo "=========================================="
echo "Galaxy Restore Script"
echo "=========================================="
echo "Backup directory: ${BACKUP_DIR}"
echo ""

if [ -z "$1" ]; then
  echo "Available backups:"
  ls -lh "${BACKUP_DIR}"/galaxy_backup_*.tar.gz 2>/dev/null || echo "No backups found"
  echo ""
  echo "Usage: $0 <backup_filename>"
  echo "Example: $0 galaxy_backup_20240115_143022.tar.gz"
  exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
  echo "Error: Backup file not found: ${BACKUP_DIR}/${BACKUP_FILE}"
  exit 1
fi

echo "WARNING: This will overwrite existing data!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

echo ""
echo "[1/4] Stopping services..."
docker compose -f "${PROJECT_DIR}/docker-compose.yml" stop galaxy-api galaxy-worker galaxy-content

echo "[2/4] Extracting backup..."
TEMP_DIR=$(mktemp -d)
tar xzf "${BACKUP_DIR}/${BACKUP_FILE}" -C "${TEMP_DIR}"

echo "[3/4] Restoring PostgreSQL database..."
DB_SQL=$(ls "${TEMP_DIR}"/*_db.sql 2>/dev/null | head -1)
if [ -n "$DB_SQL" ]; then
  docker exec -i galaxy-postgres psql -U ${POSTGRESQL_USER:-galaxy} ${POSTGRESQL_DATABASE:-galaxy} < "$DB_SQL"
  echo "      Database restored"
else
  echo "      Warning: No database backup found"
fi

echo "[4/4] Restoring Galaxy data..."
PULP_DIR=$(ls -d "${TEMP_DIR}"/*_pulp 2>/dev/null | head -1)
if [ -n "$PULP_DIR" ]; then
  docker cp "${PULP_DIR}/." galaxy-api:/var/lib/pulp/
  echo "      Data restored"
else
  echo "      Warning: No data backup found"
fi

rm -rf "${TEMP_DIR}"

echo ""
echo "[5/5] Starting services..."
docker compose -f "${PROJECT_DIR}/docker-compose.yml" start galaxy-api galaxy-worker galaxy-content

echo ""
echo "=========================================="
echo "Restore completed successfully!"
echo "=========================================="
