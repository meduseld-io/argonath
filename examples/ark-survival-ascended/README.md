# ARK: Survival Ascended

Windows dedicated server running via Wine/Proton on Linux.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 7777  | UDP      | Game    |
| 7778  | UDP      | Raw UDP |
| 27015 | UDP      | Query   |

## Setup

1. Use the `ghcr.io/meduseld-io/argonath:latest-wine` image in your `docker-compose.yml` (it adds Wine and Xvfb)
2. Set `GAME=ark-survival-ascended` in your `docker-compose.yml` and run `docker compose up -d`
3. Open the panel and click **Deploy** to download the server files via SteamCMD
4. Set your map, server name, and password in `args` (see Configuration below)
5. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: ark-survival-ascended` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

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
