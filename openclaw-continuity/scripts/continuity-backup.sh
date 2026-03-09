#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/home/fan/.openclaw/workspace}"
BACKUP_REPO="${BACKUP_REPO:-$HOME/.openclaw/continuity-backup-repo}"
STAGE_DIR="$BACKUP_REPO/openclaw-continuity"
INCLUDE_FILE="$WORKSPACE/backup/continuity-include.txt"
REPO_NAME="${REPO_NAME:-openclaw-continuity-backup}"
TZ_NAME="${TZ_NAME:-Asia/Shanghai}"

mkdir -p "$BACKUP_REPO"

if [ ! -d "$BACKUP_REPO/.git" ]; then
  git init -q "$BACKUP_REPO"
  git -C "$BACKUP_REPO" branch -M main >/dev/null 2>&1 || true
fi

git -C "$BACKUP_REPO" config user.name "${GIT_AUTHOR_NAME:-OpenClaw Assistant}"
git -C "$BACKUP_REPO" config user.email "${GIT_AUTHOR_EMAIL:-assistant@local}"

cat > "$BACKUP_REPO/.gitignore" <<'EOF'
.DS_Store
*.pyc
__pycache__/
*.log
EOF

cat > "$BACKUP_REPO/README.md" <<'EOF'
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
EOF

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"

