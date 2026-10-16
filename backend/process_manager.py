"""
Argonath Process Manager
Handles starting, stopping, killing, and monitoring the game server process.
"""

import os
import signal
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
    DATA_DIR,
    GAME_NAME,
)

logger = logging.getLogger(__name__)

# Server state
_state_lock = threading.Lock()
_server_state = "offline"  # offline, starting, running, stopping, restarting, crashed
_idle_since = None

# Launcher process started by launch_server() (None if not launched by us)
_launcher = None
# Output of the launch script itself (game output should go to log_file)
LAUNCHER_LOG = os.path.join(DATA_DIR, "launcher.log")
LAUNCHER_LOG_MAX_BYTES = 1024 * 1024

# Cached psutil.Process objects so cpu_percent() has a previous sample to compare to
_usage_procs = {}

# A2S backoff: skip querying for a while after a timeout so /api/stats stays fast
_A2S_BACKOFF = 60
_a2s_skip_until = 0

# Process names that wrap the real game process and must never be matched
_WRAPPER_NAMES = {
    "tmux", "tmux: server", "xvfb-run",
    "sh", "bash", "wine", "wine64", "wineserver", "tee",
}

# Valid state transitions
VALID_TRANSITIONS = {
    "offline": ["starting", "restarting"],
    "starting": ["running", "offline", "crashed", "stopping"],
    "running": ["stopping", "restarting", "crashed"],
    "stopping": ["offline", "crashed"],
    "restarting": ["starting", "running", "offline", "crashed"],
    "crashed": ["starting", "offline", "restarting"],
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


def find_server_processes():
    """Return psutil processes whose command line contains PROCESS_NAME (wrappers excluded)"""
    if not PROCESS_NAME:
        return []

    found = []
    try:
        for proc in psutil.process_iter(["name", "cmdline", "pid", "create_time"]):
            try:
                cmdline = proc.info["cmdline"]
                if not cmdline or proc.info["name"] in _WRAPPER_NAMES:
                    continue
                if proc.pid == os.getpid():
                    continue
                if PROCESS_NAME in " ".join(str(arg) for arg in cmdline):
                    found.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.error(f"Error scanning processes: {e}")
    return found


def is_running():
    """Check if the game server process is running"""
    return bool(find_server_processes())


def launch_server():
    """Launch the game server process"""
    global _launcher
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

        # Ensure log file parent directory exists
        if LOG_FILE:
            log_dir = os.path.dirname(LOG_FILE)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

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
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        _launcher = proc
        # The pipe must always be drained: once its buffer fills, the game
        # blocks writing to its console and freezes.
        threading.Thread(
            target=_drain_launcher_output, args=(proc.stdout,), daemon=True,
        ).start()
        logger.info(f"Launch script started (PID {proc.pid})")

        # Quick check if it died immediately. Exit code 0 is fine: some scripts
        # start the server detached (e.g. in tmux) and return straight away.
        time.sleep(2)
        if proc.poll() is not None and proc.returncode != 0:
            logger.error(f"Launch script exited immediately (code {proc.returncode})")
            logger.error(f"Output: {_tail_file(LAUNCHER_LOG)}")
            raise RuntimeError(f"Launch script exited with code {proc.returncode}")

    except Exception as e:
        logger.error(f"Failed to launch server: {e}")
        raise


def _drain_launcher_output(stream):
    """Copy the launch script's output to LAUNCHER_LOG (capped), discarding the rest.
    Scripts that tee game output to stdout would otherwise grow the file forever."""
    written = 0
    try:
        os.makedirs(os.path.dirname(LAUNCHER_LOG), exist_ok=True)
        with open(LAUNCHER_LOG, "wb") as out:
            for chunk in iter(lambda: stream.read1(65536), b""):
                if written < LAUNCHER_LOG_MAX_BYTES:
                    part = chunk[:LAUNCHER_LOG_MAX_BYTES - written]
                    out.write(part)
                    out.flush()
                    written += len(part)
    except Exception as e:
        logger.debug(f"Launcher output drain stopped: {e}")
    finally:
        stream.close()


def _tail_file(path, max_bytes=4096):
    """Return the last few KB of a text file"""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - max_bytes))
            return f.read().decode("utf-8", errors="ignore")
    except OSError:
        return ""


def _reap_launcher():
    """Collect the launcher's exit status so it doesn't linger as a zombie"""
    global _launcher
    if _launcher is not None and _launcher.poll() is not None:
        _launcher = None


