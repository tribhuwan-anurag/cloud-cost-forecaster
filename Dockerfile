# Use slim Python 3.11 — smaller image, faster pulls
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies Prophet needs to compile
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first — Docker caches this layer
# so re-builds are fast if only your code changed
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY app/       ./app/
COPY templates/ ./templates/

# Create data directory for outputs
RUN mkdir -p /app/data

# Default command — runs the full pipeline
CMD ["python3", "app/main.py"]