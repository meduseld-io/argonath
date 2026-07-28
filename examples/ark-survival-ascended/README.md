# ARK: Survival Ascended

Windows dedicated server running via Wine/Proton on Linux.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 7777  | UDP      | Game    |
| 7778  | UDP      | Raw UDP |
| 27015 | UDP      | Query   |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Ensure GE-Proton is installed at the configured path (see `compatibility.proton_version`)
3. Start the container - SteamCMD will download the server files via the Deploy button
4. Edit args in `game.yml` to set your map, server name, and password
5. Start the server from the panel

## Configuration

Server settings are passed as command-line arguments in `game.yml`:

- First arg is the map and query string: `TheIsland_WP?listen?SessionName=MyServer?ServerPassword=changeme?MaxPlayers=70`
- Available maps: `TheIsland_WP`, `ScorchedEarth_WP`, `Aberration_WP`, `TheCenter_WP`, `Extinction_WP`

Additional config lives in `ShooterGame/Saved/Config/LinuxServer/`:
- `GameUserSettings.ini` - server and game settings
- `Game.ini` - gameplay overrides (rates, taming, etc.)

## Notes

- ARK:SA requires significant RAM (12-16GB recommended)
- First startup is very slow as shaders compile under Proton
- The `-NoBattlEye` flag is required for Wine/Proton compatibility
- World saves are in `ShooterGame/Saved/SavedArks/`
