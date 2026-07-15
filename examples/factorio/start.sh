#!/bin/bash
# Factorio Headless Server start script
# Download from https://www.factorio.com/download (headless Linux64)
# Extract to /game/

cd /game

exec ./bin/x64/factorio --start-server /game/saves/world.zip \
    --server-settings /game/data/server-settings.json \
    --port 34197
