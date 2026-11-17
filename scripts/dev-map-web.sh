#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../apps/map-web"
python3 -m http.server 8081
