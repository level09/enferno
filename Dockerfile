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

# Install Python dependencies using uv (with optional wsgi extra)
COPY pyproject.toml uv.lock ./
RUN uv sync --extra wsgi --frozen --no-install-project

# Runtime stage
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy virtual environment from build stage
COPY --from=builder /app/.venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user and ensure permissions
RUN useradd -m -u 1000 enferno && \
    chown -R enferno:enferno /app /opt/venv

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
