#!/bin/bash
# Valheim dedicated server launch script
export LD_LIBRARY_PATH="/game/linux64:$LD_LIBRARY_PATH"
export SteamAppId=892970

cd /game

./valheim_server.x86_64 \
    -name "MyServer" \
    -port 2456 \
    -world "Dedicated" \
    -password "changeme" \
    -savedir "/game/saves" \
    -public 1
