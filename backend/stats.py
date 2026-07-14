"""
Argonath Stats Collection
System metrics gathering and history tracking.
"""

import time
import os
import threading
import logging
from collections import deque

import psutil

from config import STATS_COLLECTION_INTERVAL, WARNING_CPU, CRITICAL_CPU, WARNING_RAM, CRITICAL_RAM, WARNING_DISK, CRITICAL_DISK
from process_manager import is_running, get_server_usage

logger = logging.getLogger(__name__)

# Rolling history (30 minutes at 30s intervals = 60 points)
history = deque(maxlen=60)


def get_cpu_temperature():
    """Get CPU temperature in Celsius"""
    try:
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                for name in ["coretemp", "cpu_thermal", "k10temp", "zenpower"]:
                    if name in temps and temps[name]:
                        return round(temps[name][0].current, 1)

        # Fallback: thermal zone
        for zone in ["/sys/class/thermal/thermal_zone0/temp", "/sys/class/thermal/thermal_zone1/temp"]:
            if os.path.exists(zone):
                with open(zone, "r") as f:
                    return round(int(f.read().strip()) / 1000.0, 1)

        return None
    except Exception as e:
        logger.debug(f"Could not read CPU temp: {e}")
        return None


def get_system_stats():
    """Get system resource usage"""
    try:
        cpu = psutil.cpu_percent(interval=0.3)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        cpu_temp = get_cpu_temperature()

        return {
            "cpu": cpu,
            "cpu_temp": cpu_temp,
            "ram_percent": memory.percent,
            "ram_used": round(memory.used / (1024**3), 2),
            "ram_total": round(memory.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_used": round(disk.used / (1024**3), 2),
            "disk_total": round(disk.total / (1024**3), 2),
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {
            "cpu": 0, "cpu_temp": None,
            "ram_percent": 0, "ram_used": 0, "ram_total": 0,
            "disk_percent": 0, "disk_used": 0, "disk_total": 0,
        }


def get_health(stats):
    """Determine system health status from stats"""
    if stats["cpu"] > CRITICAL_CPU or stats["ram_percent"] > CRITICAL_RAM or stats["disk_percent"] > CRITICAL_DISK:
        return "critical"
    if stats["cpu"] > WARNING_CPU or stats["ram_percent"] > WARNING_RAM or stats["disk_percent"] > WARNING_DISK:
        return "warning"
    return "good"


def get_history():
    """Get the stats history as a list"""
    return list(history)


def collect_loop():
    """Background thread: collect stats periodically"""
    logger.info("Stats collection thread started")

    # Initialize CPU percent tracking for the server process
    # (first call to cpu_percent returns 0, subsequent calls are accurate)
    if is_running():
        get_server_usage()

    while True:
        try:
            stats = get_system_stats()
            server = get_server_usage() if is_running() else None

            history.append({
                "timestamp": time.strftime("%H:%M:%S"),
                "system_cpu": stats["cpu"],
                "system_ram": stats["ram_used"],
                "server_cpu": server["cpu"] if server else 0,
                "server_ram": server["ram"] if server else 0,
            })

            time.sleep(STATS_COLLECTION_INTERVAL)
        except Exception as e:
            logger.error(f"Stats collection error: {e}")
            time.sleep(STATS_COLLECTION_INTERVAL)
