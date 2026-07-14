from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Saleszy v2 Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = Field(..., description="JWT Secret Key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    ENVIRONMENT: str = "development"
    
    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()