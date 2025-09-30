# Copilot Instructions

## Overview
This repository is an automated story generation tool for Dungeons & Dragons sessions. It processes audio/text recordings and generates narrative summaries using AI, featuring a user-friendly web interface. The project integrates with OpenAI Whisper for audio-to-text conversion, GPT-4 for story generation, and Confluence Cloud for publishing.

## Folder Structure
- `app/`: Contains the main application code, including routes, services, and models.
- `alembic/`: Database migration scripts.
- `tests/`: Unit and integration tests.
- `scripts/`: Utility scripts for maintenance and setup.
- `.github/workflows/`: CI/CD workflows for testing and deployment.

## Key Features
- Audio-to-text conversion using OpenAI Whisper.
- Story generation using GPT-4.
- Confluence Cloud integration for publishing stories.
- Docker support for easy deployment.
- Real-time chat interface for AI interaction.

## Development Guidelines
1. **Environment Setup**:
   - Use the `.env` or the `.env.example` file to configure environment variables.
   - Install dependencies using `pip install -r requirements.txt`.
   - Use Docker for consistent development and deployment environments.

2. **Testing**:
   - Run unit tests with `pytest`.
   - Use `pytest --cov=app` to generate coverage reports.
   - UI tests are located in `tests/ui/` and require Playwright.

3. **Database Migrations**:
   - Use Alembic for database migrations.
   - Migration scripts are stored in the `alembic/versions/` directory.

4. **Logging and Error Handling**:
   - Ensure all services log meaningful messages.
   - Handle errors gracefully and provide actionable feedback.

## CI/CD Workflows
- **Python Tests**:
  - Located in `.github/workflows/tests.yml`.
  - Runs unit tests and uploads coverage reports to Codecov.
  - Requires secrets for `OPENAI_API_KEY`, `CONFLUENCE_API_TOKEN`, and `CONFLUENCE_URL`.

- **UI Tests**:
  - Located in `.github/workflows/ui-tests.yml`.
  - Runs Playwright-based UI tests and uploads HTML reports as artifacts.

## Project-Specific Conventions
- **Function Naming**: Use descriptive names that reflect the purpose of the function.
- **API Keys**: Store sensitive keys in the `.env` file and access them via environment variables.
- **Docker**: Always test changes in the Dockerized environment to ensure compatibility.

## Integration Points
- **OpenAI Whisper**: For audio-to-text conversion.
- **GPT-4**: For generating narrative summaries.
- **Confluence Cloud**: For publishing generated stories.

## Notes for AI Agents
- Focus on improving test coverage and ensuring compatibility with Docker.
- Prioritize robust error handling and meaningful logging.
- Refer to `app/` for core application logic and `tests/` for examples of test patterns.
- Ensure environment variables are correctly managed and documented.
- Update or add documentation as needed, especially in `README.md` and inline comments.
- Refer to `app/` for core application logic and `tests/` for examples of test patterns.
- Always follow the existing coding style and conventions used in the repository.
- Avoid introducing breaking changes without proper versioning and documentation.
- Always use best practices for security and coding, especially when handling API keys and sensitive data.

## Contact
For any questions or contributions, please contact the repository maintainer.