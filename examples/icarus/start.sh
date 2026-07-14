#!/bin/bash
# Icarus dedicated server launch script (Wine/Proton)
# Requires GE-Proton installed at /compatibilitytools/GE-Proton10-32

export STEAM_COMPAT_DATA_PATH="/game/pfx"
export STEAM_COMPAT_CLIENT_INSTALL_PATH="/opt/steamcmd"
PROTON_PATH="/compatibilitytools/GE-Proton10-32"

cd /game

# Create prefix directory if needed
mkdir -p "$STEAM_COMPAT_DATA_PATH"

# Launch via tmux so the panel can detect the process
tmux new-session -d -s gameserver \
    "$PROTON_PATH/proton" run \
    ./IcarusServer.exe \
    -SteamServerName=MyServer \
    -Port=17777 \
    -QueryPort=27015 \
    -Log
