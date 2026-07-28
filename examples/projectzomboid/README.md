# Project Zomboid

Native Linux dedicated server managed via SteamCMD. Runs on Java.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 16261 | UDP      | Game    |
| 16262 | UDP      | Game +1 |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Start the container - SteamCMD will download the server files via the Deploy button
3. The server uses `start-server.sh` (included with the download) as its launch script
4. On first launch, you'll need to set an admin password via the server console
5. Start the server from the panel

## Configuration

Config files are in `Zomboid/Server/`:

- `servertest.ini` (or `MyServer.ini` matching your `-servername` arg) - all server settings
- `servertest_SandboxVars.lua` - gameplay settings (zombie count, loot respawn, etc.)
- `servertest_spawnpoints.lua` - custom spawn locations
- `servertest_spawnregions.lua` - spawn region definitions

Key server settings:
- `ServerName` - display name
- `Password` - server password (empty for public)
- `MaxPlayers` - max concurrent players
- `PVP` - enable/disable PvP
- `SteamScoreboard` - show in Steam server browser

## Notes

- Project Zomboid runs on Java (bundled with the server download)
- RAM usage is typically 4-8GB
- The server generates its admin password on first run - check the console output
- Workshop mods are supported via `WorkshopItems=` in the server config
- Save data is in `Zomboid/Saves/Multiplayer/`
- The process name is `java` since PZ runs on the JVM
