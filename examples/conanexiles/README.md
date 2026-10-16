# Conan Exiles

Windows dedicated server running via Wine/Proton on Linux.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 7777  | UDP      | Game    |
| 7778  | UDP      | Raw UDP |
| 27015 | UDP      | Query   |

## Setup

1. Use the `ghcr.io/meduseld-io/argonath:latest-wine` image in your `docker-compose.yml` (it adds Wine and Xvfb)
2. Set `GAME=conanexiles` in your `docker-compose.yml` and run `docker compose up -d`
3. Open the panel and click **Deploy** to download the server files via SteamCMD
4. Start the server once to generate default config files
5. Edit settings in `ConanSandbox/Saved/Config/WindowsServer/`
6. Restart the server from the panel
7. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: conanexiles` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

## Configuration

Config files are in `ConanSandbox/Saved/Config/WindowsServer/`:

- `ServerSettings.ini` - server name, password, max players, PvP/PvE mode
- `Engine.ini` - network settings, tick rate
- `Game.ini` - gameplay overrides (harvest rates, XP multipliers)

Key `ServerSettings.ini` entries:
- `ServerName` - display name
- `ServerPassword` - empty for public
- `MaxPlayers` - max concurrent players (default 40)
- `IsBattlEyeEnabled` - set to `False` for Proton

## Notes

- Conan Exiles uses an internal SQLite database for world state
- BattlEye must be disabled for Wine/Proton
- RAM usage is typically 6-8GB
- Saves are in `ConanSandbox/Saved/` (the `game.db` file is the world)
