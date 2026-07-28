# Enshrouded

Windows dedicated server running via Wine/Proton on Linux.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 15636 | UDP      | Game    |
| 15637 | UDP      | Query   |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Ensure GE-Proton is installed at the configured path
3. Start the container - SteamCMD will download the server files via the Deploy button
4. On first launch, a `enshrouded_server.json` config is generated
5. Edit the config to set your server name, password, and settings
6. Restart the server from the panel

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
