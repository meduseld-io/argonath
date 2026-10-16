# Factorio

Native Linux headless server. Does not use SteamCMD - download the official headless binary directly from Factorio's website.

## Ports

| Port  | Protocol | Purpose |
| ----- | -------- | ------- |
| 34197 | UDP      | Game    |

## Prerequisites

Download the headless server binary:
1. Go to https://www.factorio.com/download (select "Headless" and "Linux64")
2. You need a Factorio account (the game must be registered to it)
3. Extract the archive contents into your game directory

## Setup

1. Set `GAME=factorio` in your `docker-compose.yml` and run `docker compose up -d`
2. Create a world save:
   ```
   docker exec -it argonath /game/bin/x64/factorio --create /game/saves/world.zip
   ```
3. Edit `data/server-settings.json` with your server name and settings
4. Click **Start**

To change settings such as the server name, password or ports, create `config/game.yml` with `preset: factorio` and only the fields you want to change (for example `game:` → `args:`). It is applied on top of the built-in preset; see [game.yml](game.yml) for everything the preset sets.

## Configuration

- `data/server-settings.json` - server name, description, visibility, password, autosave settings
- `data/map-gen-settings.json` - world generation (resource richness, map size, etc.)
- `data/map-settings.json` - runtime map settings (pollution, evolution, enemy expansion)

Key server settings:
```json
{
  "name": "MyServer",
  "description": "A Factorio server",
  "visibility": {"public": false, "lan": true},
  "game_password": "changeme",
  "autosave_interval": 5,
  "autosave_slots": 3
}
```

## Notes

- Factorio is very CPU-efficient - a single core can handle large bases
- RAM usage scales with factory size (2-8GB typical)
- Mods go in `mods/` directory - must match client mod versions exactly
- The server writes its own log to `factorio-current.log`
