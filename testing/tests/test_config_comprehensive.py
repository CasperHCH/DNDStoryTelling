"""Comprehensive tests for configuration management."""

import os
import pytest
from unittest.mock import patch
from app.config import Settings, get_settings


class TestSettings:
    """Test configuration settings."""

    def test_default_settings(self):
        """Test default configuration values.""" 
        with patch.dict(os.environ, {
            'DATABASE_URL': 'sqlite:///test.db',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation'
        }):
            settings = Settings()
            
            # Test default values that exist in the actual Settings class
            assert settings.APP_NAME == "D&D Story Telling"
            assert settings.VERSION == "1.0.0"
            assert settings.DEBUG is False
            assert settings.ENVIRONMENT == "development"
            assert settings.DATABASE_URL is not None
            assert settings.SECRET_KEY is not None
            assert settings.is_testing is False  # Should be False by default

    def test_environment_overrides(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            'DEBUG': 'true',
            'DATABASE_URL': 'postgresql://test:test@localhost/testdb',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation-here',
            'OPENAI_API_KEY': 'test-openai-key',
            'ALLOWED_HOSTS': 'localhost,127.0.0.1,example.com',
            'ENVIRONMENT': 'production'
        }):
            settings = Settings()
            
            assert settings.DEBUG is True
            assert 'postgresql+asyncpg://' in settings.DATABASE_URL  # Should be converted to async
            assert settings.SECRET_KEY == 'test-secret-key-that-is-long-enough-for-validation-here'
            assert settings.OPENAI_API_KEY == 'test-openai-key'
            assert settings.ALLOWED_HOSTS == 'localhost,127.0.0.1,example.com'
            assert settings.ENVIRONMENT == 'production'

    def test_database_url_postgresql_conversion(self):
        """Test PostgreSQL URL conversion to async driver."""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://user:pass@localhost/db',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation'
        }):
            settings = Settings()
            # Should convert postgresql:// to postgresql+asyncpg://
            assert settings.DATABASE_URL.startswith('postgresql+asyncpg://')

    def test_allowed_hosts_parsing(self):
        """Test allowed hosts configuration."""
        with patch.dict(os.environ, {
            'ALLOWED_HOSTS': 'host1.com,host2.com,host3.com',
            'DATABASE_URL': 'sqlite:///test.db',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation'
        }):
            settings = Settings()
            assert settings.ALLOWED_HOSTS == 'host1.com,host2.com,host3.com'
            
            # Test the property method
            hosts = settings.allowed_hosts_list
            assert 'host1.com' in hosts
            assert 'host2.com' in hosts
            assert 'host3.com' in hosts

    def test_environment_validation(self):
        """Test environment setting validation."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DATABASE_URL': 'sqlite:///test.db',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation'
        }):
            settings = Settings()
            assert settings.ENVIRONMENT == 'production'

    def test_api_key_configurations(self):
        """Test API key configurations."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123',
            'CONFLUENCE_API_TOKEN': 'conf-token-123',
            'CONFLUENCE_URL': 'https://company.atlassian.net',
            'DATABASE_URL': 'sqlite:///test.db',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation'
        }):
            settings = Settings()
            
            assert settings.OPENAI_API_KEY == 'sk-test123'
            assert settings.CONFLUENCE_API_TOKEN == 'conf-token-123'
            assert settings.CONFLUENCE_URL == 'https://company.atlassian.net'

    def test_file_upload_configurations(self):
        """Test file upload configurations."""
        with patch.dict(os.environ, {
            'MAX_FILE_SIZE': '10485760',  # 10MB
            'UPLOAD_DIR': 'custom_uploads',
            'SUPPORTED_AUDIO_FORMATS': 'mp3,wav,m4a',
            'DATABASE_URL': 'sqlite:///test.db',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation'
        }):
            settings = Settings()
            
            assert settings.MAX_FILE_SIZE == 10485760
            assert settings.UPLOAD_DIR == 'custom_uploads'
            assert settings.SUPPORTED_AUDIO_FORMATS == 'mp3,wav,m4a'

    def test_boolean_conversion(self):
        """Test boolean environment variable conversion."""
        base_env = {
            'DATABASE_URL': 'sqlite:///test.db',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation'
        }
        
        # Test true values
        for true_val in ['true', 'True', 'TRUE', '1']:
            env = {**base_env, 'DEBUG': true_val}
            with patch.dict(os.environ, env):
                settings = Settings()
                assert settings.DEBUG is True
        
        # Test false values  
        for false_val in ['false', 'False', 'FALSE', '0']:
            env = {**base_env, 'DEBUG': false_val}
            with patch.dict(os.environ, env):
                settings = Settings()
                assert settings.DEBUG is False

    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2

    def test_cors_origins_configuration(self):
        """Test CORS origins configuration."""
        with patch.dict(os.environ, {
            'CORS_ORIGINS': 'http://localhost:3000,https://app.example.com',
            'DATABASE_URL': 'sqlite:///test.db',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation'
        }):
            settings = Settings()
            assert settings.CORS_ORIGINS == 'http://localhost:3000,https://app.example.com'

    def test_rate_limiting_configurations(self):
        """Test rate limiting configurations."""
        with patch.dict(os.environ, {
            'RATE_LIMIT_REQUESTS': '200',
            'RATE_LIMIT_WINDOW': '7200',  # 2 hours
            'DATABASE_URL': 'sqlite:///test.db',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation'
        }):
            settings = Settings()
            assert settings.RATE_LIMIT_REQUESTS == 200
            assert settings.RATE_LIMIT_WINDOW == 7200

    def test_database_pool_configurations(self):
        """Test database connection pool configurations."""
        with patch.dict(os.environ, {
            'DB_POOL_SIZE': '10',
            'DB_MAX_OVERFLOW': '20',
            'DB_POOL_TIMEOUT': '60',
            'DB_POOL_RECYCLE': '7200',
            'DATABASE_URL': 'sqlite:///test.db',  
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation'
        }):
            settings = Settings()
            assert settings.DB_POOL_SIZE == 10
            assert settings.DB_MAX_OVERFLOW == 20
            assert settings.DB_POOL_TIMEOUT == 60
            assert settings.DB_POOL_RECYCLE == 7200

    def test_access_token_expiry(self):
        """Test access token expiry configuration."""
        with patch.dict(os.environ, {
            'ACCESS_TOKEN_EXPIRE_MINUTES': '60',
            'DATABASE_URL': 'sqlite:///test.db',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation'
        }):
            settings = Settings()
            assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60

    def test_supported_audio_formats_property(self):
        """Test supported audio formats property."""
        with patch.dict(os.environ, {
            'SUPPORTED_AUDIO_FORMATS': 'mp3,wav,flac,ogg',
            'DATABASE_URL': 'sqlite:///test.db',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation'
        }):
            settings = Settings()
            assert settings.SUPPORTED_AUDIO_FORMATS == 'mp3,wav,flac,ogg'
            
            # Test the property method
            formats = settings.supported_audio_formats_list
            assert 'mp3' in formats
            assert 'wav' in formats
            assert 'flac' in formats
            assert 'ogg' in formats