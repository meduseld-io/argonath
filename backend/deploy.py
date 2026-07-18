"""
Argonath Deploy Manager
Handles initial game server installation via SteamCMD.
"""

import os
import subprocess
import threading
import time
import logging

import re

from config import (
    STEAM_APP_ID,
    STEAMCMD_ENABLED,
    STEAMCMD_PATH,
    STEAMCMD_INSTALL_DIR,
    STEAMCMD_VALIDATE,
    LAUNCH_SCRIPT,
    SERVER_DIR,
    SERVER_ARGS,
    GAME_NAME,
    WINE_ENABLED,
)

logger = logging.getLogger(__name__)

# Deploy state
_deploy_lock = threading.Lock()
_deploy_in_progress = False
_deploy_status = "idle"  # idle, running, complete, failed
_deploy_output = ""
_deploy_line_count = 0


def is_deployed():
    """Check if the game server files have been installed"""
    # Check if the server directory has content (more than just empty dirs)
    if not os.path.isdir(SERVER_DIR):
        return False

    entries = os.listdir(SERVER_DIR)
    # Filter out common empty-state files
    meaningful = [e for e in entries if e not in [".gitkeep", ".gitignore", "start.sh"]]
    return len(meaningful) > 1


def start_deploy():
    """Start the deploy process in a background thread. Returns False if already running."""
    global _deploy_in_progress

    with _deploy_lock:
        if _deploy_in_progress:
            return False
        _deploy_in_progress = True

    threading.Thread(target=_run_deploy, daemon=True).start()
    return True


def _run_deploy():
    """Run SteamCMD to install the game server files"""
    global _deploy_in_progress, _deploy_status, _deploy_output, _deploy_line_count

    _deploy_status = "running"
    _deploy_output = ""
    _deploy_line_count = 0

    try:
        if not os.path.exists(STEAMCMD_PATH):
            _deploy_status = "failed"
            _deploy_output = f"SteamCMD not found at {STEAMCMD_PATH}"
            logger.error(_deploy_output)
            return

        # Ensure install directory exists
        os.makedirs(STEAMCMD_INSTALL_DIR, exist_ok=True)

        # Build SteamCMD command
        cmd = [
            STEAMCMD_PATH,
            "+force_install_dir", STEAMCMD_INSTALL_DIR,
            "+login", "anonymous",
            "+app_update", STEAM_APP_ID,
        ]
        if STEAMCMD_VALIDATE:
            cmd.append("validate")
        cmd.append("+quit")

        logger.info(f"Deploy: Running SteamCMD for app {STEAM_APP_ID}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        lines = []
        _ansi_re = re.compile(r'\x1b\[[0-9;]*m')
        for line in iter(process.stdout.readline, ""):
            clean = _ansi_re.sub('', line.rstrip())
            if clean:
                lines.append(clean)
            _deploy_line_count = len(lines)
            # Keep last 50 lines in output
            _deploy_output = "\n".join(lines[-50:])

        process.wait()

        if process.returncode == 0:
            logger.info("Deploy: SteamCMD completed successfully")
            # Generate start.sh if it doesn't exist
            _generate_start_script()
            # Save build ID so update detection works
            try:
                from updates import get_latest_build_id, save_current_build_id
                build_id = get_latest_build_id()
                if build_id:
                    save_current_build_id(build_id)
                    logger.info(f"Deploy: Saved initial build ID: {build_id}")
            except Exception as e:
                logger.warning(f"Deploy: Could not save build ID: {e}")
            _deploy_status = "complete"
        else:
            _deploy_status = f"failed (exit code {process.returncode})"
            logger.error(f"Deploy: SteamCMD failed with exit code {process.returncode}")

    except Exception as e:
        _deploy_status = f"failed"
        _deploy_output += f"\nError: {str(e)}"
        logger.error(f"Deploy error: {e}")
    finally:
        _deploy_in_progress = False


def _generate_start_script():
    """Generate a default start.sh for the game.
    
    The script pipes server output to server.log so the panel's log viewer
    can display it. The log file path matches what's set in game.yml log_file.
    """
    script_path = LAUNCH_SCRIPT or os.path.join(SERVER_DIR, "start.sh")

    if os.path.exists(script_path):
        logger.info(f"Deploy: start.sh already exists at {script_path}")
        return

    # Build args string
    args_str = " ".join(SERVER_ARGS) if SERVER_ARGS else ""

    # Detect the correct executable
    game_lower = GAME_NAME.lower()

    if "palworld" in game_lower:
        exe = "./PalServer.sh"
    elif "valheim" in game_lower:
        exe = "./valheim_server.x86_64"
    elif "satisfactory" in game_lower:
        exe = "./FactoryServer.sh"
    else:
        exe = ""

    # Use the configured log_file path, falling back to server.log in the game dir
    from config import LOG_FILE
    log_path = LOG_FILE or os.path.join(SERVER_DIR, "server.log")

    if exe:
        content = (
            f"#!/bin/bash\n"
            f"cd {SERVER_DIR}\n"
            f"{exe} {args_str} 2>&1 | tee -a {log_path}\n"
        )
    else:
        content = (
            f"#!/bin/bash\n"
            f"cd {SERVER_DIR}\n"
            f"echo 'Edit this script to launch your server'\n"
            f"# ./YOUR_SERVER_EXE {args_str} 2>&1 | tee -a {log_path}\n"
        )

    try:
        os.makedirs(os.path.dirname(script_path), exist_ok=True)
        with open(script_path, "w") as f:
            f.write(content)
        os.chmod(script_path, 0o755)
        logger.info(f"Deploy: Generated start.sh at {script_path}")
    except Exception as e:
        logger.error(f"Deploy: Failed to generate start.sh: {e}")


def get_deploy_status():
    """Get the current deploy status"""
    return {
        "status": _deploy_status,
        "output": _deploy_output,
        "line_count": _deploy_line_count,
        "in_progress": _deploy_in_progress,
    }
