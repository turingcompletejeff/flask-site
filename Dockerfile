# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create and switch to a non-root user
RUN groupadd --gid 1000 flask && \
    useradd --uid 1000 --gid flask --shell /bin/bash --create-home flask

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up Python environment
WORKDIR /app
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Create flask user
RUN groupadd --gid 1000 flask && \
    useradd --uid 1000 --gid flask --shell /bin/bash --create-home flask

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=flask:flask . .

# Create uploads directory with proper permissions
RUN mkdir -p uploads/blog-posts && \
    chown -R flask:flask uploads/

# Switch to non-root user
USER flask

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Use gunicorn as in your grun.sh script
CMD ["gunicorn", "--workers", "6", "--bind", "0.0.0.0:8000", "--timeout", "120", "--keepalive", "5", "run:app"]