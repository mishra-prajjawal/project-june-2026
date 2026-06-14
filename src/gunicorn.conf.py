import os

# Gunicorn configuration
# This file is automatically loaded by Gunicorn to configure worker settings.

# Bind address and port
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Use the threaded worker class to support concurrent SSE stream connections
worker_class = "gthread"

# Allocate threads to handle multiple concurrent requests without blocking
threads = 20

# Keepalive and timeout settings
timeout = 60
keepalive = 5
