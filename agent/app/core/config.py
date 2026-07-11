# app/core/config.py
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "药店智能客服"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # 数据库
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "pharmacy_db"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+asyncmy://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_EXPIRE_SECONDS: int = 604800

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # LLM
    OPENAI_API_KEY: str = Field(..., alias='DEEPSEEK_API_KEY')
    OPENAI_BASE_URL: str = "https://api.deepseek.com/v1"
    OPENAI_MODEL: str = "deepseek-chat"

    # 智能体
    MAX_HISTORY_MESSAGES: int = 20
    TOKEN_LIMIT: int = 4000
    SESSION_TIMEOUT_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file="configs/.env.dev",      # 指定环境文件
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True
    )


# 全局单例
settings = Settings()