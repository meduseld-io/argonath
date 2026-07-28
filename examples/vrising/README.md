# V Rising

Windows dedicated server running via Wine/Proton on Linux.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 9876  | UDP      | Game    |
| 9877  | UDP      | Query   |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Ensure GE-Proton is installed at the configured path
3. Start the container - SteamCMD will download the server files via the Deploy button
4. Edit args in `game.yml` to set your server name and save name
5. Start the server from the panel

## Configuration

Server settings are split across launch args and JSON config files:

Launch args in `game.yml`:
- `-persistenceDataPath "/game/save-data"` - save location
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
