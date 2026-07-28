# Sons of the Forest

Windows dedicated server running via Wine/Proton on Linux.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 8766  | UDP      | Game    |
| 27016 | UDP      | Query   |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Ensure GE-Proton is installed at the configured path
3. Start the container - SteamCMD will download the server files via the Deploy button
4. On first launch, a `dedicatedserver.cfg` is generated
5. Edit the config to set your server name, password, and settings
6. Restart the server from the panel

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
