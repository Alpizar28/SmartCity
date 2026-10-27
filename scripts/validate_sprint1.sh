#!/usr/bin/env bash
# Default: offline suite. --engines adds canonical SQL and supplemental PG/Mongo integration.
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
export PYTHONDONTWRITEBYTECODE=1
if [[ "$#" -gt 1 || ( "$#" -eq 1 && "$1" != "--engines" ) ]]; then
  echo 'Usage: bash scripts/validate_sprint1.sh [--engines]' >&2
  exit 2
fi
python3 -m unittest discover -s tests/sprint1 -p 'test_*.py' -v
if ! command -v node >/dev/null 2>&1; then
  echo 'Node.js >=18 is required for the MongoDB builder tests.' >&2
  exit 1
fi
node --test tests/sprint1/test_mongodb.js
git diff --check
echo 'New Sprint 1 offline suite passed. No engine or historical reproduction PASS implied.'
if [[ "${1:-}" == "--engines" ]]; then
  python3 scripts/test_sprint1_sql.py
  python3 scripts/test_sprint1_engines.py
fi
