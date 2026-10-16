# Unturned

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 27015 | UDP      | Game    |
| 27016 | UDP      | Query   |

## Setup

1. Set `GAME=unturned` in your `docker-compose.yml` and run `docker compose up -d`
2. Open the panel and click **Deploy** to download the server files via SteamCMD
3. The server name in args (`+secureserver/MyServer`) defines the server config folder
4. Create the config directory at `Servers/MyServer/` and add your settings
5. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: unturned` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

## Configuration

Config files live in `Servers/MyServer/`:

- `Server/Commands.dat` - server startup commands
- `Server/Config.json` - advanced server config

Example `Commands.dat`:
```
Name MyServer
Port 27015
MaxPlayers 24
Map PEI
Password changeme
Perspective Both
```

Available maps: `PEI`, `Washington`, `Russia`, `Germany`, `Hawaii`

## Notes

- Unturned is free-to-play so no game purchase needed for clients
- RAM usage is low (2-4GB)
- Workshop mods are supported via the `WorkshopDownloadConfig.json` file
- The server runs with `-batchmode -nographics` for headless operation
- Save data is in `Servers/MyServer/Level/`
