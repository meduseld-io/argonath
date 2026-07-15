<p align="center"><img src="https://github.com/user-attachments/assets/2c5dab06-d116-47d8-bb2e-fa54396dd4b1" alt="Argonath" width="250"></p>

# Argonath

A lightweight, single-game server management panel with a clean web UI - packaged as a Docker image.

Fills the gap between Pterodactyl (complex, overkill for one game) and LinuxGSM (CLI-only, no UI). A simple Docker container that gives you start/stop/restart/kill controls, live system stats, server logs, and update management for any Steam-based dedicated server.

## Features

- **Process management** - Start, stop, restart, force kill with toast notifications
- **Live system stats** - CPU, RAM, disk, temperature with 30-min history charts
- **Player count** - Shows current players when detectable
- **Server logs** - Real-time game server log viewer
- **Startup logs** - Separate panel for launch script output
- **Activity log** - Tracks who did what and when
- **Update detection** - SteamCMD build ID checking, one-click update on restart
- **Health monitoring** - Server state detection (running/offline/crashed)
- **Customisable dashboard** - Drag, drop, and resize any widget. Layout saved per user.
- **Colour themes** - Pick from preset accent colours or use a custom colour picker. Background customisable too.
- **Mobile responsive** - Automatically stacks to single-column on small screens
- **Rate limiting** - Prevent accidental double-starts
- **Simple auth** - Local username/password (first user = admin), or disable auth entirely
- **Docker healthcheck** - Built-in health endpoint for container orchestration

## Quick Start

```bash
# 1. Create directories
mkdir -p config game

# 2. Create your config
cp config/game.yml.example config/game.yml
# Edit config/game.yml for your game

# 3. Run
docker compose up -d
```

Open `http://localhost:5000` - the first user to register becomes admin.

## Configuration

All configuration lives in a single `config/game.yml` file:

```yaml
game:
  name: "Valheim"
  steam_app_id: "896660"
  process_name: "valheim_server.x86_64"
  launch_script: "/game/start.sh"
  server_dir: "/game"
  log_file: "/game/logs/valheim.log"
  max_players: 10

auth:
  mode: "local"   # "local" or "none"

steamcmd:
  enabled: true
  install_dir: "/game"
  validate: true

compatibility:
  wine: false
```

## Example Configs

The `examples/` directory includes ready-to-use configurations for 22 games:

**Native Linux:**
Valheim, Satisfactory, Palworld, Project Zomboid, Terraria, Rust, 7 Days to Die, Counter-Strike 2, Core Keeper, Left 4 Dead 2, Don't Starve Together, Unturned, Arma 3

**Wine/Proton required:**
Icarus, Enshrouded, V Rising, ARK: Survival Ascended, Sons of the Forest, Conan Exiles, Astroneer

**Non-Steam (no SteamCMD):**
Minecraft (Java), Factorio

## Docker Compose

```yaml
services:
  panel:
    image: ghcr.io/meduseld-io/argonath:latest
    ports:
      - "5000:5000"
    volumes:
      - ./game:/game
      - ./config:/config
      - panel-data:/data
    environment:
      - TZ=America/New_York
    restart: unless-stopped

volumes:
  panel-data:
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TZ` | `UTC` | Timezone |
| `SECRET_KEY` | (generated) | Flask session secret |
| `IDLE_SHUTDOWN_MINUTES` | `0` | Auto-stop after N minutes with 0 players (0 = disabled) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Dashboard Customisation

Click the gear icon in the header to open settings:

- **Accent colour** - 10 presets (Stone, Gold, Blue, Teal, Green, Purple, Red, Orange, Pink, Cyan) plus a custom picker
- **Background** - 8 dark presets (Charcoal, Midnight, Deep Green, Navy, Slate, Dark Brown, Pure Black, Warm Grey) plus a custom picker
- **Layout lock** - Uncheck to drag and resize widgets freely, recheck to lock in place

All preferences are saved to your browser's localStorage and persist across sessions. Click "Reset All" to restore defaults.

## Auth Modes

- **`local`** (default) - Username/password accounts. First user to register becomes admin. Admins can start/stop/restart. Viewers can only see stats and logs.
- **`none`** - No authentication. Use when behind a VPN or reverse proxy that handles auth.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Public health check |
| `/api/stats` | GET | System + server stats + player count |
| `/api/history` | GET | 30-min stats history |
| `/api/logs` | GET | Game server logs |
| `/api/startup-logs` | GET | Startup/shutdown log |
| `/api/activity` | GET | Recent activity log |
| `/api/start` | POST | Start server |
| `/api/stop` | POST | Stop server |
| `/api/restart` | POST | Restart (with update) |
| `/api/kill` | POST | Force kill |
| `/api/check-update` | GET | Check for Steam updates |

## Architecture

```
docker container
├── Flask app (port 5000)
│   ├── Web UI (gridstack.js dashboard)
│   ├── Process manager (subprocess + psutil)
│   ├── Stats collector (background thread)
│   └── SQLite database (users, activity log)
└── volumes
    ├── /game    → game server files
    ├── /config  → game.yml
    └── /data    → SQLite DB, logs
```

## License

MIT
