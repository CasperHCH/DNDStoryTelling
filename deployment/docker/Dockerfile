# Build arguments for PIP configuration
ARG PIP_DEFAULT_TIMEOUT=300
ARG PIP_RETRIES=5

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies in single layer with cleanup
RUN apt-get update && apt-get install -y \
    gcc \
    ffmpeg \
    libpq-dev \
    netcat-openbsd \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Configure pip with build args
ENV PIP_DEFAULT_TIMEOUT=${PIP_DEFAULT_TIMEOUT}
ENV PIP_RETRIES=${PIP_RETRIES}
ENV PIP_NO_CACHE_DIR=1

# Configure testing environment
ENV PYTHONPATH=/app
ENV TESTING=1
ENV MOCK_AUDIO_PROCESSING=true
ENV SKIP_AUDIO_TESTS=false

# Copy requirements and install Python packages in single layer
COPY requirements.txt .
COPY testing/test-requirements.txt ./testing/
RUN pip install -r requirements.txt \
    && pip install -r testing/test-requirements.txt \
    && pip install playwright ffmpeg-python asyncpg \
    && playwright install --with-deps \
    && rm -rf /root/.cache/pip

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/static /app/templates /data

# Set Python path
ENV PYTHONPATH=/app

# Set default values for environment variables during build
ARG OPENAI_API_KEY=default_openai_key
ARG DATABASE_URL=postgresql+asyncpg://user:password@localhost/test_db

# Pass build arguments as environment variables
ENV OPENAI_API_KEY=$OPENAI_API_KEY
ENV DATABASE_URL=$DATABASE_URL

# Expose port
EXPOSE 8000

# Add health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]