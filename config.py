import os


class BaseConfig:
    """Base configuration shared by all environments."""

    # Flask
    DEBUG = False
    TESTING = False

    # Database (PostgreSQL)
    DB_HOST = os.getenv("APP_DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("APP_DB_PORT", "5432"))
    DB_NAME = os.getenv("APP_DB_NAME", "app_db")
    DB_USER = os.getenv("APP_DB_USER", "app_user")
    DB_PASSWORD = os.getenv("APP_DB_PASSWORD", "bsd0030")
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

class DevConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True


class TestConfig(BaseConfig):
    """Test configuration."""
    TESTING = True
    # You could point to a separate test DB here if desired.
    # DB_NAME = os.getenv("APP_TEST_DB_NAME", "app_db_test")


class ProdConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    TESTING = False