"""
Argonath - Lightweight Game Server Panel
Main Flask application entry point.
"""

import os
import time
import threading
import logging
from logging.handlers import RotatingFileHandler
from datetime import timedelta

from flask import Flask, render_template, jsonify, request, session, redirect, url_for

from config import (
    FLASK_HOST,
    FLASK_PORT,
    SECRET_KEY,
    LOG_LEVEL,
    LOG_FILE_PATH,
    LOG_FILE,
    DATA_DIR,
    GAME_NAME,
    MAX_PLAYERS,
    STEAM_APP_ID,
    STEAMCMD_ENABLED,
    AUTH_MODE,
    STARTUP_LOG,
    RESTART_COOLDOWN,
    START_TIMEOUT,
    STOP_TIMEOUT,
    RATE_LIMIT_WINDOW,
    RATE_LIMIT_MAX_REQUESTS,
)

# Configure logging
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE_PATH, maxBytes=5 * 1024 * 1024, backupCount=3),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Import modules after logging is configured
from models import init_db, log_activity as db_log_activity
from auth import get_current_user, require_auth, require_admin, login, logout, register
from process_manager import (
    get_state, set_state, is_running, launch_server, kill_server,
    get_uptime, get_server_usage, get_player_count, monitor_loop, write_startup_marker,
)
from stats import get_system_stats, get_health, get_history, collect_loop
from updates import check_for_updates, run_update, get_update_info, check_updates_loop

# Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(days=30)

# Rate limiting
_rate_limits = {}


