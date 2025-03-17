import os
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()


class Environment(str, Enum):
    """環境の種類"""

    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """環境設定クラス"""

    # 基本設定
    ENV: Environment = Field(
        default_factory=lambda: Environment(os.getenv("ENV", "development"))
    )
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))

    # Azure OpenAI API設定
    AZURE_OPENAI_API_KEY: str = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_API_KEY")
    )
    AZURE_OPENAI_ENDPOINT: str = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    AZURE_OPENAI_API_VERSION: str = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    )
    AZURE_OPENAI_DEPLOYMENT_NAME: str = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    )

    # CosmosDB設定
    COSMOS_DB_CONNECTION_STRING: Optional[str] = None
    COSMOS_DB_DATABASE_NAME: Optional[str] = None
    COSMOS_DB_CONTAINER_NAME: Optional[str] = None

    # 画像処理設定
    IMAGE_DPI: int = Field(default_factory=lambda: int(os.getenv("IMAGE_DPI", "200")))
    IMAGE_QUALITY: int = Field(
        default_factory=lambda: int(os.getenv("IMAGE_QUALITY", "95"))
    )

    # ディレクトリ設定
    BASE_DIR: Path = Field(default=Path(__file__).parent.parent.parent)
    TEMP_DIR: Path = Field(
        default_factory=lambda: (
            Path(os.getenv("TEMP_DIR"))
            if os.getenv("TEMP_DIR")
            else Path(__file__).parent.parent.parent / "temp"
        )
    )

    # ログ関連の設定
    LOG_DIR: str = "logs"
    LOG_FORMAT: Optional[str] = None

    def is_development(self) -> bool:
        """開発環境かどうかを判定する"""
        return self.ENV == Environment.DEVELOPMENT

    def is_production(self) -> bool:
        """本番環境かどうかを判定する"""
        return self.ENV == Environment.PRODUCTION

    @property
    def get_temp_dir(self) -> Path:
        """一時ディレクトリのパスを取得する"""
        if not self.TEMP_DIR.exists():
            self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        return self.TEMP_DIR

    def validate_production(self) -> bool:
        """本番環境用の設定を検証する"""
        if not self.is_production():
            return True

        required_vars = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT_NAME",
            "COSMOS_DB_CONNECTION_STRING",
            "COSMOS_DB_DATABASE_NAME",
            "COSMOS_DB_CONTAINER_NAME",
        ]

        missing_vars = [var for var in required_vars if not getattr(self, var)]

        if missing_vars:
            raise ValueError(
                f"必須の環境変数が設定されていません: {', '.join(missing_vars)}"
            )

        return True

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
