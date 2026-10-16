# Terraria

Native Linux dedicated server. The server isn't available through anonymous SteamCMD, so you download it once from terraria.org. Compatible with tModLoader for modded servers.

## Ports

| Port | Protocol | Purpose |
| ---- | -------- | ------- |
| 7777 | TCP      | Game    |

## Setup

1. Set `GAME=terraria` in your `docker-compose.yml` and run `docker compose up -d`
2. Download the dedicated server zip from https://terraria.org (link at the bottom of the page, "PC Dedicated Server") and copy the contents of its `Linux` folder into your `game/` folder
3. Create a `serverconfig.txt` in the server root with your settings
4. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: terraria` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

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
