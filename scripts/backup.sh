#!/usr/bin/env bash
set -euo pipefail
ENV_FILE="${ENV_FILE:-.env}"
COMPOSE_FILE="compose/compose.yaml"
BACKUP_DIR="backups"
mkdir -p "${BACKUP_DIR}"

# shellcheck disable=SC2046
set -a; [ -f "${ENV_FILE}" ] && . "${ENV_FILE}"; set +a

ts="$(date +%Y%m%d-%H%M%S)"
db_dump="${BACKUP_DIR}/db-${ts}.sql.gz"
fs_tar="${BACKUP_DIR}/filestore-${ts}.tar.gz"

# DB dump
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T db \
  pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" | gzip > "${db_dump}"

# Filestore archive (named volume)
docker run --rm -v odoo_filestore:/data -v "$(pwd)/${BACKUP_DIR}:/backup" alpine \
  sh -lc "cd /data && tar czf /backup/$(basename "${fs_tar}") ."

echo "Created:"
echo "  ${db_dump}"
echo "  ${fs_tar}"
