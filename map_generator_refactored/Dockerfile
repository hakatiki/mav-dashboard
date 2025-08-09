# Lightweight Python image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Ensure entrypoint is executable
RUN chmod +x /app/entrypoint.sh

# Default entrypoint forwards CLI args to the module
ENTRYPOINT ["/app/entrypoint.sh"]
CMD []


