<p align="center"><img src="https://github.com/user-attachments/assets/2c5dab06-d116-47d8-bb2e-fa54396dd4b1" alt="Argonath" width="250"></p>

# Argonath

A lightweight, open-source game server management panel with a clean web UI - packaged as a Docker image. Free to use, modify, and distribute under the [MIT license](LICENSE).

Fills the gap between [Pterodactyl](https://pterodactyl.io/) (multi-server, multi-game) and [LinuxGSM](https://linuxgsm.com/) (CLI-based). Argonath is for when you just want a single Docker container with a web UI to manage one dedicated server.

## Features

- **Process management** - Start, stop, restart, force kill with toast notifications
- **Live system stats** - CPU, RAM, disk, temperature with 30-min history charts
- **Player count** - Shows current players when detectable
- **Server logs** - Real-time game server log viewer
- **Startup logs** - Separate panel for start, stop and crash events
- **Activity log** - Tracks who did what and when
- **Update detection** - SteamCMD build ID checking, one-click update on restart
- **Health monitoring** - Server state detection (running/offline/crashed)
- **Save backups** - One-click backup of game saves to timestamped .tar.gz archives with auto-cleanup
- **Customisable dashboard** - Drag, drop, and resize any widget. Layout saved per user.
- **Colour themes** - Pick from preset accent colours or use a custom colour picker. Background customisable too.
- **Mobile responsive** - Automatically stacks to single-column on small screens
- **Rate limiting** - Prevent accidental double-starts
- **Simple auth** - Local username/password (first user = admin, registration then closes unless enabled), or disable auth entirely
- **Docker healthcheck** - Built-in health endpoint for container orchestration

## Quick Start

On any Linux server with Docker:

```bash
mkdir argonath && cd argonath
curl -fsSLO https://raw.githubusercontent.com/meduseld-io/argonath/main/docker-compose.yml
# Edit GAME= in docker-compose.yml (valheim, palworld, minecraft, rust... see the list below)
docker compose up -d
```

Open `http://<your-server>:5000`. The first user to register becomes admin. Click **Deploy** to download the game server, then **Start**. That's it: no config files or start scripts to write.

To change the server name, password or anything else, create `config/game.yml` with only what you want to change. It's applied on top of the built-in preset:

```yaml
preset: valheim
game:
  args: ["-name", "My Viking Server", "-port", "2456", "-world", "Midgard", "-password", "secret123",
         "-savedir", "/game/saves", "-public", "1"]
```

Restart the container after editing it (`docker compose restart`).

> **Headless server?** Access the panel from your own machine with an SSH tunnel: `ssh -L 5000:localhost:5000 user@your-server-ip`, then open `http://localhost:5000`. Or put it behind a reverse proxy with a domain (see [Custom Domain](#custom-domain) below).

## Supported Games

Each preset has a README in `examples/<name>/` with ports, setup steps and game-specific settings. Use the folder name as `GAME`.

| Game | `GAME=` | Image | Notes |
|------|---------|-------|-------|
| 7 Days to Die | `7daystodie` | `latest` | |
| Counter-Strike 2 | `csgo2` | `latest` | Needs a GSLT token |
| Don't Starve Together | `dontstarvetogether` | `latest` | Needs a Klei cluster token |
| Factorio | `factorio` | `latest` | Download the headless server once (not on SteamCMD) |
| Left 4 Dead 2 | `left4dead2` | `latest` | |
| Minecraft (Java) | `minecraft` | `latest` | Deploys via Mojang; Java is downloaded automatically |
| Palworld | `palworld` | `latest` | |
| Project Zomboid | `projectzomboid` | `latest` | |
| Rust | `rust` | `latest` | |
| Satisfactory | `satisfactory` | `latest` | |
| Terraria | `terraria` | `latest` | Download the server once from terraria.org |
| Unturned | `unturned` | `latest` | |
| Valheim | `valheim` | `latest` | |
| Core Keeper | `corekeeper` | `latest-wine` | Native, but needs Xvfb from the Wine image |
| Enshrouded | `enshrouded` | `latest-wine` | Windows server under Wine |
| V Rising | `vrising` | `latest-wine` | Windows server under Wine |
| ARK: Survival Ascended | `ark-survival-ascended` | `latest-wine` | Windows server under Wine, experimental |
| Conan Exiles | `conanexiles` | `latest-wine` | Windows server under Wine, experimental |
| Icarus | `icarus` | `latest-wine` | Windows server under Wine, experimental |
| Sons of the Forest | `theforest` | `latest-wine` | Windows server under Wine, experimental |

### Images

- `ghcr.io/meduseld-io/argonath:latest` - small image for native Linux servers (SteamCMD included)
- `ghcr.io/meduseld-io/argonath:latest-wine` - adds Wine and Xvfb for Windows-only servers. Set `compatibility.proton_version` and mount GE-Proton at `/compatibilitytools` if you prefer Proton.

## What Happens Automatically

- **Deploy** downloads the game with SteamCMD (or Mojang for Minecraft, including a matching Java runtime)
- **Start** launches the game's executable directly with the preset's arguments and environment. Its console output goes to `console_log`, which the panel shows when the game has no log file of its own
- **Stop** asks the server to shut down cleanly so it can save, and force kills it only after `stop_timeout`
- **Update detection** checks for new builds every hour, shows an "Update Available" badge, and updates on the next start or restart
- **Process monitoring** detects crashes and updates the panel state
- **Backups** archive `save_dir` to timestamped `.tar.gz` files in `/data/backups/`
- **Files stay yours**: Argonath and the game run as `PUID`/`PGID` (default 1000), so `./game` on the host isn't owned by root

## Configuration

`config/game.yml` is optional when you use a preset. Everything you put in it overrides the preset (lists like `args` are replaced, not merged). To run a game that has no preset, write the whole file yourself:

```yaml
game:
  name: "My Game"
  steam_app_id: "123456"            # SteamCMD app ID of the dedicated server
  executable: "MyServer.x86_64"     # relative to server_dir
  process_name: "MyServer.x86_64"   # used to detect that the server is running
  args: ["-port", "27015"]
  env:
    LD_LIBRARY_PATH: "./linux64:$LD_LIBRARY_PATH"
  log_file: "/game/server.log"
  port: 27015
  port_protocol: "udp"

backup:
  save_dir: "/game/saves"
```

### Key Fields

| Field | Purpose |
|-------|---------|
| `preset` | Built-in game preset to start from (same as the `GAME` environment variable) |
| `executable` | Program Argonath runs, relative to `server_dir` (default `/game`) |
| `args` | Arguments passed to the executable |
| `env` | Extra environment variables. `$VAR` refers to the existing value |
| `working_dir` | Folder to run in, relative to `server_dir` (default: `server_dir`) |
| `process_name` | Text in the command line that identifies the running server process |
| `log_file` | File shown in the panel's Server Logs. Defaults to `console_log` |
| `console_log` | Where the game's console output is written (default `<server_dir>/console.log`) |
| `xvfb` | Run under a virtual display (needs the `latest-wine` image) |
| `launch_script` | Run this script instead of `executable` (for custom setups) |
| `steam_app_id` | SteamCMD app ID for deploy and update checks |
| `port` / `port_protocol` | Game port and `udp`/`tcp` for the "Port open" check and the address shown in the panel. Otherwise parsed from `args` (`-port=N`, `-port N`, `+server.port N`) |
| `query_port` | Steam query port used for the player count (default `27015`) |
| `stop_timeout` | Seconds Stop/Restart wait for the server to save and exit before force killing it (default `60`) |
| `backup.save_dir` | Directory to archive when you click Backup |
| `steamcmd.platform` | `windows` to download Windows builds (set automatically when `compatibility.wine` is on) |
| `compatibility.wine` | Run the executable with Wine (needs the `latest-wine` image) |
| `auth.allow_registration` | Let more people sign up as viewers after the first admin (default `false`) |

### How Logs Work

Argonath has two log panels:

- **Server Logs** - shows `log_file`. For most games that's the console output Argonath captures; for games that write their own log (Minecraft, Unreal and Unity servers), the preset points it at that file.
- **Startup Logs** - lifecycle events (start, stop, crash, kill) in `/data/startup.log`. If a start fails, the reason is here.

## Docker Compose

```yaml
services:
  argonath:
    image: ghcr.io/meduseld-io/argonath:latest
    container_name: argonath
    network_mode: host
    volumes:
      - ./game:/game
      - ./config:/config
      - argonath-data:/data
    environment:
      - GAME=valheim
      - PUID=1000
      - PGID=1000
      - TZ=America/New_York
    restart: unless-stopped

volumes:
  argonath-data:
```

`network_mode: host` makes the game's ports reachable without listing them and lets Steam's server browser find the server. Remember to open the game's ports in your firewall (each game README lists them). If you'd rather use Docker's bridge network, replace `network_mode: host` with a `ports:` list containing `5000:5000` and the game's ports from its README, e.g. `- "2456-2457:2456-2457/udp"` for Valheim.

> **Already have a game server running?** To monitor a server process that Argonath didn't launch, add `pid: host` to the compose file and mount the real game directory instead of `./game`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GAME` | (none) | Built-in preset to use, e.g. `valheim` |
| `PUID` / `PGID` | `1000` | User and group the panel and game run as. Use `id` on the host to find yours; `0` runs as root |
| `TZ` | `UTC` | Timezone |
| `SECRET_KEY` | (generated) | Flask session secret. If unset, a random key is generated and saved to `/data/secret_key` |
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

- **`local`** (default) - Username/password accounts. The first user to register becomes admin, and registration then closes. Set `auth.allow_registration: true` to let others sign up as viewers. Admins can start/stop/restart and download backups. Viewers can only see stats and logs.
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

POST requests must include the header `X-Requested-With: argonath` (the panel adds it automatically). This blocks cross-site request forgery.

## Architecture

```
docker container
├── Flask app served by waitress (port 5000)
│   ├── Web UI (gridstack.js dashboard)
│   ├── Process manager (subprocess + psutil)
│   ├── Stats collector (background thread)
│   └── SQLite database (users, activity log)
└── volumes
    ├── /game    → game server files
    ├── /config  → game.yml (optional overrides)
    └── /data    → SQLite DB, logs, backups
```

## License

MIT - free to use, modify, and distribute. See [LICENSE](LICENSE) for details.
