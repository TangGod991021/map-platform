#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../apps/admin-web"
[ -d node_modules ] || npm install
[ -f .env ] || cp .env.example .env
npm run dev
