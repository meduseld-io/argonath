FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    procps \
    tmux \
    curl \
    lib32gcc-s1 \
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

# Copy application
COPY backend/ /app/

# Expose port
EXPOSE 5000

# Volumes
VOLUME ["/game", "/config", "/data"]

# Entrypoint
ENTRYPOINT ["python", "app.py"]
