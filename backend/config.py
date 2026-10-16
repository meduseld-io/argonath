"""
Argonath Configuration
Loads settings from a built-in game preset (GAME env var or `preset:` in
game.yml), /config/game.yml and environment variables.
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

# Built-in presets: /app/presets/<name>.yml in the image, examples/<name>/game.yml locally
PRESETS_DIR = os.path.join(_app_dir, "presets")
_EXAMPLES_DIR = os.path.join(_project_root, "examples")


def list_presets():
    """Names of the bundled game presets"""
    if os.path.isdir(PRESETS_DIR):
        return sorted(f[:-4] for f in os.listdir(PRESETS_DIR) if f.endswith(".yml"))
    if os.path.isdir(_EXAMPLES_DIR):
        return sorted(
            d for d in os.listdir(_EXAMPLES_DIR)
            if os.path.isfile(os.path.join(_EXAMPLES_DIR, d, "game.yml"))
        )
    return []


def _preset_path(name):
    name = os.path.basename(str(name).strip().lower())
    for path in (
        os.path.join(PRESETS_DIR, f"{name}.yml"),
        os.path.join(_EXAMPLES_DIR, name, "game.yml"),
    ):
        if os.path.isfile(path):
            return path
    return None


def _read_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def _merge(base, override):
    """Recursively merge override into base (lists and scalars are replaced)"""
    result = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config():
    """Load the selected preset, then apply /config/game.yml on top of it"""
    user = _read_yaml(CONFIG_FILE) if os.path.exists(CONFIG_FILE) else {}
    preset_name = os.environ.get("GAME") or user.get("preset")

    config = {}
    if preset_name:
        path = _preset_path(preset_name)
        if path:
            config = _read_yaml(path)
            logger.info(f"Using built-in preset '{preset_name}'")
        else:
            logger.error(
                f"Unknown game preset '{preset_name}'. Available: {', '.join(list_presets())}"
            )
    elif not user:
        logger.warning(
            f"No GAME set and no config at {CONFIG_FILE}. "
            f"Set GAME to one of: {', '.join(list_presets())}"
        )

    return _merge(config, user)


_config = load_config()

# ================= GAME SETTINGS =================
_game = _config.get("game", {})

GAME_NAME = _game.get("name", "Game Server")
STEAM_APP_ID = str(_game.get("steam_app_id", ""))
PROCESS_NAME = _game.get("process_name", "")
LAUNCH_SCRIPT = _game.get("launch_script", "")
SERVER_DIR = _game.get("server_dir", GAME_DIR)
# Program to run, relative to server_dir (or absolute). Argonath launches it
# directly with `args`, so no start script is needed. `launch_exe` is the old name.
EXECUTABLE = _game.get("executable") or _game.get("launch_exe", "")
# Directory to run the executable in, relative to server_dir
WORKING_DIR = _game.get("working_dir", "")
# Extra environment variables for the game process
GAME_ENV = {str(k): str(v) for k, v in (_game.get("env") or {}).items()}
# Run the game under a virtual X display (some Unity servers need one)
USE_XVFB = bool(_game.get("xvfb", False))
# Where the game's stdout/stderr go when Argonath launches it
CONSOLE_LOG = _game.get("console_log", "")
# The file shown in the panel's Server Logs
LOG_FILE = _game.get("log_file", "") or CONSOLE_LOG or (
    os.path.join(SERVER_DIR, "console.log") if EXECUTABLE else ""
)
CONSOLE_LOG = CONSOLE_LOG or LOG_FILE
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

WINE_ENABLED = bool(_compat.get("wine", False))
PROTON_VERSION = _compat.get("proton_version", "")
# Where GE-Proton builds are looked up when proton_version is set
PROTON_DIR = os.environ.get("PROTON_DIR", "/compatibilitytools")

# SteamCMD platform: "windows" for servers that only ship Windows builds
STEAMCMD_PLATFORM = str(_steamcmd.get("platform", "windows" if WINE_ENABLED else "")).lower()

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
