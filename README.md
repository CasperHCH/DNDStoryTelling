# DNDStoryTelling

An automated story generation tool for Dungeons & Dragons sessions that processes audio/text recordings and generates narrative summaries using AI.

## Features

- Audio to text conversion using OpenAI Whisper
- Story generation using GPT-4
- Confluence Cloud integration for story publishing
- Support for multiple audio formats (.mp3, .wav)
- Session continuity tracking
- Docker support for easy deployment

## Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15 or higher
- Docker (optional)
- FFmpeg (for audio processing)
- OpenAI API key
- Confluence Cloud API token

### Clone the Repository

```bash
git clone git@github.com:CasperHCH/DNDStoryTelling.git
cd DNDStoryTelling
```

### Installation

#### Local Development Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg:
   - Download from: https://ffmpeg.org/download.html
   - Add to system PATH

4. Create .env file:
```bash
cp .env.example .env
```

5. Configure your .env file with:
   - Database credentials
   - OpenAI API key
   - Confluence Cloud token
   - Secret key for JWT

#### Docker Setup

1. Build and run using Docker Compose:
```bash
docker-compose up --build
```

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `OPENAI_API_KEY`: Your OpenAI API key
- `CONFLUENCE_API_TOKEN`: Confluence Cloud API token
- `CONFLUENCE_URL`: Your Confluence instance URL
- `DEBUG`: Debug mode (True/False)

### Database Setup

1. Create PostgreSQL database:
```bash
createdb dndstory
```

2. Run migrations:
```bash
alembic upgrade head
```

## Usage

### Starting the Application

1. Local development:
```bash
uvicorn app.main:app --reload
```

2. Docker:
```bash
docker-compose up
```

### Processing a D&D Session

1. Upload your session recording or text file through the API
2. Review and verify the generated story
3. Approve for publishing to Confluence

### API Endpoints

- `POST /auth/register`: Register new user
- `POST /auth/token`: Get authentication token
- `POST /story/upload`: Upload session recording/text
- `POST /confluence/publish`: Publish story to Confluence

## Testing

Run the test suite:

```bash
pytest
```

For coverage report:

```bash
pytest --cov=app --cov-report=html
```

## Deployment

### Synology DS718+

1. Install Docker Package from Package Center
2. Upload docker-compose.yml and .env files
3. Run:
```bash
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository.