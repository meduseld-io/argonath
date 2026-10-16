# Minecraft Java Edition

Vanilla Minecraft server. Uses Mojang's version manifest API for automatic deploy and update detection - no SteamCMD needed. Deploy also downloads the Java runtime the release needs into `/game/jre`, so the base image stays small.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 25565 | TCP      | Game    |
| 25575 | TCP      | RCON    |

## Setup

1. Set `GAME=minecraft` in your `docker-compose.yml` and run `docker compose up -d`
2. Open the panel and click **Deploy**. It downloads the latest `server.jar` from Mojang and the Java runtime it needs, and accepts the EULA
3. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: minecraft` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

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

The preset allocates 4GB max / 1GB min. Adjust `-Xmx` and `-Xms` in `args` (in `config/game.yml`) based on your available RAM:

- 1-5 players: 2-4GB
- 5-10 players: 4-6GB
- 10-20 players with mods: 6-10GB

## Notes

- The EULA is auto-accepted during deploy
- For modded servers (Forge/Fabric), replace `server.jar` manually and adjust `args`
- World data is in the `world/` directory
- Logs are in `logs/latest.log` (written by Minecraft); raw console output goes to `logs/console.log`
- The process name is `server.jar` rather than `java`, so other Java processes are never matched (or killed)
