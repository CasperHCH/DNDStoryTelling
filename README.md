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

To configure the application, use the web UI to provide the following details:

1. **Confluence URL**: The base URL of your Confluence instance (e.g., `https://your-domain.atlassian.net`).
2. **Confluence API Token**: Your API token for authenticating with Confluence.
3. **Confluence Parent Page ID**: The ID of the parent page where stories will be published.
4. **OpenAI API Key**: Your API key for accessing OpenAI services.

### Steps:
1. Start the application using Docker.
2. Open the web UI in your browser.
3. Navigate to the Configuration section.
4. Fill in the required fields and click "Save Configuration."

The application will validate and store the provided settings.

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.