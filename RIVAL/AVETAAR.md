# Avetaar AI Suite Bot — RIVAL

- Developer: Avetaar — Telegram @Avetaar
- Team / rights: Rival

Full docs: see README.md (Arabic + English).

## Run
    python Avetaar.py

The launcher reads token/owner from RIVAL/bot_credentials.json or the
RIVAL_BOT_TOKEN / RIVAL_OWNER_ID / RIVAL_OWNER_USERNAME environment
variables, self-installs httpx + Pillow when missing, verifies the bot
via getMe, pings the owner, then enters the update loop with proxy
auto-recovery.

## Notes
- The Dev Board is owner-only; closed/banned users get a Contact Dev button.
- Provider base URLs are base64-encoded in RIVAL_config.py.
- Images/audio are re-uploaded to Telegram as files, never raw links.
- Single-instance lock (Mutex/flock) prevents dual-poll conflicts.
