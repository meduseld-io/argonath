"""
Argonath Process Manager
Handles starting, stopping, killing, and monitoring the game server process.
"""

import os
import subprocess
import time
import threading
import logging

import psutil

from config import (
    PROCESS_NAME,
    LAUNCH_SCRIPT,
    LAUNCH_EXE,
    SERVER_DIR,
    SERVER_ARGS,
    LOG_FILE,
    START_TIMEOUT,
    STOP_TIMEOUT,
    MONITOR_INTERVAL,
    IDLE_SHUTDOWN_MINUTES,
    STARTUP_LOG,
    WINE_ENABLED,
)

logger = logging.getLogger(__name__)

# Server state
_state_lock = threading.Lock()
_server_state = "offline"  # offline, starting, running, stopping, restarting, crashed
_idle_since = None

# Valid state transitions
VALID_TRANSITIONS = {
    "offline": ["starting"],
    "starting": ["running", "offline", "crashed"],
    "running": ["stopping", "restarting", "crashed"],
    "stopping": ["offline", "crashed"],
    "restarting": ["starting", "running", "offline", "crashed"],
    "crashed": ["starting", "offline"],
}


def get_state():
    """Get the current server state"""
    with _state_lock:
        return _server_state


def set_state(new_state, force=False):
    """Set the server state with transition validation"""
    global _server_state
    with _state_lock:
        if not force and new_state not in VALID_TRANSITIONS.get(_server_state, []):
            logger.warning(f"Invalid state transition: {_server_state} -> {new_state}")
            return False
        old = _server_state
        _server_state = new_state
        logger.info(f"State: {old} -> {new_state}")
        return True


def is_running():
    """Check if the game server process is running"""
    if not PROCESS_NAME:
        return False

    try:
        for proc in psutil.process_iter(["name", "cmdline", "pid"]):
            if proc.info["cmdline"]:
                try:
                    cmdline_str = " ".join(str(arg) for arg in proc.info["cmdline"])

                    # Skip wrapper processes
                    if proc.info["name"] in [
                        "tmux", "tmux: server", "xvfb-run",
                        "sh", "bash", "wine", "wine64", "wineserver",
                    ]:
                        continue

                    if PROCESS_NAME in cmdline_str:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
    except Exception as e:
        logger.error(f"Error checking if server is running: {e}")

    return False


