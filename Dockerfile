FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    ffmpeg \
    libpq-dev \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its browsers
RUN pip install playwright && playwright install --with-deps

# Install ffmpeg-python explicitly
RUN pip install ffmpeg-python

# Install asyncpg for asynchronous database support
RUN pip install asyncpg

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