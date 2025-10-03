# 🤝 Contributing to D&D Story Telling

> **Welcome contributors! Help us build the ultimate AI-powered D&D story generation platform.**

We're excited to have you contribute to D&D Story Telling! This guide will help you get started with development, understand our codebase, and submit meaningful contributions.

## 🚀 Quick Start for Contributors

### 1. **Development Setup**

```bash
# Fork and clone your fork
git clone https://github.com/YOUR_USERNAME/DNDStoryTelling.git
cd DNDStoryTelling

# Add upstream remote
git remote add upstream https://github.com/CasperHCH/DNDStoryTelling.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -r test-requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your development settings
```

### 2. **Configure Development Environment**

```bash
# .env for development
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./test.db
SECRET_KEY=dev-secret-key-for-development-only
OPENAI_API_KEY=your-development-api-key-here
```

### 3. **Run the Application**

```bash
# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, run database migrations
alembic upgrade head

# Access the application
# Web UI: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 🏗️ Project Architecture

### 📁 **Codebase Structure**

```
DNDStoryTelling/
├── 📱 app/                          # Main application
│   ├── 🔐 auth/                     # Authentication & JWT handling
│   │   ├── auth_handler.py          # JWT token management
│   │   └── dependencies.py          # Auth dependencies
│   ├── 🛡️ middleware/               # Request/response middleware
│   │   └── security.py              # Security headers & logging
│   ├── 📊 models/                   # Database models & schemas
│   │   ├── database.py              # Database connection
│   │   ├── user.py                  # User model
│   │   └── story.py                 # Story model
│   ├── 🛣️ routes/                   # API endpoints
│   │   ├── auth.py                  # Authentication endpoints
│   │   ├── health.py                # Health check endpoints
│   │   ├── story.py                 # Story processing endpoints
│   │   └── confluence.py            # Confluence integration
│   ├── ⚙️ services/                 # Business logic
│   │   ├── audio_processor.py       # Whisper integration
│   │   ├── story_generator.py       # GPT integration
│   │   └── confluence.py            # Confluence API client
│   ├── 🎨 static/                   # Frontend assets
│   │   ├── css/                     # Stylesheets
│   │   ├── js/                      # JavaScript files
│   │   └── images/                  # Images and icons
│   ├── 📄 templates/                # Jinja2 HTML templates
│   │   ├── base.html                # Base template
│   │   ├── index.html               # Main page
│   │   └── chat.html                # Chat interface
│   ├── 🔧 utils/                    # Utility functions
│   │   └── temp_manager.py          # Temporary file management
│   ├── ⚙️ config.py                 # Application configuration
│   └── 🚀 main.py                   # FastAPI application entry
├── 🗄️ alembic/                     # Database migrations
├── 🧪 tests/                        # Test suite
│   ├── 🌐 ui/                       # Browser/UI tests (Playwright)
│   ├── test_auth.py                 # Authentication tests
│   ├── test_audio_processor.py      # Audio processing tests
│   ├── test_health_check.py         # Health endpoint tests
│   └── conftest.py                  # Test configuration
├── 📄 docs/                         # Documentation
└── 🛠️ scripts/                     # Utility scripts
```

### 🔧 **Technology Stack**

#### Backend Framework
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **SQLAlchemy**: Async ORM for database operations
- **Alembic**: Database migration management
- **Pydantic**: Data validation and serialization

#### AI & Processing
- **OpenAI Whisper**: Speech-to-text conversion
- **OpenAI GPT**: Story generation and chat
- **PyDub**: Audio file processing
- **FFmpeg**: Audio format conversion

#### Frontend
- **Vanilla JavaScript**: Lightweight, no framework dependencies
- **Modern CSS3**: Responsive design with CSS Grid and Flexbox
- **WebSocket**: Real-time communication for chat

#### Database
- **PostgreSQL**: Production database
- **SQLite**: Development/testing database
- **AsyncPG**: Async PostgreSQL driver

## 📝 Development Guidelines

### 🐍 **Python Code Standards**

#### Code Style
```python
# Follow PEP 8 with these specifics:
# - Line length: 88 characters (Black formatter)
# - Use type hints for all functions
# - Docstrings in Google style

from typing import Optional, Dict, List
from pydantic import BaseModel

class StoryRequest(BaseModel):
    \"\"\"Request model for story generation.

    Args:
        text: The input text to process
        tone: Optional tone for the story
        length: Desired story length
    \"\"\"
    text: str
    tone: Optional[str] = None
    length: int = 500

async def generate_story(
    request: StoryRequest,
    user_id: int
) -> Dict[str, str]:
    \"\"\"Generate a D&D story from input text.

    Args:
        request: Story generation request
        user_id: ID of the requesting user

    Returns:
        Dictionary containing generated story and metadata

    Raises:
        ValueError: If request validation fails
        OpenAIError: If AI service is unavailable
    \"\"\"
    # Implementation here
    pass
