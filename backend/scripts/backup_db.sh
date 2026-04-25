#!/usr/bin/env bash
# Back up the live Postgres database to backend/backups/.
# Reads DATABASE_URL from backend/.env (root .env is consulted as fallback).
# Produces a plain-SQL dump suitable for psql restore.
#
# Usage:
#   ./backend/scripts/backup_db.sh
#
# Exit codes:
#   0 — backup succeeded; path printed on stdout
#   1 — DATABASE_URL not found in any .env
#   2 — pg_dump not installed
#   3 — pg_dump failed

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
PROJECT_ROOT="$( cd "$BACKEND_DIR/.." && pwd )"
BACKUP_DIR="$BACKEND_DIR/backups"

# --- locate DATABASE_URL ------------------------------------------------------
read_db_url() {
    local env_file="$1"
    [[ -f "$env_file" ]] || return 1
    local line
    line=$(grep -E '^[[:space:]]*DATABASE_URL[[:space:]]*=' "$env_file" | head -n1) || return 1
    [[ -n "$line" ]] || return 1
    # Strip key, optional surrounding whitespace, and surrounding single/double quotes.
    line="${line#*=}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    line="${line%\"}"; line="${line#\"}"
    line="${line%\'}"; line="${line#\'}"
    printf '%s' "$line"
}

DATABASE_URL=""
for candidate in "$BACKEND_DIR/.env" "$PROJECT_ROOT/.env"; do
    if val=$(read_db_url "$candidate"); then
        DATABASE_URL="$val"
        SOURCE_ENV="$candidate"
        break
    fi
done

if [[ -z "$DATABASE_URL" ]]; then
    echo "ERROR: DATABASE_URL not found in backend/.env or project .env" >&2
    exit 1
fi

# Drop any SQLAlchemy async-driver suffix that pg_dump cannot parse.
DATABASE_URL="${DATABASE_URL/postgresql+asyncpg:/postgresql:}"
DATABASE_URL="${DATABASE_URL/postgresql+psycopg:/postgresql:}"

# Pick the highest-version pg_dump available. Debian's /usr/bin/pg_dump is a
# wrapper (postgresql-common) that often defaults to an older cluster version,
# but Postgres requires the dump client to be >= the server's major version.
PG_DUMP=""
for candidate in /usr/lib/postgresql/*/bin/pg_dump /usr/local/pgsql/bin/pg_dump; do
    [[ -x "$candidate" ]] || continue
    PG_DUMP="$candidate"
done
if [[ -z "$PG_DUMP" ]] && command -v pg_dump >/dev/null 2>&1; then
    PG_DUMP="$(command -v pg_dump)"
fi
if [[ -z "$PG_DUMP" ]]; then
    echo "ERROR: pg_dump is not installed (apt: postgresql-client-17, mac: brew install postgresql@17)" >&2
    exit 2
fi
echo "pg_dump:      $PG_DUMP ($("$PG_DUMP" --version))"

mkdir -p "$BACKUP_DIR"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTFILE="$BACKUP_DIR/backup_${TIMESTAMP}.sql"

# Mask credentials when logging.
masked="$(printf '%s' "$DATABASE_URL" | sed -E 's#(://[^:]+):[^@]+@#\1:***@#')"
echo "Source env:   $SOURCE_ENV"
echo "Target:       $masked"
echo "Output file:  $OUTFILE"
echo "Running pg_dump (this may take a moment)..."

# --no-owner / --no-acl keep the dump portable to local DBs without role setup.
# --format=plain produces a psql-readable .sql file.
if ! "$PG_DUMP" \
    --no-owner \
    --no-acl \
    --format=plain \
    --file="$OUTFILE" \
    "$DATABASE_URL"
then
    echo "ERROR: pg_dump failed; partial file removed" >&2
    rm -f "$OUTFILE"
    exit 3
fi

SIZE="$(du -h "$OUTFILE" | cut -f1)"
LINES="$(wc -l < "$OUTFILE")"
echo "OK — wrote $OUTFILE ($SIZE, $LINES lines)"
