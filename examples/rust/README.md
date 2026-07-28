# Rust

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 28015 | UDP      | Game    |
| 28016 | TCP      | RCON    |
| 28017 | UDP      | Query   |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Start the container - SteamCMD will download the server files via the Deploy button
3. Edit args in `game.yml` to set your server name, password, map seed, and world size
4. Start the server from the panel

## Configuration

Rust server settings are passed as launch arguments in `game.yml`:

- `+server.hostname "MyServer"` - server name
- `+server.password "changeme"` - password (remove for public)
- `+server.port 28015` - game port
- `+server.queryport 28016` - query port
- `+server.level "Procedural Map"` - map type
- `+server.seed 12345` - map seed (change for different terrain)
- `+server.worldsize 3000` - map size (1000-6000, default 3000)
- `+server.maxplayers 50` - max players

Additional runtime config via `server/rustserver/cfg/server.cfg` and RCON commands.

## Notes

- Rust is very resource-intensive: 8-16GB RAM recommended
- First startup takes several minutes as the map generates
- Map wipes happen on forced updates (first Thursday of each month)
- The server must be shut down cleanly to save data
- Oxide/uMod can be installed for plugins (extract to server root)
- World saves are in `server/rustserver/`
- Player data is in `server/rustserver/player.*.db`
