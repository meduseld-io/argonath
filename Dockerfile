# ---------------------------------------------------------------------------
# Base image: native Linux game servers (SteamCMD, no Java, no Wine)
#   ghcr.io/meduseld-io/argonath:latest
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS base

# lib32gcc-s1 and ca-certificates are needed by SteamCMD; tmux for scripts that use it
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    lib32gcc-s1 \
    procps \
    tmux \
    && rm -rf /var/lib/apt/lists/*

# Install SteamCMD
RUN mkdir -p /opt/steamcmd && \
    curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | \
    tar -xz -C /opt/steamcmd

# Create directories
RUN mkdir -p /game /config /data

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and the built-in game presets (selected with GAME=<name>)
COPY backend/ /app/
COPY examples/ /tmp/examples/
RUN mkdir -p /app/presets && \
    for d in /tmp/examples/*/; do \
        name=$(basename "$d"); \
        [ -f "$d/game.yml" ] && cp "$d/game.yml" "/app/presets/$name.yml"; \
    done; \
    rm -rf /tmp/examples
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run as this user/group (matches the owner of ./game on the host)
ENV PUID=1000 PGID=1000

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

VOLUME ["/game", "/config", "/data"]

ENTRYPOINT ["/entrypoint.sh"]

# ---------------------------------------------------------------------------
# Wine image: adds Wine and Xvfb for Windows-only servers (and Core Keeper)
#   ghcr.io/meduseld-io/argonath:latest-wine
# ---------------------------------------------------------------------------
FROM base AS wine

RUN apt-get update && apt-get install -y --no-install-recommends \
    wine \
    wine64 \
    xauth \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# The default target stays the slim base image
FROM base
