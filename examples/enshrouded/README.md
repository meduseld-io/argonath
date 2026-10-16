# Enshrouded

Windows dedicated server running via Wine/Proton on Linux.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 15636 | UDP      | Game    |
| 15637 | UDP      | Query   |

## Setup

1. Use the `ghcr.io/meduseld-io/argonath:latest-wine` image in your `docker-compose.yml` (it adds Wine and Xvfb)
2. Set `GAME=enshrouded` in your `docker-compose.yml` and run `docker compose up -d`
3. Open the panel and click **Deploy** to download the server files via SteamCMD
4. On first launch, a `enshrouded_server.json` config is generated
5. Edit the config to set your server name, password, and settings
6. Restart the server from the panel
7. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: enshrouded` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

## Configuration

The main config file is `enshrouded_server.json` in the server root:

```json
{
  "name": "MyServer",
  "password": "changeme",
  "saveDirectory": "./savegame",
  "logDirectory": "./logs",
  "ip": "0.0.0.0",
  "gamePort": 15636,
  "queryPort": 15637,
  "slotCount": 16
}
```

## Notes

- Enshrouded requires Wine/Proton as there is no native Linux server binary
- RAM usage is typically 8-12GB
- The server can take 2-3 minutes to fully start under Proton
- World saves are in the `savegame/` directory
- Max players is 16 (hard limit by the game)
