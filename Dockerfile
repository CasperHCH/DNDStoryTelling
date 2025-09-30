FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    ffmpeg \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install FFmpeg for audio processing
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install netcat-openbsd for the wait-for-it.sh script
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

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

# Verify environment variables
RUN python -c "import os; assert 'OPENAI_API_KEY' in os.environ, 'Missing OPENAI_API_KEY'; assert 'DATABASE_URL' in os.environ, 'Missing DATABASE_URL'"

# Add a script to wait for the database to be ready before running migrations
COPY wait-for-it.sh /usr/local/bin/wait-for-it
RUN chmod +x /usr/local/bin/wait-for-it

# Update the command to wait for the database before running Alembic migrations
CMD ["/usr/local/bin/wait-for-it", "db:5432", "--", "alembic", "upgrade", "head"]