#!/bin/bash
# publish.sh — универсальная утилита публикации артефакта на собственный сайт
#
# Usage:
#   publish.sh --local <path> --remote <remote_path> [--title <title>] [--index]
#
# --local       абсолютный путь к локальному файлу (HTML / MP4 / PNG / ...)
# --remote      абсолютный путь на сервере куда копировать
# --title       (опционально) заголовок, добавляется в index
# --index       (флаг) добавить запись в /studio/index.html и на главную
#
# ENV:
#   SSH_HOST={{SSH_HOST}}
#   SSH_USER={{SSH_USER}}
#   SSH_KEY={{SSH_KEY_PATH}}
#   PUBLIC_DOMAIN={{YOUR_DOMAIN}}
#   PUBLIC_SITE_ROOT={{PUBLIC_SITE_ROOT}}

set -euo pipefail

LOCAL=""
REMOTE=""
TITLE=""
ADD_INDEX=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --local)  LOCAL="$2"; shift 2 ;;
        --remote) REMOTE="$2"; shift 2 ;;
        --title)  TITLE="$2"; shift 2 ;;
        --index)  ADD_INDEX=true; shift ;;
        *) echo "Unknown arg: $1" >&2; exit 1 ;;
    esac
done

[[ -z "$LOCAL" ]] && { echo "ERROR: --local required"; exit 1; }
[[ -z "$REMOTE" ]] && { echo "ERROR: --remote required"; exit 1; }
[[ ! -f "$LOCAL" ]] && { echo "ERROR: local file not found: $LOCAL"; exit 1; }

: "${SSH_HOST:?SSH_HOST env var not set}"
: "${SSH_USER:?SSH_USER env var not set}"
: "${SSH_KEY:?SSH_KEY env var not set}"
: "${PUBLIC_DOMAIN:?PUBLIC_DOMAIN env var not set}"

echo "[publish] local=$LOCAL"
echo "[publish] remote=${SSH_USER}@${SSH_HOST}:${REMOTE}"

# Upload
scp -q -i "$SSH_KEY" "$LOCAL" "${SSH_USER}@${SSH_HOST}:${REMOTE}"

# Set permissions + touch (cache-bust via Last-Modified)
ssh -i "$SSH_KEY" "${SSH_USER}@${SSH_HOST}" \
    "chown www-data:www-data '$REMOTE' 2>/dev/null || true; \
     chmod 644 '$REMOTE'; \
     touch '$REMOTE'"

# Build public URL
REMOTE_REL="${REMOTE#${PUBLIC_SITE_ROOT:-/var/www/}}"
REMOTE_REL="${REMOTE_REL#/}"
PUBLIC_URL="https://${PUBLIC_DOMAIN}/${REMOTE_REL}"

echo "[publish] ok"
echo "[publish] url: $PUBLIC_URL"

# Добавить в index (опционально)
if [[ "$ADD_INDEX" == true ]]; then
    [[ -z "$TITLE" ]] && TITLE="$(basename "$LOCAL")"
    DATE="$(date -u +'%Y-%m-%d %H:%M UTC')"
    ENTRY="<li><time>$DATE</time> · <a href=\"/$REMOTE_REL\">$TITLE</a></li>"

    # Добавить в начало /studio/index.html (после тега <ul>)
    ssh -i "$SSH_KEY" "${SSH_USER}@${SSH_HOST}" \
        "STUDIO='${PUBLIC_SITE_ROOT:-/var/www/}/studio/index.html'; \
         [[ -f \$STUDIO ]] || { echo '<!DOCTYPE html><html><body><h1>Studio</h1><ul></ul></body></html>' > \$STUDIO; }; \
         sed -i '0,/<ul>/s|<ul>|<ul>\n$ENTRY|' \$STUDIO; \
         chown www-data:www-data \$STUDIO"
    echo "[publish] added to /studio/index.html"
fi

echo "$PUBLIC_URL"
