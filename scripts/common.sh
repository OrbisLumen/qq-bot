#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
if command -v docker >/dev/null 2>&1; then
  DOCKER_BIN="$(command -v docker)"
elif [[ -x /Applications/Docker.app/Contents/Resources/bin/docker ]]; then
  DOCKER_BIN=/Applications/Docker.app/Contents/Resources/bin/docker
else
  echo 'Docker is missing. Install and open Docker Desktop first.' >&2
  exit 1
fi
# Docker may invoke bundled credential helpers by name.
export PATH="$(dirname "$DOCKER_BIN"):$PATH"
compose() {
  "$DOCKER_BIN" compose --project-directory "$PROJECT_DIR" -f "$PROJECT_DIR/compose.yaml" "$@"
}
