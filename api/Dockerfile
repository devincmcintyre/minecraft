FROM ubuntu:22.04

# Install system dependencies
RUN apt update && apt install -y \
    python3 \
    python3-pip \
    curl \
    sqlite3 \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Set up a working directory
WORKDIR /app

# Install Python dependencies
RUN pip3 install --no-cache-dir flask flask_sqlalchemy
RUN pip3 install --no-cache-dir flask flask_sqlalchemy python-dateutil

# Ensure `python` points to `python3`
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Copy the Python script into the container
COPY server.py /app/server.py

# Expose the Flask API port
EXPOSE 5000

# Run the API
CMD ["python3", "/app/server.py"]