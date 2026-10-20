#!/usr/bin/env bash
# Minimal offline repository validation. It never starts services or contacts remote systems.
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
cd "$root"
python="${PYTHON:-$root/.venv/bin/python}"
if [[ ! -x "$python" ]]; then
  echo "Missing virtualenv interpreter: $python" >&2
  echo 'Create it from research/datasets/scripts/requirements.lock before validating.' >&2
  exit 2
fi

# The historical Phase 6 validator writes its report files. Preserve them so a
# maintenance validation never presents regenerated evidence as historical work.
tmpbase="${TMPDIR:-/tmp}"
if [[ -d /tmp/opencode ]]; then
  tmpbase=/tmp/opencode
fi
tmpdir="$(mktemp -d "$tmpbase/smartcity-validation.XXXXXX")"
phase6_outputs=(
  research/datasets/results/phase6/candidate_inventory.csv
  research/datasets/results/phase6/outputs_manifest.csv
  research/datasets/results/phase6/validation.json
)
for output in "${phase6_outputs[@]}"; do
  cp "$output" "$tmpdir/$(basename "$output")"
done
cleanup() {
  for output in "${phase6_outputs[@]}"; do
    cp "$tmpdir/$(basename "$output")" "$output"
  done
  rm -rf "$tmpdir"
}
trap cleanup EXIT

if git grep -nE '^(<<<<<<<|=======|>>>>>>>)'; then
  echo 'Merge markers found.' >&2
  exit 1
fi

"$python" -m compileall -q research/datasets/scripts research/datasets/tests
"$python" research/datasets/scripts/phase6_validate_docs.py
"$python" -m pytest research/datasets/tests -q
# Check the intended diff, not the temporary CSV reports emitted by Phase 6.
cleanup
trap - EXIT
git diff --check

echo 'Repository validation passed.'
