"""
環境設定のテスト
"""

import os
import pytest
from pathlib import Path
from src.utils.config import Settings, Environment


@pytest.fixture
def mock_env(monkeypatch):
    """環境変数のモックを提供"""
    # 既存の環境変数をクリア
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT_NAME", raising=False)
    monkeypatch.delenv("IMAGE_DPI", raising=False)
    monkeypatch.delenv("IMAGE_QUALITY", raising=False)
    monkeypatch.delenv("TEMP_DIR", raising=False)
    return monkeypatch


def test_default_values(mock_env):
    """デフォルト値のテスト"""
    settings = Settings()
    assert settings.ENV == Environment.DEVELOPMENT
    assert settings.LOG_LEVEL == "INFO"
    assert settings.PORT == 8000
    assert settings.IMAGE_DPI == 200
    assert settings.IMAGE_QUALITY == 95
    assert isinstance(settings.get_temp_dir, Path)


def test_environment_variables(mock_env):
    """環境変数からの値読み込みテスト"""
    # 環境変数の設定
    mock_env.setenv("ENV", "production")
    mock_env.setenv("LOG_LEVEL", "DEBUG")
    mock_env.setenv("PORT", "9000")
    mock_env.setenv("IMAGE_DPI", "300")
    mock_env.setenv("IMAGE_QUALITY", "90")
    mock_env.setenv("TEMP_DIR", "/custom/temp")

    # 設定値の検証
    settings = Settings()
    assert settings.ENV == Environment.PRODUCTION
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.PORT == 9000
    assert settings.IMAGE_DPI == 300
    assert settings.IMAGE_QUALITY == 90
    temp_dir = settings.get_temp_dir
    assert isinstance(temp_dir, Path)
    assert temp_dir.name == "temp"
    assert temp_dir.parent.name == "custom"


def test_environment_detection(mock_env):
    """環境判定のテスト"""
    # 開発環境
    mock_env.setenv("ENV", "development")
    settings = Settings()
    assert settings.is_development() is True
    assert settings.is_production() is False

    # 本番環境
    mock_env.setenv("ENV", "production")
    settings = Settings()
    assert settings.is_development() is False
    assert settings.is_production() is True


def test_get_temp_dir(mock_env):
    """一時ディレクトリ取得のテスト"""
    # デフォルトの一時ディレクトリ
    settings = Settings()
    temp_dir = settings.get_temp_dir
    assert isinstance(temp_dir, Path)
    assert temp_dir.name == "temp"

    # カスタムの一時ディレクトリ
    mock_env.setenv("TEMP_DIR", "/custom/temp")
    settings = Settings()
    temp_dir = settings.get_temp_dir
    assert isinstance(temp_dir, Path)
    assert temp_dir.name == "temp"
    assert temp_dir.parent.name == "custom"


def test_validation_development(mock_env):
    """開発環境でのバリデーションテスト"""
    # 開発環境では必須項目が少ない
    mock_env.setenv("ENV", "development")
    settings = Settings()
    assert settings.validate_production() is True


def test_validation_production(mock_env):
    """本番環境でのバリデーションテスト"""
    # 必須項目が不足している場合
    mock_env.setenv("ENV", "production")
    settings = Settings(
        ENV=Environment.PRODUCTION,
        AZURE_OPENAI_API_KEY=None,
        AZURE_OPENAI_ENDPOINT=None,
        AZURE_OPENAI_DEPLOYMENT_NAME=None,
        COSMOS_DB_CONNECTION_STRING=None,
        COSMOS_DB_DATABASE_NAME=None,
        COSMOS_DB_CONTAINER_NAME=None,
    )
    with pytest.raises(ValueError) as exc_info:
        settings.validate_production()
    assert "必須の環境変数が設定されていません" in str(exc_info.value)
    assert "AZURE_OPENAI_API_KEY" in str(exc_info.value)

    # 必須項目がすべて設定されている場合
    settings = Settings(
        ENV=Environment.PRODUCTION,
        AZURE_OPENAI_API_KEY="test-key",
        AZURE_OPENAI_ENDPOINT="test-endpoint",
        AZURE_OPENAI_DEPLOYMENT_NAME="test-deployment",
        COSMOS_DB_CONNECTION_STRING="test-connection",
        COSMOS_DB_DATABASE_NAME="test-db",
        COSMOS_DB_CONTAINER_NAME="test-container",
    )

    # バリデーションを実行
    result = settings.validate_production()
    assert result is True


def test_base_dir():
    """BASE_DIRの設定テスト"""
    settings = Settings()
    assert isinstance(settings.BASE_DIR, Path)
    assert settings.BASE_DIR.exists()
    assert (settings.BASE_DIR / "src").exists()
