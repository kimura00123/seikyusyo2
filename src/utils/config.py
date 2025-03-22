import os
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from functools import lru_cache

# .envファイルの読み込み
load_dotenv()


class Environment(str, Enum):
    """環境の種類"""

    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Settings(BaseModel):
    # アプリケーション設定
    APP_ENV: str = Field("development", env="APP_ENV")
    PORT: int = Field(8000, env="PORT")
    
    # ログ設定
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_DIR: Path = Field("logs", env="LOG_DIR")
    
    # 一時ファイル設定
    TEMP_DIR: Path = Field("temp", env="TEMP_DIR")
    
    def is_development(self) -> bool:
        """開発環境かどうかを判定する"""
        return self.APP_ENV.lower() == "development"
    
    def is_production(self) -> bool:
        """本番環境かどうかを判定する"""
        return self.APP_ENV.lower() == "production"
    
    def get_temp_dir(self) -> Path:
        """一時ディレクトリのパスを取得（後方互換性のため）"""
        return self.TEMP_DIR

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

    COSMOS_DB_URI: Optional[str] = Field(
        default_factory=lambda: os.getenv("COSMOS_DB_URI")
    )
    COSMOS_DB_KEY: Optional[str] = Field(
        default_factory=lambda: os.getenv("COSMOS_DB_KEY")
    )
    COSMOS_DB_DATABASE_NAME: Optional[str] = Field(
        default_factory=lambda: os.getenv("COSMOS_DB_DATABASE_NAME")
    )
    COSMOS_DB_CONTAINER_NAME: Optional[str] = Field(
        default_factory=lambda: os.getenv("COSMOS_DB_CONTAINER_NAME")
    )

    # 画像処理設定
    IMAGE_DPI: int = Field(default_factory=lambda: int(os.getenv("IMAGE_DPI", "200")))
    IMAGE_QUALITY: int = Field(
        default_factory=lambda: int(os.getenv("IMAGE_QUALITY", "95"))
    )

    # ディレクトリ設定
    BASE_DIR: Path = Field(default=Path(__file__).parent.parent.parent)

    # ログ関連の設定
    LOG_FORMAT: Optional[str] = None

    def validate_production(self) -> bool:
        """本番環境用の設定を検証する"""
        if not self.is_production():
            return True

        required_vars = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT_NAME",
            "COSMOS_DB_URI",
            "COSMOS_DB_KEY",
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

@lru_cache()
def get_settings() -> Settings:
    """設定を取得する（キャッシュ付き）"""
    return Settings()
