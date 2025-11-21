from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Customer Inquiry App"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Database
    DATABASE_URL: str = "sqlite:///./inquiries.db"
    
    # AI
    GROQ_API_KEY: str = ""
    
    # Vector DB
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "customer-inquiries"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()
