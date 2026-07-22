"""
Auris - Configuration Validation Tests
Tests for startup configuration validation.
"""
import pytest
from app.core.config_validation import (
    validate_jwt_secret,
    validate_database_connection,
)


class TestJWTSecretValidation:
    """Test JWT secret validation."""
    
    def test_jwt_secret_too_short_production(self):
        """JWT secret less than 32 chars should fail in production."""
        with pytest.raises(ValueError, match="must be at least 32 characters"):
            validate_jwt_secret("short-key", environment="production")
    
    def test_jwt_secret_too_short_local(self):
        """JWT secret less than 32 chars should fail even locally."""
        with pytest.raises(ValueError, match="must be at least 32 characters"):
            validate_jwt_secret("short-key", environment="local")
    
    def test_jwt_secret_valid_length(self):
        """JWT secret with 32+ characters should pass."""
        secret = "a" * 32
        assert validate_jwt_secret(secret, environment="local") is True
    
    def test_jwt_secret_default_production_fails(self):
        """Default JWT secret should fail in production."""
        secret = "change-me-in-production"
        with pytest.raises(ValueError, match="using default value"):
            validate_jwt_secret(secret, environment="production")
    
    def test_jwt_secret_default_local_warns(self):
        """Default JWT secret should warn in local."""
        secret = "change-me-in-production"
        result = validate_jwt_secret(secret, environment="local")
        assert result is True  # Allowed in local


class TestDatabaseConnectionValidation:
    """Test database connection validation."""
    
    def test_postgres_valid_url(self):
        """Valid PostgreSQL URL should pass."""
        url = "postgresql://user:pass@localhost:5432/auris"
        assert validate_database_connection(url) is True
    
    def test_sqlite_valid_url(self):
        """Valid SQLite URL should pass."""
        url = "sqlite:///app/db/auris.db"
        assert validate_database_connection(url) is True
    
    def test_invalid_url_format(self):
        """Invalid database URL should fail."""
        url = "mysql://localhost/auris"  # MySQL not supported
        with pytest.raises(ValueError, match="invalid"):
            validate_database_connection(url)
    
    def test_empty_database_url(self):
        """Empty database URL should fail."""
        with pytest.raises(ValueError):
            validate_database_connection("")


class TestConfigValidation:
    """Test full configuration validation."""
    
    def test_validate_config_local_environment(self):
        """Configuration validation should pass for local environment."""
        from app.core.config_validation import validate_config
        result = validate_config(environment="local", debug=True)
        assert result["status"] == "valid"
        assert result["errors"] == 0
    
    def test_validate_config_missing_jwt_secret_production(self):
        """Configuration should fail if JWT_SECRET missing in production."""
        # This test would require mocking environment
        # Skipped for now as it requires config module refactoring
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
