# V Rising

Windows dedicated server running via Wine/Proton on Linux.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 9876  | UDP      | Game    |
| 9877  | UDP      | Query   |

## Setup

1. Use the `ghcr.io/meduseld-io/argonath:latest-wine` image in your `docker-compose.yml` (it adds Wine and Xvfb)
2. Set `GAME=vrising` in your `docker-compose.yml` and run `docker compose up -d`
3. Open the panel and click **Deploy** to download the server files via SteamCMD
4. Set your server name and save name in `args` (see Configuration below)
5. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: vrising` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

## Configuration

Server settings are split across launch args and JSON config files:

Launch args in `game.yml`:
- `-persistentDataPath "/game/save-data"` - save location
- `-serverName "MyServer"` - display name
- `-saveName "world1"` - save file name

Config files in `VRisingServer_Data/StreamingAssets/Settings/`:
- `ServerHostSettings.json` - network, name, password, max players
- `ServerGameSettings.json` - gameplay settings (PvP, rates, castle limits)

Key `ServerHostSettings.json` settings:
```json
{
  "Name": "MyServer",
  "Password": "changeme",
  "MaxConnectedUsers": 40,
  "GameSettingsPreset": "StandardPvP",
  "Port": 9876,
  "QueryPort": 9877
}
```

## Notes

- V Rising requires Wine/Proton (no native Linux server)
- RAM usage is typically 6-10GB
- Save data is stored at the `-persistenceDataPath` location
- Game settings presets: `StandardPvP`, `StandardPvE`, `HardcorePvP`
- The server supports both PvP and PvE modes
