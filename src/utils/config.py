import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()


class Config:
    """環境設定クラス"""

    # 基本設定
    ENV = os.getenv("ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    PORT = int(os.getenv("PORT", "8000"))

    # Azure OpenAI API設定
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    # 画像処理設定
    IMAGE_DPI = int(os.getenv("IMAGE_DPI", "200"))
    IMAGE_QUALITY = int(os.getenv("IMAGE_QUALITY", "95"))

    # ディレクトリ設定
    BASE_DIR = Path(__file__).parent.parent.parent
    TEMP_DIR = os.getenv("TEMP_DIR", str(BASE_DIR / "temp"))

    @classmethod
    def is_development(cls) -> bool:
        """開発環境かどうかを判定する"""
        return cls.ENV.lower() == "development"

    @classmethod
    def is_production(cls) -> bool:
        """本番環境かどうかを判定する"""
        return cls.ENV.lower() == "production"

    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        環境変数の値を取得する

        Args:
            key (str): 環境変数名
            default (Optional[str], optional): デフォルト値

        Returns:
            Optional[str]: 環境変数の値
        """
        return os.getenv(key, default)

    @classmethod
    def get_temp_dir(cls) -> Path:
        """
        一時ディレクトリのパスを取得する

        Returns:
            Path: 一時ディレクトリのパス
        """
        return Path(cls.TEMP_DIR)

    @classmethod
    def validate(cls) -> bool:
        """
        必須の環境変数が設定されているか検証する

        Returns:
            bool: 検証結果
        """
        # 基本設定の検証
        required_vars = []

        # 本番環境の場合はAzure OpenAI APIの設定を検証
        if cls.is_production():
            required_vars.extend(
                [
                    "AZURE_OPENAI_API_KEY",
                    "AZURE_OPENAI_ENDPOINT",
                    "AZURE_OPENAI_DEPLOYMENT_NAME",
                ]
            )

        missing_vars = [var for var in required_vars if not getattr(cls, var)]

        if missing_vars:
            raise ValueError(
                f"必須の環境変数が設定されていません: {', '.join(missing_vars)}"
            )

        return True


# 使用例:
"""
# 環境変数の取得
api_key = Config.AZURE_OPENAI_API_KEY
temp_dir = Config.get_temp_dir()

# 環境の判定
if Config.is_development():
    # 開発環境用の処理
    pass

# 環境変数の検証
try:
    Config.validate()
except ValueError as e:
    print(f"設定エラー: {e}")
"""
