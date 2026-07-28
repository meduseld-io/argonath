# Valheim

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port | Protocol | Purpose |
| ---- | -------- | ------- |
| 2456 | UDP      | Game    |
| 2457 | UDP      | Game +1 |

## Setup

1. Copy `game.yml` and `start.sh` to your Argonath `config/` folder
2. Start the container - SteamCMD will download the server files via the Deploy button
3. Edit `game.yml` args (or `start.sh`) to set your server name, world name, and password
4. Start the server from the panel

## Configuration

Settings are passed as launch arguments in `start.sh`:

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
