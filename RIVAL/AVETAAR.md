# Avetaar AI Suite Bot — RIVAL

Developer: Avetaar (Telegram @Avetaar)
Team / rights: Rival

## What this is
A button-driven Telegram assistant. No commands to type — just tap. One bot
for chat, images, voice, music and translation. Full details are in
README.md (Arabic + English).

## Run
```
python Avetaar.py
```
The launcher loads the bot token and owner ID from
`RIVAL/bot_credentials.json` (or the environment), self-installs its
dependencies when they are missing, checks that the bot works, pings the
owner, and enters the update loop with automatic recovery.

## Notes
- The owner panel is visible to the owner only; a closed bot or a banned
  user sees a "Contact Dev" button instead.
- Images and audio are sent as files, not links.
- A single-instance lock prevents two copies of the bot from running at
  once on the same token.
