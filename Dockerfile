# Use Python 3.9 slim image for smaller size
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for web scraping and health checks
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud SDK
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && apt-get install -y google-cloud-cli && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY scraper/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the scraper directory
COPY scraper/ ./scraper/

# Copy the CSV data to the correct location for the web_scraper.py path reference
COPY scraper/data/ ./data/

# Copy stations.json (now accessible since Dockerfile is in root)
COPY stations/stations.json ./stations/

# Copy the CSV data files
COPY ends/ ./ends/

# Create necessary directories
RUN mkdir -p scraper/json_output scraper/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json

# Make scripts executable
RUN chmod +x scraper/automated_scraper.py scraper/web_scraper.py

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Health check - check web service health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command - start web service with gunicorn for better production performance
# This can be overridden for Cloud Run Jobs
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "3600", "--keep-alive", "2", "scraper.web_scraper:app"] 