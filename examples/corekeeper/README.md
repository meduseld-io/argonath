# Core Keeper

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 27015 | UDP      | Game    |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Start the container - SteamCMD will download the server files via the Deploy button
3. On first launch, a `GameID.txt` file is generated - this is your server's unique ID
4. Players join using the Game ID (not by IP), so share the contents of `GameID.txt`
5. Start the server from the panel

## Configuration

Core Keeper server configuration is minimal:

- `ServerConfig.json` (generated on first run) - world settings, max players
- The server generates a Game ID that players use to connect (peer-to-peer style matchmaking through Steam relay)

## Notes

- Core Keeper uses Steam's relay networking - players connect via Game ID, not direct IP
- RAM usage is relatively low (2-4GB)
- World saves are in the `CoreKeeper/` subdirectory
- The server must be fully shut down before backing up saves
