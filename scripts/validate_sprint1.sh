#!/usr/bin/env bash
# Default: offline. --engines: controlled DB tests. --datos: real local v2 sources too.
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
export PYTHONDONTWRITEBYTECODE=1
if [[ "$#" -gt 1 || ( "$#" -eq 1 && "$1" != "--engines" && "$1" != "--datos" ) ]]; then
  echo 'Usage: bash scripts/validate_sprint1.sh [--engines|--datos]' >&2
  exit 2
fi
python3 -m unittest discover -s tests/sprint1 -p 'test_*.py' -v
if ! command -v node >/dev/null 2>&1; then
  echo 'Node.js >=18 is required for the MongoDB builder tests.' >&2
  exit 1
fi
node --test tests/sprint1/test_mongodb.js tests/sprint1/test_mongodb_v2.js
git diff --check
echo 'New Sprint 1 offline suite passed. No engine or historical reproduction PASS implied.'
if [[ "${1:-}" == "--engines" || "${1:-}" == "--datos" ]]; then
  python3 scripts/test_sprint1_sql.py
  python3 scripts/test_sprint1_engines.py
fi
if [[ "${1:-}" == "--datos" ]]; then
  python_datos="${PYTHON_DATOS:-$root/research/datasets/.venv/bin/python}"
  if [[ ! -x "$python_datos" ]]; then
    echo 'Prepare el entorno de datos con research/datasets/scripts/requirements.lock.' >&2
    echo 'O defina PYTHON_DATOS con la ruta al intérprete que tiene esas dependencias.' >&2
    exit 2
  fi
  "$python_datos" -m sprint1.basico.preparar_v2
  "$python_datos" scripts/validar_v2.py
  "$python_datos" scripts/verificar_v2.py
fi
