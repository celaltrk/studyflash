from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    supabase_url: str = "https://ayfkizjqgqaskhraxlfl.supabase.co"
    supabase_service_key: str = ""
    anthropic_api_key: str = ""
    ms_tenant_id: str = ""
    ms_client_id: str = ""
    ms_client_secret: str = ""
    ms_shared_mailbox: str = "support@studyflash.ch"
    email_poll_interval_seconds: int = 15

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
