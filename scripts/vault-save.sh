#!/usr/bin/env bash
# Auto-saves session log to Obsidian vault on Claude Code Stop

VAULT="/Users/floakii/Claudio/agro-content-ob/agro-content"
REPO="/Users/floakii/Claudio/agro-content"
NOW=$(date +"%Y-%m-%d-%H")
DATE=$(date +"%Y-%m-%d")
HOUR=$(date +"%H")
LOG_FILE="$VAULT/logs/$NOW.md"

# Skip if log already exists for this hour
[ -f "$LOG_FILE" ] && exit 0

# Collect git data
COMMITS=$(git -C "$REPO" log --oneline -5 2>/dev/null || echo "sem commits")
CHANGED=$(git -C "$REPO" diff --stat HEAD 2>/dev/null | tail -1 || echo "")
FILES=$(git -C "$REPO" diff --name-only HEAD 2>/dev/null | sed 's/^/- /' || echo "- (sem alterações não commitadas)")
STATUS=$(git -C "$REPO" status --short 2>/dev/null | sed 's/^/- /' || echo "- limpo")

cat > "$LOG_FILE" << EOF
---
title: Sessão $NOW
tags: [log, sessao]
created: $DATE
updated: $DATE
status: active
type: log
---

# Log de Sessão — $DATE $HOUR:00

## O que foi feito

- (preencher)

## Decisões tomadas

- (preencher)

## Arquivos modificados

$FILES

## Status git

\`\`\`
$COMMITS
\`\`\`
$CHANGED

## Próximos passos

- (preencher)

## Links relacionados

- [[status-tecnico]]
EOF

# Update status-tecnico with last session date
STATUS_FILE="$VAULT/meta/status-tecnico.md"
if [ -f "$STATUS_FILE" ]; then
  sed -i '' "s/^updated: .*/updated: $DATE/" "$STATUS_FILE" 2>/dev/null || true
fi

echo "{\"systemMessage\": \"Log salvo em logs/$NOW.md — complete a narrativa no Obsidian.\"}"
