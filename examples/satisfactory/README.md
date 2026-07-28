# Satisfactory

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 7777  | UDP      | Game    |
| 15000 | UDP      | Beacon  |
| 15777 | UDP      | Query   |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Start the container - SteamCMD will download the server files via the Deploy button
3. Start the server from the panel
4. On first connection, a player will be prompted to "claim" the server and set an admin password
5. Server settings are then configured in-game via the Server Manager UI

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
