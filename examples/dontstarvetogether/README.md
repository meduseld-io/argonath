# Don't Starve Together

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port  | Protocol | Purpose       |
| ----- | -------- | ------------- |
| 10999 | UDP      | Game (Master) |
| 11000 | UDP      | Game (Caves)  |

## Prerequisites

You need a **Cluster Token** from Klei:
1. Open Don't Starve Together on your PC
2. Press `~` to open the console
3. Type `TheNet:GenerateClusterToken()`
4. The token is saved to your clipboard and to `cluster_token.txt` in your DST data folder

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Start the container - SteamCMD will download the server files via the Deploy button
3. Create the cluster directory structure:
   ```
   /game/.klei/DoNotStarveTogether/Cluster_1/
   ├── cluster.ini
   ├── cluster_token.txt
   └── Master/
       └── server.ini
   ```
4. Paste your cluster token into `cluster_token.txt`
5. Start the server from the panel

## Configuration

- `cluster.ini` - cluster-wide settings (name, password, game mode, max players)
- `Master/server.ini` - shard-specific settings (port, is_master)
- `Master/worldgenoverride.lua` - world generation settings

Key `cluster.ini` settings:
```ini
[GAMEPLAY]
game_mode = survival
max_players = 6
pvp = false

[NETWORK]
cluster_name = MyServer
cluster_password = changeme
```

## Notes

- This config runs the Overworld (Master) shard only - no caves
- For caves, you'd need a second instance (separate shard with `is_master = false`)
- The cluster token is tied to your Klei account
- Mods are configured in `Master/modoverrides.lua`
- Save data is in `.klei/DoNotStarveTogether/Cluster_1/Master/save/`
