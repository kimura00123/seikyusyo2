import os
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from functools import lru_cache

# .envファイルの読み込み
load_dotenv()


class Environment(str, Enum):
    """環境の種類"""

    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # アプリケーション設定
    APP_ENV: str = "development"
    PORT: int = 8000
    
    # ログ設定
    LOG_LEVEL: str = "INFO"
    LOG_DIR: Path = "logs"
    
    # 一時ファイル設定
    TEMP_DIR: Path = "tmp"
    CLEANUP_INTERVAL_SECONDS: int = 3600  # デフォルト: 1時間（3600秒）
    CLEANUP_FILE_AGE_HOURS: int = 24  # デフォルト: 24時間
    
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
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2023-05-15"
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = None

    # CosmosDB設定
    COSMOS_DB_URI: Optional[str] = None
    COSMOS_DB_KEY: Optional[str] = None
    COSMOS_DB_DATABASE_NAME: Optional[str] = None
    COSMOS_DB_CONTAINER_NAME: Optional[str] = None

    # 画像処理設定
    IMAGE_DPI: int = 200
    IMAGE_QUALITY: int = 95

    # ディレクトリ設定
    BASE_DIR: Path = Path(__file__).parent.parent.parent

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

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_prefix": "",
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """設定を取得する（キャッシュ付き）"""
    settings = Settings()
    return settings
