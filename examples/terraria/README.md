# Terraria

Native Linux dedicated server managed via SteamCMD. Compatible with tModLoader for modded servers.

## Ports

| Port | Protocol | Purpose |
| ---- | -------- | ------- |
| 7777 | TCP      | Game    |

## Setup

1. Copy `game.yml` to your Argonath `config/` folder
2. Start the container - SteamCMD will download the server files via the Deploy button
3. Create a `serverconfig.txt` in the server root with your settings
4. Start the server from the panel

## Configuration

Create `serverconfig.txt` in the server directory:

```
world=/game/Worlds/world.wld
worldname=MyWorld
autocreate=2
worldpath=/game/Worlds
difficulty=0
maxplayers=8
port=7777
password=changeme
motd=Welcome!
```

Key settings:
- `autocreate` - world size (1=small, 2=medium, 3=large)
- `difficulty` - 0=classic, 1=expert, 2=master, 3=journey
- `password` - remove the line for public

## Notes

- For tModLoader, use Steam App ID `1281930` instead
- RAM usage is low (1-2GB typically)
- World files are `.wld` in the configured world path
- The server creates a world automatically on first start if none exists
