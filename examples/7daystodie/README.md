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

1. Set `GAME=7daystodie` in your `docker-compose.yml` and run `docker compose up -d`
2. Open the panel and click **Deploy** to download the server files via SteamCMD
3. On first launch, a default `serverconfig.xml` is generated in the server directory
4. Edit `serverconfig.xml` to set your server name, password, max players, and world settings
5. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: 7daystodie` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

## Configuration

The main config file is `serverconfig.xml` in the server root. Key settings:

- `ServerName` - display name in the server browser
- `ServerPassword` - empty for public, set a value for private
- `GameWorld` - world name (e.g. `Navezgane` or `RWG` for random gen)
- `WorldGenSeed` - seed for random gen worlds
- `MaxPlayerCount` - max concurrent players

## Notes

- First startup takes a while as the server generates the world
- The server writes logs to `logs/output_log.txt`, and saves to `.local/share/7DaysToDie` in the game folder
- EAC (Easy Anti-Cheat) is disabled by default on Linux dedicated servers