def launch_server():
    """Launch the game server process"""
    try:
        script = LAUNCH_SCRIPT or LAUNCH_EXE
        if not script:
            raise ValueError("No launch_script or launch_exe configured in game.yml")

        if not os.path.exists(script):
            raise FileNotFoundError(f"Launch script not found: {script}")

        # Ensure script is executable
        try:
            os.chmod(script, 0o755)
        except Exception as e:
            logger.warning(f"Could not set execute permission: {e}")

        # Kill stale tmux session if it exists
        try:
            tmux_check = subprocess.run(
                ["tmux", "has-session", "-t", "gameserver"],
                capture_output=True, timeout=5,
            )
            if tmux_check.returncode == 0:
                logger.warning("Stale tmux session found - killing it")
                subprocess.run(
                    ["tmux", "kill-session", "-t", "gameserver"],
                    capture_output=True, timeout=5,
                )
        except Exception as e:
            logger.debug(f"tmux check: {e}")

        # Launch
        cwd = os.path.dirname(os.path.abspath(script)) if os.path.dirname(script) else SERVER_DIR
        logger.info(f"Launching: {script}")

        proc = subprocess.Popen(
            ["bash", script],
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info(f"Launch script started (PID {proc.pid})")

        # Quick check if it died immediately
        time.sleep(2)
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            logger.error(f"Launch script exited immediately (code {proc.returncode})")
            logger.error(f"STDOUT: {stdout.decode('utf-8', errors='ignore')}")
            logger.error(f"STDERR: {stderr.decode('utf-8', errors='ignore')}")
            raise RuntimeError("Launch script exited immediately")

    except Exception as e:
        logger.error(f"Failed to launch server: {e}")
        raise


def kill_server():
    """Kill the game server process"""
    try:
        killed = False
        for proc in psutil.process_iter(["name", "cmdline", "pid"]):
            if proc.info["cmdline"]:
                try:
                    cmdline_str = " ".join(str(arg) for arg in proc.info["cmdline"])
                    if PROCESS_NAME in cmdline_str:
                        # Skip wrappers
                        if proc.info["name"] in ["sh", "bash", "tmux", "tmux: server"]:
                            continue
                        logger.info(f"Killing PID {proc.info['pid']}: {proc.info['name']}")
                        proc.kill()
                        killed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        # Fallback
        if not killed:
            subprocess.call(f'pkill -9 -f "{PROCESS_NAME}"', shell=True)

        logger.info("Kill command executed")
    except Exception as e:
        logger.error(f"Failed to kill server: {e}")


def get_uptime():
    """Get server uptime in seconds"""
    if not PROCESS_NAME:
        return 0

    try:
        for proc in psutil.process_iter(["name", "cmdline", "pid", "create_time"]):
            if proc.info["cmdline"]:
                try:
                    cmdline_str = " ".join(str(arg) for arg in proc.info["cmdline"])
                    if proc.info["name"] in ["sh", "bash", "tmux", "tmux: server", "wine", "wine64", "wineserver"]:
                        continue
                    if PROCESS_NAME in cmdline_str:
                        return int(time.time() - proc.info["create_time"])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
    except Exception as e:
        logger.error(f"Error getting uptime: {e}")

    return 0


def get_server_usage():
    """Get game server CPU and RAM usage"""
    if not PROCESS_NAME:
        return None

    try:
        for proc in psutil.process_iter(["name", "cmdline", "pid"]):
            if proc.info["cmdline"]:
                try:
                    cmdline_str = " ".join(str(arg) for arg in proc.info["cmdline"])
                    if proc.info["name"] in ["sh", "bash", "tmux", "tmux: server", "wine", "wine64", "wineserver"]:
                        continue
                    if PROCESS_NAME in cmdline_str:
                        p = psutil.Process(proc.info["pid"])
                        cpu_raw = p.cpu_percent(interval=None)
                        ram_gb = round(p.memory_info().rss / (1024**3), 2)
                        cpu_norm = round(cpu_raw / psutil.cpu_count(), 2)
                        return {"cpu": cpu_norm, "cpu_raw": cpu_raw, "ram": ram_gb}
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
    except Exception as e:
        logger.error(f"Error getting server usage: {e}")

    return None


def write_startup_marker(message):
    """Write a marker to the startup log"""
    try:
        os.makedirs(os.path.dirname(STARTUP_LOG), exist_ok=True)
        with open(STARTUP_LOG, "a") as f:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] {message}\n")
    except Exception as e:
        logger.warning(f"Could not write startup marker: {e}")


def get_player_count():
    """
    Get current player count. Returns int or None if unavailable.
    This is a best-effort implementation that tries common patterns:
    - Reads the game log file and looks for player join/leave messages
    - Falls back to None if the game doesn't have a recognizable pattern

    Override this function or extend it for game-specific player counting.
    """
    if not LOG_FILE or not os.path.exists(LOG_FILE):
        return None

    try:
        # Try to count connected players from log patterns
        # Common patterns across games:
        # - "player connected" / "player disconnected"
        # - "joined the game" / "left the game"
        # - Active connection count from recent log lines
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-500:]

        connected = set()
        for line in lines:
            lower = line.lower()
            # Generic patterns - covers many Source/Unity games
            if "connected" in lower or "joined" in lower or "logged in" in lower:
                connected.add(line.strip())
            if "disconnected" in lower or "left" in lower or "logged out" in lower:
                connected.discard(line.strip())

        # If we found no join/leave patterns, return None (unknown)
        # This avoids showing "0" when we simply can't detect players
        return None
    except Exception as e:
        logger.debug(f"Player count detection failed: {e}")
        return None


def monitor_loop():
    """Background thread: monitor server state and detect crashes"""
    global _idle_since

    logger.info("Monitor thread started")

    while True:
        try:
            time.sleep(MONITOR_INTERVAL)
            current = get_state()
            running = is_running()

            if current == "running" and not running:
                logger.error("CRASH DETECTED - server process disappeared")
                write_startup_marker("CRASH: Server process died unexpectedly")
                set_state("crashed")

            elif current == "crashed" and running:
                logger.info("Server recovered from crash")
                set_state("running", force=True)

            # Idle shutdown
            if IDLE_SHUTDOWN_MINUTES > 0 and current == "running" and running:
                # Note: player count detection is game-specific
                # Override get_player_count() in a plugin or leave disabled
                pass

        except Exception as e:
            logger.error(f"Monitor error: {e}")
            time.sleep(MONITOR_INTERVAL)
