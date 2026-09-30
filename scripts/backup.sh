#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
if [[ -n "$(compose ps --status running -q)" ]]; then
  echo 'Stop both services first: bash scripts/stop.sh' >&2
  echo 'This prevents inconsistent SQLite and QQ session backups.' >&2
  exit 1
fi
[[ -d runtime && -f .env ]] || { echo 'No initialized deployment to back up.' >&2; exit 1; }
umask 077
mkdir -p backups
BACKUP_DIR="$(mktemp -d "$PROJECT_DIR/backups/backup-$(date +%Y%m%d-%H%M%S)-XXXXXX")"
COPYFILE_DISABLE=1 tar -czf "$BACKUP_DIR/data.tar.gz" runtime .env compose.yaml config
tar -tzf "$BACKUP_DIR/data.tar.gz" >/dev/null
echo "Backup created: $BACKUP_DIR/data.tar.gz"
echo 'Contains credentials. Store privately. Restart with: bash scripts/start.sh'
