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
docker build -t dnd_storytelling .
docker-compose up -d
```

4. Run database migrations:
```bash
docker exec -it dnd_storytelling alembic upgrade head
```

5. Access the application at `http://localhost:8000`.

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

## Configuration Options

The application requires the following environment variables to be set in the `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key for GPT-4 and Whisper.
- `CONFLUENCE_API_TOKEN`: API token for Confluence Cloud integration.
- `DATABASE_URL`: Connection string for the PostgreSQL database.
- `SECRET_KEY`: Secret key for JWT authentication.
- `FFMPEG_PATH`: Path to the FFmpeg binary for audio processing.

## Installing FFmpeg

FFmpeg is required for audio processing. Follow these steps to install it:

1. Download FFmpeg from the [official website](https://ffmpeg.org/download.html).
2. Extract the downloaded archive.
3. Add the `bin` directory to your system's PATH.

To verify the installation, run:
```bash
ffmpeg -version
```

## Installation Guide: Running the Program as a Docker Image

This guide will walk you through the steps to install and run the program as a Docker image.

### Prerequisites

1. **Docker Installed**: Ensure Docker is installed on your system. You can download it from [Docker's official website](https://www.docker.com/).
2. **Docker Compose Installed**: Install Docker Compose if it is not included with your Docker installation.
3. **Environment Variables**: Prepare the following environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key.
   - `CONFLUENCE_API_TOKEN`: Your Confluence API token.
   - `CONFLUENCE_URL`: The base URL of your Confluence instance.
   - `CONFLUENCE_PARENT_PAGE_ID`: The ID of the parent page where stories will be published.

### Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/CasperHCH/DNDStoryTelling.git
   cd DNDStoryTelling
   ```

2. **Set Up Environment Variables**
   Create a `.env` file in the `DNDStoryTelling` directory and add the following:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   CONFLUENCE_API_TOKEN=your_confluence_api_token
   CONFLUENCE_URL=https://your-domain.atlassian.net
   CONFLUENCE_PARENT_PAGE_ID=123456789
   ```

3. **Build the Docker Image**
   Run the following command to build the Docker image:
   ```bash
   docker build -t dndstorytelling:latest .
   ```

4. **Run the Application**
   Use Docker Compose to start the application:
   ```bash
   docker-compose up -d
   ```

   This will start the application and its dependencies (e.g., PostgreSQL database).

5. **Access the Application**
   Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

6. **Stop the Application**
   To stop the application, run:
   ```bash
   docker-compose down
   ```

### Notes

- Ensure the `.env` file is not shared publicly as it contains sensitive information.
- If you encounter any issues, check the logs using:
  ```bash
  docker-compose logs
  ```

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.