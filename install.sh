#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ -t 1 ] && [ -t 0 ]; then
  R=$'\e[0m'; B=$'\e[1m'; C=$'\e[36m'; G=$'\e[32m'; Y=$'\e[33m'
else
  R=""; B=""; C=""; G=""; Y=""
fi

spin_pid=""
spin() {
  local f='| / - ' i=0
  while :; do
    i=$((i+1))
    printf "\r%s%s %s%s" "$C" "${f:$((i%4)):1}" "$1" "$R"
    sleep 0.1
  done &
  spin_pid=$!
}
stop_spin() {
  [ -n "$spin_pid" ] && kill "$spin_pid" 2>/dev/null
  [ -n "$spin_pid" ] && wait "$spin_pid" 2>/dev/null
  printf "\r\033[K"
  spin_pid=""
}

echo "${C}${B}══════════════════════════════════════════
  RIVAL Suite Bot  •  v0.1  •  Avetaar AI
══════════════════════════════════════════${R}"

echo "${C}[1/4] Python${R}"
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" --version >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "${Y}Python not found — installing…${R}"
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y >/dev/null 2>&1 || true
    sudo apt-get install -y python3 python3-pip
    PY=python3
  elif command -v pkg >/dev/null 2>&1; then
    pkg install -y python
    PY=python
  elif command -v apk >/dev/null 2>&1; then
    sudo apk add python3 py3-pip
    PY=python3
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3
    PY=python3
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y python3
    PY=python3
  else
    echo "${R}Install Python, then run this script again." >&2
    exit 1
  fi
fi
echo "     $(${PY} --version 2>&1)   ${G}→ ${PY}${R}"

echo "${C}[2/4] Installing dependencies…${R}"
spin "installing httpx + Pillow"
$PY -m pip install --quiet httpx Pillow
stop_spin
echo "     ${G}done${R}"

CRED="RIVAL/bot_credentials.json"
if [ -f "$CRED" ]; then
  echo "${C}[3/4] Credentials already exist — keeping them${R} (${CRED})"
else
  echo "${C}[3/4] Setup — 3 quick questions${R}"
  echo -n "${B}① Bot token${R} (from @BotFather) > "
  read -r T_TOKEN
  echo -n "${B}② Your Telegram username${R} (developer contact, without @) > "
  read -r T_USER
  echo -n "${B}③ Your numeric Telegram ID${R} (the owner) > "
  read -r T_ID
  $PY - "$CRED" "$T_TOKEN" "$T_USER" "$T_ID" <<'EOF'
import json, sys
path, token, user, owner = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
try:
    owner_i = int(owner)
except ValueError:
    print("owner id must be numeric - ask @userinfobot for it")
    owner_i = 0
json.dump({"token": token, "owner_id": owner_i, "owner_username": user}, open(path, "w"), indent=1)
print("credentials written to", path)
EOF
  echo "     ${G}saved → $CRED${R}"
fi

echo "${C}[4/4] Starting the bot…${R}   ${Y}(Ctrl+C stops it, rerun to start again)${R}"
$PY Avetaar.py
