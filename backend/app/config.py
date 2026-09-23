from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./attune.db"
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://127.0.0.1:8000/auth/callback"
    session_secret: str = "dev-secret-change-me"
    frontend_url: str = "http://127.0.0.1:5173"
    gemini_api_key: str = ""


settings = Settings()
