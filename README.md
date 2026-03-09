# OpenClaw Continuity Backup

Private continuity backup for OpenClaw.

Backs up only continuity-critical, low-noise files:
- identity / persona / preferences
- curated memory and daily memory
- custom skills and backup config

Explicitly excludes:
- secrets, tokens, cookies, env files
- caches, logs, node_modules, temp files
- large unrelated project directories

Restore order:
1. `openclaw-continuity/AGENTS.md`
2. `openclaw-continuity/SOUL.md`
3. `openclaw-continuity/USER.md`
4. `openclaw-continuity/IDENTITY.md`
5. `openclaw-continuity/MEMORY.md`
6. `openclaw-continuity/memory/`
7. `openclaw-continuity/skills/`
8. `openclaw-continuity/HEARTBEAT.md`
9. `openclaw-continuity/TOOLS.md`
