"""
Argonath Configuration
Loads settings from /config/game.yml and environment variables.
"""

import os
import yaml
import logging

logger = logging.getLogger(__name__)

# Paths - detect local dev vs Docker
_app_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_app_dir)

CONFIG_DIR = os.environ.get("ARGONATH_CONFIG_DIR", "/config")
DATA_DIR = os.environ.get("ARGONATH_DATA_DIR", "/data")
GAME_DIR = os.environ.get("ARGONATH_GAME_DIR", "/game")

# If running locally (not in Docker), use project-relative paths
if not os.path.isdir(CONFIG_DIR):
    CONFIG_DIR = os.path.join(_project_root, "config")
if not os.path.isdir(DATA_DIR) and "ARGONATH_DATA_DIR" not in os.environ:
    DATA_DIR = os.path.join(_project_root, "data")
if not os.path.isdir(GAME_DIR) and "ARGONATH_GAME_DIR" not in os.environ:
    GAME_DIR = os.path.join(_project_root, "game")

CONFIG_FILE = os.path.join(CONFIG_DIR, "game.yml")

# Load game.yml
def load_config():
    """Load and validate game.yml configuration"""
    if not os.path.exists(CONFIG_FILE):
        logger.warning(f"Config file not found at {CONFIG_FILE}, using defaults")
        return {}

    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f) or {}


_config = load_config()

# ================= GAME SETTINGS =================
_game = _config.get("game", {})

GAME_NAME = _game.get("name", "Game Server")
STEAM_APP_ID = str(_game.get("steam_app_id", ""))
PROCESS_NAME = _game.get("process_name", "")
LAUNCH_SCRIPT = _game.get("launch_script", "")
LAUNCH_EXE = _game.get("launch_exe", "")
SERVER_DIR = _game.get("server_dir", GAME_DIR)
LOG_FILE = _game.get("log_file", "")
MAX_PLAYERS = _game.get("max_players", 8)
QUERY_PORT = int(_game.get("query_port", 27015))
SERVER_ARGS = [str(a) for a in (_game.get("args") or [])]
# Game port shown in the panel and used for the "port open" check.
# Falls back to parsing SERVER_ARGS when not set.
GAME_PORT = int(_game["port"]) if _game.get("port") else None
GAME_PORT_PROTOCOL = str(_game.get("port_protocol", "")).lower()  # "udp", "tcp" or "" (auto)
# Seconds to wait for the server to shut down cleanly before force killing
STOP_TIMEOUT = int(_game.get("stop_timeout", 60))

# ================= SERVER SETTINGS =================
_server = _config.get("server", {})

FLASK_HOST = _server.get("host", "0.0.0.0")
FLASK_PORT = int(_server.get("port", 5000))

# ================= AUTH SETTINGS =================
_auth = _config.get("auth", {})

AUTH_MODE = _auth.get("mode", "local")  # "local" or "none"
# Allow new accounts (as viewers) after the first admin has registered
ALLOW_REGISTRATION = bool(_auth.get("allow_registration", False))

# ================= STEAMCMD SETTINGS =================
_steamcmd = _config.get("steamcmd", {})

STEAMCMD_ENABLED = _steamcmd.get("enabled", True)
STEAMCMD_INSTALL_DIR = _steamcmd.get("install_dir", GAME_DIR)
STEAMCMD_VALIDATE = _steamcmd.get("validate", True)
STEAMCMD_PATH = os.environ.get("STEAMCMD_PATH", "/opt/steamcmd/steamcmd.sh")

# ================= COMPATIBILITY =================
_compat = _config.get("compatibility", {})

WINE_ENABLED = _compat.get("wine", False)
PROTON_VERSION = _compat.get("proton_version", "")

# ================= TIMEOUTS & THRESHOLDS =================
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 10
RESTART_COOLDOWN = 30  # seconds between restarts
START_TIMEOUT = 120  # seconds to wait for server to start
UPDATE_TIMEOUT = 600  # seconds to wait for update

# Monitoring intervals
UPDATE_CHECK_INTERVAL = 3600  # 1 hour
STATS_COLLECTION_INTERVAL = 30  # seconds
MONITOR_INTERVAL = 5  # seconds

# Health thresholds
WARNING_CPU = 80
CRITICAL_CPU = 95
WARNING_RAM = 80
CRITICAL_RAM = 95
WARNING_DISK = 85
CRITICAL_DISK = 95

# Idle shutdown (0 to disable)
IDLE_SHUTDOWN_MINUTES = int(os.environ.get("IDLE_SHUTDOWN_MINUTES", "0"))

# ================= BACKUP SETTINGS =================
_backup = _config.get("backup", {})

BACKUP_ENABLED = _backup.get("enabled", True)
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
BACKUP_SOURCE = _backup.get("save_dir", os.path.join(GAME_DIR, "Saved"))
BACKUP_MAX_KEEP = _backup.get("max_keep", 5)

# ================= INTERNAL PATHS =================
DATABASE_PATH = os.path.join(DATA_DIR, "argonath.db")
LOG_FILE_PATH = os.path.join(DATA_DIR, "argonath.log")
VERSION_FILE = os.path.join(DATA_DIR, "build_id.txt")
STARTUP_LOG = os.path.join(DATA_DIR, "startup.log")

# ================= SECRETS =================
def _load_secret_key():
    """Use SECRET_KEY from the environment, or generate one and persist it in DATA_DIR"""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key

    key_file = os.path.join(DATA_DIR, "secret_key")
    try:
        with open(key_file, "r") as f:
            key = f.read().strip()
        if key:
            return key
    except FileNotFoundError:
        pass

    import secrets
    key = secrets.token_hex(32)
    os.makedirs(DATA_DIR, exist_ok=True)
    fd = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(key)
    return key


SECRET_KEY = _load_secret_key()

# ================= LOGGING =================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
