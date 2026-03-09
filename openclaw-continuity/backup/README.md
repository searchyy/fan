# Continuity Backup Config

This folder defines the allowlist for OpenClaw continuity backups.

- `continuity-include.txt`: paths copied into the backup repo
- `scripts/continuity-backup.sh`: local backup + git + optional GitHub push automation

Design goals:
- continuity first
- minimal leak surface
- exclude secrets by default
- commit only on change
