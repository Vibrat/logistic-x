FROM python:3.11-slim

WORKDIR /app

# Install system deps needed by psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (overridden by volume mount in dev)
COPY . .

EXPOSE 8000

# Production start: migrate → seed → serve
# In docker-compose (dev) this CMD is overridden by the 'command:' field.
# On Render (or any container host) this runs as-is.
CMD ["sh", "-c", "alembic upgrade head && python -m db.seed && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
