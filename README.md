# Minecraft Bedrock Server with Web Dashboard

## Overview

This project provides a **Minecraft Bedrock Server** running within a Docker container, complemented by a **web-based dashboard** that offers real-time server statistics, player activity tracking, and a leaderboard. The system includes a Flask-powered API backend to facilitate data retrieval and visualization.

## Features

- **Containerized Minecraft Bedrock Server** using Docker
- **Web dashboard** displaying live server stats, active players, and leaderboard rankings
- **RESTful API service** built with Flask for querying server details
- **Persistent SQLite database** to store player statistics and session data
- **Nginx reverse proxy** for efficiently serving the web dashboard

## Project Structure

```
/srv/minecraft
│── docker-compose.yml  # Defines all service containers
│── nginx/              # Nginx configuration files
│── web/                # Frontend dashboard (HTML, JavaScript, CSS)
│── api/                # Backend API service (Flask application)
│── data/               # SQLite database for storing player statistics
│── README.md           # Project documentation
```

## Services

The project is orchestrated via `docker-compose`, comprising the following containers:

1. **bedrock-server**: The Minecraft Bedrock server instance.
2. **minecraft-api**: A Flask-based API that retrieves server metrics and player statistics.
3. **minecraft-web**: An Nginx service hosting the web-based frontend dashboard.

## Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_GITHUB/minecraft.git /srv/minecraft
cd /srv/minecraft
```

### 2. Launch the Server

```bash
docker compose up -d
```

This initializes all services in detached mode.

### 3. Monitor Server Logs

Ensure proper operation by inspecting logs:

```bash
docker logs -f bedrock-server
```

### 4. Access the Web Dashboard

Navigate to the following URL in a browser:

```
http://your-server-ip/
```

## Managing the Server

### Stopping the Server

To halt all running containers gracefully:

```bash
docker compose down
```

### Updating and Rebuilding the API

For modifications to the API service, execute:

```bash
docker compose down minecraft-api
docker compose build minecraft-api
docker compose up -d minecraft-api
```

## Roadmap

- **Administrative Panel**: Develop an interface for modifying server settings (difficulty level, whitelisted players, etc.).
- **User Authentication**: Implement authentication mechanisms for access control.
- **Enhanced Live Tracking**: Improve real-time monitoring of server TPS, entity counts, and player interactions.

## Contributing

Contributions are welcome! Please submit issues or pull requests to suggest improvements.

## Credits

This project utilizes the **Minecraft Bedrock Server Docker container** maintained by [itzg](https://github.com/itzg/docker-minecraft-bedrock-server). Huge thanks to them for their work in making Minecraft server hosting more accessible!

