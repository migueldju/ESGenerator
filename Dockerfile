# Use Python 3.11 slim image for better performance
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for frontend build
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy package files first (for better Docker layer caching)
COPY frontend/package*.json ./frontend/
COPY backend/requirements.txt ./backend/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Install Node dependencies and build frontend
COPY frontend/ ./frontend/
RUN cd frontend && \
    npm ci --only=production && \
    npm run build && \
    rm -rf node_modules

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend to backend's build directory
RUN cp -r frontend/dist/* backend/build/ 2>/dev/null || \
    cp -r frontend/build/* backend/build/ 2>/dev/null || \
    echo "Frontend build directory not found, continuing..."

# Create logs directory
RUN mkdir -p backend/logs

# Set working directory to backend
WORKDIR /app/backend

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port (Cloud Run uses PORT env variable)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the application
CMD exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class sync \
    --worker-connections 1000 \
    --timeout 300 \
    --keepalive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app