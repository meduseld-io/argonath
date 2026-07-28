# Minecraft Java Edition

Vanilla Minecraft server. Does not use SteamCMD - download `server.jar` directly from Minecraft's website.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 25565 | TCP      | Game    |
| 25575 | TCP      | RCON    |

## Prerequisites

- Java 21+ must be installed in the container (OpenJDK recommended)
- Download `server.jar` from https://www.minecraft.net/en-us/download/server

## Setup

1. Copy `game.yml` and `start.sh` to your Argonath `config/` folder
2. Install Java 21 in your Docker image (e.g. `apt install openjdk-21-jre-headless`)
3. Download `server.jar` and place it in `/game/`
4. Run the server once - it will generate `eula.txt`
5. Edit `eula.txt` and set `eula=true`
6. Start the server from the panel

## Configuration

- `server.properties` - all server settings (generated on first run)
- `ops.json` - operator (admin) list
- `whitelist.json` - whitelist (if enabled)
- `banned-players.json` / `banned-ips.json` - ban lists

Key `server.properties` settings:
```properties
server-name=MyServer
motd=A Minecraft Server
max-players=20
difficulty=normal
gamemode=survival
white-list=false
enable-rcon=false
```

## Memory

The `start.sh` allocates 4GB max / 2GB min by default. Adjust `-Xmx` and `-Xms` in `start.sh` based on your available RAM and expected player count:

- 1-5 players: 2-4GB
- 5-10 players: 4-6GB
- 10-20 players with mods: 6-10GB

## Notes

- Accept the EULA on first run or the server won't start
- For modded servers (Forge/Fabric), replace `server.jar` with the modded server jar and adjust the start command
- World data is in the `world/` directory
- Logs are in `logs/latest.log`
- The process name is `java` since Minecraft runs on the JVM
