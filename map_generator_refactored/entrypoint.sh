#!/bin/sh
set -eu

# Forward all args directly to the CLI script to avoid module path issues when building from a subfolder
exec python /app/cli.py "$@"


