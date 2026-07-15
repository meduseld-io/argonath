#!/bin/bash
# Minecraft Java Edition start script
# Download server.jar from https://www.minecraft.net/en-us/download/server
# Place it in /game/server.jar

cd /game

exec java -Xmx4G -Xms2G -jar server.jar nogui
