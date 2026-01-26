#!/bin/bash
set -e
source "$(dirname "$0")/seed.env"
VENV_ACTIVATE="$(dirname "$0")/../.venv/bin/activate"
if [ -f "$VENV_ACTIVATE" ]; then
  source "$VENV_ACTIVATE"
fi

echo "Resetting tables..."
userdb db drop
userdb db init