#!/bin/bash
set -euo pipefail
# Llave del replica set en un archivo temporal. El secreto viene del entorno.
umask 077
rm -f /tmp/sc-key
printf '%s' "$MONGO_REPL_KEY" > /tmp/sc-key
chown mongodb:mongodb /tmp/sc-key
chmod 400 /tmp/sc-key
exec /usr/local/bin/docker-entrypoint.sh "$@"