```

#### Error Handling
```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def process_audio(file_path: str) -> str:
    try:
        # Processing logic
        result = await whisper_service.transcribe(file_path)
        return result
    except FileNotFoundError:
        logger.error(f"Audio file not found: {file_path}")
        raise HTTPException(status_code=404, detail="Audio file not found")
    except Exception as e:
        logger.exception(f"Audio processing failed: {e}")
        raise HTTPException(status_code=500, detail="Audio processing failed")
```

### 🌐 **Frontend Standards**

#### JavaScript
```javascript
// Use modern ES6+ features
// Modular approach with classes

class AudioUploader {
    constructor(uploadAreaId) {
        this.uploadArea = document.getElementById(uploadAreaId);
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        this.uploadArea.addEventListener('drop', this.handleDrop.bind(this));
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Upload error:', error);
            throw error;
        }
    }
}
```

#### CSS
```css
/* Use CSS custom properties for theming */
:root {
    --primary-color: #3b82f6;
    --secondary-color: #6b7280;
    --background-color: #f9fafb;
    --text-color: #111827;
    --border-radius: 0.5rem;
    --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Mobile-first responsive design */
.upload-area {
    border: 2px dashed var(--secondary-color);
    border-radius: var(--border-radius);
    padding: 2rem;
    text-align: center;
    transition: all 0.3s ease;
}

.upload-area:hover {
    border-color: var(--primary-color);
    background-color: rgba(59, 130, 246, 0.05);
}

@media (min-width: 768px) {
    .upload-area {
        padding: 3rem;
    }
}
```

### 🗄️ **Database Guidelines**

#### Model Definition
```python
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.models.database import Base

class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_published = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="stories")
```

#### Migration Best Practices
```python
# alembic/versions/001_create_stories_table.py
\"\"\"Create stories table

Revision ID: 001
Revises:
Create Date: 2025-09-30 12:00:00.000000
\"\"\"
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'stories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stories_title'), 'stories', ['title'])

def downgrade():
    op.drop_index(op.f('ix_stories_title'), table_name='stories')
    op.drop_table('stories')
```

## 🧪 Testing Strategy

### 🏃 **Running Tests**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test types
pytest tests/test_auth.py                    # Authentication tests
pytest tests/test_audio_processor.py         # Audio processing tests
pytest tests/ui/ --headed                    # UI tests with browser visible

# Run tests in Docker (CI environment)
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### 🧪 **Test Categories**

#### Unit Tests
```python
# tests/test_story_generator.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.story_generator import StoryGenerator

@pytest.mark.asyncio
async def test_generate_story_success():
    \"\"\"Test successful story generation with modern OpenAI API.\"\"\"
    generator = StoryGenerator()

    with patch('openai.AsyncOpenAI') as mock_openai_class:
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Generated story"
        mock_client.chat.completions.create.return_value = mock_response

        result = await generator.generate_story("Test input")

        assert result == "Generated story"
        mock_client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_generate_story_api_error():
    \"\"\"Test story generation with API error using modern OpenAI API.\"\"\"
    generator = StoryGenerator()

    with patch('openai.AsyncOpenAI') as mock_openai_class:
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await generator.generate_story("Test input")
```

#### Integration Tests
```python
# tests/test_routes.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    \"\"\"Test health check endpoint.\"\"\"
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_upload_audio_file():
    \"\"\"Test audio file upload.\"\"\"
    with open("tests/fixtures/test_audio.wav", "rb") as audio_file:
        response = client.post(
            "/api/upload",
            files={"file": ("test_audio.wav", audio_file, "audio/wav")}
        )

    assert response.status_code == 200
    assert "transcription" in response.json()
```

#### UI Tests (Playwright)
```python
# tests/ui/test_upload.py
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_file_upload_interface():
    \"\"\"Test file upload drag and drop interface.\"\"\"
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate to application
        await page.goto("http://localhost:8000")

        # Verify upload area exists
        upload_area = page.locator("[data-testid='upload-area']")
        await expect(upload_area).to_be_visible()

        # Test file selection
        file_input = page.locator("input[type='file']")
        await file_input.set_input_files("tests/fixtures/test_audio.wav")

        # Verify upload starts
        progress_bar = page.locator("[data-testid='progress-bar']")
        await expect(progress_bar).to_be_visible()

        await browser.close()
```

### 📊 **Coverage Requirements**

- **Overall Coverage**: Minimum 80%
- **New Code**: 90% coverage required
- **Critical Paths**: 100% coverage (auth, payment, data processing)

## 🔄 Contribution Workflow

### 1. **Planning Your Contribution**

#### Types of Contributions
- 🐛 **Bug Fixes**: Fix issues, improve error handling
- ✨ **New Features**: Add functionality, integrations
- 📚 **Documentation**: Improve guides, add examples
- 🎨 **UI/UX**: Enhance interface, accessibility
- ⚡ **Performance**: Optimize code, reduce latency
- 🧪 **Testing**: Add test coverage, improve reliability

#### Before You Start
1. **Check existing issues** and discussions
2. **Create or comment on issue** to discuss approach
3. **Fork the repository** to your GitHub account
4. **Create feature branch** from `main`

### 2. **Development Process**

```bash
# Create feature branch
git checkout -b feature/add-story-templates

