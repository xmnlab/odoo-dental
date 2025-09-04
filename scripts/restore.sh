#!/usr/bin/env bash
set -euo pipefail
if [ $# -ne 2 ]; then
  echo "Usage: scripts/restore.sh <db.sql.gz> <filestore.tar.gz>"
  exit 1
fi
DB_GZ="$1"
FS_TAR="$2"
ENV_FILE="${ENV_FILE:-.env}"
COMPOSE_FILE="compose/compose.yaml"

set -a; [ -f "${ENV_FILE}" ] && . "${ENV_FILE}"; set +a

# Stop Odoo to avoid file/db writes during restore
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" stop odoo

# Restore DB (drop schema public to avoid residue, then recreate)
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T db \
  bash -lc "psql -U '${POSTGRES_USER}' -d '${POSTGRES_DB}' -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO ${POSTGRES_USER};'"

gzip -dc "${DB_GZ}" | docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T db \
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"

# Restore filestore volume
docker run --rm -v odoo_filestore:/data -v "$(pwd):/backup" alpine \
  sh -lc "rm -rf /data/* && tar xzf \"/backup/${FS_TAR}\" -C /data"

# Start Odoo back
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" start odoo
echo "Restore finished."
