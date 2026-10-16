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
import shlex

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
    LOG_FILE,
    EXECUTABLE,
)
from minecraft import is_minecraft

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
    # Filter out files that exist before (or without) an actual install
    ignored = {
        ".gitkeep", ".gitignore", "start.sh", "server.log", "console.log", "logs",
        ".steam", ".wine", "jre",
    }
    if LOG_FILE:
        ignored.add(os.path.basename(LOG_FILE))
    if LAUNCH_SCRIPT:
        ignored.add(os.path.basename(LAUNCH_SCRIPT))
    meaningful = [e for e in entries if e not in ignored]
    return len(meaningful) > 0


def start_deploy():
    """Start the deploy process in a background thread. Returns False if already running."""
    global _deploy_in_progress

    with _deploy_lock:
        if _deploy_in_progress:
            return False
        _deploy_in_progress = True

    if is_minecraft(GAME_NAME):
        threading.Thread(target=_run_minecraft_deploy, daemon=True).start()
    else:
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

        if not STEAM_APP_ID:
            raise ValueError("steam_app_id is not set in game.yml")

        from updates import steamcmd_command, steamcmd_env
        logger.info(f"Deploy: Running SteamCMD for app {STEAM_APP_ID}")

        process = subprocess.Popen(
            steamcmd_command(),
            env=steamcmd_env(),
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
            # Older configs without `executable` still rely on a generated start.sh
            if not EXECUTABLE:
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

    # Build args string (quoted so values with spaces survive)
    args_str = " ".join(shlex.quote(a) for a in SERVER_ARGS) if SERVER_ARGS else ""

    # Detect the correct executable
    game_lower = GAME_NAME.lower()

    env = ""
    if "palworld" in game_lower:
        exe = "./PalServer.sh"
    elif "valheim" in game_lower:
        exe = "./valheim_server.x86_64"
        # Valheim needs its bundled Steam libraries and the client app ID
        env = (
            f'export LD_LIBRARY_PATH="{SERVER_DIR}/linux64:$LD_LIBRARY_PATH"\n'
            "export SteamAppId=892970\n"
        )
    elif "satisfactory" in game_lower:
        exe = "./FactoryServer.sh"
    else:
        exe = ""

    # Use the configured log_file path, falling back to server.log in the game dir
    from config import LOG_FILE
    log_path = LOG_FILE or os.path.join(SERVER_DIR, "server.log")

    # exec so the game replaces the shell and receives stop signals directly
    if exe:
        content = (
            f"#!/bin/bash\n"
            f"{env}"
            f"cd {SERVER_DIR}\n"
            f"mkdir -p \"$(dirname {log_path})\"\n"
            f"exec {exe} {args_str} >> {log_path} 2>&1\n"
        )
    else:
        content = (
            f"#!/bin/bash\n"
            f"cd {SERVER_DIR}\n"
            f"mkdir -p \"$(dirname {log_path})\"\n"
            f"echo 'Edit {script_path} to launch your server'\n"
            f"exit 1\n"
            f"# exec ./YOUR_SERVER_EXE {args_str} >> {log_path} 2>&1\n"
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


def _run_minecraft_deploy():
    """Deploy Minecraft server by downloading server.jar from Mojang."""
    global _deploy_in_progress, _deploy_status, _deploy_output, _deploy_line_count

    _deploy_status = "running"
    _deploy_output = ""
    _deploy_line_count = 0

    try:
        from minecraft import (
            get_latest_release_info,
            download_server_jar,
            generate_minecraft_start_script,
            accept_eula,
            ensure_java,
        )
        from updates import save_current_build_id

        _deploy_output = "Fetching latest Minecraft version..."
        _deploy_line_count = 1

        version_id, jar_url = get_latest_release_info()
        if not version_id or not jar_url:
            _deploy_status = "failed"
            _deploy_output += "\nFailed to fetch Minecraft version manifest"
            logger.error("Minecraft deploy: Failed to get version info")
            return

        _deploy_output += f"\nLatest release: {version_id}"
        _deploy_output += f"\nDownloading server.jar..."
        _deploy_line_count = 3

        success = download_server_jar(jar_url, SERVER_DIR)
        if not success:
            _deploy_status = "failed"
            _deploy_output += "\nFailed to download server.jar"
            return

        _deploy_output += "\nDownload complete"
        _deploy_output += "\nAccepting EULA..."
        _deploy_line_count = 5

        accept_eula(SERVER_DIR)

        _deploy_output += "\nGenerating start script..."
        _deploy_line_count = 6

        _deploy_output += "\nDownloading Java runtime..."
        _deploy_line_count = 7
        if not ensure_java(SERVER_DIR, version_id):
            _deploy_status = "failed"
            _deploy_output += "\nFailed to download Java"
            return

        if not EXECUTABLE:
            script_path = LAUNCH_SCRIPT or os.path.join(SERVER_DIR, "start.sh")
            generate_minecraft_start_script(SERVER_DIR, script_path)

        # Save the version as the build ID for update detection
        save_current_build_id(version_id)

        _deploy_output += f"\nDeployed Minecraft {version_id} successfully"
        _deploy_line_count = 8
        _deploy_status = "complete"
        logger.info("Minecraft deploy complete: version %s", version_id)

    except Exception as e:
        _deploy_status = "failed"
        _deploy_output += f"\nError: {str(e)}"
        logger.error("Minecraft deploy error: %s", e)
    finally:
        _deploy_in_progress = False
