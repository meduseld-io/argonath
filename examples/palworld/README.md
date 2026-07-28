# Palworld

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 8211  | UDP      | Game    |
| 27015 | UDP      | Query   |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Start the container - SteamCMD will download the server files via the Deploy button
3. Start the server once to generate default config files
4. Edit `Pal/Saved/Config/LinuxServer/PalWorldSettings.ini` with your settings
5. Restart the server from the panel

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
