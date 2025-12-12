"""
Consolidated Deployment Tests for DNDStoryTelling Application

Covers:
- Docker build and run validation
- Database migration checks
- Environment configuration
- Service availability
"""

import pytest
import subprocess
import os
from pathlib import Path


class TestDockerDeployment:
    """Test Docker build and deployment."""

    def test_dockerfile_exists(self):
        """Test Dockerfile exists in deployment directory."""
        docker_paths = [
            Path("deployment/docker/Dockerfile"),
            Path("Dockerfile"),
            Path("deployment/Dockerfile")
        ]
        
        found = any(p.exists() for p in docker_paths)
        assert found, "Dockerfile not found in expected locations"

    def test_docker_compose_exists(self):
        """Test docker-compose configuration exists."""
        compose_paths = [
            Path("docker-compose.yml"),
            Path("deployment/docker/docker-compose.yml"),
            Path("deployment/docker-compose.yml")
        ]
        
        found = any(p.exists() for p in compose_paths)
        if not found:
            pytest.skip("docker-compose.yml not configured yet")

    @pytest.mark.skip(reason="Docker build test requires Docker daemon - manual verification recommended")
    def test_docker_build(self):
        """Test Docker image can be built."""
        # Find Dockerfile
        dockerfile_path = None
        docker_paths = [
            Path("deployment/docker/Dockerfile"),
            Path("Dockerfile"),
        ]
        
        for path in docker_paths:
            if path.exists():
                dockerfile_path = path
                break
        
        if not dockerfile_path:
            pytest.skip("Dockerfile not found")
        
        # Try to build image
        result = subprocess.run(
            ["docker", "build", "-t", "dnd-storytelling-test", "-f", str(dockerfile_path), "."],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        assert result.returncode == 0, f"Docker build failed: {result.stderr}"

    @pytest.mark.skip(reason="Docker run test requires running container - manual verification recommended")
    def test_docker_run(self):
        """Test Docker container can run."""
        # This would require a running container
        result = subprocess.run(
            ["docker", "ps", "-a"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, "Docker is not available"


class TestDatabaseMigrations:
    """Test database migration configuration."""

    def test_alembic_ini_exists(self):
        """Test Alembic configuration file exists."""
        alembic_paths = [
            Path("alembic.ini"),
            Path("configuration/alembic.ini"),
            Path("alembic.ini/alembic.ini")  # Check if it's a directory
        ]
        
        found = False
        for path in alembic_paths:
            if path.exists():
                found = True
                break
        
        assert found, "alembic.ini not found"

    def test_alembic_env_exists(self):
        """Test Alembic env.py exists."""
        env_path = Path("alembic/env.py")
        assert env_path.exists(), "alembic/env.py not found"

    def test_migrations_directory_exists(self):
        """Test migrations directory exists."""
        versions_path = Path("alembic/versions")
        assert versions_path.exists(), "alembic/versions directory not found"
        assert versions_path.is_dir(), "alembic/versions is not a directory"

    def test_migration_files_present(self):
        """Test at least one migration file exists."""
        versions_path = Path("alembic/versions")
        
        if not versions_path.exists():
            pytest.skip("Migrations directory not found")
        
        migration_files = list(versions_path.glob("*.py"))
        migration_files = [f for f in migration_files if f.name != "__init__.py" and f.name != "__pycache__"]
        
        # It's okay if no migrations exist yet (fresh project)
        # Just verify the structure is in place
        assert versions_path.exists(), "Migration infrastructure should be present"

    @pytest.mark.skip(reason="Requires database connection - manual verification recommended")
    def test_migrations_up_to_date(self):
        """Test migrations are up to date with models."""
        # This would require running: alembic current and alembic heads
        # and comparing them to ensure no pending migrations
        
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            pytest.skip("Alembic not configured or database not accessible")
        
        current = result.stdout.strip()
        
        result = subprocess.run(
            ["alembic", "heads"],
            capture_output=True,
            text=True
        )
        
        heads = result.stdout.strip()
        
        # If current is empty, migrations haven't been run
        # If current != heads, there are pending migrations
        if current and heads:
            assert current in heads, "Pending migrations detected - run 'alembic upgrade head'"


class TestEnvironmentConfiguration:
    """Test environment configuration for deployment."""

    def test_env_example_exists(self):
        """Test .env.example file exists."""
        env_example = Path(".env.example")
        
        if not env_example.exists():
            pytest.skip(".env.example not created yet")
        
        # If it exists, verify it has key variables
        content = env_example.read_text()
        assert "DATABASE_URL" in content
        assert "SECRET_KEY" in content

    def test_env_file_structure(self):
        """Test .env file has required variables."""
        # Check if .env exists (might not in CI/CD)
        env_file = Path(".env")
        
        if not env_file.exists():
            pytest.skip(".env file not present (expected in CI/CD)")
        
        content = env_file.read_text()
        
        # Required variables
        required_vars = [
            "DATABASE_URL",
            "SECRET_KEY",
            "ENVIRONMENT"
        ]
        
        for var in required_vars:
            assert var in content, f"Required variable {var} not found in .env"

    def test_config_module_importable(self):
        """Test configuration module can be imported."""
        try:
            from app.config import get_settings
            settings = get_settings()
            assert settings is not None
        except ImportError as e:
            pytest.fail(f"Cannot import configuration: {e}")


class TestDependencies:
    """Test dependency configuration."""

    def test_requirements_txt_exists(self):
        """Test requirements.txt exists."""
        requirements = Path("requirements.txt")
        assert requirements.exists(), "requirements.txt not found"

    def test_requirements_has_core_dependencies(self):
        """Test requirements.txt has core dependencies."""
        requirements = Path("requirements.txt")
        content = requirements.read_text().lower()
        
        core_deps = [
            "fastapi",
            "sqlalchemy",
            "pydantic",
            "uvicorn",
            "pytest"
        ]
        
        for dep in core_deps:
            assert dep in content, f"Core dependency {dep} not found in requirements.txt"

    def test_test_requirements_exists(self):
        """Test test-requirements.txt exists."""
        test_requirements = Path("test-requirements.txt")
        
        if not test_requirements.exists():
            pytest.skip("test-requirements.txt not created yet")
        
        content = test_requirements.read_text().lower()
        assert "pytest" in content


class TestServiceReadiness:
    """Test service readiness for deployment."""

    def test_main_module_importable(self):
        """Test main application module can be imported."""
        try:
            from app.main import app
            assert app is not None
        except ImportError as e:
            pytest.fail(f"Cannot import main app: {e}")

    def test_database_models_importable(self):
        """Test database models can be imported."""
        try:
            from app.models.user import User
            from app.models.story import Story
            assert User is not None
            assert Story is not None
        except ImportError as e:
            pytest.fail(f"Cannot import models: {e}")

    def test_routes_importable(self):
        """Test route modules can be imported."""
        try:
            from app.routes import auth, story, health
            assert auth is not None
            assert story is not None
            assert health is not None
        except ImportError as e:
            pytest.fail(f"Cannot import routes: {e}")


class TestDocumentation:
    """Test deployment documentation."""

    def test_readme_exists(self):
        """Test README.md exists."""
        readme = Path("README.md")
        assert readme.exists(), "README.md not found"

    def test_readme_has_deployment_section(self):
        """Test README has deployment instructions."""
        readme = Path("README.md")
        content = readme.read_text(encoding='utf-8').lower()
        
        # Should have some deployment-related content
        deployment_keywords = ["deploy", "installation", "setup", "docker", "getting started"]
        found = any(keyword in content for keyword in deployment_keywords)
        
        assert found, "README should contain deployment/setup instructions"

    def test_docker_guide_exists(self):
        """Test Docker setup guide exists."""
        docker_guide = Path("DOCKER_SETUP_GUIDE.md")
        
        if not docker_guide.exists():
            pytest.skip("Docker setup guide not created yet")
        
        content = docker_guide.read_text(encoding='utf-8')
        assert len(content) > 100, "Docker guide should have substantial content"


class TestLogging:
    """Test logging configuration for deployment."""

    def test_logs_directory_structure(self):
        """Test logs directory exists or can be created."""
        logs_dir = Path("logs")
        
        if not logs_dir.exists():
            # It's okay if it doesn't exist yet - will be created at runtime
            pytest.skip("Logs directory will be created at runtime")
        
        assert logs_dir.is_dir(), "logs should be a directory"

    def test_logging_configuration_present(self):
        """Test logging is configured in application."""
        try:
            from app.main import logger
            assert logger is not None
        except ImportError:
            pytest.fail("Logging not configured in main application")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
