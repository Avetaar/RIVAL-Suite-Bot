#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "=============================================="
echo "  RIVAL Suite Bot - Avetaar AI Suite (v0.1)"
echo "  One-command installer: Termux / Linux / macOS / hosting"
echo "=============================================="
_py_ok() { "$1" --version >/dev/null 2>&1; }
PY=""
for c in python3 py python; do
  if command -v "$c" >/dev/null 2>&1 && _py_ok "$c"; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "python not found - installing..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y && sudo apt-get install -y python3 python3-pip
  elif command -v pkg >/dev/null 2>&1; then
    sudo pkg install -y python
  elif command -v apk >/dev/null 2>&1; then
    sudo apk add python3 py3-pip
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y python3
  else
    echo "install python3 manually, then rerun this script"; exit 1
  fi
  PY="$(command -v python3 >/dev/null 2>&1 && echo python3 || echo python)"
fi
echo "[1/4] python: $($PY --version 2>&1)"
$PY -m pip install --quiet --upgrade pip 2>/dev/null || true
$PY -m pip install --quiet httpx Pillow
echo "[2/4] dependencies installed (httpx + Pillow)"
CRED="RIVAL/bot_credentials.json"
if [ ! -f "$CRED" ]; then
  echo "[3/4] setup credentials - press ENTER to skip defaults where marked"
  printf "bot token (from @BotFather) > "
  read -r T_TOKEN
  printf "bot username WITHOUT @ (used for dev contact link) > "
  read -r T_USER
  printf "owner telegram user id (numeric) > "
  read -r T_ID
  $PY - "$CRED" "$T_TOKEN" "$T_USER" "$T_ID" <<'EOF'
import json, sys
path, token, user, owner = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
try:
    owner_i = int(owner)
except ValueError:
    print("owner id must be numeric - getting it via @userinfobot is the easy way")
    owner_i = 0
json.dump({"token": token, "owner_id": owner_i, "owner_username": user}, open(path, "w"), indent=1)
print("credentials written to", path)
EOF
else
  echo "[3/4] credentials already in $CRED - keeping them"
fi
echo "[4/4] starting bot (Ctrl+C stops it; rerun to start again)"
$PY Avetaar.py
