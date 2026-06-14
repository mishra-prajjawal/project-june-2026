# Step 1: Build Frontend Assets (Tailwind CSS)
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY tailwind.config.js ./
COPY src/ ./src/
RUN npm run build:css

# Step 2: Build Python Runtime
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies for compilation (mysqlclient, psycopg2-binary, Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy built app and CSS compiled from the builder stage
COPY --from=frontend-builder /app/src/ ./src/
COPY docs/ ./docs/

# Collect static files for WhiteNoise production serving
RUN python src/manage.py collectstatic --noinput

# Expose server port
EXPOSE 8000

# Set environment defaults
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV DATABASE_URL="sqlite:///db.sqlite3"

# Entrypoint script that runs migrations, seeds demo accounts, and boots Gunicorn
CMD ["sh", "-c", "python src/manage.py migrate && python src/manage.py seed_data && gunicorn --bind 0.0.0.0:8000 --worker-class gthread --threads 20 --chdir src foodconnect.wsgi:application"]
