# Valheim

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port | Protocol | Purpose |
| ---- | -------- | ------- |
| 2456 | UDP      | Game    |
| 2457 | UDP      | Game +1 |

## Setup

1. Set `GAME=valheim` in your `docker-compose.yml` and run `docker compose up -d`
2. Open the panel and click **Deploy** to download the server files via SteamCMD
3. Set your server name, world name, and password in `args` (see Configuration below)
4. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: valheim` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

## Configuration

Settings are passed as launch arguments in `args`:

- `-name "MyServer"` - server name in the browser
- `-port 2456` - game port
- `-world "Dedicated"` - world file name (creates new if doesn't exist)
- `-password "changeme"` - password (minimum 5 characters, cannot be contained in server name)
- `-savedir "/game/saves"` - save directory
- `-public 1` - list in server browser (0 to hide)

## Notes

- Valheim's password must be at least 5 characters and cannot be part of the server name
- RAM usage is typically 2-4GB
- The `SteamAppId=892970` environment variable is required (the game's client App ID, not the server's)
- World saves are `.db` and `.fwl` files in the save directory
- First world generation takes 1-2 minutes
- Crossplay is enabled by default in recent versions
