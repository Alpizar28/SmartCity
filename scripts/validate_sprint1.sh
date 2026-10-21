#!/usr/bin/env bash
# New offline suite only: no databases, downloads or historical report writes.
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
export PYTHONDONTWRITEBYTECODE=1
python3 -m unittest discover -s tests/sprint1 -p 'test_*.py' -v
if ! command -v node >/dev/null 2>&1; then
  echo 'Node.js >=18 is required for the MongoDB builder tests.' >&2
  exit 1
fi
node --test tests/sprint1/test_mongodb.js
git diff --check
echo 'New Sprint 1 offline suite passed. No engine or historical reproduction PASS implied.'
