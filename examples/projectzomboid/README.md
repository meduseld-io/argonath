# Project Zomboid

Native Linux dedicated server managed via SteamCMD. Runs on Java.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 16261 | UDP      | Game    |
| 16262 | UDP      | Game +1 |

## Setup

1. Set `GAME=projectzomboid` in your `docker-compose.yml` and run `docker compose up -d`
2. Open the panel and click **Deploy** to download the server files via SteamCMD
3. Change the admin password: set `-adminpassword` in `args` (the preset uses `changeme`)
4. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: projectzomboid` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

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
- The admin password comes from `-adminpassword` on first start; after that it is stored in the server database
- Workshop mods are supported via `WorkshopItems=` in the server config
- Save data is in `Zomboid/Saves/Multiplayer/`
- The process name is `ProjectZomboid64` (the native launcher that hosts the JVM). Matching `java` would also match any other Java process the panel can see
