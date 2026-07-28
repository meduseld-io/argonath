# Icarus

Windows dedicated server running via Wine/Proton on Linux.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 17777 | UDP      | Game    |
| 27015 | UDP      | Query   |

## Prerequisites

- GE-Proton must be installed (see `compatibility.proton_version` in `game.yml`)
- Recommended: mount Proton at `/compatibilitytools/GE-Proton10-32` in your Docker setup

## Setup

1. Copy `game.yml` and `start.sh` to your Argonath `config/` folder
2. Ensure GE-Proton is available in the container
3. Start the container - SteamCMD will download the server files via the Deploy button
4. Edit `game.yml` args to set your server name and password
5. Start the server from the panel

## Configuration

Server settings are passed via command-line arguments in `game.yml`:

- `-SteamServerName=MyServer` - server name in the browser
- `-Port=17777` - game port
- `-QueryPort=27015` - Steam query port
- `-Password=changeme` - server password (remove for public)

Additional settings can be configured in `Icarus/Saved/Config/WindowsServer/ServerSettings.ini` after first run.

## Notes

- Icarus requires Proton/Wine as there is no native Linux server
- The `start.sh` script uses tmux to launch the process (required for Argonath process detection)
- A Proton prefix directory is created automatically at `/game/pfx/`
- RAM usage is typically 4-8GB
- Save data (prospect files) are in `Icarus/Saved/PlayerData/`
- First launch creates the Proton prefix which takes a minute or two
