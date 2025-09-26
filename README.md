# D&D Story Telling

An automated story generation tool for Dungeons & Dragons sessions that processes audio/text recordings and generates narrative summaries using AI, featuring a user-friendly web interface.

## Features

- User-friendly web interface with drag-and-drop file upload
- Real-time chat interface for AI interaction
- Audio to text conversion using OpenAI Whisper
- Story generation using GPT-4
- Confluence Cloud integration for story publishing
- Support for multiple audio formats (.mp3, .wav)
- Session continuity tracking
- Docker support for easy deployment

## Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Confluence Cloud API token

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/CasperHCH/DNDStoryTelling.git
cd DNDStoryTelling
```

2. Create and configure .env file:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

3. Build and run with Docker:
```bash
docker-compose up -d
```

4. Access the application:
   - Open http://localhost:8000 in your browser
   - Use the drag-and-drop interface to upload files
   - Interact with the AI through the chat interface

## Usage Guide

### File Upload
- Drag and drop your D&D session recording or text file
- Supported formats: .mp3, .wav (audio), .txt (text)
- Maximum file size: Unlimited (dependent on server capacity)

### AI Interaction
- Chat with the AI to refine the story
- Provide context and clarifications
- Specify tone and style preferences
- Review and approve generated content

### Publishing to Confluence
- Review the final story
- Select parent page in Confluence
- Approve for publishing

## Development Setup

### Local Development
1. Create virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

### Project Structure
```
DNDStoryTelling/
├── app/
│   ├── static/          # Static files (JS, CSS)
│   ├── templates/       # HTML templates
│   ├── routes/          # API routes
│   ├── services/        # Business logic
│   ├── models/          # Database models
│   └── auth/           # Authentication
├── postgres/           # PostgreSQL configuration
├── tests/             # Test files
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Application secret key
- `OPENAI_API_KEY`: OpenAI API key
- `CONFLUENCE_API_TOKEN`: Confluence Cloud token
- `CONFLUENCE_URL`: Confluence instance URL
- `DEBUG`: Debug mode (True/False)

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.