# Conan Exiles

Windows dedicated server running via Wine/Proton on Linux.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 7777  | UDP      | Game    |
| 7778  | UDP      | Raw UDP |
| 27015 | UDP      | Query   |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Ensure GE-Proton is installed at the configured path
3. Start the container - SteamCMD will download the server files via the Deploy button
4. Start the server once to generate default config files
5. Edit settings in `ConanSandbox/Saved/Config/WindowsServer/`
6. Restart the server from the panel

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
