"""
Argonath Process Manager
Handles starting, stopping, killing, and monitoring the game server process.
"""

import os
import socket
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
    QUERY_PORT,
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
    """Kill the game server process (force - SIGKILL)"""
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


def graceful_stop():
    """Attempt graceful shutdown via tmux Ctrl+C, then force kill if needed"""
    graceful = False
    try:
        result = subprocess.run(
            ["tmux", "send-keys", "-t", "gameserver", "C-c", ""],
            capture_output=True, timeout=5,
        )
        if result.returncode == 0:
            graceful = True
            logger.info("Sent Ctrl+C to tmux session 'gameserver' for graceful shutdown")
    except Exception as e:
        logger.warning(f"Could not send graceful stop via tmux: {e}")

    # If graceful signal was sent, wait for it to take effect
    grace_period = 10 if graceful else 0
    for _ in range(grace_period):
        time.sleep(1)
        if not is_running():
            set_state("offline")
            return True

    # If still running after grace period, force kill
    if is_running():
        logger.info("Server did not stop gracefully, force killing")
        kill_server()

    for _ in range(STOP_TIMEOUT - grace_period):
        time.sleep(1)
        if not is_running():
            set_state("offline")
            return True

    # Failed to stop
    logger.error("Server failed to stop within timeout")
    if is_running():
        set_state("crashed")
    else:
        set_state("offline")
    return False


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
    Get current player count. Tries A2S Steam query first, then falls back
    to parsing join/leave messages from the game server log.
    Returns int or None if unavailable.
    """
    # Try A2S protocol first (works for most Steam-based dedicated servers)
    count = _get_player_count_a2s()
    if count is not None:
        return count

    # Fall back to log-based counting
    count = _get_player_count_from_logs()
    return count


def _get_player_count_a2s():
    """Query Steam server for player count using A2S_INFO protocol."""
    try:
        query_host = "127.0.0.1"

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)

        request = b"\xff\xff\xff\xff\x54Source Engine Query\x00"
        sock.sendto(request, (query_host, QUERY_PORT))
        data, addr = sock.recvfrom(4096)
        sock.close()

        if len(data) < 6:
            return None

        response_type = data[4]

        # Handle challenge response (0x41)
        if response_type == 0x41:
            if len(data) < 9:
                return None
            challenge = data[5:9]
            challenge_request = b"\xff\xff\xff\xff\x54Source Engine Query\x00" + challenge
            sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock2.settimeout(2)
            sock2.sendto(challenge_request, (query_host, QUERY_PORT))
            data, addr = sock2.recvfrom(4096)
            sock2.close()

            if len(data) < 6:
                return None
            response_type = data[4]

        # Expect A2S_INFO response (0x49)
        if response_type != 0x49:
            return None

        offset = 6

        # Skip null-terminated strings: server name, map, folder, game
        for _ in range(4):
            while offset < len(data) and data[offset] != 0:
                offset += 1
            offset += 1

        # Skip app ID (2 bytes)
        offset += 2

        # Read player count (1 byte)
        if offset < len(data):
            players = data[offset]
            logger.debug(f"A2S query: {players} players online")
            return players

        return None

    except socket.timeout:
        logger.debug("A2S query timeout - server may not respond to queries")
        return None
    except Exception as e:
        logger.debug(f"A2S query error: {e}")
        return None


def _get_player_count_from_logs():
    """
    Count players by parsing join/leave messages from the game server log.
    Supports common patterns across many game servers:
    - "NAME joined the server" / "NAME left the server" (Palworld, etc.)
    - "NAME connected" / "NAME disconnected" (Source-based)
    - "NAME logged in" / "NAME logged out" (Minecraft-style)
    Returns int or None if no recognizable pattern found.
    """
    if not LOG_FILE or not os.path.exists(LOG_FILE):
        return None

    try:
        # Read the last 256KB of the log file efficiently
        chunk_size = 256 * 1024
        with open(LOG_FILE, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()
            read_start = max(0, file_size - chunk_size)
            f.seek(read_start)
            data = f.read()

        text = data.decode("utf-8", errors="ignore")
        lines = text.splitlines()

        # Track players by name using join/leave patterns
        online_players = set()
        found_pattern = False

        for line in lines:
            lower = line.lower()

            # Pattern: "NAME joined the server" / "NAME left the server"
            if "joined the server" in lower:
                found_pattern = True
                name = _extract_player_name(line, "joined the server")
                if name:
                    online_players.add(name)
            elif "left the server" in lower:
                found_pattern = True
                name = _extract_player_name(line, "left the server")
                if name:
                    online_players.discard(name)

            # Pattern: "NAME connected" / "NAME disconnected"
            elif "player connected" in lower or "] connected" in lower:
                found_pattern = True
                name = _extract_player_name(line, "connected")
                if name:
                    online_players.add(name)
            elif "player disconnected" in lower or "] disconnected" in lower:
                found_pattern = True
                name = _extract_player_name(line, "disconnected")
                if name:
                    online_players.discard(name)

            # Pattern: "NAME logged in" / "NAME logged out"
            elif "logged in" in lower:
                found_pattern = True
                name = _extract_player_name(line, "logged in")
                if name:
                    online_players.add(name)
            elif "logged out" in lower:
                found_pattern = True
                name = _extract_player_name(line, "logged out")
                if name:
                    online_players.discard(name)

        # If no join/leave patterns were found at all, return None (unknown)
        if not found_pattern:
            return None

        return len(online_players)

    except Exception as e:
        logger.debug(f"Log-based player count failed: {e}")
        return None


def _extract_player_name(line, keyword):
    """
    Extract player name from a log line containing the given keyword.
    Handles common log formats:
    - [timestamp] [TAG] NAME keyword...
    - [timestamp] NAME keyword...
    - NAME keyword...
    """
    try:
        lower = line.lower()
        idx = lower.index(keyword.lower())
        # Get the text before the keyword
        prefix = line[:idx].strip()

        # Strip common log prefixes: [timestamp] [TAG]
        # Remove bracketed sections from the left
        while prefix.startswith("["):
            end = prefix.find("]")
            if end == -1:
                break
            prefix = prefix[end + 1:].strip()

        # Some formats have "LOG]" or similar without leading bracket
        # e.g. "[2026-07-17 17:11:00] [LOG] stewart joined..."
        # After stripping brackets, we should have just the player name
        name = prefix.strip()

        # Skip if it looks like a system message or is empty
        if not name or len(name) > 64 or " " in name and len(name) > 32:
            return None

        return name
    except Exception:
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
