#!/bin/bash
set -e
export USERDB_PATH="$(dirname "$0")/../demo.sqlite"
source "$(dirname "$0")/seed.env"
VENV_ACTIVATE="$(dirname "$0")/../.venv/bin/activate"
if [ -f "$VENV_ACTIVATE" ]; then
  source "$VENV_ACTIVATE"
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

"$SCRIPT_DIR/reset.sh"
echo

echo "Creating users..."
"$SCRIPT_DIR/seed_users.sh"
echo

echo "Creating invoices..."
"$SCRIPT_DIR/seed_invoices.sh"
echo

echo "===== INITIAL USERS AND INVOICES ====="
userdb invoices list
echo 

JOHN_ID=$(userdb users get --email "$JOHN_EMAIL" | grep -m1 -o '[0-9]\+')
: "${JOHN_ID:?Failed to resolve JOHN_ID}"

INVOICE_ID=$(userdb invoices list --user-id "$JOHN_ID" | grep -m1 -o '[0-9]\+')
: "${INVOICE_ID:?Failed to resolve INVOICE_ID}"

echo "===== UPDATE INVOICE TOTAL & DATE DUE ====="
userdb invoices update --id "$INVOICE_ID" --total 1234 --date-due 8/12/2026
echo

echo "===== UPDATE JOHN ====="
userdb users update --id "$JOHN_ID" --name "Willam" --new-email "willam@hotmail.com"
echo

ALICE_ID=$(userdb users get --email "$ALICE_EMAIL" | grep -m1 -o '[0-9]\+')
: "${ALICE_ID:?Failed to resolve ALICE_ID}"

echo "===== DELETE ALICE ====="
userdb users delete --id "$ALICE_ID"
echo

echo "===== FINAL USERS AND INVOICES ====="
userdb invoices list
echo

echo "Done."