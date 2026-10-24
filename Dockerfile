# ==============================================================================
# HouseRent - Multi-stage Containerization Dockerfile
# Module 3: Containerization Using Docker
# ==============================================================================

FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered streaming logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000 \
    DATABASE_PATH=/app/data/houserent.db \
    UPLOAD_FOLDER=/app/data/uploads

# Install system dependencies (curl for container health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code into the container
COPY app.py config.py ./
COPY database/ ./database/
COPY templates/ ./templates/
COPY static/ ./static/

# Create persistent data and uploads directory and a non-privileged user for security
RUN mkdir -p /app/data /app/data/uploads && \
    useradd -u 10001 -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose web service port
EXPOSE 5000

# Container health check using the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Launch using production-grade WSGI server Gunicorn with 3 worker processes
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5000", "app:app"]
