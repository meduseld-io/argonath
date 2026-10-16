# Palworld

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 8211  | UDP      | Game    |
| 27015 | UDP      | Query   |

## Setup

1. Set `GAME=palworld` in your `docker-compose.yml` and run `docker compose up -d`
2. Open the panel and click **Deploy** to download the server files via SteamCMD
3. Start the server once to generate default config files
4. Edit `Pal/Saved/Config/LinuxServer/PalWorldSettings.ini` with your settings
5. Restart the server from the panel
6. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: palworld` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

## Configuration

The main config file is `Pal/Saved/Config/LinuxServer/PalWorldSettings.ini`. It contains a single `OptionSettings=(...)` line with all settings comma-separated:

Key settings:
- `ServerName="MyServer"` - display name
- `ServerPassword=""` - empty for public
- `AdminPassword="admin"` - RCON/admin password
- `ServerPlayerMaxNum=32` - max players
- `PublicPort=8211` - game port
- `bIsMultiplay=True` - enable multiplayer

Other useful settings:
- `ExpRate=1.0` - XP multiplier
- `PalCaptureRate=1.0` - capture rate multiplier
- `DeathPenalty=All` - what drops on death (`None`, `Item`, `ItemAndEquipment`, `All`)

## Notes

- Palworld's Linux server is native (no Wine needed)
- RAM usage is typically 8-16GB depending on player count and base complexity
- The server does not write to `Pal/Saved/Logs/` despite the `-log` flag - stdout is the actual log
- Save data is in `Pal/Saved/SaveGames/0/<WorldID>/`
- The performance flags (`-useperfthreads`, `-NoAsyncLoadingThread`, `-UseMultithreadForDS`) are recommended by the devs
- Backup config is included - saves are in `Pal/Saved/`
