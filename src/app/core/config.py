from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "auction-api"
    app_version: str = "1.0.0"
    build_time: str = ""

    database_url: str
    jwt_secret: str
    jwt_access_expires_min: int = 30
    jwt_refresh_expires_days: int = 14

    cors_origins: str = "http://localhost:3000"
    rate_limit: str = "60/minute"

    class Config:
        env_file = ".env"

settings = Settings()
