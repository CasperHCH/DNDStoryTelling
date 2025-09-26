# Contributing to D&D Story Telling

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment
3. Install dependencies
4. Create feature branch
5. Make changes
6. Run tests
7. Submit pull request

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for functions and classes
- Include unit tests for new features

## Project Structure

### Frontend
- `app/templates/`: Jinja2 templates
- `app/static/`: Static assets
  - `css/`: Stylesheets
  - `js/`: JavaScript files

### Backend
- `app/routes/`: API endpoints
- `app/services/`: Business logic
- `app/models/`: Database models
- `app/auth/`: Authentication

## Testing

Run tests with:
```bash
pytest
```

Generate coverage report:
```bash
pytest --cov=app --cov-report=html
```