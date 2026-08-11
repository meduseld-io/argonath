<p align="center"><img src="https://github.com/user-attachments/assets/2c5dab06-d116-47d8-bb2e-fa54396dd4b1" alt="Argonath" width="250"></p>

# Argonath

A lightweight, open-source game server management panel with a clean web UI - packaged as a Docker image. Free to use, modify, and distribute under the [MIT license](LICENSE).

Fills the gap between [Pterodactyl](https://pterodactyl.io/) (multi-server, multi-game) and [LinuxGSM](https://linuxgsm.com/) (CLI-based). Argonath is for when you just want a single Docker container with a web UI to manage one dedicated server.

## Features

- **Process management** - Start, stop, restart, force kill with toast notifications
- **Live system stats** - CPU, RAM, disk, temperature with 30-min history charts
- **Player count** - Shows current players when detectable
- **Server logs** - Real-time game server log viewer
- **Startup logs** - Separate panel for launch script output
- **Activity log** - Tracks who did what and when
- **Update detection** - SteamCMD build ID checking, one-click update on restart
- **Health monitoring** - Server state detection (running/offline/crashed)
- **Save backups** - One-click backup of game saves to timestamped .tar.gz archives with auto-cleanup
- **Customisable dashboard** - Drag, drop, and resize any widget. Layout saved per user.
- **Colour themes** - Pick from preset accent colours or use a custom colour picker. Background customisable too.
- **Mobile responsive** - Automatically stacks to single-column on small screens
- **Rate limiting** - Prevent accidental double-starts
- **Simple auth** - Local username/password (first user = admin), or disable auth entirely
- **Docker healthcheck** - Built-in health endpoint for container orchestration

## Quick Start

```bash
# 1. Create project directory
mkdir argonath && cd argonath

# 2. Create subdirectories
mkdir -p config

# 3. Create your config
# Copy an example from the repo's examples/ folder into config/game.yml
# Edit config/game.yml for your game

# 4. Create docker-compose.yml (see Docker Compose section below)

# 5. Run
docker compose up -d
```

Open `http://localhost:5000` - the first user to register becomes admin.

Click **Deploy** to download the game server via SteamCMD. Once complete, click **Start** to launch it. That's it.

> **Headless server?** If you're running on a remote Linux box without a desktop, access the panel from your local machine using an SSH tunnel: `ssh -L 5000:localhost:5000 user@your-server-ip`, then open `http://localhost:5000` in your local browser. Alternatively, put it behind a reverse proxy with a domain (see [Custom Domain](#custom-domain) below).

## What Happens Automatically

After you click Deploy:

- **SteamCMD** downloads and installs the game server files (bundled in the Docker image - no separate install needed)
- **start.sh** is auto-generated for known games (Palworld, Valheim, Satisfactory) with output piped to `server.log`
- **Game logs** are captured to the file specified by `log_file` in your `game.yml` via the generated start script
- **Startup logs** track start/stop/crash events in `/data/startup.log` (internal, always works)
- **Update detection** checks for new Steam builds every hour and shows an "Update Available" badge
- **Process monitoring** detects crashes and updates the panel state automatically
- **Backups** archive the configured `save_dir` to timestamped `.tar.gz` files in `/data/backups/`

For unknown games, the generated `start.sh` contains a template you'll need to edit once with your server executable name.

## Configuration

All configuration lives in a single `config/game.yml` file:

```yaml
game:
  name: "Valheim"
  steam_app_id: "896660"
  process_name: "valheim_server.x86_64"
  launch_script: "/game/start.sh"
  server_dir: "/game"
  log_file: "/game/server.log"
  max_players: 10

auth:
  mode: "local"   # "local" or "none"

steamcmd:
  enabled: true
  install_dir: "/game"
  validate: true

backup:
  enabled: true
  save_dir: "/game/Saved"
  max_keep: 5

compatibility:
  wine: false
```

### Key Fields

| Field | Purpose |
|-------|---------|
| `process_name` | The executable name psutil scans for to detect if the server is running |
| `launch_script` | Path to the start script (auto-generated on deploy for known games) |
| `log_file` | Where game server output is written - the panel's "Server Logs" reads this file |
| `save_dir` | Directory to archive when you click Backup |
| `steam_app_id` | Used by SteamCMD for deploy and update checks |

### How Logs Work

Argonath has two log panels:

- **Server Logs** - reads the file at `log_file` in your `game.yml`. The auto-generated `start.sh` pipes game server stdout/stderr to this file using `tee`. If you write your own start script, make sure it pipes output to this path.
- **Startup Logs** - tracks lifecycle events (start, stop, crash, kill) in `/data/startup.log`. This is managed internally by Argonath and always works.

## Example Configs

The `examples/` directory includes ready-to-use configurations for 20 games, each with a README covering ports, setup steps, and configuration:

**Native Linux:**
Valheim, Satisfactory, Palworld, Project Zomboid, Terraria, Rust, 7 Days to Die, Counter-Strike 2, Core Keeper, Left 4 Dead 2, Don't Starve Together, Unturned

**Wine/Proton required:**
Icarus, Enshrouded, V Rising, ARK: Survival Ascended, Sons of the Forest, Conan Exiles

**Non-Steam (no SteamCMD):**
Minecraft (Java) - auto-deploys via Mojang API, Factorio

## Docker Compose

```yaml
services:
  argonath:
    image: ghcr.io/meduseld-io/argonath:latest
    container_name: argonath
    ports:
      - "5000:5000"
    # pid: host  # Uncomment to monitor a game server running outside the container
    volumes:
      - ./game:/game
      - ./config:/config
      - argonath-data:/data
    environment:
      - TZ=America/New_York
    restart: unless-stopped

volumes:
  argonath-data:
```

> **Already have a game server running?** If you want Argonath to monitor an existing server process (not launched by Argonath), add `pid: host` to the compose file and mount the real game directory instead of `./game`. This lets psutil see host processes.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TZ` | `UTC` | Timezone |
| `SECRET_KEY` | (generated) | Flask session secret |
| `IDLE_SHUTDOWN_MINUTES` | `0` | Auto-stop after N minutes with 0 players (0 = disabled) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Custom Domain

To serve Argonath on a custom domain (e.g. `panel.example.com`), put a reverse proxy in front of it. Here's an example with Nginx:

```nginx
server {
    listen 443 ssl;
    server_name panel.example.com;

    ssl_certificate /etc/letsencrypt/live/panel.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/panel.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

With Caddy (automatic HTTPS):

```
panel.example.com {
    reverse_proxy 127.0.0.1:5000
}
```

Or with Cloudflare Tunnel (no port forwarding needed):

```bash
cloudflared tunnel route dns <tunnel-id> panel.example.com
```

Then add the ingress rule in your tunnel config:

```yaml
ingress:
  - hostname: panel.example.com
    service: http://127.0.0.1:5000
```

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
| `/api/backup` | POST | Create a backup of the save directory |
| `/api/backup/status` | GET | Backup progress and list of archives |
| `/api/backup/download/<file>` | GET | Download a specific backup |
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
    └── /data    → SQLite DB, logs, backups
```

## License

MIT - free to use, modify, and distribute. See [LICENSE](LICENSE) for details.
