"""
Argonath Minecraft Provider
Handles deploy and update detection for Minecraft Java Edition servers
using Mojang's version manifest API instead of SteamCMD.
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"


def is_minecraft(game_name):
    """Check if the configured game is Minecraft"""
    return "minecraft" in game_name.lower()


def get_latest_release_info():
    """Fetch the latest Minecraft release version and its server jar URL.

    Returns:
        tuple: (version_id, server_jar_url) or (None, None) on failure
    """
    try:
        resp = requests.get(MANIFEST_URL, timeout=10)
        resp.raise_for_status()
        manifest = resp.json()

        latest_id = manifest.get("latest", {}).get("release")
        if not latest_id:
            logger.error("Minecraft manifest missing latest release")
            return None, None

        # Find the version entry to get its package URL
        version_entry = None
        for v in manifest.get("versions", []):
            if v["id"] == latest_id:
                version_entry = v
                break

        if not version_entry:
            logger.error("Minecraft version %s not found in manifest", latest_id)
            return None, None

        # Fetch the version-specific manifest for the download URL
        version_resp = requests.get(version_entry["url"], timeout=10)
        version_resp.raise_for_status()
        version_data = version_resp.json()

        server_download = version_data.get("downloads", {}).get("server", {})
        jar_url = server_download.get("url")

        if not jar_url:
            logger.error("Minecraft version %s has no server download", latest_id)
            return latest_id, None

        return latest_id, jar_url

    except requests.RequestException as e:
        logger.error("Failed to fetch Minecraft version manifest: %s", e)
        return None, None
    except (KeyError, ValueError) as e:
        logger.error("Failed to parse Minecraft version manifest: %s", e)
        return None, None


def download_server_jar(jar_url, dest_dir):
    """Download the Minecraft server.jar to the specified directory.

    Args:
        jar_url: URL to download from
        dest_dir: Directory to save server.jar into

    Returns:
        bool: True on success, False on failure
    """
    dest_path = os.path.join(dest_dir, "server.jar")
    try:
        logger.info("Downloading Minecraft server.jar from %s", jar_url)
        resp = requests.get(jar_url, timeout=120, stream=True)
        resp.raise_for_status()

        os.makedirs(dest_dir, exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        logger.info("Downloaded server.jar (%.1f MB) to %s", size_mb, dest_path)
        return True

    except requests.RequestException as e:
        logger.error("Failed to download Minecraft server.jar: %s", e)
        return False
    except OSError as e:
        logger.error("Failed to write server.jar: %s", e)
        return False


def generate_minecraft_start_script(dest_dir, launch_script_path, log_file):
    """Generate a start.sh for Minecraft if one doesn't exist."""
    if os.path.exists(launch_script_path):
        return

    content = (
        "#!/bin/bash\n"
        f"cd {dest_dir}\n"
        f"mkdir -p $(dirname {log_file})\n"
        f"exec java -Xmx4G -Xms2G -jar server.jar nogui 2>&1 | tee -a {log_file}\n"
    )

    try:
        os.makedirs(os.path.dirname(launch_script_path), exist_ok=True)
        with open(launch_script_path, "w") as f:
            f.write(content)
        os.chmod(launch_script_path, 0o755)
        logger.info("Generated Minecraft start.sh at %s", launch_script_path)
    except OSError as e:
        logger.error("Failed to generate Minecraft start.sh: %s", e)


def accept_eula(dest_dir):
    """Auto-accept the Minecraft EULA."""
    eula_path = os.path.join(dest_dir, "eula.txt")
    try:
        with open(eula_path, "w") as f:
            f.write("# Auto-accepted by Argonath\neula=true\n")
        logger.info("Accepted Minecraft EULA at %s", eula_path)
    except OSError as e:
        logger.error("Failed to write eula.txt: %s", e)
