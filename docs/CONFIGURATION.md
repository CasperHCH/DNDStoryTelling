# Environment Configuration Guide

The D&D Story Telling application can be fully configured using environment variables. This allows for easy deployment across different environments without code changes.

## Configuration Files

### `.env` file
Copy `.env.example` to `.env` and customize your settings:

```bash
cp .env.example .env
```

### Environment Variables Reference

#### Server Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `ENVIRONMENT` | `development` | Environment (development/production/test) |
| `DEBUG` | `False` | Enable debug mode |

#### Database Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | *Required* | Database connection string |
| `DB_POOL_SIZE` | `5` | Database connection pool size |
| `DB_MAX_OVERFLOW` | `10` | Maximum pool overflow |
| `DB_POOL_TIMEOUT` | `30` | Connection timeout seconds |
| `DB_POOL_RECYCLE` | `3600` | Connection recycle time seconds |

#### Security Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | *Required* | Application secret key (min 32 chars) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT token expiration |
| `ALLOWED_HOSTS` | `*` | Comma-separated allowed hosts |
| `CORS_ORIGINS` | `*` | Comma-separated CORS origins |

#### File Upload Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_FILE_SIZE` | `5368709120` | Maximum file size in bytes (5GB) |
| `UPLOAD_DIR` | `uploads` | Upload directory path |
| `SUPPORTED_AUDIO_FORMATS` | `mp3,wav,m4a,ogg,flac` | Supported audio formats |

#### API Integration
| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | `None` | OpenAI API key for story generation |
| `CONFLUENCE_URL` | `None` | Confluence base URL |
| `CONFLUENCE_API_TOKEN` | `None` | Confluence API token |
| `CONFLUENCE_PARENT_PAGE_ID` | `None` | Parent page ID for new stories |

#### Rate Limiting
| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_REQUESTS` | `100` | Requests per window |
| `RATE_LIMIT_WINDOW` | `3600` | Rate limit window in seconds |

#### Logging Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `LOG_FILE` | `None` | Log file path (empty for stdout) |

#### Health Check Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `HEALTH_CHECK_ENDPOINT` | `/health` | Health check endpoint path |
| `HEALTH_CHECK_TIMEOUT` | `10` | Health check timeout seconds |

#### Socket.IO Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `SOCKETIO_PING_INTERVAL` | `25000` | Ping interval in milliseconds |
| `SOCKETIO_PING_TIMEOUT` | `20000` | Ping timeout in milliseconds |
| `SOCKETIO_MAX_HTTP_BUFFER_SIZE` | `1000000` | Max HTTP buffer size in bytes |

## Common Configuration Examples

### Development Environment
```env
ENVIRONMENT=development
DEBUG=True
HOST=127.0.0.1
PORT=8000
DATABASE_URL=sqlite+aiosqlite:///./dev.db
LOG_LEVEL=DEBUG
```

### Production Environment
```env
ENVIRONMENT=production
DEBUG=False
HOST=0.0.0.0
PORT=8000
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/dndstory
SECRET_KEY=your-super-secure-secret-key-here
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log
```

### Large File Handling
```env
# Support for very large D&D session files (up to 10GB)
MAX_FILE_SIZE=10737418240
UPLOAD_DIR=/mnt/large-storage/uploads
```

### High Performance Setup
```env
# Optimized for high traffic
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```

## Docker Configuration

When using Docker, you can override settings in `docker-compose.yml`:

```yaml
services:
  web:
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - MAX_FILE_SIZE=10737418240
      - LOG_LEVEL=INFO
    ports:
      - "8001:8000"  # Map container port to host
```

## Environment-Specific Files

You can create environment-specific configuration files:

- `.env.development` - Development settings
- `.env.production` - Production settings
- `.env.test` - Test environment settings

The application will automatically load the appropriate file based on the `ENVIRONMENT` variable.

## Validation and Defaults

All configuration values are validated at startup:
- Required fields will cause startup failure if missing
- Invalid values will show helpful error messages
- All settings have sensible defaults for quick setup

## Getting Started

1. Copy the example file: `cp .env.example .env`
2. Set your OpenAI API key: `OPENAI_API_KEY=sk-your-key-here`
3. Configure your database: `DATABASE_URL=your-database-url`
4. Set a secure secret key: `SECRET_KEY=your-32-char-secret`
5. Adjust file size limits if needed: `MAX_FILE_SIZE=5368709120`
6. Start the application: `python scripts/start_server.py`

The server will display all active configuration on startup for verification.