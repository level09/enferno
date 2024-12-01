# Use Python slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -u 1000 enferno && \
    chown -R enferno:enferno /app /opt/venv

# Install Python dependencies
COPY --chown=enferno:enferno requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY --chown=enferno:enferno . .

# Switch to non-root user
USER enferno

# Run the application
CMD ["uwsgi", "--http", "0.0.0.0:5000", "--master", "--wsgi", "run:app", "--uid", "1000"]
