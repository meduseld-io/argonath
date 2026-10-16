# Icarus

Windows dedicated server running via Wine/Proton on Linux.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 17777 | UDP      | Game    |
| 27015 | UDP      | Query   |

## Setup

1. Use the `ghcr.io/meduseld-io/argonath:latest-wine` image in your `docker-compose.yml` (it adds Wine and Xvfb)
2. Set `GAME=icarus` in your `docker-compose.yml` and run `docker compose up -d`
3. Open the panel and click **Deploy** to download the server files via SteamCMD
4. Set your server name and password in `args` (see Configuration below)
5. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: icarus` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

## Configuration

Server settings are passed via command-line arguments in `game.yml`:

- `-SteamServerName=MyServer` - server name in the browser
- `-Port=17777` - game port
- `-QueryPort=27015` - Steam query port
- `-Password=changeme` - server password (remove for public)

Additional settings can be configured in `Icarus/Saved/Config/WindowsServer/ServerSettings.ini` after first run.

## Notes

- Icarus requires Proton/Wine as there is no native Linux server
- A Wine prefix is created automatically at `/game/.wine/`
- RAM usage is typically 4-8GB
- Save data (prospect files) are in `Icarus/Saved/PlayerData/`
- First launch creates the Wine prefix, which takes a minute or two
