"""
Argonath Update Manager
SteamCMD build ID checking and update execution.
"""

import os
import subprocess
import time
import threading
import logging

import requests

from config import (
    STEAM_APP_ID,
    STEAMCMD_ENABLED,
    STEAMCMD_PATH,
    STEAMCMD_INSTALL_DIR,
    STEAMCMD_VALIDATE,
    VERSION_FILE,
    UPDATE_TIMEOUT,
    UPDATE_CHECK_INTERVAL,
    GAME_NAME,
    SERVER_DIR,
)
from minecraft import is_minecraft

logger = logging.getLogger(__name__)

# Update state
_version_lock = threading.Lock()
current_build_id = None
latest_build_id = None
last_update_status = None
last_update_time = None
last_update_output = None


def _init_build_id():
    """Load the stored build ID on startup"""
    global current_build_id
    current_build_id = get_current_build_id()


def get_current_build_id():
    """Read the locally stored build ID"""
    with _version_lock:
        if os.path.exists(VERSION_FILE):
            try:
                with open(VERSION_FILE, "r") as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Error reading version file: {e}")
    return None


def save_current_build_id(build_id):
    """Save the current build ID"""
    with _version_lock:
        try:
            os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)
            with open(VERSION_FILE, "w") as f:
                f.write(str(build_id))
            logger.info(f"Saved build ID: {build_id}")
        except Exception as e:
            logger.error(f"Error saving version file: {e}")


def get_latest_build_id(retries=3):
    """Query Steam API for the latest build ID"""
    if not STEAM_APP_ID:
        return None

    for attempt in range(retries):
        try:
            url = f"https://api.steamcmd.net/v1/info/{STEAM_APP_ID}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if "data" in data and STEAM_APP_ID in data["data"]:
                    depots = data["data"][STEAM_APP_ID].get("depots", {})
                    branches = depots.get("branches", {})
                    public = branches.get("public", {})
                    build_id = public.get("buildid")
                    if build_id:
                        return build_id

            logger.warning(f"Steam API returned status {response.status_code} (attempt {attempt + 1})")
        except requests.Timeout:
            logger.warning(f"Steam API timeout (attempt {attempt + 1}/{retries})")
        except Exception as e:
            logger.warning(f"Steam API error (attempt {attempt + 1}/{retries}): {e}")

        if attempt < retries - 1:
            time.sleep(1)

    return None


def check_for_updates():
    """Check if an update is available. Returns True if update available."""
    global current_build_id, latest_build_id

    # Minecraft uses Mojang API instead of Steam
    if is_minecraft(GAME_NAME):
        return _check_minecraft_updates()

    if not STEAMCMD_ENABLED or not STEAM_APP_ID:
        return False

    current_build_id = get_current_build_id()
    latest_build_id = get_latest_build_id()

    if current_build_id and latest_build_id:
        available = current_build_id != latest_build_id
        if available:
            logger.info(f"Update available: {current_build_id} -> {latest_build_id}")
        return available

    return False


def _check_minecraft_updates():
    """Check Mojang API for a newer Minecraft version."""
    global current_build_id, latest_build_id

    from minecraft import get_latest_release_info

    current_build_id = get_current_build_id()
    version_id, _ = get_latest_release_info()
    latest_build_id = version_id

    if current_build_id and latest_build_id:
        available = current_build_id != latest_build_id
        if available:
            logger.info(
                "Minecraft update available: %s -> %s",
                current_build_id, latest_build_id
            )
        return available

    return False


def run_update():
    """Run SteamCMD to update the game server, or download new Minecraft jar."""
    global last_update_status, last_update_time, last_update_output, current_build_id

    # Minecraft update path
    if is_minecraft(GAME_NAME):
        return _run_minecraft_update()

    if not STEAMCMD_ENABLED:
        last_update_status = "disabled"
        return False

    if not os.path.exists(STEAMCMD_PATH):
        logger.error(f"SteamCMD not found at {STEAMCMD_PATH}")
        last_update_status = "steamcmd not found"
        last_update_time = time.time()
        return False

    try:
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

        logger.info(f"Running SteamCMD update for app {STEAM_APP_ID}")
        result = subprocess.run(
            cmd,
            timeout=UPDATE_TIMEOUT,
            capture_output=True,
            text=True,
        )

        last_update_time = time.time()
        last_update_output = result.stdout

        if result.returncode == 0:
            last_update_status = "success"
            logger.info("SteamCMD update completed successfully")

            # Update stored build ID
            new_build = get_latest_build_id()
            if new_build:
                save_current_build_id(new_build)
                current_build_id = new_build
            return True
        else:
            last_update_status = f"failed (exit code {result.returncode})"
            logger.error(f"SteamCMD update failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        last_update_status = "timeout"
        last_update_time = time.time()
        logger.error("SteamCMD update timed out")
        return False
    except Exception as e:
        last_update_status = f"error: {str(e)}"
        last_update_time = time.time()
        logger.error(f"SteamCMD update error: {e}")
        return False


def _run_minecraft_update():
    """Download the latest Minecraft server.jar."""
    global last_update_status, last_update_time, last_update_output, current_build_id

    from minecraft import get_latest_release_info, download_server_jar

    try:
        version_id, jar_url = get_latest_release_info()
        if not version_id or not jar_url:
            last_update_status = "failed (could not fetch version)"
            last_update_time = time.time()
            return False

        success = download_server_jar(jar_url, SERVER_DIR)
        last_update_time = time.time()

        if success:
            last_update_status = "success"
            last_update_output = f"Updated to Minecraft {version_id}"
            save_current_build_id(version_id)
            current_build_id = version_id
            logger.info("Minecraft updated to %s", version_id)
            return True
        else:
            last_update_status = "failed (download error)"
            return False

    except Exception as e:
        last_update_status = f"error: {str(e)}"
        last_update_time = time.time()
        logger.error("Minecraft update error: %s", e)
        return False


def get_update_info():
    """Get update status info"""
    return {
        "current_build": current_build_id,
        "latest_build": latest_build_id,
        "update_available": (
            current_build_id != latest_build_id
            if current_build_id and latest_build_id
            else None
        ),
        "last_status": last_update_status,
        "last_time": last_update_time,
    }


def check_updates_loop():
    """Background thread: check for updates periodically"""
    logger.info("Update check thread started")

    # Initial load
    _init_build_id()

    while True:
        try:
            check_for_updates()
            time.sleep(UPDATE_CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Update check error: {e}")
            time.sleep(UPDATE_CHECK_INTERVAL)
