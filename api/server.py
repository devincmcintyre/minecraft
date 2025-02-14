from flask import Flask, jsonify
import subprocess
import time
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB_FILE = "/app/data/player_stats.db"  # Persistent database file

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create players table
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            xuid TEXT PRIMARY KEY,
            username TEXT,
            total_playtime INTEGER DEFAULT 0,
            last_joined INTEGER DEFAULT 0
        );
    ''')

    # Create sessions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            xuid TEXT PRIMARY KEY,
            username TEXT,
            joined_at INTEGER
        );
    ''')

    conn.commit()
    conn.close()

init_db()

player_sessions = {}  # In-memory tracking for active players

def get_player_activity():
    try:
        logs = subprocess.run(
            ["docker", "logs", "--since", "10s", "bedrock-server"],
            capture_output=True,
            text=True
        ).stdout.split("\n")
    except Exception as e:
        print(f"[ERROR] Failed to retrieve logs: {e}")
        return {"active_players": [], "recent_players": []}

    recent_players = set()
    global player_sessions

    for line in logs:
        if "Player connected:" in line:
            try:
                # Parse the log line once
                parts = line.split("Player connected: ")[1].split(", xuid: ")
                username = parts[0].strip()
                xuid = parts[1].strip()
            except IndexError:
                print("[ERROR] Failed to parse 'Player connected' line: " + line)
                continue

            current_time = time.time()

            # Update sessions table in the database
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("""
                INSERT INTO sessions (xuid, username, joined_at) 
                VALUES (?, ?, ?) 
                ON CONFLICT(xuid) DO UPDATE SET joined_at = excluded.joined_at
            """, (xuid, username, current_time))
            conn.commit()
            conn.close()

            # Store session in memory
            player_sessions[xuid] = {"username": username, "joined_at": current_time}
            print(f"[DEBUG] Player {username} (XUID: {xuid}) joined at {current_time}")
            recent_players.add(username)

            # Ensure player exists in the players table and update last_joined
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("""
                INSERT INTO players (xuid, username, last_joined, total_playtime) 
                VALUES (?, ?, ?, 0) 
                ON CONFLICT(xuid) DO UPDATE SET last_joined = excluded.last_joined
            """, (xuid, username, current_time))
            conn.commit()
            conn.close()

        elif "Player disconnected:" in line:
            try:
                # First extract username and xuid from the log line
                parts = line.split("Player disconnected: ")[1].split(", xuid: ")
                username = parts[0].strip()
                xuid = parts[1].split(",")[0].strip() if len(parts[1].split(",")) > 0 else parts[1].strip()
            except IndexError:
                print("[ERROR] Failed to parse 'Player disconnected' line: " + line)
                continue

            if xuid in player_sessions:
                join_time = player_sessions[xuid].get("joined_at")
                if join_time is None:
                    print(f"[ERROR] No join time recorded for {username} (XUID: {xuid}). Cannot calculate playtime.")
                    continue

                current_time = time.time()
                playtime = int(current_time - join_time)

                # Validate playtime
                if playtime <= 0:
                    print(f"[WARNING] Ignoring invalid playtime calculation for {username}: {playtime} seconds.")
                elif playtime < 5:
                    print(f"[INFO] Ignoring short session for {username}: {playtime} seconds.")
                elif playtime >= 86400:
                    print(f"[ERROR] Unrealistic playtime for {username}: {playtime} seconds. Skipping update.")
                else:
                    print(f"[DEBUG] Player {username} (XUID: {xuid}) disconnected. Adding {playtime} seconds to total playtime.")
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()

                    # Debug: Print before updating
                    c.execute("SELECT total_playtime FROM players WHERE xuid = ?", (xuid,))
                    old_playtime_row = c.fetchone()
                    old_playtime = old_playtime_row[0] if old_playtime_row else 0
                    print(f"[DEBUG] Old playtime for {username}: {old_playtime} seconds")

                    # Update the total playtime
                    c.execute("""
                        UPDATE players 
                        SET total_playtime = total_playtime + ? 
                        WHERE xuid = ?
                    """, (playtime, xuid))

                    # Debug: Print after updating
                    c.execute("SELECT total_playtime FROM players WHERE xuid = ?", (xuid,))
                    new_playtime_row = c.fetchone()
                    if new_playtime_row:
                        print(f"[DEBUG] Updated playtime for {username}: {new_playtime_row[0]} seconds")

                    conn.commit()
                    conn.close()
                    recent_players.add(username)

                # Remove the session after processing the disconnect
                del player_sessions[xuid]
            else:
                print(f"[WARNING] Player {username} (XUID: {xuid}) was not found in active sessions.")

    active_players = [data["username"] for data in player_sessions.values()]
    return {
        "active_players": active_players,
        "recent_players": list(recent_players)
    }

def is_server_running():
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", "bedrock-server"],
            capture_output=True,
            text=True
        ).stdout.strip()
        return result.lower() == "true"
    except Exception as e:
        print(f"[ERROR] Failed to check server status: {e}")
        return False

from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from datetime import datetime, timezone
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
import subprocess
import time

def get_server_stats():
    try:
        uptime_raw = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.StartedAt}}", "bedrock-server"],
            capture_output=True,
            text=True
        ).stdout.strip()

        uptime_seconds = 0
        uptime_formatted = "Unavailable"

        if uptime_raw:
            try:
                # Use dateutil's isoparse to handle nanosecond precision correctly.
                uptime_parsed = isoparse(uptime_raw)
                now = datetime.now(timezone.utc)
                uptime_seconds = int((now - uptime_parsed).total_seconds())

                # Calculate detailed uptime using relativedelta
                delta = relativedelta(now, uptime_parsed)
                uptime_formatted = (
                    f"{delta.years} years, {delta.months} months, {delta.days} days, "
                    f"{delta.hours:02d}:{delta.minutes:02d}:{delta.seconds:02d}"
                )
            except Exception as e:
                print("[ERROR] Failed to parse uptime:", e)

        cpu_usage = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.CPUPerc}}", "bedrock-server"],
            capture_output=True,
            text=True
        ).stdout.strip()
        ram_usage = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", "bedrock-server"],
            capture_output=True,
            text=True
        ).stdout.strip()

        return {
            "status": "Online" if is_server_running() else "Offline",
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": uptime_formatted,
            "cpu_usage": cpu_usage if cpu_usage else "Unavailable",
            "ram_usage": ram_usage if ram_usage else "Unavailable",
            "player_activity": get_player_activity()
        }
    except Exception as e:
        print(f"[ERROR] Failed to get server stats: {e}")
        return {"error": str(e)}

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, total_playtime FROM players ORDER BY total_playtime DESC LIMIT 10")
    players = [{"username": row[0], "playtime_seconds": row[1]} for row in c.fetchall()]
    conn.close()

    if not players:
        return jsonify([{"username": "No players yet", "playtime_seconds": 0}])

    return jsonify(players)

@app.route('/api/server-info', methods=['GET'])
def server_info():
    stats = get_server_stats() or {
        "status": "Offline", 
        "cpu_usage": "Unavailable", 
        "ram_usage": "Unavailable", 
        "uptime_seconds": 0, 
        "uptime_formatted": "00:00:00", 
        "player_activity": {"active_players": [], "recent_players": []}
    }
    return jsonify({
        "status": stats["status"],
        "uptime_seconds": stats["uptime_seconds"],
        "uptime_formatted": stats["uptime_formatted"],
        "cpu_usage": stats["cpu_usage"],
        "ram_usage": stats["ram_usage"],
        "player_activity": stats["player_activity"]
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