def rate_limit_check():
    """Check if the current request exceeds rate limits"""
    ip = request.remote_addr
    now = time.time()

    if ip not in _rate_limits:
        _rate_limits[ip] = []

    # Clean old entries
    _rate_limits[ip] = [t for t in _rate_limits[ip] if now - t < RATE_LIMIT_WINDOW]

    if len(_rate_limits[ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return True  # Rate limited

    _rate_limits[ip].append(now)
    return False


# Restart cooldown
_last_restart_time = 0


# ================= AUTH ROUTES =================


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if AUTH_MODE == "none":
        return redirect("/")

    if request.method == "POST":
        data = request.form
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return render_template("login.html", error="Username and password required", game_name=GAME_NAME)

        user = login(username, password)
        if user:
            return redirect("/")
        return render_template("login.html", error="Invalid credentials", game_name=GAME_NAME)

    return render_template("login.html", error=None, game_name=GAME_NAME)


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if AUTH_MODE == "none":
        return redirect("/")

    if request.method == "POST":
        data = request.form
        username = data.get("username", "").strip()
        password = data.get("password", "")
        confirm = data.get("confirm", "")

        if not username or not password:
            return render_template("register.html", error="All fields required", game_name=GAME_NAME)
        if len(username) < 3:
            return render_template("register.html", error="Username must be at least 3 characters", game_name=GAME_NAME)
        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters", game_name=GAME_NAME)
        if password != confirm:
            return render_template("register.html", error="Passwords don't match", game_name=GAME_NAME)

        user = register(username, password)
        if user:
            return redirect("/")
        return render_template("register.html", error="Username already taken", game_name=GAME_NAME)

    return render_template("register.html", error=None, game_name=GAME_NAME)


@app.route("/logout")
def logout_page():
    logout()
    return redirect("/login")


# ================= MAIN UI =================


@app.route("/")
@require_auth
def home():
    user = get_current_user()
    return render_template(
        "panel.html",
        game_name=GAME_NAME,
        max_players=MAX_PLAYERS,
        steam_app_id=STEAM_APP_ID,
        steamcmd_enabled=STEAMCMD_ENABLED,
        auth_mode=AUTH_MODE,
        user=user,
    )


# ================= API: SERVER CONTROL =================


@app.route("/api/start", methods=["POST"])
@require_auth
def api_start():
    if rate_limit_check():
        return jsonify({"error": "Rate limited"}), 429

    user = get_current_user()
    if user and user["role"] == "viewer":
        return jsonify({"error": "Insufficient permissions"}), 403

    current = get_state()
    if current in ["running", "starting", "restarting"]:
        return "", 204

    if not set_state("starting"):
        return jsonify({"error": "Invalid state transition"}), 400

    db_log_activity(user["id"] if user else None, "START server")
    write_startup_marker("User start: Server started by user")

    # Check for updates before starting
    if STEAMCMD_ENABLED and check_for_updates():
        logger.info("Update available - running update before start")
        run_update()
        time.sleep(2)

    launch_server()

    def wait():
        for i in range(START_TIMEOUT):
            time.sleep(1)
            if is_running():
                set_state("running")
                logger.info(f"Server started after {i + 1}s")
                return
        logger.error(f"Server failed to start within {START_TIMEOUT}s")
        set_state("offline")

    threading.Thread(target=wait, daemon=True).start()
    return "", 204


@app.route("/api/stop", methods=["POST"])
@require_auth
def api_stop():
    if rate_limit_check():
        return jsonify({"error": "Rate limited"}), 429

    user = get_current_user()
    if user and user["role"] == "viewer":
        return jsonify({"error": "Insufficient permissions"}), 403

    current = get_state()
    if current in ["offline", "stopping"]:
        return "", 204

    if not set_state("stopping"):
        return jsonify({"error": "Invalid state transition"}), 400

    db_log_activity(user["id"] if user else None, "STOP server")
    write_startup_marker("User stop: Server stopped by user")

    kill_server()

    def wait():
        for _ in range(STOP_TIMEOUT):
            time.sleep(1)
            if not is_running():
                set_state("offline")
                return
        logger.error("Server failed to stop within timeout")
        if is_running():
            set_state("crashed")
        else:
            set_state("offline")

    threading.Thread(target=wait, daemon=True).start()
    return "", 204


@app.route("/api/restart", methods=["POST"])
@require_auth
def api_restart():
    global _last_restart_time

    if rate_limit_check():
        return jsonify({"error": "Rate limited"}), 429

    user = get_current_user()
    if user and user["role"] == "viewer":
        return jsonify({"error": "Insufficient permissions"}), 403

    now = time.time()
    if now - _last_restart_time < RESTART_COOLDOWN:
        remaining = int(RESTART_COOLDOWN - (now - _last_restart_time))
        return jsonify({"error": "Cooldown active", "remaining": remaining}), 429

    current = get_state()
    if current in ["starting", "stopping", "restarting"]:
        return "", 204

    if not set_state("restarting"):
        return jsonify({"error": "Invalid state transition"}), 400

    _last_restart_time = now
    db_log_activity(user["id"] if user else None, "RESTART server")
    write_startup_marker("User restart: Server restarted by user")

    def restart_sequence():
        # Kill
        kill_server()
        for i in range(20):
            time.sleep(1)
            if not is_running():
                break

        # Update
        if STEAMCMD_ENABLED:
            run_update()

        time.sleep(2)

        # Launch
        launch_server()
        for i in range(START_TIMEOUT):
            time.sleep(1)
            if is_running():
                set_state("running")
                logger.info(f"Server restarted after {i + 1}s")
                return

        logger.error("Server failed to start after restart")
        set_state("offline")

    threading.Thread(target=restart_sequence, daemon=True).start()
    return "", 204


@app.route("/api/kill", methods=["POST"])
@require_auth
def api_kill():
    if rate_limit_check():
        return jsonify({"error": "Rate limited"}), 429

    user = get_current_user()
    if user and user["role"] == "viewer":
        return jsonify({"error": "Insufficient permissions"}), 403

    if not is_running():
        set_state("offline", force=True)
        return "", 204

    set_state("stopping", force=True)
    db_log_activity(user["id"] if user else None, "FORCE KILL server")
    write_startup_marker("User kill: Server force killed by user")

    def kill_sequence():
        kill_server()
        for _ in range(15):
            time.sleep(1)
            if not is_running():
                set_state("offline")
                return

        # Retry
        kill_server()
        time.sleep(3)
        if not is_running():
            set_state("offline")
        else:
            set_state("crashed")

    threading.Thread(target=kill_sequence, daemon=True).start()
    return "", 204


# ================= API: STATS =================


@app.route("/api/stats")
@require_auth
def api_stats():
    try:
        stats = get_system_stats()
        running = is_running()
        current = get_state()
        update_info = get_update_info()

        return jsonify({
            "state": current,
            "stats": stats,
            "server": get_server_usage() if running else None,
            "uptime": get_uptime() if running else 0,
            "health": get_health(stats),
            "version": update_info,
            "players": get_player_count() if running else None,
        })
    except Exception as e:
        logger.error(f"Error in /api/stats: {e}")
        return jsonify({"error": "Internal error", "state": "offline"}), 500


@app.route("/api/history")
@require_auth
def api_history():
    return jsonify({"history": get_history()})


# ================= API: LOGS =================


@app.route("/api/logs")
@require_auth
def api_logs():
    """Get game server logs"""
    if not LOG_FILE or not os.path.exists(LOG_FILE):
        return jsonify({"lines": []})

    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-200:]
        return jsonify({"lines": [l.rstrip("\n") for l in lines]})
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return jsonify({"lines": [], "error": str(e)})


@app.route("/api/startup-logs")
@require_auth
def api_startup_logs():
    """Get startup/shutdown log"""
    if not os.path.exists(STARTUP_LOG):
        return jsonify({"lines": []})

    try:
        with open(STARTUP_LOG, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-100:]
        return jsonify({"lines": [l.rstrip("\n") for l in lines]})
    except Exception as e:
        logger.error(f"Error reading startup log: {e}")
        return jsonify({"lines": [], "error": str(e)})


# ================= API: UPDATES =================


@app.route("/api/check-update")
@require_auth
def api_check_update():
    available = check_for_updates()
    return jsonify(get_update_info())


# ================= API: HEALTH (PUBLIC) =================


@app.route("/health")
def health_check():
    return jsonify({"status": "ok", "game": GAME_NAME, "state": get_state()})


# ================= API: ACTIVITY LOG =================


@app.route("/api/activity")
@require_auth
def api_activity():
    """Get recent activity log"""
    from models import get_activity_log
    return jsonify({"activity": get_activity_log(limit=30)})


# ================= STARTUP =================


def start_background_threads():
    """Start all background monitoring threads"""
    threading.Thread(target=monitor_loop, daemon=True, name="monitor").start()
    threading.Thread(target=collect_loop, daemon=True, name="stats").start()
    if STEAMCMD_ENABLED and STEAM_APP_ID:
        threading.Thread(target=check_updates_loop, daemon=True, name="updates").start()


if __name__ == "__main__":
    logger.info(f"Argonath starting - managing '{GAME_NAME}'")
    logger.info(f"Auth mode: {AUTH_MODE}")
    logger.info(f"SteamCMD: {'enabled' if STEAMCMD_ENABLED else 'disabled'}")

    # Initialize database
    init_db()

    # Detect initial state
    if is_running():
        set_state("running", force=True)
        logger.info("Server detected as already running")
    else:
        logger.info("Server is offline")

    # Start background threads
    start_background_threads()

    # Run Flask
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
