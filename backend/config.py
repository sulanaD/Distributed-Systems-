import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application configuration using Pydantic"""
    
    # Application
    APP_NAME: str = "Distributed Banking System"
    DEBUG: bool = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Database
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'bankingdb')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'password')
    
    # Redis
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD: str | None = os.getenv('REDIS_PASSWORD', None)
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_CONSUMER_GROUP: str = os.getenv('KAFKA_CONSUMER_GROUP', 'banking-consumers')
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_ALGORITHM: str = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS
    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', 'http://localhost,http://localhost:3000,http://localhost:80')
    
    @field_validator('CORS_ORIGINS')
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # Cache TTLs (seconds)
    CACHE_TTL_SESSION: int = 1800  # 30 minutes
    CACHE_TTL_BALANCE: int = 300   # 5 minutes
    CACHE_TTL_ACCOUNT: int = 600   # 10 minutes
    CACHE_TTL_IDEMPOTENCY: int = 86400  # 24 hours
    
    # Transfer settings
    MIN_TRANSFER_AMOUNT: float = 0.01
    MAX_TRANSFER_AMOUNT: float = 1000000.00
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        case_sensitive = True

settings = Settings()

# Legacy support for old Config class
class Config:
    """Legacy configuration class for backward compatibility"""
    DB_HOST = settings.DB_HOST
    DB_PORT = str(settings.DB_PORT)
    DB_NAME = settings.DB_NAME
    DB_USER = settings.DB_USER
    DB_PASSWORD = settings.DB_PASSWORD
    JWT_SECRET_KEY = settings.JWT_SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    DEBUG = settings.DEBUG
    
    @classmethod
    def get_db_uri(cls):
        return settings.database_url
