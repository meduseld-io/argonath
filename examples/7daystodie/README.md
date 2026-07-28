# 7 Days to Die

Native Linux dedicated server managed via SteamCMD.

## Ports

| Port  | Protocol | Purpose    |
| ----- | -------- | ---------- |
| 26900 | TCP/UDP  | Game       |
| 26901 | UDP      | Game +1    |
| 26902 | UDP      | Game +2    |
| 8080  | TCP      | Web panel  |
| 8081  | TCP      | Telnet     |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Start the container - SteamCMD will download the server files automatically via the Deploy button
3. On first launch, a default `serverconfig.xml` is generated in the server directory
4. Edit `serverconfig.xml` to set your server name, password, max players, and world settings
5. Start the server from the panel

## Configuration

The main config file is `serverconfig.xml` in the server root. Key settings:

- `ServerName` - display name in the server browser
- `ServerPassword` - empty for public, set a value for private
- `GameWorld` - world name (e.g. `Navezgane` or `RWG` for random gen)
- `WorldGenSeed` - seed for random gen worlds
- `MaxPlayerCount` - max concurrent players

## Notes

- First startup takes a while as the server generates the world
- The server writes logs to `7DaysToDieServer_Data/output_log.txt`
- EAC (Easy Anti-Cheat) is disabled by default on Linux dedicated servers
