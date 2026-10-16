# Sons of the Forest

Windows dedicated server running via Wine/Proton on Linux.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 8766  | UDP      | Game    |
| 27016 | UDP      | Query   |

## Setup

1. Use the `ghcr.io/meduseld-io/argonath:latest-wine` image in your `docker-compose.yml` (it adds Wine and Xvfb)
2. Set `GAME=theforest` in your `docker-compose.yml` and run `docker compose up -d`
3. Open the panel and click **Deploy** to download the server files via SteamCMD
4. On first launch, a `dedicatedserver.cfg` is generated
5. Edit the config to set your server name, password, and settings
6. Restart the server from the panel
7. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: theforest` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

## Configuration

The config file is `dedicatedserver.cfg` (JSON format):

```json
{
  "IpAddress": "0.0.0.0",
  "GamePort": 8766,
  "QueryPort": 27016,
  "ServerName": "MyServer",
  "MaxPlayers": 8,
  "Password": "changeme",
  "AdminPassword": "admin"
}
```

## Notes

- Sons of the Forest requires Wine/Proton (no native Linux server)
- RAM usage is typically 4-8GB
- Save data is in `save-data/`
- The game folder name is `theforest` but the config is for Sons of the Forest (the sequel)
- Max 8 players (hard limit by the game)
