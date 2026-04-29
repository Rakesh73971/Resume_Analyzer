from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    gemini_key: str

    
    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

settings = Settings()
