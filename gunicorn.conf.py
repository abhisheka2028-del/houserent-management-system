"""
Gunicorn WSGI server configuration for House Rental Management System.

Compatible with Render Web Services and containerized environments.
When executing `gunicorn app:app`, Gunicorn automatically loads this configuration file.
"""
import os

# Render dynamically assigns an external listening port through the PORT env var.
# Default to 10000 as fallback for Render production, overridable by environment.
port = os.environ.get("PORT", "10000")
bind = f"0.0.0.0:{port}"

# Process & concurrency model
# Render free tier provides 512MB RAM and 0.1 CPU.
# 2 workers with 2 threads per worker provide reliable concurrency without memory pressure.
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "gthread")
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))

# Logging configuration: stream directly to stdout/stderr for Render live log viewing
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")
capture_output = True

# Forwarded headers: Render reverse proxy sets X-Forwarded-For and X-Forwarded-Proto
forwarded_allow_ips = "*"
proxy_allow_ips = "*"
