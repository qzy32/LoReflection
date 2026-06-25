$ErrorActionPreference = "Stop"

$LocalRoot = git rev-parse --show-toplevel
Set-Location $LocalRoot

python scripts/a800_reverse_proxy_clone_sources.py `
  --output reports/reverse_proxy_source_clone_sanitized.json `
  --download-dir outputs/manual_review/r8a_source_resolution
