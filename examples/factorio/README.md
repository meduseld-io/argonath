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

1. Copy `game.yml` and `start.sh` to your Argonath `config/` folder
2. Download and extract the Factorio headless binary into `/game/`
3. Create a world save:
   ```
   ./bin/x64/factorio --create /game/saves/world.zip
   ```
4. Edit `data/server-settings.json` with your server name and settings
5. Start the server from the panel

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
