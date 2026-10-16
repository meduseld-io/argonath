# Core Keeper

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 27015 | UDP      | Game    |

## Setup

1. Use the `ghcr.io/meduseld-io/argonath:latest-wine` image in your `docker-compose.yml` (it adds Wine and Xvfb)
2. Set `GAME=corekeeper` in your `docker-compose.yml` and run `docker compose up -d`
3. Open the panel and click **Deploy** to download the server files via SteamCMD
4. On first launch, a `GameID.txt` file is generated - this is your server's unique ID
5. Players join using the Game ID (not by IP), so share the contents of `GameID.txt`
6. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: corekeeper` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

## Configuration

Core Keeper server configuration is minimal:

- `ServerConfig.json` (generated on first run) - world settings, max players
- The server generates a Game ID that players use to connect (peer-to-peer style matchmaking through Steam relay)

## Notes

- Core Keeper uses Steam's relay networking - players connect via Game ID, not direct IP
- RAM usage is relatively low (2-4GB)
- World saves are in the `CoreKeeper/` subdirectory
- The server must be fully shut down before backing up saves
