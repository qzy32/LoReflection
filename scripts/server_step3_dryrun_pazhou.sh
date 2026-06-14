#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-server_configs/paths.local.env}"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE"
  echo "Please copy server_configs/paths.pazhou.template.env to server_configs/paths.local.env and fill real paths."
  exit 1
fi

echo "[Step 3.0] Checking server paths..."
python tools/check_server_paths.py \
  --env-file "$ENV_FILE" \
  --report reports/server_path_check_report.json \
  --strict

echo "[Step 3.1] Inspecting real sources..."
python tools/inspect_real_sources.py \
  --env-file "$ENV_FILE" \
  --output reports/real_source_inspection_report.json \
  --max-files 5 \
  --verbose

echo "Pazhou server dry-run passed. No data/model/training was executed."
