# Build stage
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
# Using pip as uv is not yet available in Debian repositories. 
# Alternatively, use: curl -sSf https://astral.sh/uv/install.sh | sh
RUN pip install --no-cache-dir uv

# Create virtual environment
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN uv pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim

# Copy virtual environment from build stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 enferno && \
    chown -R enferno:enferno /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY --chown=enferno:enferno . .

# Switch to non-root user
USER enferno

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

# Run the application
CMD ["uwsgi", "--http", "0.0.0.0:5000", "--master", "--wsgi", "run:app", "--uid", "1000"]