def kill_server():
    """Kill the game server process (force - SIGKILL)"""
    try:
        for proc in find_server_processes():
            try:
                logger.info(f"Killing PID {proc.pid}: {proc.info['name']}")
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Also take down the rest of the launch script's process group (tee, wrappers)
        if _launcher is not None and _launcher.poll() is None:
            try:
                os.killpg(_launcher.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass

        logger.info("Kill command executed")
    except Exception as e:
        logger.error(f"Failed to kill server: {e}")
    finally:
        _reap_launcher()


def _wait_until_stopped(seconds):
    """Poll until the server process is gone. Returns True if it stopped."""
    for _ in range(max(0, seconds)):
        if not is_running():
            return True
        time.sleep(1)
    return not is_running()


def stop_process(timeout=STOP_TIMEOUT):
    """Ask the server to shut down cleanly, force killing it after timeout seconds.
    Returns True if the server is no longer running. Does not change state."""
    if not is_running():
        _reap_launcher()
        return True

    # Servers started in a tmux session get Ctrl+C typed into their console
    sent = False
    try:
        result = subprocess.run(
            ["tmux", "send-keys", "-t", "gameserver", "C-c"],
            capture_output=True, timeout=5,
        )
        sent = result.returncode == 0
        if sent:
            logger.info("Sent Ctrl+C to tmux session 'gameserver'")
    except Exception as e:
        logger.debug(f"tmux send-keys: {e}")

    # Otherwise signal the game process directly so it can save and exit
    if not sent:
        for proc in find_server_processes():
            try:
                logger.info(f"Sending SIGINT to PID {proc.pid}")
                proc.send_signal(signal.SIGINT)
                sent = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    if sent and _wait_until_stopped(timeout):
        logger.info("Server stopped gracefully")
        _reap_launcher()
        return True

    logger.info("Server did not stop gracefully, force killing")
    kill_server()
    return _wait_until_stopped(15)


def graceful_stop():
    """Stop the server cleanly (force kill as a last resort) and update state"""
    if stop_process():
        set_state("offline")
        return True

    logger.error("Server failed to stop within timeout")
    set_state("crashed")
    return False


def get_uptime():
    """Get server uptime in seconds"""
    procs = find_server_processes()
    if not procs:
        return 0
    return int(time.time() - min(p.info["create_time"] for p in procs))


def get_server_usage():
    """Get game server CPU and RAM usage"""
    procs = find_server_processes()
    if not procs:
        return None

    # Reuse Process objects between calls: cpu_percent(interval=None) measures
    # since the previous call on the same object and returns 0.0 on the first.
    live = set()
    cpu_raw = 0.0
    ram = 0
    for found in procs:
        pid = found.pid
        live.add(pid)
        proc = _usage_procs.get(pid)
        if proc is None:
            proc = found
            _usage_procs[pid] = proc
        try:
            cpu_raw += proc.cpu_percent(interval=None)
            ram += proc.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    for pid in list(_usage_procs):
        if pid not in live:
            del _usage_procs[pid]

    cpu_norm = round(cpu_raw / (psutil.cpu_count() or 1), 2)
    return {"cpu": cpu_norm, "cpu_raw": round(cpu_raw, 2), "ram": round(ram / (1024**3), 2)}


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
    global _a2s_skip_until

    # Try A2S protocol first (works for most Steam-based dedicated servers).
    # Minecraft doesn't speak A2S; for other games back off after a miss so
    # every stats poll doesn't wait for the query timeout.
    if "minecraft" not in GAME_NAME.lower() and time.time() >= _a2s_skip_until:
        count = _get_player_count_a2s()
        if count is not None:
            return count
        _a2s_skip_until = time.time() + _A2S_BACKOFF

    # Fall back to log-based counting
    count = _get_player_count_from_logs()
    return count


def _get_player_count_a2s():
    """Query Steam server for player count using A2S_INFO protocol."""
    try:
        query_host = "127.0.0.1"

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)

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
            sock2.settimeout(1)
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

            # Pattern: "NAME joined the game" / "NAME left the game" (Minecraft)
            if "joined the game" in lower:
                found_pattern = True
                name = _extract_player_name(line, "joined the game")
                if name:
                    online_players.add(name)
            elif "left the game" in lower:
                found_pattern = True
                name = _extract_player_name(line, "left the game")
                if name:
                    online_players.discard(name)

            # Pattern: "NAME joined the server" / "NAME left the server"
            elif "joined the server" in lower:
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
        # After stripping brackets, we should have just the player name.
        # Minecraft puts ": " after its tags and "[/ip:port]" after the name.
        name = prefix.lstrip(": ").strip()
        if name.endswith("]") and "[" in name:
            name = name[:name.rindex("[")].strip()

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

            _reap_launcher()

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
