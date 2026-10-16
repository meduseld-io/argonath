# Satisfactory

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 7777  | UDP      | Game    |
| 15000 | UDP      | Beacon  |
| 15777 | UDP      | Query   |

## Setup

1. Set `GAME=satisfactory` in your `docker-compose.yml` and run `docker compose up -d`
2. Open the panel and click **Deploy** to download the server files via SteamCMD
3. On first connection, a player will be prompted to "claim" the server and set an admin password
4. Server settings are then configured in-game via the Server Manager UI
5. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: satisfactory` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

## Configuration

Satisfactory uses in-game configuration rather than config files. After claiming the server:

1. Connect to the server as a client
2. Open Server Manager (from the main menu or in-game)
3. Set server name, password, auto-save interval, etc.

Config files (after first run) are in `FactoryGame/Saved/Config/LinuxServer/`:
- `GameUserSettings.ini` - graphics and game settings
- `Scalability.ini` - performance settings

## Notes

- Satisfactory requires 6-12GB RAM depending on factory complexity
- The server uses `FactoryServer.sh` as the launch script (included with the download)
- Max players is 4 (hard limit by the game)
- Save files can be large (100MB+) for complex factories
- World saves are in `FactoryGame/Saved/SaveGames/server/`
- The server claims process only happens once per install
