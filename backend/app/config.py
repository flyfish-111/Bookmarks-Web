from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "bookmarks"
    db_password: str = "bookmarks"
    db_name: str = "bookmarks"

    fetch_timeout: float = 15.0
    max_fetch_bytes: int = 10 * 1024 * 1024  # 10MB
    max_redirects: int = 5
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    # JWT 签名密钥：务必在 .env 里设为随机串（openssl rand -hex 32），改它会令所有 token 失效
    secret_key: str = "change_me_secret_key_for_jwt"
    token_expire_minutes: int = 10080  # 7 天
    # 管理员引导：配置后启动时自动创建该账号，并把存量（无归属）数据归入它
    admin_username: str = ""
    admin_password: str = ""

    @field_validator("secret_key")
    @classmethod
    def _secret_key_fallback(cls, v: str) -> str:
        # 防止 docker-compose 把未配置的 SECRET_KEY 传成空串覆盖掉默认值
        return v or "change_me_secret_key_for_jwt"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+asyncmy://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


settings = Settings()
