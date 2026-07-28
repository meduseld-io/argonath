# Left 4 Dead 2

Native Linux dedicated server (Source engine) managed via SteamCMD.

## Ports

| Port  | Protocol | Purpose  |
| ----- | -------- | -------- |
| 27015 | TCP/UDP  | Game     |
| 27020 | UDP      | SourceTV |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Start the container - SteamCMD will download the server files via the Deploy button
3. Edit args in `game.yml` to set your starting map and max players
4. Start the server from the panel

## Configuration

Server settings are primarily via launch args in `game.yml`:

- `-game left4dead2` - required, specifies the game
- `+map` - starting map (e.g. `c1m1_hotel`, `c2m1_highway`, `c5m1_waterfront`)
- `+maxplayers` - max players (4 survivors + extras for versus/scavenge)
- `-port` - game port

Additional config via `left4dead2/cfg/server.cfg`:
```
hostname "MyServer"
sv_password "changeme"
sv_lan 0
```

## Notes

- L4D2 dedicated server is lightweight (1-2GB RAM)
- The server runs the Source Dedicated Server (`srcds_linux`)
- Custom campaigns go in `left4dead2/addons/`
- SourceMod and MetaMod can be installed for server plugins
- Maps: `c1m1` through `c14m2` cover all official campaigns
