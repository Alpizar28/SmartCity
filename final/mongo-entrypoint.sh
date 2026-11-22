#!/bin/bash
set -euo pipefail
# Qué hace: deja la llave del replica set en un archivo temporal y arranca mongod. El secreto viene del entorno, no del repo.
umask 077
printf '%s' "$MONGO_REPL_KEY" > /tmp/sc-key
chown mongodb:mongodb /tmp/sc-key
chmod 400 /tmp/sc-key
exec /usr/local/bin/docker-entrypoint.sh "$@"
