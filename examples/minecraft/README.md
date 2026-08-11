# Minecraft Java Edition

Vanilla Minecraft server. Uses Mojang's version manifest API for automatic deploy and update detection - no SteamCMD needed. Java is included in the Docker image.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 25565 | TCP      | Game    |
| 25575 | TCP      | RCON    |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Click **Deploy** in the panel - it will:
   - Download the latest `server.jar` from Mojang
   - Accept the EULA automatically
   - Generate a `start.sh` script
3. Click **Start** to launch the server

## Update Detection

Argonath checks Mojang's version manifest API every hour for new releases. When a new Minecraft version is published:

- The panel shows an "Update Available" badge (e.g. `1.21.1 -> 1.21.2`)
- Clicking **Restart** downloads the new `server.jar` and relaunches
- Starting the server also auto-updates if a new version is available

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

The generated `start.sh` allocates 4GB max / 2GB min by default. Adjust `-Xmx` and `-Xms` in `start.sh` based on your available RAM:

- 1-5 players: 2-4GB
- 5-10 players: 4-6GB
- 10-20 players with mods: 6-10GB

## Notes

- The EULA is auto-accepted during deploy
- For modded servers (Forge/Fabric), replace `server.jar` manually and adjust `start.sh`
- World data is in the `world/` directory
- Logs are in `logs/latest.log`
- The process name is `java` since Minecraft runs on the JVM