while IFS= read -r rel || [ -n "$rel" ]; do
  rel="${rel%%$'\r'}"
  [[ -z "$rel" || "${rel:0:1}" == "#" ]] && continue
  src="$WORKSPACE/$rel"
  dst="$STAGE_DIR/$rel"
  if [ -d "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    rsync -a --delete \
      --exclude '.git/' \
      --exclude 'node_modules/' \
      --exclude '__pycache__/' \
      --exclude '*.pyc' \
      --exclude '*.log' \
      --exclude '.DS_Store' \
      "$src"/ "$dst"/
  elif [ -f "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    cp -a "$src" "$dst"
  fi
done < "$INCLUDE_FILE"

cat > "$BACKUP_REPO/BACKUP-MANIFEST.txt" <<EOF
Generated: $(TZ="$TZ_NAME" date '+%Y-%m-%d %H:%M:%S %Z')
Workspace: $WORKSPACE
Stage: $STAGE_DIR
Included from: $INCLUDE_FILE
EOF
find "$STAGE_DIR" -type f | sed "s#^$STAGE_DIR/##" | sort >> "$BACKUP_REPO/BACKUP-MANIFEST.txt"

# Fail closed on real secrets, but allow documentation placeholders inside skills.
if grep -RInE 'BEGIN[[:space:]].*PRIVATE KEY' "$STAGE_DIR" > /tmp/continuity-backup-sensitive.txt 2>/dev/null; then
  echo "Private key material detected in staged files; aborting backup." >&2
  sed -n '1,20p' /tmp/continuity-backup-sensitive.txt >&2
  exit 2
fi

SECRET_FILE="$HOME/.openclaw/openclaw.json"
if [ -f "$SECRET_FILE" ]; then
  python3 - <<'PY' > /tmp/continuity-backup-known-secrets.txt
import json, re, os
p=os.path.expanduser('~/.openclaw/openclaw.json')
try:
    data=json.load(open(p,'r',encoding='utf-8'))
except Exception:
    raise SystemExit(0)
vals=[]

def walk(x):
    if isinstance(x, dict):
        for k,v in x.items():
            if isinstance(v, str) and re.search(r'(token|apikey|secret|cookie)', k, re.I) and len(v) >= 16:
                vals.append(v)
            else:
                walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)
walk(data)
for v in sorted(set(vals)):
    print(v)
PY
  while IFS= read -r secret || [ -n "$secret" ]; do
    [ -z "$secret" ] && continue
    if grep -RInF -- "$secret" "$STAGE_DIR" >> /tmp/continuity-backup-sensitive.txt 2>/dev/null; then :; fi
  done < /tmp/continuity-backup-known-secrets.txt
fi

if [ -s /tmp/continuity-backup-sensitive.txt ]; then
  echo "Configured secret values detected in staged files; aborting backup." >&2
  sed -n '1,20p' /tmp/continuity-backup-sensitive.txt >&2
  exit 2
fi
rm -f /tmp/continuity-backup-sensitive.txt /tmp/continuity-backup-known-secrets.txt

git -C "$BACKUP_REPO" add .gitignore README.md BACKUP-MANIFEST.txt openclaw-continuity

if git -C "$BACKUP_REPO" diff --cached --quiet; then
  exit 0
fi

COUNT=$(git -C "$BACKUP_REPO" diff --cached --name-only | wc -l | tr -d ' ')
SUMMARY=$(git -C "$BACKUP_REPO" diff --cached --name-status | awk 'NR<=8{print $1":"$2}' | paste -sd ', ' -)
STAMP=$(TZ="$TZ_NAME" date '+%Y-%m-%d %H:%M:%S %Z')
if [ -z "$SUMMARY" ]; then
  SUMMARY="continuity refresh"
fi

git -C "$BACKUP_REPO" commit -m "backup: $STAMP | $COUNT paths | $SUMMARY" >/dev/null

# Try remote push if already configured.
if git -C "$BACKUP_REPO" remote get-url origin >/dev/null 2>&1; then
  ORIGIN_URL=$(git -C "$BACKUP_REPO" remote get-url origin)
  TOKEN_FILE="${GITHUB_TOKEN_FILE:-$HOME/.openclaw/continuity-backup.token}"
  TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
  if [ -z "$TOKEN" ] && [ -f "$TOKEN_FILE" ]; then
    TOKEN=$(cat "$TOKEN_FILE")
  fi
  if [ -n "$TOKEN" ] && printf '%s' "$ORIGIN_URL" | grep -q '^https://github.com/'; then
    AUTH_URL=$(ORIGIN_URL="$ORIGIN_URL" TOKEN="$TOKEN" python3 - <<'PY'
import os
url=os.environ['ORIGIN_URL']
tok=os.environ['TOKEN']
print(url.replace('https://github.com/', f'https://x-access-token:{tok}@github.com/', 1))
PY
)
    git -C "$BACKUP_REPO" push "$AUTH_URL" main:main >/dev/null 2>&1 || true
  else
    git -C "$BACKUP_REPO" push origin main >/dev/null 2>&1 || true
  fi
  exit 0
fi

# Try GitHub CLI if available and authenticated later.
if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then
    OWNER=$(gh api user --jq .login)
    gh repo view "$OWNER/$REPO_NAME" >/dev/null 2>&1 || gh repo create "$OWNER/$REPO_NAME" --private --description "OpenClaw continuity backup" >/dev/null
    git -C "$BACKUP_REPO" remote add origin "https://github.com/$OWNER/$REPO_NAME.git" 2>/dev/null || true
    gh auth setup-git >/dev/null 2>&1 || true
    git -C "$BACKUP_REPO" push -u origin main >/dev/null 2>&1 || true
    exit 0
  fi
fi

# Try token-based auto-create/push later if token appears.
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
if [ -n "$TOKEN" ]; then
  USER_JSON=$(curl -sS -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" https://api.github.com/user || true)
  OWNER=$(USER_JSON="$USER_JSON" python3 - <<'PY'
import json, os
try:
    d=json.loads(os.environ.get('USER_JSON',''))
    print(d.get('login',''))
except Exception:
    print('')
PY
)
  if [ -n "$OWNER" ]; then
    curl -sS -X POST \
      -H "Authorization: Bearer $TOKEN" \
      -H "Accept: application/vnd.github+json" \
      https://api.github.com/user/repos \
      -d "{\"name\":\"$REPO_NAME\",\"private\":true,\"description\":\"OpenClaw continuity backup\"}" >/dev/null 2>&1 || true
    git -C "$BACKUP_REPO" remote add origin "https://github.com/$OWNER/$REPO_NAME.git" 2>/dev/null || true
    git -C "$BACKUP_REPO" push "https://x-access-token:$TOKEN@github.com/$OWNER/$REPO_NAME.git" main:main >/dev/null 2>&1 || true
  fi
fi