# Make your changes
# ... development work ...

# Run tests locally
pytest
pytest --cov=app

# Run linting
black app/ tests/
flake8 app/ tests/
mypy app/

# Commit with descriptive messages
git add .
git commit -m "✨ Add story template system

- Add template model and database schema
- Implement template selection in UI
- Add template management endpoints
- Include comprehensive tests and documentation

Fixes #123"
```

### 3. **Pull Request Guidelines**

#### PR Title Format
```
<type>(<scope>): <description>

Examples:
✨ feat(auth): add OAuth2 integration
🐛 fix(audio): handle corrupt file uploads
📚 docs(api): update endpoint documentation
🎨 style(ui): improve mobile responsiveness
⚡ perf(db): optimize story query performance
🧪 test(routes): add integration test coverage
```

#### PR Description Template
```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Manual testing completed

## Screenshots (if applicable)
Include screenshots for UI changes.

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes (or breaking changes documented)
```

### 4. **Code Review Process**

#### For Contributors
- **Respond promptly** to review feedback
- **Keep PRs focused** - one feature/fix per PR
- **Update documentation** alongside code changes
- **Maintain backward compatibility** when possible

#### Review Checklist
- [ ] ✅ Code follows project standards
- [ ] 🧪 Tests cover new functionality
- [ ] 📚 Documentation updated
- [ ] 🔒 Security considerations addressed
- [ ] ⚡ Performance impact acceptable
- [ ] 🎯 Code solves the intended problem

## 🏷️ Release Process

### Version Numbering (Semantic Versioning)
- **Major** (1.0.0): Breaking changes
- **Minor** (0.1.0): New features, backward compatible
- **Patch** (0.0.1): Bug fixes, backward compatible

### Release Workflow
1. **Create release branch**: `release/v1.2.0`
2. **Update version numbers** in relevant files
3. **Update CHANGELOG.md** with new features/fixes
4. **Run full test suite** and manual testing
5. **Create release PR** to `main`
6. **Tag release** after merge: `git tag v1.2.0`
7. **Deploy to production** via CI/CD

## 🎯 Areas for Contribution

### 🔥 **High Priority**
- **Audio Processing**: Improve Whisper integration, add format support
- **Story Generation**: Enhance GPT prompts, add story templates
- **User Experience**: Mobile optimization, accessibility improvements
- **Performance**: Database query optimization, caching strategies
- **Security**: Enhanced authentication, input validation

### 🚀 **Feature Ideas**
- **Multi-language Support**: I18n for global users
- **Story Collaboration**: Multi-user story editing
- **Campaign Management**: Link stories to campaigns
- **Export Options**: PDF, ePub, custom formats
- **Audio Enhancement**: Noise reduction, speaker identification
- **Integration Plugins**: Discord, Roll20, D&D Beyond

### 📚 **Documentation Needs**
- **API Examples**: More comprehensive endpoint documentation
- **Deployment Guides**: Cloud provider specific guides
- **Troubleshooting**: Common issues and solutions
- **Video Tutorials**: Setup and usage demonstrations
- **Architecture Docs**: System design documentation

## 🏆 Recognition

### Contributors Hall of Fame
We recognize contributors in:
- **README.md** acknowledgments section
- **Release notes** for significant contributions
- **GitHub contributors** page
- **Discord community** shout-outs

### Contribution Levels
- **🌟 Contributor**: First merged PR
- **⭐ Regular Contributor**: 5+ merged PRs
- **🏆 Core Contributor**: 20+ PRs, significant features
- **👑 Maintainer**: Long-term commitment, code review rights

## 📞 Getting Help

### 💬 **Communication Channels**
- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: General questions, ideas
- **Discord Server**: Real-time chat with community
- **Email**: security@dndstorytelling.dev (security issues only)

### 📖 **Resources**
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Guide**: https://docs.sqlalchemy.org/
- **Playwright Testing**: https://playwright.dev/python/
- **OpenAI API**: https://platform.openai.com/docs

### 🆘 **Getting Unstuck**
1. **Check documentation** and existing issues
2. **Search discussions** for similar questions
3. **Join Discord** for real-time help
4. **Create discussion thread** with specific details
5. **Tag maintainers** for urgent issues

## 📜 Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. Please read our [Code of Conduct](./CODE_OF_CONDUCT.md) before contributing.

### Expected Behavior
- **Be respectful** and constructive in all interactions
- **Welcome newcomers** and help them get started
- **Focus on collaboration** over competition
- **Give credit** where credit is due
- **Learn from mistakes** and help others do the same

---

<div align="center">

**🎉 Thank you for contributing to D&D Story Telling! 🎉**

*Together, we're building the future of AI-powered storytelling for the D&D community.*

[🚀 Start Contributing](https://github.com/CasperHCH/DNDStoryTelling/fork) | [💬 Join Discord](https://discord.gg/dndstorytelling) | [📖 Read Docs](./docs/)

</div>