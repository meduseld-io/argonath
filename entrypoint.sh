#!/bin/sh
# Run Argonath (and the game server it launches) as PUID:PGID instead of root,
# so files created in the mounted folders belong to the host user.
set -e

PUID="${PUID:-1000}"
PGID="${PGID:-1000}"

if [ "$(id -u)" != "0" ] || [ "$PUID" = "0" ]; then
    # Already non-root, or explicitly asked to stay root
    exec python /app/app.py
fi

# Create the group and user if they don't exist yet
if ! getent group "$PGID" >/dev/null; then
    groupadd -g "$PGID" argonath
fi
if ! getent passwd "$PUID" >/dev/null; then
    useradd -u "$PUID" -g "$PGID" -d /game -M -s /bin/sh argonath
fi

# Take ownership of the folders Argonath writes to. /game is only walked when
# its top level belongs to someone else (e.g. files left by an older root install).
chown -R "$PUID:$PGID" /data /opt/steamcmd
if [ "$(stat -c %u /game)" != "$PUID" ] || [ "$(stat -c %g /game)" != "$PGID" ]; then
    echo "Setting owner of /game to $PUID:$PGID (one-time, may take a while)"
    chown -R "$PUID:$PGID" /game
fi

exec setpriv --reuid="$PUID" --regid="$PGID" --init-groups python /app/app.py
