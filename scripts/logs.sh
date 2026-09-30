#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
# Startup logs can contain passwords and QQ QR codes. Do not publish them.
compose logs --tail 100 -f "$@"
