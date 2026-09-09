FROM python:3.11-slim

WORKDIR /app
# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Health check for ECS/Fargate
# The health endpoint is "/", not "/health": the previous path 404'd, so this
# check could only ever report the container unhealthy.
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:5000/ || exit 1

# Matches the command in the ECS task definition; makes `docker run` work directly.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]