#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
"$DOCKER_BIN" info >/dev/null
umask 077
mkdir -p runtime/astrbot runtime/napcat/config runtime/napcat/qq backups
if [[ ! -e .env ]]; then cp .env.example .env; fi
# Seed only new installations; preserve later WebUI changes.
if [[ ! -e runtime/astrbot/cmd_config.json ]]; then
  cp config/astrbot.initial.json runtime/astrbot/cmd_config.json
fi
if [[ ! -e runtime/napcat/config/onebot11.json ]]; then
  cp config/napcat.initial.json runtime/napcat/config/onebot11.json
fi
compose config --quiet
compose up -d
compose ps
echo 'Services started. See README.md for WebUI login and model setup.'
