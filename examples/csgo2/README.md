# Counter-Strike 2

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 27015 | TCP/UDP  | Game    |
| 27020 | UDP      | SourceTV|

## Prerequisites

You need a **Game Server Login Token (GSLT)** from Valve:
1. Go to https://steamcommunity.com/dev/managegameservers
2. Create a new token for App ID `730`
3. Replace `YOUR_GSLT_TOKEN` in `game.yml` args with your token

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Get a GSLT token (see above) and update the args
3. Start the container - SteamCMD will download the server files via the Deploy button
4. Start the server from the panel

## Configuration

Server settings are primarily in the launch args in `game.yml`:

- `+game_type` and `+game_mode` - determines the game mode:
  - `0/0` = Casual, `0/1` = Competitive, `1/0` = Arms Race, `1/1` = Demolition
- `+map` - starting map (e.g. `de_dust2`, `de_mirage`, `de_inferno`)
- `+sv_setsteamaccount` - your GSLT token

Additional config via `csgo/cfg/server.cfg` and `csgo/cfg/gamemode_*.cfg`.

## Notes

- A GSLT token is mandatory - the server won't appear in the browser without one
- CS2 updates frequently - expect SteamCMD validation on restarts
- RAM usage is typically 2-4GB
- The server App ID for SteamCMD is `730` (same as the client)
