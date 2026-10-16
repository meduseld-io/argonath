# Rust

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 28015 | UDP      | Game    |
| 28016 | TCP      | RCON    |
| 28017 | UDP      | Query   |

## Setup

1. Set `GAME=rust` in your `docker-compose.yml` and run `docker compose up -d`
2. Open the panel and click **Deploy** to download the server files via SteamCMD
3. Set your server name, password, map seed, and world size in `args` (see Configuration below)
4. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: rust` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

## Configuration

Rust server settings are passed as launch arguments in `game.yml`:

- `+server.hostname "MyServer"` - server name
- `+server.password "changeme"` - password (remove for public)
- `+server.port 28015` - game port
- `+server.queryport 28017` - query port
- `+server.level "Procedural Map"` - map type
- `+server.seed 12345` - map seed (change for different terrain)
- `+server.worldsize 3000` - map size (1000-6000, default 3000)
- `+server.maxplayers 50` - max players

Additional runtime config via `server/argonath/cfg/server.cfg` and RCON commands.

## Notes

- Rust is very resource-intensive: 8-16GB RAM recommended
- First startup takes several minutes as the map generates
- Map wipes happen on forced updates (first Thursday of each month)
- The server must be shut down cleanly to save data
- Oxide/uMod can be installed for plugins (extract to server root)
- World saves are in `server/argonath/`
- Player data is in `server/argonath/player.*.db`
