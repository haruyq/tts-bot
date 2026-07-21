from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    token: str = "YOUR_BOT_TOKEN"
    tts_base_url: str = "http://localhost:8000"
    tts_password: str = "youshallnotpass"
    default_plugin: str = "voicevox"
    default_speaker: str = "東北きりたん"
    default_style: str = "ノーマル"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file="config/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

@lru_cache
def get_config() -> Config:
    return Config()
